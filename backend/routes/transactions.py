# backend/routes/transactions.py
"""
Multi-party approval transaction routes for LandLock.

Sale flow:
  seller initiates → buyer confirms → chief approves → witness approves → completed
  Any party can reject at their step → rejected

Approval is done via unique codes sent by SMS (Africa's Talking).
All state changes are logged to the immutable transaction_events table.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from db.sqlite_db import db
from utils.approval import (
    find_chief_for_plot,
    generate_approval_code,
    log_transaction_event,
    send_approval_sms,
    verify_event_chain,
)
from utils.notifications import (
    notify_all_parties_completed,
    notify_all_parties_rejected,
    notify_buyer_to_confirm,
    notify_chief_to_approve,
    notify_parties_approved,
    notify_witness_to_approve,
)
from utils.security import token_required

tx_bp = Blueprint("transactions_v2", __name__)


# ──────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────

def _get_user_by_id(user_id):
    rows = db.select("users", eq={"id": user_id})
    return rows[0] if rows else None


def _get_plot_by_id(plot_id):
    rows = db.select("plots", eq={"id": plot_id})
    return rows[0] if rows else None


def _normalize_phone(phone):
    if not phone:
        return ""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+").strip()
    if cleaned.startswith("+265"):
        return "0" + cleaned[4:]
    if cleaned.startswith("265"):
        return "0" + cleaned[3:]
    return cleaned


def _is_fully_approved(tx):
    """Check if all required parties have approved."""
    return (
        tx.get("buyer_approval_status") == "approved"
        and tx.get("chief_approval_status") == "approved"
        and tx.get("witness_approval_status") == "approved"
    )


def _enrich_transaction(tx):
    """Add human-readable names to a transaction dict."""
    enriched = dict(tx)

    # Seller info
    if tx.get("seller_id"):
        seller = _get_user_by_id(tx["seller_id"])
        if seller:
            enriched["seller_name"] = seller.get("full_name", "Unknown")
            enriched["seller_phone"] = seller.get("phone", "")

    # Buyer info
    if tx.get("buyer_id"):
        buyer = _get_user_by_id(tx["buyer_id"])
        if buyer:
            enriched["buyer_name"] = buyer.get("full_name", "Unknown")
            enriched["buyer_phone"] = buyer.get("phone", "")

    # Witness info
    if tx.get("witness_id"):
        witness = _get_user_by_id(tx["witness_id"])
        if witness:
            enriched["witness_name"] = witness.get("full_name", "Unknown")
            enriched["witness_phone"] = witness.get("phone", "")

    # Chief info
    if tx.get("chief_id"):
        chief = _get_user_by_id(tx["chief_id"])
        if chief:
            enriched["chief_name"] = chief.get("full_name", "Unknown")
            enriched["chief_phone"] = chief.get("phone", "")

    # Plot info
    if tx.get("plot_id"):
        plot = _get_plot_by_id(tx["plot_id"])
        if plot:
            enriched["plot_name"] = plot.get("plot_name", "")
            enriched["plot_district"] = plot.get("district", "")
            enriched["plot_village"] = plot.get("village", "")

    return enriched


# ──────────────────────────────────────────────────────
# 1. Initiate a Land Sale
# ──────────────────────────────────────────────────────

@tx_bp.route("/api/transactions/sale", methods=["POST"])
@token_required
def initiate_sale(current_user):
    """
    Seller initiates a land sale transaction.

    Required body:
    {
        "plot_id": <int>,
        "buyer_phone": "<buyer phone number>",
        "witness_phone": "<witness phone number>",
        "amount": <float>,            # optional
        "notes": "<string>"           # optional
    }

    The system will:
    1. Validate the plot belongs to the seller
    2. Verify buyer & witness are registered users
    3. Auto-assign the chief based on plot location
    4. Generate approval codes for chief & witness
    5. Send SMS notifications
    6. Create the transaction in 'pending_buyer' status
    """
    data = request.json
    required = ["plot_id", "buyer_phone", "witness_phone"]
    if not all(k in data for k in required):
        return jsonify({"error": "plot_id, buyer_phone, and witness_phone are required"}), 400

    # ── Validate plot ownership ──
    plot = _get_plot_by_id(data["plot_id"])
    if not plot:
        return jsonify({"error": "Plot not found"}), 404
    if plot["user_id"] != current_user.id:
        return jsonify({"error": "You can only sell plots you own"}), 403
    if plot.get("status") not in ("approved", "verified"):
        return jsonify({"error": "Plot must be approved or verified before selling"}), 400

    # ── Validate buyer ──
    buyer_phone = _normalize_phone(data["buyer_phone"])
    buyer_rows = db.select("users", eq={"phone": buyer_phone})
    if not buyer_rows:
        return jsonify({"error": f"Buyer with phone {buyer_phone} is not registered"}), 404
    buyer = buyer_rows[0]
    if buyer["id"] == current_user.id:
        return jsonify({"error": "You cannot sell land to yourself"}), 400

    # ── Validate witness ──
    witness_phone = _normalize_phone(data["witness_phone"])
    witness_rows = db.select("users", eq={"phone": witness_phone})
    if not witness_rows:
        return jsonify({"error": f"Witness with phone {witness_phone} is not registered"}), 404
    witness = witness_rows[0]
    if witness["id"] == current_user.id:
        return jsonify({"error": "Seller cannot be the witness"}), 400
    if witness["id"] == buyer["id"]:
        return jsonify({"error": "Buyer cannot be the witness"}), 400

    # ── Auto-assign chief ──
    chief_info = find_chief_for_plot(plot)
    if not chief_info:
        return jsonify({
            "error": "No chief assigned to this plot's area. "
                     "Please contact the system administrator to assign a chief for "
                     f"{plot.get('village', '')} / {plot.get('district', '')}."
        }), 400
    if chief_info["chief_id"] == current_user.id:
        return jsonify({"error": "Seller cannot be the approving chief"}), 400

    # ── Generate approval codes ──
    witness_code = generate_approval_code("WIT")
    chief_code = generate_approval_code("CHF")

    # ── Create transaction ──
    now = datetime.now().isoformat()
    tx_data = {
        "user_id": current_user.id,
        "seller_id": current_user.id,
        "buyer_id": buyer["id"],
        "witness_id": witness["id"],
        "chief_id": chief_info["chief_id"],
        "plot_id": data["plot_id"],
        "transaction_type": "sale",
        "counterparty": buyer.get("full_name", ""),
        "amount": data.get("amount", 0),
        "notes": data.get("notes", ""),
        "status": "pending_buyer",
        "buyer_approval_status": "pending",
        "chief_approval_status": "pending",
        "chief_approval_code": chief_code,
        "witness_approval_status": "pending",
        "witness_approval_code": witness_code,
        "created_at": now,
        "updated_at": now,
    }

    tx = db.insert("transactions", tx_data)
    if not tx:
        return jsonify({"error": "Failed to create transaction"}), 500

    # ── Log event: sale initiated ──
    log_transaction_event(
        transaction_id=tx["id"],
        event_type="sale_initiated",
        actor_id=current_user.id,
        actor_role="seller",
        metadata={
            "plot_id": data["plot_id"],
            "buyer_id": buyer["id"],
            "witness_id": witness["id"],
            "chief_id": chief_info["chief_id"],
            "amount": data.get("amount", 0),
        },
    )

    # ── Send SMS notifications ──
    plot_name = plot.get("plot_name", f"Plot #{data['plot_id']}")

    # Notify buyer to confirm
    send_approval_sms(
        buyer["phone"], buyer["full_name"],
        f"BUY-{tx['id']}", plot_name, "buyer"
    )

    # Notify chief
    send_approval_sms(
        chief_info["chief_phone"], chief_info["chief_name"],
        chief_code, plot_name, "chief"
    )

    # Notify witness
    send_approval_sms(
        witness["phone"], witness["full_name"],
        witness_code, plot_name, "witness"
    )

    # ── In-app notification: buyer must confirm ──
    notify_buyer_to_confirm(
        buyer_id=buyer["id"],
        seller_name=current_user.full_name or current_user.username,
        plot_name=plot_name,
        tx_id=tx["id"],
    )

    return jsonify({
        "message": "Sale initiated successfully. Approval codes sent via SMS.",
        "transaction": {
            "id": tx["id"],
            "status": tx["status"],
            "plot_name": plot_name,
            "buyer_name": buyer["full_name"],
            "witness_name": witness["full_name"],
            "chief_name": chief_info["chief_name"],
            "chief_area": chief_info["area_name"],
        },
    }), 201


# ──────────────────────────────────────────────────────
# 2. Buyer Confirms / Accepts the Sale
# ──────────────────────────────────────────────────────

@tx_bp.route("/api/transactions/<int:transaction_id>/buyer-confirm", methods=["POST"])
@token_required
def buyer_confirm(current_user, transaction_id):
    """Buyer confirms they accept the purchase."""
    tx_rows = db.select("transactions", eq={"id": transaction_id})
    if not tx_rows:
        return jsonify({"error": "Transaction not found"}), 404
    tx = tx_rows[0]

    if tx.get("buyer_id") != current_user.id:
        return jsonify({"error": "Only the buyer can confirm this transaction"}), 403
    if tx.get("status") != "pending_buyer":
        return jsonify({"error": f"Transaction is not awaiting buyer confirmation (current: {tx['status']})"}), 400
    if tx.get("buyer_approval_status") == "approved":
        return jsonify({"error": "You have already confirmed this transaction"}), 400

    now = datetime.now().isoformat()
    db.update("transactions", {
        "buyer_approval_status": "approved",
        "buyer_approved_at": now,
        "status": "pending_approvals",
        "updated_at": now,
    }, eq={"id": transaction_id})

    log_transaction_event(
        transaction_id=transaction_id,
        event_type="buyer_confirmed",
        actor_id=current_user.id,
        actor_role="buyer",
    )

    # ── In-app notifications: chief & witness need to approve ──
    enriched = _enrich_transaction(tx)
    notify_chief_to_approve(
        chief_id=tx["chief_id"],
        seller_name=enriched.get("seller_name", "Seller"),
        buyer_name=current_user.full_name or "Buyer",
        plot_name=enriched.get("plot_name", f"Plot #{tx.get('plot_id', '?')}"),
        tx_id=transaction_id,
    )
    notify_witness_to_approve(
        witness_id=tx["witness_id"],
        seller_name=enriched.get("seller_name", "Seller"),
        buyer_name=current_user.full_name or "Buyer",
        plot_name=enriched.get("plot_name", f"Plot #{tx.get('plot_id', '?')}"),
        tx_id=transaction_id,
    )

    return jsonify({"message": "Purchase confirmed. Awaiting chief and witness approval."})


# ──────────────────────────────────────────────────────
# 3. Approve via Approval Code (Chief or Witness)
# ──────────────────────────────────────────────────────

@tx_bp.route("/api/transactions/<int:transaction_id>/approve", methods=["POST"])
@token_required
def approve_transaction(current_user, transaction_id):
    """
    Chief or Witness approves the transaction.

    Two approval modes:
    1. Web dashboard (no code needed) — user is already authenticated;
       identity alone is sufficient since they share credentials across
       USSD and the web system.
    2. SMS / USSD — caller provides { "approval_code": "CHF-XXXXX" }.

    Body (optional): { "approval_code": "CHF-XXXXX" }
    """
    data = request.json or {}
    code = data.get("approval_code", "").strip().upper()

    tx_rows = db.select("transactions", eq={"id": transaction_id})
    if not tx_rows:
        return jsonify({"error": "Transaction not found"}), 404
    tx = tx_rows[0]

    if tx.get("status") not in ("pending_approvals", "pending_buyer"):
        return jsonify({"error": f"Transaction is not awaiting approvals (current: {tx['status']})"}), 400

    now = datetime.now().isoformat()

    # ── Check if chief approving (by identity OR by code) ──
    is_chief = current_user.id == tx.get("chief_id")
    chief_code_match = code and code == tx.get("chief_approval_code") and is_chief

    if is_chief or chief_code_match:
        if not is_chief:
            return jsonify({"error": "Approval code does not match your identity"}), 403
        if tx.get("chief_approval_status") == "approved":
            return jsonify({"error": "Chief has already approved this transaction"}), 400

        db.update("transactions", {
            "chief_approval_status": "approved",
            "chief_approved_at": now,
            "updated_at": now,
        }, eq={"id": transaction_id})

        log_transaction_event(
            transaction_id=transaction_id,
            event_type="chief_approved",
            actor_id=current_user.id,
            actor_role="chief",
            metadata={"method": "code" if code else "web_dashboard"},
        )

        # Notify seller & buyer that chief approved
        tx_updated = db.select("transactions", eq={"id": transaction_id})[0]
        tx_enriched = _enrich_transaction(tx_updated)
        chief_user = _get_user_by_id(current_user.id)
        notify_parties_approved(tx_enriched, chief_user.get("full_name", "Chief"), "chief")

        # Check if all parties have now approved
        if _is_fully_approved(tx_updated):
            _complete_transaction(transaction_id)
            return jsonify({"message": "Chief approved. All approvals received — transaction completed!"})

        return jsonify({"message": "Chief approved successfully. Awaiting remaining approvals."})

    # ── Check if witness approving (by identity OR by code) ──
    is_witness = current_user.id == tx.get("witness_id")
    witness_code_match = code and code == tx.get("witness_approval_code") and is_witness

    if is_witness or witness_code_match:
        if not is_witness:
            return jsonify({"error": "Approval code does not match your identity"}), 403
        if tx.get("witness_approval_status") == "approved":
            return jsonify({"error": "Witness has already approved this transaction"}), 400

        db.update("transactions", {
            "witness_approval_status": "approved",
            "witness_approved_at": now,
            "updated_at": now,
        }, eq={"id": transaction_id})

        log_transaction_event(
            transaction_id=transaction_id,
            event_type="witness_approved",
            actor_id=current_user.id,
            actor_role="witness",
            metadata={"method": "code" if code else "web_dashboard"},
        )

        # Notify seller & buyer that witness approved
        tx_updated = db.select("transactions", eq={"id": transaction_id})[0]
        tx_enriched = _enrich_transaction(tx_updated)
        witness_user = _get_user_by_id(current_user.id)
        notify_parties_approved(tx_enriched, witness_user.get("full_name", "Witness"), "witness")

        if _is_fully_approved(tx_updated):
            _complete_transaction(transaction_id)
            return jsonify({"message": "Witness approved. All approvals received — transaction completed!"})

        return jsonify({"message": "Witness approved successfully. Awaiting remaining approvals."})

    return jsonify({"error": "You are not authorized to approve this transaction. Only the assigned chief or witness can approve."}), 403


# ──────────────────────────────────────────────────────
# 4. Reject via Approval Code (Chief or Witness)
# ──────────────────────────────────────────────────────

@tx_bp.route("/api/transactions/<int:transaction_id>/reject", methods=["POST"])
@token_required
def reject_transaction(current_user, transaction_id):
    """
    Chief, Witness, or Buyer rejects the transaction.

    Web dashboard: no code needed — identity is enough.
    SMS / USSD: { "approval_code": "CHF-XXXXX", "reason": "..." }
    """
    data = request.json or {}
    code = data.get("approval_code", "").strip().upper()
    reason = data.get("reason", "")

    tx_rows = db.select("transactions", eq={"id": transaction_id})
    if not tx_rows:
        return jsonify({"error": "Transaction not found"}), 404
    tx = tx_rows[0]

    if tx.get("status") in ("completed", "rejected", "cancelled"):
        return jsonify({"error": f"Transaction is already {tx['status']}"}), 400

    now = datetime.now().isoformat()
    rejected = False
    role = None

    # Chief rejects (by identity or code)
    if current_user.id == tx.get("chief_id"):
        rejected = True
        role = "chief"
        db.update("transactions", {
            "chief_approval_status": "rejected",
            "updated_at": now,
        }, eq={"id": transaction_id})

    # Witness rejects (by identity or code)
    elif current_user.id == tx.get("witness_id"):
        rejected = True
        role = "witness"
        db.update("transactions", {
            "witness_approval_status": "rejected",
            "updated_at": now,
        }, eq={"id": transaction_id})

    # Buyer rejects (they can cancel before confirming)
    elif current_user.id == tx.get("buyer_id"):
        rejected = True
        role = "buyer"

    # Seller can also cancel before completion
    elif current_user.id == tx.get("seller_id"):
        rejected = True
        role = "seller"

    if not rejected:
        return jsonify({"error": "You are not authorized to reject this transaction"}), 403

    db.update("transactions", {
        "status": "rejected",
        "updated_at": now,
    }, eq={"id": transaction_id})

    log_transaction_event(
        transaction_id=transaction_id,
        event_type=f"{role}_rejected",
        actor_id=current_user.id,
        actor_role=role,
        metadata={"reason": reason, "method": "code" if code else "web_dashboard"},
    )

    # ── In-app notifications: tell all parties about rejection ──
    tx_updated = db.select("transactions", eq={"id": transaction_id})[0]
    tx_enriched = _enrich_transaction(tx_updated)
    notify_all_parties_rejected(tx_enriched, role, reason)

    return jsonify({"message": f"Transaction rejected by {role}."})


# ──────────────────────────────────────────────────────
# 5. Get Transactions Pending My Approval
# ──────────────────────────────────────────────────────

@tx_bp.route("/api/transactions/pending-approvals", methods=["GET"])
@token_required
def get_pending_approvals(current_user):
    """
    Returns all transactions where the current user needs to approve/reject.
    Works for chiefs, witnesses, and buyers with pending actions.
    """
    all_tx = db.select("transactions", order="created_at DESC")

    pending = []
    for tx in all_tx:
        needs_action = False
        my_role = None

        # Chief with pending approval
        if (tx.get("chief_id") == current_user.id
                and tx.get("chief_approval_status") == "pending"
                and tx.get("status") in ("pending_approvals", "pending_buyer")):
            needs_action = True
            my_role = "chief"

        # Witness with pending approval
        elif (tx.get("witness_id") == current_user.id
              and tx.get("witness_approval_status") == "pending"
              and tx.get("status") in ("pending_approvals", "pending_buyer")):
            needs_action = True
            my_role = "witness"

        # Buyer who hasn't confirmed yet
        elif (tx.get("buyer_id") == current_user.id
              and tx.get("buyer_approval_status") == "pending"
              and tx.get("status") == "pending_buyer"):
            needs_action = True
            my_role = "buyer"

        if needs_action:
            enriched = _enrich_transaction(tx)
            enriched["my_role"] = my_role
            # Only expose the code to the rightful approver
            if my_role == "chief":
                enriched["my_approval_code"] = tx.get("chief_approval_code")
            elif my_role == "witness":
                enriched["my_approval_code"] = tx.get("witness_approval_code")
            pending.append(enriched)

    return jsonify(pending)


# ──────────────────────────────────────────────────────
# 6. Get Single Transaction Detail (with audit trail)
# ──────────────────────────────────────────────────────

@tx_bp.route("/api/transactions/<int:transaction_id>", methods=["GET"])
@token_required
def get_transaction_detail(current_user, transaction_id):
    """Get full transaction detail including the immutable audit trail."""
    tx_rows = db.select("transactions", eq={"id": transaction_id})
    if not tx_rows:
        return jsonify({"error": "Transaction not found"}), 404
    tx = tx_rows[0]

    # Access control: only involved parties or admins can view
    allowed_ids = {
        tx.get("seller_id"), tx.get("buyer_id"),
        tx.get("witness_id"), tx.get("chief_id"),
    }
    if current_user.id not in allowed_ids and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized"}), 403

    enriched = _enrich_transaction(tx)

    # Get audit trail
    events = db.select(
        "transaction_events",
        eq={"transaction_id": transaction_id},
        order="id ASC",
    )
    import json
    for event in events:
        if isinstance(event.get("metadata"), str):
            try:
                event["metadata"] = json.loads(event["metadata"])
            except Exception:
                event["metadata"] = {}
        # Attach actor name
        if event.get("actor_id"):
            actor = _get_user_by_id(event["actor_id"])
            event["actor_name"] = actor.get("full_name", "Unknown") if actor else "Unknown"

    # Verify chain integrity
    chain_status = verify_event_chain(transaction_id)

    enriched["events"] = events
    enriched["audit_chain_valid"] = chain_status["valid"]

    return jsonify(enriched)


# ──────────────────────────────────────────────────────
# 7. Get My Transactions (seller + buyer combined)
# ──────────────────────────────────────────────────────

@tx_bp.route("/api/transactions/my", methods=["GET"])
@token_required
def get_my_transactions(current_user):
    """Get all transactions where the current user is any party."""
    all_tx = db.select("transactions", order="created_at DESC")

    mine = []
    for tx in all_tx:
        involved = (
            tx.get("seller_id") == current_user.id
            or tx.get("buyer_id") == current_user.id
            or tx.get("witness_id") == current_user.id
            or tx.get("chief_id") == current_user.id
        )
        if involved:
            enriched = _enrich_transaction(tx)
            # Determine my role in this transaction
            if tx.get("seller_id") == current_user.id:
                enriched["my_role"] = "seller"
            elif tx.get("buyer_id") == current_user.id:
                enriched["my_role"] = "buyer"
            elif tx.get("witness_id") == current_user.id:
                enriched["my_role"] = "witness"
            elif tx.get("chief_id") == current_user.id:
                enriched["my_role"] = "chief"
            mine.append(enriched)

    return jsonify(mine)


# ──────────────────────────────────────────────────────
# 8. Verify Audit Chain Integrity (standalone)
# ──────────────────────────────────────────────────────

@tx_bp.route("/api/transactions/<int:transaction_id>/verify-chain", methods=["GET"])
@token_required
def verify_chain(current_user, transaction_id):
    """Verify the tamper-evident hash chain for a transaction."""
    tx_rows = db.select("transactions", eq={"id": transaction_id})
    if not tx_rows:
        return jsonify({"error": "Transaction not found"}), 404

    result = verify_event_chain(transaction_id)
    return jsonify({
        "transaction_id": transaction_id,
        "chain_valid": result["valid"],
        "broken_at_event_id": result["broken_at"],
    })


# ──────────────────────────────────────────────────────
# Internal: Complete a fully-approved transaction
# ──────────────────────────────────────────────────────

def _complete_transaction(transaction_id: int):
    """
    Called when all parties (buyer, chief, witness) have approved.
    Transfers plot ownership and marks transaction as completed.
    """
    tx = db.select("transactions", eq={"id": transaction_id})[0]
    now = datetime.now().isoformat()

    # Transfer plot ownership to buyer
    db.update("plots", {
        "user_id": tx["buyer_id"],
        "updated_at": now,
    }, eq={"id": tx["plot_id"]})

    # Mark transaction as completed
    db.update("transactions", {
        "status": "completed",
        "updated_at": now,
    }, eq={"id": transaction_id})

    # Log the completion event
    log_transaction_event(
        transaction_id=transaction_id,
        event_type="completed",
        actor_id=None,
        actor_role="system",
        metadata={
            "ownership_transferred_to": tx["buyer_id"],
            "plot_id": tx["plot_id"],
            "previous_owner": tx["seller_id"],
        },
    )

    # ── In-app notifications: tell all parties the deal is done ──
    tx_enriched = _enrich_transaction(tx)
    tx_enriched["buyer_name"] = tx_enriched.get("buyer_name", "the buyer")
    notify_all_parties_completed(tx_enriched)
