from flask import Blueprint, request, jsonify
from db.sqlite_db import db
from utils.approval import (
    log_transaction_event,
    verify_event_chain,
)
from utils.notifications import (
    notify_parties_approved,
    notify_all_parties_completed,
    notify_all_parties_rejected,
)
from datetime import datetime

ussd_bp = Blueprint('ussd', __name__)


def _normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+").strip()
    if cleaned.startswith('+265'):
        return '0' + cleaned[4:]
    if cleaned.startswith('265'):
        return '0' + cleaned[3:]
    return cleaned


@ussd_bp.route('/api/ussd', methods=['POST'])
def handle_ussd():
    """Basic USSD receiver stub for testing.

    Expected JSON body (provider-like):
    {
      "sessionId": "abc123",
      "phoneNumber": "+265991234567",
      "text": "APPROVE CHF-ABCD1"
    }
    """
    data = request.json or {}
    phone = _normalize_phone(data.get('phoneNumber') or data.get('phone') or '')
    text = (data.get('text') or '').strip()

    if not phone or not text:
        return jsonify({"error": "phoneNumber and text required"}), 400

    # Normalize input
    text_up = text.upper()

    # Extract approval code token
    import re
    m = re.search(r"(CHF|WIT|BUY)-[A-Z0-9]+", text_up)
    if not m:
        return jsonify({"message": "Enter a valid approval code (e.g. CHF-XXXXX)"}), 200

    code = m.group(0)

    # Find transaction by code
    tx = None
    # chief
    rows = db.select('transactions', eq={'chief_approval_code': code})
    if rows:
        tx = rows[0]
        role = 'chief'
    else:
        rows = db.select('transactions', eq={'witness_approval_code': code})
        if rows:
            tx = rows[0]
            role = 'witness'
        else:
            # buyer confirmation codes use pattern BUY-<txid>
            rows = db.select('transactions', eq={'id': int(code.split('-')[-1])}) if code.startswith('BUY-') and code.split('-')[-1].isdigit() else []
            if rows:
                tx = rows[0]
                role = 'buyer'

    if not tx:
        return jsonify({"message": "Approval code not found or expired."}), 200

    # Find user by phone
    users = db.select('users', eq={'phone': phone})
    user = users[0] if users else None
    if not user:
        return jsonify({"message": "Phone number not registered with LandLock."}), 200

    now = datetime.now().isoformat()

    # Authorize based on role
    tx_id = tx['id']
    if role == 'chief':
        if user['id'] != tx.get('chief_id'):
            return jsonify({"message": "You are not assigned as the chief for this approval."}), 200
        if tx.get('chief_approval_status') == 'approved':
            return jsonify({"message": "Already approved."}), 200
        db.update('transactions', {'chief_approval_status': 'approved', 'chief_approved_at': now, 'updated_at': now}, eq={'id': tx_id})
        log_transaction_event(transaction_id=tx_id, event_type='chief_approved', actor_id=user['id'], actor_role='chief')
    elif role == 'witness':
        if user['id'] != tx.get('witness_id'):
            return jsonify({"message": "You are not assigned as the witness for this approval."}), 200
        if tx.get('witness_approval_status') == 'approved':
            return jsonify({"message": "Already approved."}), 200
        db.update('transactions', {'witness_approval_status': 'approved', 'witness_approved_at': now, 'updated_at': now}, eq={'id': tx_id})
        log_transaction_event(transaction_id=tx_id, event_type='witness_approved', actor_id=user['id'], actor_role='witness')
    elif role == 'buyer':
        if user['id'] != tx.get('buyer_id'):
            return jsonify({"message": "You are not the buyer for this transaction."}), 200
        if tx.get('buyer_approval_status') == 'approved':
            return jsonify({"message": "Already confirmed."}), 200
        db.update('transactions', {'buyer_approval_status': 'approved', 'buyer_approved_at': now, 'status': 'pending_approvals', 'updated_at': now}, eq={'id': tx_id})
        log_transaction_event(transaction_id=tx_id, event_type='buyer_confirmed', actor_id=user['id'], actor_role='buyer')

    # Refresh tx
    tx_updated = db.select('transactions', eq={'id': tx_id})[0]

    # If fully approved, complete it
    if tx_updated.get('buyer_approval_status') == 'approved' and tx_updated.get('chief_approval_status') == 'approved' and tx_updated.get('witness_approval_status') == 'approved':
        # mark completed
        db.update('transactions', {'status': 'completed', 'updated_at': now}, eq={'id': tx_id})
        log_transaction_event(transaction_id=tx_id, event_type='transaction_completed', actor_id=user['id'], actor_role=role)
        tx_final = db.select('transactions', eq={'id': tx_id})[0]
        notify_all_parties_completed(tx_final)
        return jsonify({"message": "All approvals received — transaction completed."}), 200

    # Notify parties about approval
    enriched = tx_updated
    actor_name = user.get('full_name') or user.get('username')
    notify_parties_approved(enriched, actor_name, role)

    return jsonify({"message": f"{role.title()} approval recorded. Thank you, {actor_name}."}), 200
