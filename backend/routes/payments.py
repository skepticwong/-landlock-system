# backend/routes/payments.py
"""
Payment routes for LandLock system.

This module provides mock payment processing for:
- Land registration fees
- Land transfer fees
- Plot verification fees
- Certificate issuance fees
"""

from flask import Blueprint, request, jsonify
from utils.security import token_required
from db.sqlite_db import db
from datetime import datetime
from models.payment import Payment, get_fee_for_service
import random

payments_bp = Blueprint('payments', __name__)

# Mock payment methods available
PAYMENT_METHODS = [
    'airtel_money',
    'tnm_mpamba',
    'bank_card',
    'cash'
]

# ──────────────────────────────────────────────────────
# Payment Processing (Mock)
# ──────────────────────────────────────────────────────

@payments_bp.route("/api/payments/initiate", methods=["POST"])
@token_required
def initiate_payment(current_user):
    """
    Initiate a payment (mock).
    
    Required body:
    {
        "payment_type": "land_registration" | "land_transfer" | "plot_verification" | "certificate_issuance",
        "payment_method": "airtel_money" | "tnm_mpamba" | "bank_card" | "cash",
        "plot_id": <int>,  # Optional, for registration/verification
        "transaction_id": <int>,  # Optional, for land transfers
        "phone_number": "<phone number>",  # For mobile money
        "card_number": "<card number>",  # For bank cards (mock)
        "card_expiry": "<MM/YY>",  # For bank cards (mock)
        "card_cvv": "<CVV>"  # For bank cards (mock)
    }
    
    Returns:
    {
        "payment_id": <int>,
        "amount": <float>,
        "currency": "MWK",
        "status": "pending",
        "payment_reference": "<mock_reference>"
    }
    """
    data = request.json
    required_fields = ['payment_type', 'payment_method']
    
    if not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    if data['payment_type'] not in ['land_registration', 'land_transfer', 'plot_verification', 'certificate_issuance']:
        return jsonify({"error": "Invalid payment type"}), 400
    
    if data['payment_method'] not in PAYMENT_METHODS:
        return jsonify({"error": "Invalid payment method"}), 400
    
    # Get fee for the service
    fee_info = get_fee_for_service(data['payment_type'])
    
    # Validate required fields based on payment method
    if data['payment_method'] in ['airtel_money', 'tnm_mpamba']:
        if 'phone_number' not in data:
            return jsonify({"error": "Phone number required for mobile money"}), 400
    elif data['payment_method'] == 'bank_card':
        if not all(k in data for k in ['card_number', 'card_expiry', 'card_cvv']):
            return jsonify({"error": "Card details required for bank card payment"}), 400
    
    # Create payment record
    payment_data = {
        'user_id': current_user.id,
        'payment_type': data['payment_type'],
        'payment_method': data['payment_method'],
        'amount': fee_info['amount'],
        'currency': 'MWK',
        'status': 'pending',
        'description': fee_info['description'],
        'plot_id': data.get('plot_id'),
        'transaction_id': data.get('transaction_id'),
        'payment_reference': f"MOCK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
    }
    
    payment = Payment.create(payment_data)
    
    if payment:
        return jsonify({
            "payment_id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "payment_reference": payment.payment_reference,
            "description": payment.description
        }), 201
    else:
        return jsonify({"error": "Failed to create payment"}), 500


@payments_bp.route("/api/payments/<int:payment_id>/confirm", methods=["POST"])
@token_required
def confirm_payment(current_user, payment_id):
    """
    Confirm/complete a payment (mock).
    
    This simulates the callback from a payment gateway.
    In production, this would be called by the payment gateway.
    """
    payment = Payment.get_by_id(payment_id)
    
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    
    if payment.user_id != current_user.id and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized"}), 403
    
    if payment.status == 'completed':
        return jsonify({"error": "Payment already completed"}), 400
    
    # Mock payment processing - always succeed
    success = payment.update_status('completed', payment.payment_reference)
    
    if success:
        return jsonify({
            "message": "Payment completed successfully",
            "payment": payment.to_dict()
        })
    else:
        return jsonify({"error": "Failed to complete payment"}), 500


@payments_bp.route("/api/payments/<int:payment_id>/cancel", methods=["POST"])
@token_required
def cancel_payment(current_user, payment_id):
    """
    Cancel a pending payment.
    """
    payment = Payment.get_by_id(payment_id)
    
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    
    if payment.user_id != current_user.id and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized"}), 403
    
    if payment.status != 'pending':
        return jsonify({"error": "Can only cancel pending payments"}), 400
    
    success = payment.update_status('failed')
    
    if success:
        return jsonify({
            "message": "Payment cancelled successfully",
            "payment": payment.to_dict()
        })
    else:
        return jsonify({"error": "Failed to cancel payment"}), 500


@payments_bp.route("/api/payments/<int:payment_id>", methods=["GET"])
@token_required
def get_payment(current_user, payment_id):
    """
    Get payment details.
    """
    payment = Payment.get_by_id(payment_id)
    
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    
    if payment.user_id != current_user.id and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized"}), 403
    
    return jsonify(payment.to_dict())


@payments_bp.route("/api/payments/user", methods=["GET"])
@token_required
def get_user_payments(current_user):
    """
    Get all payments for the current user.
    """
    payments = Payment.get_by_user(current_user.id)
    return jsonify([p.to_dict() for p in payments])


@payments_bp.route("/api/payments/fees", methods=["GET"])
def get_fee_structure():
    """
    Get the fee structure for all services.
    """
    from models.payment import FEE_STRUCTURE
    return jsonify(FEE_STRUCTURE)


@payments_bp.route("/api/payments/methods", methods=["GET"])
def get_payment_methods():
    """
    Get available payment methods.
    """
    return jsonify(PAYMENT_METHODS)


# ──────────────────────────────────────────────────────
# Admin Payment Routes
# ──────────────────────────────────────────────────────

@payments_bp.route("/api/payments/admin/all", methods=["GET"])
@token_required
def get_all_payments(current_user):
    """
    Get all payments (admin only).
    """
    if not current_user.is_superuser and current_user.role != 'official':
        return jsonify({"error": "Unauthorized"}), 403
    
    payments = db.select("payments", order="created_at DESC")
    return jsonify(payments)


@payments_bp.route("/api/payments/admin/stats", methods=["GET"])
@token_required
def get_payment_stats(current_user):
    """
    Get payment statistics (admin only).
    """
    if not current_user.is_superuser and current_user.role != 'official':
        return jsonify({"error": "Unauthorized"}), 403
    
    payments = db.select("payments")
    
    total_revenue = sum(p.get('amount', 0) for p in payments if p.get('status') == 'completed')
    total_transactions = len(payments)
    completed_transactions = len([p for p in payments if p.get('status') == 'completed'])
    pending_transactions = len([p for p in payments if p.get('status') == 'pending'])
    
    # Revenue by payment type
    revenue_by_type = {}
    for p in payments:
        if p.get('status') == 'completed':
            ptype = p.get('payment_type', 'unknown')
            revenue_by_type[ptype] = revenue_by_type.get(ptype, 0) + p.get('amount', 0)
    
    return jsonify({
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "completed_transactions": completed_transactions,
        "pending_transactions": pending_transactions,
        "revenue_by_type": revenue_by_type
    })
