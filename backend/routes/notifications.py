# backend/routes/notifications.py
"""
Notification API endpoints for LandLock.

Provides:
  GET  /api/notifications          — fetch user notifications + unread count
  POST /api/notifications/<id>/read — mark single notification as read
  POST /api/notifications/read-all  — mark all as read
"""

from flask import Blueprint, jsonify, request
from utils.security import token_required
from utils.notifications import (
    get_user_notifications,
    get_unread_count,
    mark_read,
    mark_all_read,
)

notif_bp = Blueprint("notifications", __name__)


@notif_bp.route("/api/notifications", methods=["GET"])
@token_required
def list_notifications(current_user):
    """Return the current user's notifications and unread count."""
    notifications = get_user_notifications(current_user.id)
    unread = get_unread_count(current_user.id)
    return jsonify({
        "notifications": notifications,
        "unread_count": unread,
    })


@notif_bp.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
@token_required
def mark_notification_read(current_user, notification_id):
    """Mark a single notification as read."""
    mark_read(notification_id, current_user.id)
    return jsonify({"ok": True})


@notif_bp.route("/api/notifications/read-all", methods=["POST"])
@token_required
def mark_all_notifications_read(current_user):
    """Mark all of the current user's notifications as read."""
    mark_all_read(current_user.id)
    return jsonify({"ok": True})


@notif_bp.route("/api/notifications/unread-count", methods=["GET"])
@token_required
def unread_notification_count(current_user):
    """Lightweight endpoint — just returns the unread count."""
    count = get_unread_count(current_user.id)
    return jsonify({"unread_count": count})
