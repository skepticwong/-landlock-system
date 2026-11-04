# backend/utils/approval.py
"""
Approval code generation, event logging (immutable audit trail),
and SMS notification stubs for LandLock multi-party sale approvals.
"""

import hashlib
import json
import random
import string
from datetime import datetime

from db.sqlite_db import db


# ──────────────────────────────────────────────────────
# Approval Code Generation
# ──────────────────────────────────────────────────────

def generate_approval_code(prefix: str = "APR") -> str:
    """
    Generate a unique, human-readable approval code.
    Format: APR-7X3K9  (prefix + 5 alphanumeric chars)
    """
    chars = string.ascii_uppercase + string.digits
    # Avoid ambiguous characters (0/O, 1/I/L)
    safe_chars = "".join(c for c in chars if c not in "0O1IL")
    code = "".join(random.choices(safe_chars, k=5))
    return f"{prefix}-{code}"


# ──────────────────────────────────────────────────────
# Immutable Audit Trail (transaction_events)
# ──────────────────────────────────────────────────────

def _compute_event_hash(transaction_id: int, event_type: str, actor_id: int,
                        metadata: str, previous_hash: str, created_at: str) -> str:
    """Compute SHA-256 hash for an event (tamper-evident chain)."""
    raw = f"{transaction_id}|{event_type}|{actor_id}|{metadata}|{previous_hash}|{created_at}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def log_transaction_event(transaction_id: int, event_type: str,
                          actor_id: int = None, actor_role: str = None,
                          metadata: dict = None) -> dict:
    """
    Append a new event to the immutable transaction_events table.
    Each event stores a hash of itself AND the previous event's hash,
    forming a tamper-evident chain (like a mini blockchain).
    """
    now = datetime.now().isoformat()
    meta_json = json.dumps(metadata or {})

    # Get the previous event's hash for this transaction
    prev_events = db.select(
        "transaction_events",
        eq={"transaction_id": transaction_id},
        order="id DESC"
    )
    previous_hash = prev_events[0]["event_hash"] if prev_events else "GENESIS"

    event_hash = _compute_event_hash(
        transaction_id, event_type, actor_id, meta_json, previous_hash, now
    )

    event_data = {
        "transaction_id": transaction_id,
        "event_type": event_type,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "metadata": meta_json,
        "previous_event_hash": previous_hash,
        "event_hash": event_hash,
        "created_at": now,
    }

    result = db.insert("transaction_events", event_data)
    return result


def verify_event_chain(transaction_id: int) -> dict:
    """
    Verify the integrity of the event chain for a transaction.
    Returns {"valid": True/False, "broken_at": event_id or None}.
    """
    events = db.select(
        "transaction_events",
        eq={"transaction_id": transaction_id},
        order="id ASC"
    )

    previous_hash = "GENESIS"
    for event in events:
        expected_hash = _compute_event_hash(
            event["transaction_id"],
            event["event_type"],
            event["actor_id"],
            event["metadata"],
            previous_hash,
            event["created_at"]
        )
        if expected_hash != event["event_hash"]:
            return {"valid": False, "broken_at": event["id"]}
        previous_hash = event["event_hash"]

    return {"valid": True, "broken_at": None}


# ──────────────────────────────────────────────────────
# SMS Notification (stub — ready for Africa's Talking)
# ──────────────────────────────────────────────────────

def send_approval_sms(phone: str, full_name: str, approval_code: str,
                      plot_name: str, role: str) -> bool:
    """
    Send an SMS notification with the approval code.

    In production, this calls the Africa's Talking SMS API.
    For now it logs the message and returns True.
    """
    message = (
        f"LandLock: {role.upper()} approval required for land sale.\n"
        f"Plot: {plot_name}\n"
        f"Your approval code: {approval_code}\n\n"
        f"To APPROVE: Reply 'APPROVE {approval_code}'\n"
        f"To REJECT: Reply 'REJECT {approval_code}'\n\n"
        f"Or approve via USSD: dial *384# and enter the code.\n"
        f"- LandLock Malawi"
    )

    # ── Africa's Talking integration point ──
    # Uncomment and configure when API key is available:
    #
    # import africastalking
    # africastalking.initialize(username, api_key)
    # sms = africastalking.SMS
    # response = sms.send(message, [phone])
    # return response is not None

    # Use sms service abstraction (mock or real provider)
    try:
        from utils.sms_service import send_sms
    except Exception:
        # best-effort import fallback
        def send_sms(p, m):
            print(f"[SMS FALLBACK] To: {p}")
            print(m)
            return True

    sent = send_sms(phone, message)
    return bool(sent)


# ──────────────────────────────────────────────────────
# Chief Auto-Assignment
# ──────────────────────────────────────────────────────

def find_chief_for_plot(plot: dict) -> dict | None:
    """
    Given a plot dict (with district/traditional_authority/village),
    find the assigned chief from the chief_areas table.

    Priority: village > traditional_authority > district (most specific wins).
    """
    from models.chief_area import ChiefArea

    all_areas = db.select("chief_areas")
    if not all_areas:
        return None

    plot_district = (plot.get("district") or "").lower()
    plot_ta = (plot.get("traditional_authority") or "").lower()
    plot_village = (plot.get("village") or "").lower()

    best_match = None
    best_specificity = 0  # village=3, TA=2, district=1

    for area_data in all_areas:
        chief_area = ChiefArea(**area_data)

        if chief_area.area_type == "village" and plot_village:
            if (plot_village == (chief_area.area_id or "").lower()
                    or plot_village in (chief_area.area_name or "").lower()):
                if best_specificity < 3:
                    best_match = area_data
                    best_specificity = 3

        elif chief_area.area_type == "traditional_authority" and plot_ta:
            if (plot_ta == (chief_area.area_id or "").lower()
                    or plot_ta in (chief_area.area_name or "").lower()):
                if best_specificity < 2:
                    best_match = area_data
                    best_specificity = 2

        elif chief_area.area_type == "district" and plot_district:
            if (plot_district == (chief_area.area_id or "").lower()
                    or plot_district in (chief_area.area_name or "").lower()):
                if best_specificity < 1:
                    best_match = area_data
                    best_specificity = 1

    if best_match:
        # Fetch the chief user record
        chief_user = db.select("users", eq={"id": best_match["chief_id"]})
        if chief_user:
            return {
                "chief_id": best_match["chief_id"],
                "chief_name": chief_user[0].get("full_name", "Unknown"),
                "chief_phone": chief_user[0].get("phone", ""),
                "area_name": best_match.get("area_name", ""),
            }

    return None
