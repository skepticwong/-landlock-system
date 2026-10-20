# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import requests
import os
from config import config
from utils.security import (
    create_access_token, 
    get_password_hash, 
    verify_password,
    token_required
)

# Initialize Flask app first
app = Flask(__name__)

def normalize_phone(phone):
    if not phone:
        return ""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+").strip()
    if cleaned.startswith('+265'):
        return '0' + cleaned[4:]
    if cleaned.startswith('265'):
        return '0' + cleaned[3:]
    return cleaned

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# SQLite Configuration
from db.sqlite_db import db

# Admin Routes
from routes.admin import admin_bp
app.register_blueprint(admin_bp)

# Transaction Approval Routes (v2 — multi-party approval)
from routes.transactions import tx_bp
app.register_blueprint(tx_bp)

# Notification Routes
from routes.notifications import notif_bp
app.register_blueprint(notif_bp)

# USSD endpoint (incoming USSD/SMS provider webhooks)
from routes.ussd import ussd_bp
app.register_blueprint(ussd_bp)

# Official Routes
from routes.official import official_bp
app.register_blueprint(official_bp)

# Chief Routes
from routes.chief import chief_bp
app.register_blueprint(chief_bp)

# Payment Routes
from routes.payments import payments_bp
app.register_blueprint(payments_bp)

# Health Check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "db": "sqlite"}), 200

# Auth routes
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json
    # LandLock specific required fields
    required_fields = ['national_id', 'full_name', 'email', 'pin', 'phone']
    if not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    phone = normalize_phone(data['phone'])

    # Check if user exists (by national_id/username, email, or phone)
    existing_user = db.select("users", eq={"username": data['national_id']})
    existing_email = db.select("users", eq={"email": data['email']})
    existing_phone = db.select("users", eq={"phone": phone})
    
    if existing_user or existing_email or existing_phone:
        return jsonify({"error": "User with this National ID, email, or phone already exists"}), 400

    # Create new user
    user_data = {
        "username": data['national_id'], # Store National ID in username column
        "email": data['email'],
        "phone": phone,
        "password_hash": get_password_hash(data['pin']), # Store PIN in password_hash column
        "full_name": data['full_name'],
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    user = db.insert("users", user_data)

    if user:
        access_token = create_access_token(
            data={"sub": str(user['id'])},
            expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "phone": user['phone']
            }
        }), 201
    else:
        return jsonify({"error": "Failed to register user"}), 500

@app.route("/api/auth/register-citizen", methods=["POST"])
@token_required
def register_citizen(current_user):
    data = request.json
    required_fields = ['national_id', 'full_name', 'phone', 'temporary_pin']
    if not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    phone = normalize_phone(data['phone'])

    # Check if user exists (by national_id/username, or phone)
    existing_user = db.select("users", eq={"username": data['national_id']})
    existing_phone = db.select("users", eq={"phone": phone})
    
    if existing_user or existing_phone:
        return jsonify({"error": "User with this National ID or phone already exists"}), 400

    # Create new user
    user_data = {
        "username": data['national_id'],
        "email": f"{data['national_id']}@landlock.gov.mw",
        "phone": phone,
        "password_hash": get_password_hash(data['temporary_pin']),
        "full_name": data['full_name'],
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    user = db.insert("users", user_data)

    if user:
        return jsonify({
            "message": "Citizen registered successfully",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "phone": user['phone']
            }
        }), 201
    else:
        return jsonify({"error": "Failed to register citizen"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    print(f"[DEBUG LOGIN] Received data: {data}")
    try:
        with open("login_attempts.log", "a") as f:
            f.write(f"Received: {data}\n")
    except Exception:
        pass
    
    # Allow login with phone and pin
    if not all(k in data for k in ['phone', 'password']):
        print("[DEBUG LOGIN] Missing phone or password")
        return jsonify({"error": "Phone and PIN are required"}), 400

    phone = normalize_phone(data['phone'])
    print(f"[DEBUG LOGIN] Looking for phone: {phone}")
    # Find user by phone
    response = db.select("users", eq={"phone": phone})

    if not response:
        print("[DEBUG LOGIN] Phone not found at all")
        try:
            with open("login_attempts.log", "a") as f:
                f.write(f"Result: Phone not found at all\n")
        except Exception:
            pass
        return jsonify({"error": "Invalid phone number or PIN"}), 401

    user = response[0]
    print(f"[DEBUG LOGIN] Found user: {user['username']}, id: {user['id']}")
    
    # Check both password_hash and hashed_password columns
    password_hash = user.get('password_hash', '') or user.get('hashed_password', '')
    print(f"[DEBUG LOGIN] User hash present: {bool(password_hash)}")
    
    is_valid = verify_password(data['password'], password_hash)
    print(f"[DEBUG LOGIN] Password verification result: {is_valid}")
    try:
        with open("login_attempts.log", "a") as f:
            f.write(f"Result: user={user['phone']}, hash_present={bool(password_hash)}, is_valid={is_valid}\n")
    except Exception:
        pass
        
    if not is_valid:
        return jsonify({"error": "Invalid phone number or PIN"}), 401

    access_token = create_access_token(
        data={"sub": str(user['id'])},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "phone": user['phone'],
            "full_name": user.get('full_name', ''),
            "role": user.get('role', 'citizen'),
            "is_superuser": bool(user.get('is_superuser', False))
        }
    })

# Plot routes
@app.route("/api/plots", methods=["POST"])
@token_required
def create_plot(current_user):
    data = request.json
    required = ["plot_name", "points"]
    
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    if len(data.get("points", [])) < 3:
        return jsonify({"error": "At least 3 boundary points required"}), 400

    # Add user_id to the plot data
    plot_data = {
        **data,
        "user_id": current_user.id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    plot = db.insert("plots", plot_data)

    if plot:
        # Convert points string back to list for response if needed
        import json
        if isinstance(plot.get('points'), str):
            plot['points'] = json.loads(plot['points'])
        
        # Record creation in history
        history_data = {
            "plot_id": plot['id'],
            "user_id": current_user.id,
            "change_type": "created",
            "previous_status": None,
            "new_status": plot.get('status', 'pending'),
            "changes": json.dumps({"plot_name": plot.get('plot_name')}),
            "created_at": datetime.now().isoformat()
        }
        db.insert("plot_history", history_data)
        
        return jsonify(plot), 201
    else:
        return jsonify({"error": "Failed to create plot"}), 500

@app.route("/api/plots", methods=["GET"])
@token_required
def get_user_plots(current_user):
    plots = db.select("plots", eq={"user_id": current_user.id})
    import json
    for p in plots:
        if isinstance(p.get('points'), str):
            p['points'] = json.loads(p['points'])
            
    return jsonify(plots)

@app.route("/api/plots/<int:plot_id>", methods=["GET"])
@token_required
def get_plot(current_user, plot_id):
    plots = db.select("plots", eq={"id": plot_id})
    
    if not plots:
        return jsonify({"error": "Plot not found"}), 404
    
    plot = plots[0]
    
    # Check if user owns this plot or is superuser
    if plot['user_id'] != current_user.id and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized"}), 403
    
    import json
    if isinstance(plot.get('points'), str):
        plot['points'] = json.loads(plot['points'])
    
    return jsonify(plot)

@app.route("/api/plots/<int:plot_id>", methods=["PUT"])
@token_required
def update_plot(current_user, plot_id):
    plots = db.select("plots", eq={"id": plot_id})
    
    if not plots:
        return jsonify({"error": "Plot not found"}), 404
    
    plot = plots[0]
    
    # Check if user owns this plot
    if plot['user_id'] != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    import json
    
    # Track changes for history
    changes = {}
    previous_status = plot.get('status')
    
    # Track which fields are being changed
    if 'plot_name' in data and data['plot_name'] != plot.get('plot_name'):
        changes['plot_name'] = data['plot_name']
    if 'district' in data and data['district'] != plot.get('district'):
        changes['district'] = data['district']
    if 'traditional_authority' in data and data['traditional_authority'] != plot.get('traditional_authority'):
        changes['traditional_authority'] = data['traditional_authority']
    if 'village' in data and data['village'] != plot.get('village'):
        changes['village'] = data['village']
    if 'landmark_description' in data and data['landmark_description'] != plot.get('landmark_description'):
        changes['landmark_description'] = data['landmark_description']
    if 'land_use' in data and data['land_use'] != plot.get('land_use'):
        changes['land_use'] = data['land_use']
    if 'acquisition_method' in data and data['acquisition_method'] != plot.get('acquisition_method'):
        changes['acquisition_method'] = data['acquisition_method']
    if 'estimated_size' in data and data['estimated_size'] != plot.get('estimated_size'):
        changes['estimated_size'] = data['estimated_size']
    
    # Auto-approval reset: if status is being changed to pending, or if any field is changed
    if 'status' in data:
        changes['status'] = data['status']
    elif changes:  # If any field is changed but status not explicitly set
        data['status'] = 'pending'  # Reset to pending for re-approval
        changes['status'] = 'pending'
    
    # Add updated_at timestamp
    data['updated_at'] = datetime.now().isoformat()
    
    # Update the plot
    result = db.update("plots", data, eq={"id": plot_id})
    
    if result:
        # Record the change in history
        new_status = data.get('status', previous_status)
        change_type = 'status_change' if 'status' in changes else 'edited'
        
        history_data = {
            "plot_id": plot_id,
            "user_id": current_user.id,
            "change_type": change_type,
            "previous_status": previous_status,
            "new_status": new_status,
            "changes": json.dumps(changes),
            "created_at": datetime.now().isoformat()
        }
        db.insert("plot_history", history_data)
        
        # Return updated plot
        updated_plots = db.select("plots", eq={"id": plot_id})
        if updated_plots:
            updated_plot = updated_plots[0]
            if isinstance(updated_plot.get('points'), str):
                updated_plot['points'] = json.loads(updated_plot['points'])
            return jsonify(updated_plot)
    
    return jsonify({"error": "Failed to update plot"}), 500

@app.route("/api/plots/<int:plot_id>/history", methods=["GET"])
@token_required
def get_plot_history(current_user, plot_id):
    plots = db.select("plots", eq={"id": plot_id})
    
    if not plots:
        return jsonify({"error": "Plot not found"}), 404
    
    plot = plots[0]
    
    # Check if user owns this plot or is superuser
    if plot['user_id'] != current_user.id and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized"}), 403
    
    import json
    history = db.select("plot_history", eq={"plot_id": plot_id}, order="created_at DESC")
    
    # Parse changes JSON
    for entry in history:
        if isinstance(entry.get('changes'), str):
            try:
                entry['changes'] = json.loads(entry['changes'])
            except:
                entry['changes'] = {}
    
    return jsonify(history)

# User data endpoint
@app.route("/api/user/me", methods=["GET"])
@token_required
def get_current_user(current_user):
    user = db.select("users", eq={"id": current_user.id})
    if user:
        user_data = user[0]
        # Remove sensitive data
        user_data.pop('password_hash', None)
        user_data.pop('hashed_password', None)
        # Ensure is_staff is exposed for frontend gating
        user_data['is_staff'] = current_user.is_official
        return jsonify(user_data)
    return jsonify({"error": "User not found"}), 404

# Parcels endpoint (similar to plots but with more details for frontend)
@app.route("/api/parcels", methods=["GET"])
@token_required
def get_user_parcels(current_user):
    # Officials see all plots, regular users see only their own
    if current_user.is_superuser:
        plots = db.select("plots", order="created_at DESC")
    else:
        plots = db.select("plots", eq={"user_id": current_user.id}, order="created_at DESC")
    
    import json
    parcels = []
    for plot in plots:
        parcel = {
            "id": f"MLW-{plot['id']}",  # Generate parcel ID
            "plot_name": plot.get('plot_name', ''),
            "location": plot.get('plot_name', ''),  # Using plot_name as location for now
            "size": 0,  # Will need to calculate from points or add size field
            "status": plot.get('status', 'pending'),  # Use actual status from database
            "points": json.loads(plot['points']) if isinstance(plot.get('points'), str) else plot.get('points', []),
            "created_at": plot.get('created_at', '')
        }
        parcels.append(parcel)
    return jsonify(parcels)

# Certificates endpoint
@app.route("/api/certificates", methods=["GET"])
@token_required
def get_user_certificates(current_user):
    plots = db.select("plots", eq={"user_id": current_user.id}) or []
    valid_statuses = {"verified", "approved", "completed", "issued"}
    eligible_plots = []

    for plot in plots:
        status = str(plot.get('status') or '').strip().lower()
        if status in valid_statuses:
            eligible_plots.append(plot)

    eligible_plots.sort(
        key=lambda plot: (
            plot.get('updated_at') or plot.get('created_at') or '',
            plot.get('id', 0)
        ),
        reverse=True
    )

    certificates = []
    for plot in eligible_plots:
        created_at = plot.get('created_at') or plot.get('updated_at') or ''
        issue_date = created_at.split('T')[0] if isinstance(created_at, str) and 'T' in created_at else str(created_at).split('T')[0] if created_at else ''
        year = created_at[:4] if isinstance(created_at, str) and created_at else '2024'
        status = str(plot.get('status') or 'verified').strip().lower()
        if status not in valid_statuses:
            status = 'verified'

        cert = {
            "id": f"CERT-{plot['id']}",
            "parcelId": f"MLW-{plot['id']}",
            "location": plot.get('plot_name', ''),
            "ownerName": current_user.full_name if hasattr(current_user, 'full_name') else 'Unknown',
            "size": 0,
            "issueDate": issue_date,
            "type": "ownership",
            "status": status,
            "verificationCode": f"VC-{year}-MLW-{plot['id']}-001",
            "qrCode": f"QR-CODE-DATA-{plot['id']}"
        }
        certificates.append(cert)

    return jsonify(certificates)

# Static data endpoints for dropdowns
@app.route("/api/districts", methods=["GET"])
def get_districts():
    districts = ['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba', 'Kasungu', 'Mangochi', 'Salima', 'Dedza', 'Ntcheu', 'Mwanza']
    return jsonify(districts)

@app.route("/api/traditional-authorities", methods=["GET"])
def get_traditional_authorities():
    authorities = ['Chief Mwase', 'Chief Bvumbwe', 'Chief Kuntaja', 'Chief Nkhoma', 'Chief Chapola', 'Chief Mbelwa', 'Chief Chikuse']
    return jsonify(authorities)

@app.route("/api/villages", methods=["GET"])
def get_villages():
    villages = ['Chilomoni', 'Area 25', 'Kawale', 'Mchenga', 'Njewa', 'Area 18', 'Area 43', 'Biwi', 'Lilongwe City Centre']
    return jsonify(villages)

# Transactions endpoints
@app.route("/api/transactions", methods=["GET"])
@token_required
def get_user_transactions(current_user):
    transactions = db.select("transactions", eq={"user_id": current_user.id}, order="created_at DESC")
    return jsonify(transactions)

@app.route("/api/transactions", methods=["POST"])
@token_required
def create_transaction(current_user):
    data = request.json
    required = ["transaction_type", "plot_id"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    tx_data = {
        "user_id": current_user.id,
        "plot_id": data["plot_id"],
        "transaction_type": data["transaction_type"],
        "counterparty": data.get("counterparty", ""),
        "status": data.get("status", "pending"),
        "amount": data.get("amount", 0),
        "notes": data.get("notes", ""),
        "created_at": datetime.now().isoformat()
    }
    tx = db.insert("transactions", tx_data)
    if tx:
        return jsonify(tx), 201
    return jsonify({"error": "Failed to create transaction"}), 500

# Dashboard summary endpoint
@app.route("/api/dashboard/summary", methods=["GET"])
@token_required
def get_dashboard_summary(current_user):
    plots = db.select("plots", eq={"user_id": current_user.id})
    transactions = db.select("transactions", eq={"user_id": current_user.id})

    import json
    total_parcels = len(plots)
    verified = total_parcels  # all registered plots are considered verified
    pending_actions = sum(1 for t in transactions if t.get("status") == "pending")
    active_deals = sum(1 for t in transactions if t.get("status") in ("pending", "in_progress"))

    # Build recent activity from plots and transactions
    activity = []
    for p in plots:
        activity.append({
            "type": "plot_registered",
            "title": f"Plot registered: {p.get('plot_name', 'Unnamed')}",
            "created_at": p.get("created_at", "")
        })
    for t in transactions:
        activity.append({
            "type": "transaction",
            "title": f"Transaction {t.get('transaction_type', '')} – {t.get('status', '')}",
            "created_at": t.get("created_at", "")
        })
    # Sort by created_at descending, take last 5
    activity.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    recent_activity = activity[:5]

    return jsonify({
        "total_parcels": total_parcels,
        "pending_actions": pending_actions,
        "active_deals": active_deals,
        "verified": verified,
        "recent_activity": recent_activity
    })

# Official Dashboard Statistics
@app.route("/api/dashboard/official/stats", methods=["GET"])
@token_required
def get_official_dashboard_stats(current_user):
    # Only allow officials/superusers to access this
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get all plots and transactions
    all_plots = db.select("plots")
    all_transactions = db.select("transactions")
    all_users = db.select("users")
    
    # Calculate statistics
    total_plots = len(all_plots)
    total_users = len(all_users)
    total_transactions = len(all_transactions)
    
    # Plot status breakdown
    plot_status = {}
    for plot in all_plots:
        status = plot.get('status', 'unknown')
        plot_status[status] = plot_status.get(status, 0) + 1
    
    # Transaction status breakdown
    tx_status = {}
    for tx in all_transactions:
        status = tx.get('status', 'unknown')
        tx_status[status] = tx_status.get(status, 0) + 1
    
    # Recent activity (last 10 items combined)
    activity = []
    for p in all_plots:
        activity.append({
            "type": "plot_registered",
            "title": f"Plot registered: {p.get('plot_name', 'Unnamed')}",
            "created_at": p.get("created_at", "")
        })
    for t in all_transactions:
        activity.append({
            "type": "transaction",
            "title": f"Transaction {t.get('transaction_type', '')} – {t.get('status', '')}",
            "created_at": t.get("created_at", "")
        })
    activity.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    recent_activity = activity[:10]
    
    # Since plots don't have district field, we'll show plots by user for now
    plots_by_user = {}
    for plot in all_plots:
        user_id = plot.get('user_id')
        plots_by_user[user_id] = plots_by_user.get(user_id, 0) + 1
    
    return jsonify({
        "total_plots": total_plots,
        "total_users": total_users,
        "total_transactions": total_transactions,
        "plot_status": plot_status,
        "transaction_status": tx_status,
        "recent_activity": recent_activity,
        "plots_by_user": plots_by_user
    })

# Official Caseload - Get all plots for officials to review
@app.route("/api/official/caseload", methods=["GET"])
@token_required
def get_official_caseload(current_user):
    # Allow superusers and users with role='official'
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized"}), 403

    # Get all plots (all officials can see all)
    all_plots = db.select("plots", order="created_at DESC")

    import json
    caseload = []
    for plot in all_plots:
        # Get user info for each plot
        user = db.select("users", eq={"id": plot.get('user_id')})
        user_name = user[0].get('full_name', 'Unknown') if user else 'Unknown'

        # Get approving official info if approved
        approved_by_name = None
        if plot.get('approved_by'):
            approver = db.select("users", eq={"id": plot.get('approved_by')})
            approved_by_name = approver[0].get('full_name', 'Unknown') if approver else 'Unknown'

        caseload.append({
            "id": plot.get('id'),
            "parcelId": f"MLW-{plot['id']}",
            "plot_name": plot.get('plot_name', 'Unnamed'),
            "claimant": user_name,
            "status": plot.get('status', 'pending'),
            "submittedDate": plot.get('created_at', ''),
            "approved_by": approved_by_name,
            "approved_at": plot.get('approved_at'),
            "district": plot.get('district', ''),
            "village": plot.get('village', ''),
            "traditional_authority": plot.get('traditional_authority', ''),
            "land_use": plot.get('land_use', ''),
            "estimated_size": plot.get('estimated_size', ''),
            "points": json.loads(plot['points']) if isinstance(plot.get('points'), str) else plot.get('points', [])
        })

    return jsonify(caseload)


# Chief Caseload - Get plots within chief's assigned area
@app.route("/api/chief/caseload", methods=["GET"])
@token_required
def get_chief_caseload(current_user):
    # Get user's role from database
    user = db.select("users", eq={"id": current_user.id})
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user_data = user[0]
    user_role = user_data.get('role', 'citizen')
    
    # Allow chiefs and admins to access this
    if user_role != 'chief' and not user_data.get('is_superuser', False):
        return jsonify({"error": "Unauthorized - chiefs only"}), 403
    
    # Get chief's assigned area
    chief_areas = db.select("chief_areas", eq={"chief_id": current_user.id})
    
    import json
    from models.chief_area import ChiefArea
    
    # If admin/superuser, show all plots
    if user_data.get('is_superuser', False):
        all_plots = db.select("plots", order="created_at DESC")
        caseload = []
        for plot in all_plots:
            plot_user = db.select("users", eq={"id": plot.get('user_id')})
            user_name = plot_user[0].get('full_name', 'Unknown') if plot_user else 'Unknown'
            
            caseload.append({
                "id": plot.get('id'),
                "parcelId": f"MLW-{plot['id']}",
                "plot_name": plot.get('plot_name', 'Unnamed'),
                "claimant": user_name,
                "status": plot.get('status', 'pending'),
                "submittedDate": plot.get('created_at', ''),
                "points": json.loads(plot['points']) if isinstance(plot.get('points'), str) else plot.get('points', []),
                "district": plot.get('district', ''),
                "village": plot.get('village', '')
            })
        return jsonify(caseload)
    
    # If chief, filter plots by assigned area
    if not chief_areas:
        # Chief has no assigned area, return empty list
        return jsonify([])
    
    # Get all plots and filter by chief's area
    all_plots = db.select("plots", order="created_at DESC")
    caseload = []
    
    for area_data in chief_areas:
        chief_area = ChiefArea(**area_data)
        
        for plot in all_plots:
            # Skip if already added
            if any(c['id'] == plot.get('id') for c in caseload):
                continue
            
            # Check if plot is within chief's area using predefined area matching
            if chief_area.contains_plot(plot):
                plot_user = db.select("users", eq={"id": plot.get('user_id')})
                user_name = plot_user[0].get('full_name', 'Unknown') if plot_user else 'Unknown'
                
                caseload.append({
                    "id": plot.get('id'),
                    "parcelId": f"MLW-{plot['id']}",
                    "plot_name": plot.get('plot_name', 'Unnamed'),
                    "claimant": user_name,
                    "status": plot.get('status', 'pending'),
                    "submittedDate": plot.get('created_at', ''),
                    "points": json.loads(plot['points']) if isinstance(plot.get('points'), str) else plot.get('points', []),
                    "district": plot.get('district', ''),
                    "village": plot.get('village', ''),
                    "area_name": area_data.get('area_name', 'Unknown')
                })
    
    return jsonify(caseload)

# Official Caseload - Approve/Reject a plot
@app.route("/api/official/caseload/<int:plot_id>/approve", methods=["POST"])
@token_required
def approve_plot(current_user, plot_id):
    # Only allow officials/superusers to access this
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    action = data.get('action', 'approve')  # 'approve' or 'reject'

    if action not in ['approve', 'reject']:
        return jsonify({"error": "Invalid action"}), 400

    # Check if plot exists
    plots = db.select("plots", eq={"id": plot_id})
    if not plots:
        return jsonify({"error": "Plot not found"}), 404

    plot = plots[0]

    # Update plot status and record who approved it
    update_data = {
        "status": action,
        "approved_by": current_user.id,
        "approved_at": datetime.now().isoformat()
    }

    result = db.update("plots", update_data, eq={"id": plot_id})

    if result:
        return jsonify({
            "message": f"Plot {action}d successfully",
            "approved_by": current_user.full_name if hasattr(current_user, 'full_name') else 'Unknown'
        })
    else:
        return jsonify({"error": "Failed to update plot"}), 500

# Land Registration endpoint
@app.route("/api/land-registration", methods=["POST"])
@token_required
def land_registration(current_user):
    data = request.json

    # Create a plot from the land registration data
    plot_name = f"{data.get('village', '')}, {data.get('district', '')}"
    points = data.get('map_boundary', [])

    # If no map boundary, create a default boundary
    if not points or len(points) < 3:
        # Create a simple default boundary (placeholder)
        points = [
            {"lat": -13.9833, "lng": 33.7833},
            {"lat": -13.9840, "lng": 33.7833},
            {"lat": -13.9840, "lng": 33.7840},
            {"lat": -13.9833, "lng": 33.7840}
        ]

    import json
    plot_data = {
        "plot_name": plot_name,
        "points": json.dumps(points),
        "user_id": current_user.id,
        "status": "pending",
        "district": data.get('district', ''),
        "traditional_authority": data.get('traditional_authority', ''),
        "village": data.get('village', ''),
        "landmark_description": data.get('landmark_description', ''),
        "witnesses": json.dumps(data.get('witnesses', [])),
        "land_use": data.get('land_use', ''),
        "acquisition_method": data.get('acquisition_method', ''),
        "estimated_size": data.get('estimated_size', ''),
        "has_map_boundary": data.get('has_map_boundary', False),
        "created_at": datetime.now().isoformat()
    }

    plot = db.insert("plots", plot_data)

    if plot:
        return jsonify({
            "message": "Land registration submitted successfully",
            "temp_id": f"MLW-{plot['id']}",
            "plot_id": plot['id']
        }), 201
    else:
        return jsonify({"error": "Failed to submit land registration"}), 500

# ──────────────────────────────────────────────────────
# Land Listings — Marketplace (sell / lease)
# ──────────────────────────────────────────────────────

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'listings')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve uploaded images as static files
@app.route('/uploads/listings/<path:filename>', methods=['GET'])
def serve_listing_image(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/api/listings', methods=['POST'])
@token_required
def create_listing(current_user):
    data = request.json
    required = ['title', 'listing_type']
    if not all(k in data for k in required):
        return jsonify({'error': 'title and listing_type are required'}), 400

    plot_id = data.get('plot_id')
    if not plot_id:
        return jsonify({'error': 'plot_id is required to create a listing'}), 400

    # Verify plot exists, belongs to current user, and is verified/approved
    plots = db.select('plots', eq={'id': plot_id})
    if not plots:
        return jsonify({'error': 'Plot not found'}), 404
    
    plot = plots[0]
    if plot['user_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized: You do not own this plot'}), 403

    if plot.get('status') not in ['verified', 'approve']:
        return jsonify({'error': 'Only verified or approved plots can be listed on the marketplace'}), 400

    # Verify no active listing already exists for this plot
    existing_listings = db.select('land_listings', eq={'plot_id': plot_id, 'status': 'active'})
    if existing_listings:
        return jsonify({'error': 'An active listing already exists for this plot'}), 400

    # Override listing location and size_description from registered plot details
    size_label = ''
    unit = plot.get('size_unit', '')
    if unit == 'meters':
        size_label = 'm'
    elif unit == 'sqmeters':
        size_label = 'm²'
    elif unit == 'acres':
        size_label = 'acres'
    elif unit == 'hectares':
        size_label = 'ha'

    size_description = f"{plot.get('estimated_size', '')} {size_label}".strip() if plot.get('estimated_size') else 'N/A'
    location = plot.get('district') or plot.get('village') or 'N/A'

    listing_data = {
        'user_id': current_user.id,
        'plot_id': plot_id,
        'title': data['title'],
        'description': data.get('description', ''),
        'asking_price': data.get('asking_price'),
        'location': location,
        'size_description': size_description,
        'listing_type': data['listing_type'],  # 'sale' or 'lease'
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
    }

    listing = db.insert('land_listings', listing_data)
    if listing:
        listing['images'] = []
        return jsonify(listing), 201
    return jsonify({'error': 'Failed to create listing'}), 500


@app.route('/api/listings', methods=['GET'])
def get_all_listings():
    """Public endpoint — returns all active listings with their images."""
    import json
    listings = db.select('land_listings', eq={'status': 'active'}, order='created_at DESC')

    result = []
    for listing in listings:
        # Attach images
        images = db.select('listing_images', eq={'listing_id': listing['id']})
        listing['images'] = images

        # Attach seller first name (no sensitive data)
        user = db.select('users', eq={'id': listing['user_id']})
        listing['seller_name'] = user[0].get('full_name', 'Unknown') if user else 'Unknown'

        result.append(listing)

    return jsonify(result)


@app.route('/api/listings/my', methods=['GET'])
@token_required
def get_my_listings(current_user):
    """Authenticated — returns the current user's own listings."""
    listings = db.select('land_listings', eq={'user_id': current_user.id}, order='created_at DESC')

    result = []
    for listing in listings:
        images = db.select('listing_images', eq={'listing_id': listing['id']})
        listing['images'] = images
        result.append(listing)

    return jsonify(result)


@app.route('/api/listings/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    """Public — get a single listing with all images and seller info."""
    listings = db.select('land_listings', eq={'id': listing_id})
    if not listings:
        return jsonify({'error': 'Listing not found'}), 404

    listing = listings[0]
    images = db.select('listing_images', eq={'listing_id': listing_id})
    listing['images'] = images

    user = db.select('users', eq={'id': listing['user_id']})
    listing['seller_name'] = user[0].get('full_name', 'Unknown') if user else 'Unknown'

    return jsonify(listing)


@app.route('/api/listings/<int:listing_id>/images', methods=['POST'])
@token_required
def upload_listing_images(current_user, listing_id):
    """Upload images for a listing (owner only). Accepts multipart/form-data."""
    import uuid

    listings = db.select('land_listings', eq={'id': listing_id})
    if not listings:
        return jsonify({'error': 'Listing not found'}), 404

    listing = listings[0]
    if listing['user_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Check existing image count
    existing = db.select('listing_images', eq={'listing_id': listing_id})
    if len(existing) >= 5:
        return jsonify({'error': 'Maximum 5 images per listing'}), 400

    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400

    files = request.files.getlist('images')
    uploaded = []

    for file in files:
        if len(existing) + len(uploaded) >= 5:
            break
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            save_path = os.path.join(UPLOAD_FOLDER, unique_name)
            file.save(save_path)

            image_data = {
                'listing_id': listing_id,
                'image_path': f'/uploads/listings/{unique_name}',
                'image_filename': file.filename,
                'created_at': datetime.now().isoformat(),
            }
            img_row = db.insert('listing_images', image_data)
            if img_row:
                uploaded.append(img_row)

    return jsonify({'uploaded': uploaded, 'count': len(uploaded)}), 201


@app.route('/api/listings/<int:listing_id>', methods=['DELETE'])
@token_required
def delete_listing(current_user, listing_id):
    """Delete a listing (owner only)."""
    listings = db.select('land_listings', eq={'id': listing_id})
    if not listings:
        return jsonify({'error': 'Listing not found'}), 404

    listing = listings[0]
    if listing['user_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Soft-delete: mark as cancelled
    db.update('land_listings', {'status': 'cancelled', 'updated_at': datetime.now().isoformat()}, eq={'id': listing_id})
    return jsonify({'message': 'Listing removed successfully'})


# ──────────────────────────────────────────────────────
# Buyer Interests — Marketplace interest requests
# ──────────────────────────────────────────────────────

@app.route('/api/listings/<int:listing_id>/interest', methods=['POST'])
@token_required
def register_interest(current_user, listing_id):
    """Register interest in a listing (buyer only)."""
    # Check if listing exists and is active
    listings = db.select('land_listings', eq={'id': listing_id})
    if not listings:
        return jsonify({'error': 'Listing not found'}), 404

    listing = listings[0]
    if listing['user_id'] == current_user.id:
        return jsonify({'error': 'Cannot express interest in your own listing'}), 400

    # Check if user already expressed interest
    existing = db.select('buyer_interests', eq={'listing_id': listing_id, 'buyer_id': current_user.id})
    if existing:
        return jsonify({'error': 'You have already expressed interest in this listing'}), 400

    data = request.json
    interest_data = {
        'listing_id': listing_id,
        'buyer_id': current_user.id,
        'seller_id': listing['user_id'],
        'message': data.get('message', ''),
        'status': 'pending_consent',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

    interest = db.insert('buyer_interests', interest_data)
    if interest:
        return jsonify(interest), 201
    return jsonify({'error': 'Failed to register interest'}), 500


@app.route('/api/interests', methods=['GET'])
@token_required
def get_buyer_interests(current_user):
    """Get all buyer interests for the current user's listings (seller view)."""
    # Get all listings owned by current user
    user_listings = db.select('land_listings', eq={'user_id': current_user.id})
    listing_ids = [l['id'] for l in user_listings]

    if not listing_ids:
        return jsonify([])

    # Get all interests for these listings
    interests = []
    for listing_id in listing_ids:
        listing_interests = db.select('buyer_interests', eq={'listing_id': listing_id}, order='created_at DESC')
        for interest in listing_interests:
            # Get buyer info
            buyer = db.select('users', eq={'id': interest['buyer_id']})
            buyer_info = buyer[0] if buyer else None

            # Get listing info
            listing = db.select('land_listings', eq={'id': interest['listing_id']})
            listing_info = listing[0] if listing else None

            interest_data = {
                'id': interest['id'],
                'listing_id': interest['listing_id'],
                'buyer_id': interest['buyer_id'],
                'buyerName': buyer_info.get('full_name', 'Unknown') if buyer_info else 'Unknown',
                'buyerPhone': buyer_info.get('phone', '') if buyer_info else '',
                'seller_id': interest['seller_id'],
                'message': interest.get('message', ''),
                'status': interest.get('status', 'pending_consent'),
                'parcelId': f"MLW-{listing_info.get('plot_id', '')}" if listing_info else 'Unknown',
                'requestedAt': interest.get('created_at', '')
            }
            interests.append(interest_data)

    return jsonify(interests)


@app.route('/api/interests/my', methods=['GET'])
@token_required
def get_my_interests(current_user):
    """Get all interests the current user has expressed as a buyer."""
    interests = db.select('buyer_interests', eq={'buyer_id': current_user.id}, order='created_at DESC')

    result = []
    for interest in interests:
        # Get seller info
        seller = db.select('users', eq={'id': interest['seller_id']})
        seller_info = seller[0] if seller else None

        # Get listing info
        listing = db.select('land_listings', eq={'id': interest['listing_id']})
        listing_info = listing[0] if listing else None

        interest_data = {
            'id': interest['id'],
            'listing_id': interest['listing_id'],
            'listing_title': listing_info.get('title', 'Unknown') if listing_info else 'Unknown',
            'listing_price': listing_info.get('asking_price') if listing_info else None,
            'listing_location': listing_info.get('location') if listing_info else None,
            'seller_id': interest['seller_id'],
            'sellerName': seller_info.get('full_name', 'Unknown') if seller_info else 'Unknown',
            'sellerPhone': seller_info.get('phone', '') if seller_info and interest.get('status') == 'contact_shared' else '',
            'sellerEmail': seller_info.get('email', '') if seller_info and interest.get('status') == 'contact_shared' else '',
            'message': interest.get('message', ''),
            'status': interest.get('status', 'pending_consent'),
            'requestedAt': interest.get('created_at', '')
        }
        result.append(interest_data)

    return jsonify(result)


@app.route('/api/interests/<int:interest_id>/approve', methods=['POST'])
@token_required
def approve_interest(current_user, interest_id):
    """Approve a buyer interest request (seller only)."""
    interests = db.select('buyer_interests', eq={'id': interest_id})
    if not interests:
        return jsonify({'error': 'Interest not found'}), 404

    interest = interests[0]
    if interest['seller_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Update status to contact_shared
    db.update('buyer_interests', 
             {'status': 'contact_shared', 'updated_at': datetime.now().isoformat()}, 
             eq={'id': interest_id})

    return jsonify({'message': 'Contact information shared successfully'})


@app.route('/api/interests/<int:interest_id>/reject', methods=['POST'])
@token_required
def reject_interest(current_user, interest_id):
    """Reject a buyer interest request (seller only)."""
    interests = db.select('buyer_interests', eq={'id': interest_id})
    if not interests:
        return jsonify({'error': 'Interest not found'}), 404

    interest = interests[0]
    if interest['seller_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Update status to rejected
    db.update('buyer_interests',
             {'status': 'rejected', 'updated_at': datetime.now().isoformat()},
             eq={'id': interest_id})

    return jsonify({'message': 'Interest rejected successfully'})


# ──────────────────────────────────────────────────────
# Messages — Buyer-Seller Chat
# ──────────────────────────────────────────────────────

@app.route('/api/interests/<int:interest_id>/messages', methods=['GET'])
@token_required
def get_messages(current_user, interest_id):
    """Get all messages for a specific interest (both buyer and seller)."""
    # Check if user is part of this interest
    interests = db.select('buyer_interests', eq={'id': interest_id})
    if not interests:
        return jsonify({'error': 'Interest not found'}), 404

    interest = interests[0]
    if interest['buyer_id'] != current_user.id and interest['seller_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Check if interest is approved
    if interest['status'] != 'contact_shared':
        return jsonify({'error': 'Interest must be approved before accessing messages'}), 403

    # Get all messages for this interest
    messages = db.select('messages', eq={'interest_id': interest_id}, order='created_at ASC')

    result = []
    for msg in messages:
        sender = db.select('users', eq={'id': msg['sender_id']})
        sender_info = sender[0] if sender else None

        message_data = {
            'id': msg['id'],
            'interest_id': msg['interest_id'],
            'sender_id': msg['sender_id'],
            'senderName': sender_info.get('full_name', 'Unknown') if sender_info else 'Unknown',
            'receiver_id': msg['receiver_id'],
            'message': msg.get('message', ''),
            'message_type': msg.get('message_type', 'text'),
            'is_read': msg.get('is_read', 0),
            'created_at': msg.get('created_at', ''),
            'isMine': msg['sender_id'] == current_user.id
        }
        result.append(message_data)

    # Mark messages as read if current user is receiver
    db.update('messages', {'is_read': 1}, eq={'interest_id': interest_id, 'receiver_id': current_user.id, 'is_read': 0})

    return jsonify(result)


@app.route('/api/interests/<int:interest_id>/messages', methods=['POST'])
@token_required
def send_message(current_user, interest_id):
    """Send a message for a specific interest."""
    # Check if user is part of this interest
    interests = db.select('buyer_interests', eq={'id': interest_id})
    if not interests:
        return jsonify({'error': 'Interest not found'}), 404

    interest = interests[0]
    if interest['buyer_id'] != current_user.id and interest['seller_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Check if interest is approved
    if interest['status'] != 'contact_shared':
        return jsonify({'error': 'Interest must be approved before sending messages'}), 400

    data = request.json
    receiver_id = interest['seller_id'] if current_user.id == interest['buyer_id'] else interest['buyer_id']

    message_data = {
        'interest_id': interest_id,
        'sender_id': current_user.id,
        'receiver_id': receiver_id,
        'message': data.get('message', ''),
        'message_type': data.get('message_type', 'text'),
        'is_read': 0,
        'created_at': datetime.now().isoformat()
    }

    message = db.insert('messages', message_data)
    if message:
        return jsonify(message), 201
    return jsonify({'error': 'Failed to send message'}), 500


if __name__ == "__main__":
    print("Starting LandLock Backend Server...")
    print("Server running at: http://localhost:5000")
    print("CORS enabled for all origins")
    app.run(host="0.0.0.0", port=5000, debug=True)
