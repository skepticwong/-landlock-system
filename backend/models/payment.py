# backend/models/payment.py
"""
Payment model for LandLock system.

Handles payment records for various land-related services:
- Land registration fees
- Land transfer fees
- Plot verification fees
- Certificate issuance fees
"""

from datetime import datetime
from db.sqlite_db import db

class Payment:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.transaction_id = kwargs.get('transaction_id')  # For land sales
        self.plot_id = kwargs.get('plot_id')  # For registration/verification
        self.payment_type = kwargs.get('payment_type')  # registration, transfer, verification, certificate
        self.amount = kwargs.get('amount')
        self.currency = kwargs.get('currency', 'MWK')
        self.status = kwargs.get('status', 'pending')  # pending, completed, failed, refunded
        self.payment_method = kwargs.get('payment_method')  # airtel_money, tnm_mpamba, bank_card, cash
        self.payment_reference = kwargs.get('payment_reference')  # Transaction ID from payment gateway
        self.description = kwargs.get('description')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.completed_at = kwargs.get('completed_at')

    @staticmethod
    def get_by_id(payment_id):
        """Get a payment by ID."""
        result = db.select("payments", eq={"id": payment_id})
        if result:
            return Payment(**result[0])
        return None

    @staticmethod
    def get_by_user(user_id, limit=50):
        """Get all payments for a specific user."""
        results = db.select("payments", eq={"user_id": user_id}, order="created_at DESC", limit=limit)
        return [Payment(**r) for r in results]

    @staticmethod
    def get_by_transaction(transaction_id):
        """Get payment by land transaction ID."""
        result = db.select("payments", eq={"transaction_id": transaction_id})
        if result:
            return Payment(**result[0])
        return None

    @staticmethod
    def get_by_plot(plot_id):
        """Get payments for a specific plot."""
        results = db.select("payments", eq={"plot_id": plot_id}, order="created_at DESC")
        return [Payment(**r) for r in results]

    @staticmethod
    def create(payment_data):
        """Create a new payment record."""
        payment_data['created_at'] = datetime.utcnow().isoformat()
        payment_data['updated_at'] = datetime.utcnow().isoformat()
        result = db.insert("payments", [payment_data])
        if result:
            return Payment(**result[0])
        return None

    def update_status(self, status, payment_reference=None):
        """Update payment status."""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        if payment_reference:
            update_data['payment_reference'] = payment_reference
        if status == 'completed':
            update_data['completed_at'] = datetime.utcnow().isoformat()
        
        result = db.update("payments", update_data, eq={"id": self.id})
        if result:
            self.status = status
            self.updated_at = update_data['updated_at']
            if payment_reference:
                self.payment_reference = payment_reference
            if status == 'completed':
                self.completed_at = update_data['completed_at']
            return True
        return False

    def to_dict(self):
        """Convert payment to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_id': self.transaction_id,
            'plot_id': self.plot_id,
            'payment_type': self.payment_type,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at
        }


# Fee structure for different services
FEE_STRUCTURE = {
    'land_registration': {
        'amount': 5000,  # MWK
        'description': 'Land Registration Fee'
    },
    'land_transfer': {
        'amount': 10000,  # MWK
        'description': 'Land Transfer Fee'
    },
    'plot_verification': {
        'amount': 2000,  # MWK
        'description': 'Plot Verification Fee'
    },
    'certificate_issuance': {
        'amount': 3000,  # MWK
        'description': 'Land Certificate Issuance Fee'
    }
}


def get_fee_for_service(service_type):
    """Get fee amount and description for a service type."""
    return FEE_STRUCTURE.get(service_type, {'amount': 0, 'description': 'Unknown Service'})
