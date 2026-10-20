# backend/routes/official.py
"""
Official-specific routes for LandLock.

This module provides routes for land officials to:
- Register chiefs
- Manage chief jurisdictions
- View official-specific data
"""

from flask import Blueprint, request, jsonify
from utils.security import token_required
from db.sqlite_db import db
from datetime import datetime
from utils.security import get_password_hash

official_bp = Blueprint('official', __name__)

def normalize_phone(phone):
    if not phone:
        return ""
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+").strip()
    if cleaned.startswith('+265'):
        return '0' + cleaned[4:]
    if cleaned.startswith('265'):
        return '0' + cleaned[3:]
    return cleaned

# ──────────────────────────────────────────────────────
# Chief Registration
# ──────────────────────────────────────────────────────

@official_bp.route("/api/official/register-chief", methods=["POST"])
@token_required
def register_chief(current_user):
    """
    Register a new chief account.
    
    Required body:
    {
        "national_id": "<national ID>",
        "full_name": "<chief's full name>",
        "phone": "<phone number>",
        "temporary_pin": "<temporary PIN (4-6 digits)>",
        "district": "<district name>",
        "traditional_authority": "<TA name>",
        "village": "<village name>"
    }
    
    The system will:
    1. Validate the official has permission
    2. Check for duplicate users
    3. Create user with role='chief'
    4. Return the new chief's details
    """
    # Only officials and superusers can register chiefs
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403
    
    data = request.json
    required_fields = ['national_id', 'full_name', 'phone', 'temporary_pin']
    if not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    phone = normalize_phone(data['phone'])
    
    # Validate PIN length
    if len(data['temporary_pin']) < 4:
        return jsonify({"error": "PIN must be at least 4 characters"}), 400
    
    # Check if user already exists
    existing_user = db.select("users", eq={"username": data['national_id']})
    existing_phone = db.select("users", eq={"phone": phone})
    
    if existing_user or existing_phone:
        return jsonify({"error": "User with this National ID or phone already exists"}), 400
    
    # Create new chief user
    user_data = {
        "username": data['national_id'],
        "email": f"{data['national_id']}@landlock.gov.mw",
        "phone": phone,
        "password_hash": get_password_hash(data['temporary_pin']),
        "full_name": data['full_name'],
        "role": "chief",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    user = db.insert("users", user_data)
    
    if user:
        # Remove sensitive data from response
        user.pop('password_hash', None)
        user.pop('hashed_password', None)
        
        return jsonify({
            "message": "Chief registered successfully",
            "chief": user
        }), 201
    else:
        return jsonify({"error": "Failed to register chief"}), 500

@official_bp.route("/api/official/chiefs", methods=["GET"])
@token_required
def get_all_chiefs(current_user):
    """
    Get all chiefs in the system.
    
    Returns a list of users with role='chief'.
    """
    # Only officials and superusers can view chiefs
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403
    
    users = db.select("users", order="created_at DESC")
    
    # Filter users with role 'chief'
    chiefs = [u for u in users if u.get('role') == 'chief']
    
    # Remove sensitive data
    for chief in chiefs:
        chief.pop('password_hash', None)
        chief.pop('hashed_password', None)
    
    return jsonify(chiefs)

@official_bp.route("/api/official/chiefs/<int:chief_id>", methods=["GET"])
@token_required
def get_chief_details(current_user, chief_id):
    """
    Get details of a specific chief including their assigned areas.
    """
    # Only officials and superusers can view chief details
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403
    
    # Get chief user
    users = db.select("users", eq={"id": chief_id})
    if not users:
        return jsonify({"error": "Chief not found"}), 404
    
    chief = users[0]
    
    if chief.get('role') != 'chief':
        return jsonify({"error": "User is not a chief"}), 400
    
    # Get chief's assigned areas
    chief_areas = db.select("chief_areas", eq={"chief_id": chief_id})
    
    # Remove sensitive data
    chief.pop('password_hash', None)
    chief.pop('hashed_password', None)
    
    return jsonify({
        "chief": chief,
        "assigned_areas": chief_areas
    })

@official_bp.route("/api/official/chiefs/<int:chief_id>/reset-pin", methods=["POST"])
@token_required
def reset_chief_pin(current_user, chief_id):
    """
    Reset a chief's PIN.
    
    Body: { "new_pin": "<new PIN>" }
    """
    # Only officials and superusers can reset chief PINs
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403
    
    data = request.json
    new_pin = data.get('new_pin')
    
    if not new_pin or len(new_pin) < 4:
        return jsonify({"error": "PIN must be at least 4 characters"}), 400
    
    # Verify chief exists
    chief = db.select("users", eq={"id": chief_id})
    if not chief:
        return jsonify({"error": "Chief not found"}), 404
    
    if chief[0].get('role') != 'chief':
        return jsonify({"error": "User is not a chief"}), 400
    
    # Update PIN
    update_data = {
        "password_hash": get_password_hash(new_pin),
        "updated_at": datetime.now().isoformat()
    }
    
    result = db.update("users", update_data, eq={"id": chief_id})
    
    if result:
        return jsonify({"message": "Chief PIN reset successfully"})
    else:
        return jsonify({"error": "Failed to reset PIN"}), 500

# ──────────────────────────────────────────────────────
# Chief Jurisdiction Management
# ──────────────────────────────────────────────────────

@official_bp.route("/api/official/chief-areas", methods=["POST"])
@token_required
def create_chief_area_official(current_user):
    """
    Create a chief area assignment (official route).
    
    This is similar to the admin route but specifically for officials.
    """
    # Only officials and superusers can assign areas
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403
    
    data = request.json
    required = ["chief_id", "area_type", "area_id"]
    
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    if data["area_type"] not in ["district", "traditional_authority", "village"]:
        return jsonify({"error": "Invalid area type. Must be district, traditional_authority, or village"}), 400
    
    # Verify chief exists and has role 'chief'
    chief = db.select("users", eq={"id": data["chief_id"]})
    if not chief:
        return jsonify({"error": "Chief not found"}), 404
    
    if chief[0].get('role') != 'chief':
        return jsonify({"error": "User is not a chief"}), 400
    
    # Get area name from predefined areas
    from data.geographic_areas import get_area_name
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
            "message": "Chief area assigned successfully",
            "area": result[0]
        }), 201
    else:
        return jsonify({"error": "Failed to assign chief area"}), 500

@official_bp.route("/api/official/chief-areas", methods=["GET"])
@token_required
def get_chief_areas_official(current_user):
    """
    Get all chief area assignments (official route).
    """
    # Only officials and superusers can view chief areas
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403
    
    areas = db.select("chief_areas", order="created_at DESC")
    
    # Get chief information and resolve area names
    from data.geographic_areas import get_area_name
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

@official_bp.route("/api/official/chief-areas/<int:area_id>", methods=["DELETE"])
@token_required
def delete_chief_area_official(current_user, area_id):
    """
    Delete a chief area assignment (official route).
    """
    # Only officials and superusers can delete chief areas
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403
    
    result = db.delete("chief_areas", eq={"id": area_id})
    
    if result:
        return jsonify({"message": "Chief area deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete chief area"}), 500

# ──────────────────────────────────────────────────────
# Geographic Areas Data
# ──────────────────────────────────────────────────────

@official_bp.route("/api/official/geographic-areas", methods=["GET"])
@token_required
def get_geographic_areas(current_user):
    """
    Get all available geographic areas for assignment.
    
    Returns districts, traditional authorities, and villages.
    """
    # Only officials and superusers can access this
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403
    
    from data.geographic_areas import get_all_districts, get_traditional_authorities, get_villages
    
    return jsonify({
        "districts": get_all_districts(),
        "traditional_authorities": get_traditional_authorities(),
        "villages": get_villages()
    })
