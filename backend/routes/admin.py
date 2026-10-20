# backend/routes/admin.py
from flask import Blueprint, request, jsonify
from utils.security import admin_required, get_password_hash
from db.sqlite_db import db
from datetime import datetime
import json
from data.geographic_areas import get_all_districts, get_traditional_authorities, get_villages, get_area_name, get_district_boundaries

admin_bp = Blueprint('admin', __name__)

# Admin Dashboard - System Statistics
@admin_bp.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def admin_dashboard(current_user):
    total_users = db.select("users")
    total_plots = db.select("plots")
    total_transactions = db.select("transactions")
    
    # Count active users
    active_users = [u for u in total_users if u.get('is_active', True)]
    # Count superusers
    admins = [u for u in total_users if u.get('is_superuser', False)]
    # Count pending transactions
    pending_transactions = [t for t in total_transactions if t.get('status') == 'pending']
    
    return jsonify({
        "total_users": len(total_users),
        "active_users": len(active_users),
        "total_admins": len(admins),
        "total_plots": len(total_plots),
        "total_transactions": len(total_transactions),
        "pending_transactions": len(pending_transactions),
        "recent_users": total_users[-5:] if len(total_users) > 5 else total_users
    })

# User Management - View All Users
@admin_bp.route("/api/admin/users", methods=["GET"])
@admin_required
def get_all_users(current_user):
    users = db.select("users", order="created_at DESC")
    
    # Remove sensitive data
    for user in users:
        user.pop('password_hash', None)
        user.pop('hashed_password', None)
    
    return jsonify(users)

# User Management - Get Single User
@admin_bp.route("/api/admin/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(current_user, user_id):
    users = db.select("users", eq={"id": user_id})
    if not users:
        return jsonify({"error": "User not found"}), 404
    
    user = users[0]
    user.pop('password_hash', None)
    user.pop('hashed_password', None)
    
    return jsonify(user)

# User Management - Update User
@admin_bp.route("/api/admin/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(current_user, user_id):
    data = request.json
    users = db.select("users", eq={"id": user_id})
    
    if not users:
        return jsonify({"error": "User not found"}), 404
    
    update_data = {}
    if 'is_active' in data:
        update_data['is_active'] = data['is_active']
    if 'is_superuser' in data:
        update_data['is_superuser'] = data['is_superuser']
    if 'full_name' in data:
        update_data['full_name'] = data['full_name']
    if 'email' in data:
        update_data['email'] = data['email']
    if 'phone' in data:
        update_data['phone'] = data['phone']
    
    update_data['updated_at'] = datetime.now().isoformat()
    
    result = db.update("users", update_data, eq={"id": user_id})
    
    if result:
        return jsonify({"message": "User updated successfully"})
    else:
        return jsonify({"error": "Failed to update user"}), 500

# User Management - Reset User PIN
@admin_bp.route("/api/admin/users/<int:user_id>/reset-pin", methods=["POST"])
@admin_required
def reset_user_pin(current_user, user_id):
    data = request.json
    new_pin = data.get('new_pin')
    
    if not new_pin or len(new_pin) < 4:
        return jsonify({"error": "PIN must be at least 4 characters"}), 400
    
    update_data = {
        "password_hash": get_password_hash(new_pin),
        "updated_at": datetime.now().isoformat()
    }
    
    result = db.update("users", update_data, eq={"id": user_id})
    
    if result:
        return jsonify({"message": "PIN reset successfully"})
    else:
        return jsonify({"error": "Failed to reset PIN"}), 500

# User Management - Delete User
@admin_bp.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(current_user, user_id):
    # Prevent deleting yourself
    if user_id == current_user.id:
        return jsonify({"error": "Cannot delete your own account"}), 400
    
    result = db.delete("users", eq={"id": user_id})
    
    if result:
        return jsonify({"message": "User deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete user"}), 500

# Plot Oversight - View All Plots
@admin_bp.route("/api/admin/plots", methods=["GET"])
@admin_required
def get_all_plots(current_user):
    plots = db.select("plots", order="created_at DESC")
    
    import json
    for plot in plots:
        if isinstance(plot.get('points'), str):
            plot['points'] = json.loads(plot['points'])
    
    return jsonify(plots)

# Plot Oversight - Update Plot Status
@admin_bp.route("/api/admin/plots/<int:plot_id>/status", methods=["PUT"])
@admin_required
def update_plot_status(current_user, plot_id):
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['pending', 'approved', 'rejected', 'verified']:
        return jsonify({"error": "Invalid status"}), 400
    
    update_data = {
        "status": new_status,
        "updated_at": datetime.now().isoformat()
    }
    
    result = db.update("plots", update_data, eq={"id": plot_id})
    
    if result:
        return jsonify({"message": f"Plot status updated to {new_status}"})
    else:
        return jsonify({"error": "Failed to update plot status"}), 500

# Transaction Monitoring - View All Transactions
@admin_bp.route("/api/admin/transactions", methods=["GET"])
@admin_required
def get_all_transactions(current_user):
    transactions = db.select("transactions", order="created_at DESC")
    return jsonify(transactions)

# Transaction Monitoring - Update Transaction Status
@admin_bp.route("/api/admin/transactions/<int:transaction_id>/status", methods=["PUT"])
@admin_required
def update_transaction_status(current_user, transaction_id):
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['pending', 'approved', 'rejected', 'completed', 'cancelled']:
        return jsonify({"error": "Invalid status"}), 400
    
    update_data = {
        "status": new_status,
        "updated_at": datetime.now().isoformat()
    }
    
    result = db.update("transactions", update_data, eq={"id": transaction_id})
    
    if result:
        return jsonify({"message": f"Transaction status updated to {new_status}"})
    else:
        return jsonify({"error": "Failed to update transaction status"}), 500

# Certificate Authority - Issue Certificate
@admin_bp.route("/api/admin/certificates/issue", methods=["POST"])
@admin_required
def issue_certificate(current_user):
    data = request.json
    required = ["plot_id", "owner_name"]
    
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Get plot details
    plots = db.select("plots", eq={"id": data["plot_id"]})
    if not plots:
        return jsonify({"error": "Plot not found"}), 404
    
    plot = plots[0]
    
    # Generate certificate data
    cert_data = {
        "plot_id": data["plot_id"],
        "owner_name": data["owner_name"],
        "plot_name": plot.get('plot_name', ''),
        "issue_date": datetime.now().isoformat(),
        "status": "issued",
        "verification_code": f"VC-{datetime.now().year}-MLW-{plot['id']}-001",
        "created_at": datetime.now().isoformat()
    }
    
    # Update plot status to verified
    db.update("plots", {"status": "verified", "updated_at": datetime.now().isoformat()}, eq={"id": data["plot_id"]})
    
    return jsonify({
        "message": "Certificate issued successfully",
        "certificate": cert_data
    })

# Reporting - System Summary
@admin_bp.route("/api/admin/reports/summary", methods=["GET"])
@admin_required
def get_system_summary(current_user):
    users = db.select("users")
    plots = db.select("plots")
    transactions = db.select("transactions")
    
    # User statistics
    user_stats = {
        "total": len(users),
        "active": len([u for u in users if u.get('is_active', True)]),
        "admins": len([u for u in users if u.get('is_superuser', False)])
    }
    
    # Plot statistics
    plot_stats = {
        "total": len(plots),
        "pending": len([p for p in plots if p.get('status') == 'pending']),
        "approved": len([p for p in plots if p.get('status') == 'approved']),
        "verified": len([p for p in plots if p.get('status') == 'verified'])
    }
    
    # Transaction statistics
    tx_stats = {
        "total": len(transactions),
        "pending": len([t for t in transactions if t.get('status') == 'pending']),
        "completed": len([t for t in transactions if t.get('status') == 'completed'])
    }
    
    return jsonify({
        "users": user_stats,
        "plots": plot_stats,
        "transactions": tx_stats,
        "generated_at": datetime.now().isoformat()
    })

# Audit Log - Log Admin Actions
@admin_bp.route("/api/admin/audit-log", methods=["GET"])
@admin_required
def get_audit_log(current_user):
    # For now, return a placeholder - in production this would query an audit log table
    return jsonify({
        "message": "Audit log feature - to be implemented with dedicated audit table",
        "actions": []
    })

# Chief Area Management - Get All Chief Areas
@admin_bp.route("/api/admin/chief-areas", methods=["GET"])
@admin_required
def get_all_chief_areas(current_user):
    areas = db.select("chief_areas", order="created_at DESC")
    
    # Get chief information and resolve area names
    for area in areas:
        # Get chief information
        chief = db.select("users", eq={"id": area['chief_id']})
        if chief:
            area['chief_name'] = chief[0].get('full_name', 'Unknown')
            area['chief_phone'] = chief[0].get('phone', '')
        else:
            area['chief_name'] = 'Unknown'
            area['chief_phone'] = ''
        
        # Resolve area name from predefined areas
        area['resolved_area_name'] = get_area_name(area.get('area_type'), area.get('area_id'))
    
    return jsonify(areas)

# Chief Area Management - Get Single Chief Area
@admin_bp.route("/api/admin/chief-areas/<int:area_id>", methods=["GET"])
@admin_required
def get_chief_area(current_user, area_id):
    areas = db.select("chief_areas", eq={"id": area_id})
    if not areas:
        return jsonify({"error": "Chief area not found"}), 404
    
    area = areas[0]
    
    # Get chief information
    chief = db.select("users", eq={"id": area['chief_id']})
    if chief:
        area['chief_name'] = chief[0].get('full_name', 'Unknown')
        area['chief_phone'] = chief[0].get('phone', '')
    else:
        area['chief_name'] = 'Unknown'
        area['chief_phone'] = ''
    
    # Resolve area name from predefined areas
    area['resolved_area_name'] = get_area_name(area.get('area_type'), area.get('area_id'))
    
    return jsonify(area)

# Chief Area Management - Create Chief Area
@admin_bp.route("/api/admin/chief-areas", methods=["POST"])
@admin_required
def create_chief_area(current_user):
    data = request.json
    required = ["chief_id", "area_type", "area_id"]
    
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    if data["area_type"] not in ["district", "traditional_authority", "village"]:
        return jsonify({"error": "Invalid area type. Must be district, traditional_authority, or village"}), 400
    
    # Verify chief exists
    chief = db.select("users", eq={"id": data["chief_id"]})
    if not chief:
        return jsonify({"error": "Chief not found"}), 404
    
    # Verify chief has role 'chief' or update it
    if chief[0].get('role') != 'chief':
        db.update("users", {"role": "chief", "updated_at": datetime.now().isoformat()}, eq={"id": data["chief_id"]})
    
    # Get area name from predefined areas
    area_name = get_area_name(data["area_type"], data["area_id"])
    
    area_data = {
        "chief_id": data["chief_id"],
        "area_type": data["area_type"],
        "area_id": data["area_id"],
        "area_name": area_name,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    result = db.insert("chief_areas", [area_data])
    
    if result:
        return jsonify({
            "message": "Chief area created successfully",
            "area": result[0]
        }), 201
    else:
        return jsonify({"error": "Failed to create chief area"}), 500

# Chief Area Management - Update Chief Area
@admin_bp.route("/api/admin/chief-areas/<int:area_id>", methods=["PUT"])
@admin_required
def update_chief_area(current_user, area_id):
    data = request.json
    areas = db.select("chief_areas", eq={"id": area_id})
    
    if not areas:
        return jsonify({"error": "Chief area not found"}), 404
    
    update_data = {}
    if 'area_type' in data:
        if data["area_type"] not in ["district", "traditional_authority", "village"]:
            return jsonify({"error": "Invalid area type. Must be district, traditional_authority, or village"}), 400
        update_data['area_type'] = data['area_type']
    if 'area_id' in data:
        update_data['area_id'] = data['area_id']
    if 'chief_id' in data:
        # Verify new chief exists
        chief = db.select("users", eq={"id": data["chief_id"]})
        if not chief:
            return jsonify({"error": "Chief not found"}), 404
        update_data['chief_id'] = data['chief_id']
    
    # If area_type or area_id changed, update area_name
    if 'area_type' in update_data or 'area_id' in update_data:
        area_type = update_data.get('area_type', areas[0].get('area_type'))
        area_id = update_data.get('area_id', areas[0].get('area_id'))
        update_data['area_name'] = get_area_name(area_type, area_id)
    
    update_data['updated_at'] = datetime.now().isoformat()
    
    result = db.update("chief_areas", update_data, eq={"id": area_id})
    
    if result:
        return jsonify({"message": "Chief area updated successfully"})
    else:
        return jsonify({"error": "Failed to update chief area"}), 500

# Chief Area Management - Delete Chief Area
@admin_bp.route("/api/admin/chief-areas/<int:area_id>", methods=["DELETE"])
@admin_required
def delete_chief_area(current_user, area_id):
    result = db.delete("chief_areas", eq={"id": area_id})
    
    if result:
        return jsonify({"message": "Chief area deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete chief area"}), 500

# Chief Management - Get All Chiefs
@admin_bp.route("/api/admin/chiefs", methods=["GET"])
@admin_required
def get_all_chiefs(current_user):
    users = db.select("users", order="created_at DESC")
    
    # Filter users with role 'chief' or is_superuser (admins can also be chiefs)
    chiefs = [u for u in users if u.get('role') == 'chief' or u.get('is_superuser', False)]
    
    # Remove sensitive data
    for chief in chiefs:
        chief.pop('password_hash', None)
        chief.pop('hashed_password', None)
    
    return jsonify(chiefs)

# Geographic Areas - Get District Boundaries
@admin_bp.route("/api/admin/district-boundaries", methods=["GET"])
def get_district_boundaries_api():
    """Get all district boundary coordinates for map rendering"""
    boundaries = get_district_boundaries()
    return jsonify(boundaries)

# Chief Management - Assign Role to User
@admin_bp.route("/api/admin/users/<int:user_id>/role", methods=["PUT"])
@admin_required
def assign_user_role(current_user, user_id):
    data = request.json
    new_role = data.get('role')
    
    if new_role not in ['citizen', 'chief', 'admin']:
        return jsonify({"error": "Invalid role"}), 400
    
    users = db.select("users", eq={"id": user_id})
    if not users:
        return jsonify({"error": "User not found"}), 404
    
    update_data = {
        "role": new_role,
        "updated_at": datetime.now().isoformat()
    }
    
    # If role is admin, also set is_superuser
    if new_role == 'admin':
        update_data['is_superuser'] = True
    else:
        update_data['is_superuser'] = False
    
    result = db.update("users", update_data, eq={"id": user_id})
    
    if result:
        return jsonify({"message": f"User role updated to {new_role}"})
    else:
        return jsonify({"error": "Failed to update user role"}), 500
