from db.sqlite_db import db
from datetime import datetime

now = datetime.now().isoformat()

# Create users: seller, buyer, witness, chief
seller = db.insert('users', {
    'username': 'seller001', 'email': 'seller@example.com', 'phone': '0999123456',
    'password_hash': 'x', 'full_name': 'Seller One', 'is_active': 1, 'is_superuser': 0, 'created_at': now, 'updated_at': now
})
buyer = db.insert('users', {
    'username': 'buyer001', 'email': 'buyer@example.com', 'phone': '0888123456',
    'password_hash': 'x', 'full_name': 'Buyer One', 'is_active': 1, 'is_superuser': 0, 'created_at': now, 'updated_at': now
})
witness = db.insert('users', {
    'username': 'witness001', 'email': 'witness@example.com', 'phone': '0777000001',
    'password_hash': 'x', 'full_name': 'Witness One', 'is_active': 1, 'is_superuser': 0, 'created_at': now, 'updated_at': now
})
chief = db.insert('users', {
    'username': 'chief001', 'email': 'chief@example.com', 'phone': '0777000002',
    'password_hash': 'x', 'full_name': 'Chief One', 'is_active': 1, 'is_superuser': 0, 'created_at': now, 'updated_at': now
})

# Create a plot owned by seller
plot = db.insert('plots', {
    'user_id': seller['id'], 'plot_name': 'Test Plot', 'points': '[]', 'status': 'verified', 'created_at': now, 'updated_at': now
})

# Create a transaction with approval codes
tx = db.insert('transactions', {
    'user_id': seller['id'], 'seller_id': seller['id'], 'buyer_id': buyer['id'], 'witness_id': witness['id'], 'chief_id': chief['id'],
    'plot_id': plot['id'], 'transaction_type': 'sale', 'counterparty': buyer['full_name'], 'status': 'pending_buyer',
    'amount': 100000, 'notes': 'Test sale', 'created_at': now, 'updated_at': now,
    'buyer_approval_status': 'pending', 'chief_approval_status': 'pending', 'witness_approval_status': 'pending',
    'chief_approval_code': 'CHF-TEST1', 'witness_approval_code': 'WIT-TEST1'
})

print('Created test users and transaction:')
print('seller id:', seller['id'])
print('buyer id:', buyer['id'])
print('witness id:', witness['id'])
print('chief id:', chief['id'])
print('plot id:', plot['id'])
print('transaction id:', tx['id'])
