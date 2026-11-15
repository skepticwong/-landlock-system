import os
import sqlite3
import uuid
from datetime import datetime
from io import BytesIO

from cryptography.fernet import Fernet, InvalidToken
from flask import Blueprint, jsonify, request, send_file

from config import config
from db.sqlite_db import db
from utils.security import admin_required, token_required

identity_bp = Blueprint("identity", __name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
PRIVATE_IDENTITY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "private_uploads",
    "identity",
)


def _cipher():
    key = config.IDENTITY_DOCUMENT_ENCRYPTION_KEY
    if not key:
        return None
    try:
        return Fernet(key.encode("ascii"))
    except (UnicodeEncodeError, ValueError):
        return None


def _read_image(upload):
    content = upload.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        return None, None, "Each ID image must be 5 MB or smaller."

    if content.startswith(b"\xff\xd8\xff"):
        mime_type = "image/jpeg"
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
    elif len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        mime_type = "image/webp"
    else:
        return None, None, "Upload a valid JPEG, PNG, or WebP image."

    return content, mime_type, None


def _save_encrypted_image(cipher, content):
    os.makedirs(PRIVATE_IDENTITY_DIR, mode=0o700, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.enc"
    path = os.path.join(PRIVATE_IDENTITY_DIR, filename)
    with open(path, "xb") as image_file:
        image_file.write(cipher.encrypt(content))
    return path


def _remove_file(path):
    if path and os.path.exists(path):
        os.remove(path)


@identity_bp.route("/api/user/me/identity-verification", methods=["POST"])
@token_required
def submit_identity_verification(current_user):
    if current_user.is_superuser:
        return jsonify({"error": "Administrator accounts do not require identity verification."}), 403

    national_id = (request.form.get("national_id") or "").strip()
    front_upload = request.files.get("front")
    back_upload = request.files.get("back")
    if not national_id or len(national_id) > 64 or not front_upload or not back_upload:
        return jsonify({"error": "National ID number and both ID images are required."}), 400

    if current_user.identity_status == "verified":
        return jsonify({"error": "Your identity is already verified. Contact an administrator if it needs correction."}), 409

    cipher = _cipher()
    if not cipher:
        return jsonify({"error": "Identity document encryption is not configured on the server."}), 503

    front_content, front_mime, front_error = _read_image(front_upload)
    if front_error:
        return jsonify({"error": f"Front image: {front_error}"}), 400
    back_content, back_mime, back_error = _read_image(back_upload)
    if back_error:
        return jsonify({"error": f"Back image: {back_error}"}), 400

    front_path = None
    back_path = None
    try:
        front_path = _save_encrypted_image(cipher, front_content)
        back_path = _save_encrypted_image(cipher, back_content)
    except OSError:
        _remove_file(front_path)
        _remove_file(back_path)
        return jsonify({"error": "Could not securely save the ID images."}), 500

    now = datetime.now().isoformat()
    try:
        submission = db.insert("identity_verifications", {
            "user_id": current_user.id,
            "national_id_encrypted": cipher.encrypt(national_id.encode("utf-8")).decode("ascii"),
            "front_path": front_path,
            "front_mime": front_mime,
            "back_path": back_path,
            "back_mime": back_mime,
            "status": "pending",
            "submitted_at": now,
        })
    except sqlite3.Error:
        _remove_file(front_path)
        _remove_file(back_path)
        raise

    previous_pending = db.select(
        "identity_verifications",
        eq={"user_id": current_user.id, "status": "pending"},
        order="id DESC",
    )
    for previous in previous_pending:
        if previous["id"] != submission["id"]:
            db.update(
                "identity_verifications",
                {"status": "superseded"},
                eq={"id": previous["id"]},
            )

    db.update("users", {"identity_status": "pending", "updated_at": now}, eq={"id": current_user.id})
    return jsonify({
        "message": "ID submitted for administrator review.",
        "identity_status": "pending",
    }), 201


@identity_bp.route("/api/admin/identity-verifications", methods=["GET"])
@admin_required
def list_pending_identity_verifications(current_user):
    cipher = _cipher()
    if not cipher:
        return jsonify({"error": "Identity document encryption is not configured on the server."}), 503

    submissions = db.select(
        "identity_verifications",
        eq={"status": "pending"},
        order="submitted_at ASC",
    )
    pending = []
    for submission in submissions:
        user_rows = db.select("users", eq={"id": submission["user_id"]})
        if not user_rows or user_rows[0].get("is_superuser"):
            continue
        try:
            national_id = cipher.decrypt(
                submission["national_id_encrypted"].encode("ascii")
            ).decode("utf-8")
        except InvalidToken:
            return jsonify({"error": f"Could not decrypt ID for submission {submission['id']}."}), 500
        user = user_rows[0]
        pending.append({
            "id": submission["id"],
            "user": {
                "id": user["id"],
                "full_name": user.get("full_name"),
                "username": user.get("username"),
                "phone": user.get("phone"),
                "email": user.get("email"),
                "role": user.get("role", "citizen"),
            },
            "national_id": national_id,
            "submitted_at": submission["submitted_at"],
        })
    return jsonify(pending)


@identity_bp.route(
    "/api/admin/identity-verifications/<int:submission_id>/documents/<side>",
    methods=["GET"],
)
@admin_required
def get_identity_document(current_user, submission_id, side):
    if side not in ("front", "back"):
        return jsonify({"error": "Document side must be 'front' or 'back'."}), 400

    cipher = _cipher()
    if not cipher:
        return jsonify({"error": "Identity document encryption is not configured on the server."}), 503

    submissions = db.select("identity_verifications", eq={"id": submission_id})
    if not submissions:
        return jsonify({"error": "Identity submission not found."}), 404

    submission = submissions[0]
    path_key = f"{side}_path"
    mime_key = f"{side}_mime"
    if not os.path.isfile(submission[path_key]):
        return jsonify({"error": "Identity document file is missing."}), 404

    try:
        with open(submission[path_key], "rb") as image_file:
            image_data = cipher.decrypt(image_file.read())
    except (OSError, InvalidToken):
        return jsonify({"error": "Could not read the encrypted identity document."}), 500

    return send_file(
        BytesIO(image_data),
        mimetype=submission[mime_key],
        as_attachment=True,
        download_name=f"identity-{side}",
        max_age=0,
    )


@identity_bp.route(
    "/api/admin/identity-verifications/<int:submission_id>/review",
    methods=["POST"],
)
@admin_required
def review_identity_verification(current_user, submission_id):
    data = request.get_json(silent=True) or {}
    decision = data.get("decision")
    reason = (data.get("reason") or "").strip()
    if decision not in ("verified", "rejected"):
        return jsonify({"error": "Decision must be 'verified' or 'rejected'."}), 400
    if decision == "rejected" and not reason:
        return jsonify({"error": "A reason is required when rejecting an ID."}), 400

    submissions = db.select("identity_verifications", eq={"id": submission_id})
    if not submissions:
        return jsonify({"error": "Identity submission not found."}), 404
    submission = submissions[0]
    if submission["status"] != "pending":
        return jsonify({"error": "This ID submission has already been reviewed."}), 409

    latest = db.select(
        "identity_verifications",
        eq={"user_id": submission["user_id"]},
        order="id DESC",
    )
    if not latest or latest[0]["id"] != submission_id:
        return jsonify({"error": "A newer ID submission must be reviewed instead."}), 409

    now = datetime.now().isoformat()
    db.update("identity_verifications", {
        "status": decision,
        "reviewed_at": now,
        "reviewed_by": current_user.id,
        "review_reason": reason or None,
    }, eq={"id": submission_id})
    db.update("users", {
        "identity_status": decision,
        "updated_at": now,
    }, eq={"id": submission["user_id"]})

    return jsonify({
        "message": f"Identity verification {decision}.",
        "identity_status": decision,
    })
