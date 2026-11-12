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
import json

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
    required = ["area_type", "area_id"]
    
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    if data["area_type"] not in ["district", "traditional_authority", "village"]:
        return jsonify({"error": "Invalid area type. Must be district, traditional_authority, or village"}), 400
    
    chief_id = data.get("chief_id") or None
    if chief_id:
        chief = db.select("users", eq={"id": chief_id})
        if not chief or chief[0].get('role') != 'chief':
            return jsonify({"error": "Chief not found"}), 404
    
    # Get area name from predefined areas
    from data.geographic_areas import get_area_name
    area_name = data.get("area_name") or get_area_name(data["area_type"], data["area_id"])
    
    area_data = {
        "chief_id": chief_id,
        "area_type": data["area_type"],
        "area_id": data["area_id"],
        "area_name": area_name,
        "district_id": data.get("district_id"),
        "boundary": json.dumps(data["boundary"]) if data.get("boundary") else None,
        "villages_json": json.dumps(data.get("villages", [])),
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
        if area.get('boundary'):
            try:
                area['boundary'] = json.loads(area['boundary'])
            except (TypeError, json.JSONDecodeError):
                area['boundary'] = None
        try:
            area['villages'] = json.loads(area.get('villages_json') or '[]')
        except (TypeError, json.JSONDecodeError):
            area['villages'] = []
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

@official_bp.route("/api/official/chief-areas/<int:area_id>", methods=["PUT"])
@token_required
def update_chief_area_official(current_user, area_id):
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403

    areas = db.select("chief_areas", eq={"id": area_id})
    if not areas:
        return jsonify({"error": "Chief area not found"}), 404

    data = request.json or {}
    chief_id = data.get("chief_id")
    if chief_id is not None and chief_id != "":
        chief = db.select("users", eq={"id": chief_id})
        if not chief or chief[0].get('role') != 'chief':
            return jsonify({"error": "Chief not found"}), 404
        chief_id = int(chief_id)
    else:
        chief_id = None

    update_data = {
        "chief_id": chief_id,
        "area_name": data.get("area_name", areas[0].get("area_name")),
        "district_id": data.get("district_id", areas[0].get("district_id")),
        "villages_json": json.dumps(data.get("villages", [])),
        "updated_at": datetime.now().isoformat()
    }
    if data.get("boundary") is not None:
        update_data["boundary"] = json.dumps(data["boundary"])

    if db.update("chief_areas", update_data, eq={"id": area_id}):
        return jsonify({"message": "Chief area updated successfully"})
    return jsonify({"error": "Failed to update chief area"}), 500

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
# State-Held Plot Management (government / military / city)
# ──────────────────────────────────────────────────────

VALID_PLOT_TYPES = ["private", "government", "military", "city"]

@official_bp.route("/api/official/state-plots", methods=["POST"])
@token_required
def create_state_plot(current_user):
    """
    Officials register a government, military or city plot directly.
    These plots are created approved + protected: nobody but officials
    can ever modify, sell, lease or transfer them.
    """
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403

    data = request.json
    required = ["plot_name", "points", "plot_type"]
    if not all(k in data for k in required):
        return jsonify({"error": "plot_name, points and plot_type are required"}), 400

    from utils.plot_protection import is_state_plot_type
    plot_type = (data["plot_type"] or "").strip().lower()
    if plot_type not in VALID_PLOT_TYPES or plot_type == "private":
        return jsonify({"error": "plot_type must be government, military or city"}), 400
    if len(data.get("points", [])) < 3:
        return jsonify({"error": "At least 3 boundary points required"}), 400

    plot_data = {
        "plot_name": data["plot_name"],
        "points": data["points"],
        "area": data.get("area"),
        "location": data.get("location", ""),
        "description": data.get("description", ""),
        "district": data.get("district", ""),
        "village": data.get("village", ""),
        "plot_type": plot_type,
        "is_protected": 1,
        "status": "verified",  # state land is pre-approved
        "approved_by": current_user.id,
        "approved_at": datetime.now().isoformat(),
        "created_by_official": current_user.id,
        "user_id": current_user.id,  # held in trust — owner field is not transferable
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    plot = db.insert("plots", plot_data)
    if not plot:
        return jsonify({"error": "Failed to create state plot"}), 500

    import json as _json
    if isinstance(plot.get("points"), str):
        plot["points"] = _json.loads(plot["points"])

    db.insert("plot_history", {
        "plot_id": plot["id"],
        "user_id": current_user.id,
        "change_type": "created",
        "previous_status": None,
        "new_status": "verified",
        "changes": _json.dumps({"plot_type": plot_type, "protected": True}),
        "created_at": datetime.now().isoformat(),
    })

    return jsonify({
        "message": f"{plot_type.capitalize()} plot registered and locked. "
                   "It cannot be modified, sold or transferred by anyone.",
        "plot": plot,
    }), 201


@official_bp.route("/api/official/state-plots/<int:plot_id>", methods=["PUT"])
@token_required
def update_state_plot(current_user, plot_id):
    """Officials may update details of a state-held plot (and only those)."""
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403

    plots = db.select("plots", eq={"id": plot_id})
    if not plots:
        return jsonify({"error": "Plot not found"}), 404
    if not plots[0].get("is_protected"):
        return jsonify({"error": "This endpoint only manages state-held plots"}), 400

    data = request.json or {}
    allowed = ["plot_name", "area", "location", "description",
               "district", "village", "points", "status"]
    update_data = {k: data[k] for k in allowed if k in data}

    # Only officials can change the plot type of a state plot
    if "plot_type" in data:
        new_type = (data["plot_type"] or "").strip().lower()
        if new_type not in VALID_PLOT_TYPES:
            return jsonify({"error": "Invalid plot_type"}), 400
        from utils.plot_protection import is_state_plot_type
        update_data["plot_type"] = new_type
        update_data["is_protected"] = 1 if is_state_plot_type(new_type) else 0

    if not update_data:
        return jsonify({"error": "Nothing to update"}), 400

    update_data["updated_at"] = datetime.now().isoformat()
    if db.update("plots", update_data, eq={"id": plot_id}):
        db.insert("plot_history", {
            "plot_id": plot_id,
            "user_id": current_user.id,
            "change_type": "official_edit",
            "previous_status": plots[0].get("status"),
            "new_status": update_data.get("status", plots[0].get("status")),
            "changes": json.dumps({k: "updated" for k in update_data}),
            "created_at": datetime.now().isoformat(),
        })
        return jsonify({"message": "State plot updated"})
    return jsonify({"error": "Failed to update state plot"}), 500


@official_bp.route("/api/official/state-plots/<int:plot_id>", methods=["DELETE"])
@token_required
def delete_state_plot(current_user, plot_id):
    """Officials may remove a state-held plot from the registry."""
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403

    plots = db.select("plots", eq={"id": plot_id})
    if not plots:
        return jsonify({"error": "Plot not found"}), 404
    if not plots[0].get("is_protected"):
        return jsonify({"error": "This endpoint only manages state-held plots"}), 400

    db.delete("plots", eq={"id": plot_id})
    return jsonify({"message": "State plot removed from registry"})


@official_bp.route("/api/official/state-plots", methods=["GET"])
@token_required
def list_state_plots(current_user):
    """List all state-held (protected) plots."""
    if not current_user.is_superuser and not current_user.is_official:
        return jsonify({"error": "Unauthorized - officials only"}), 403

    all_plots = db.select("plots", order="created_at DESC")
    from utils.plot_protection import is_plot_protected
    import json as _json
    result = []
    for plot in all_plots:
        if not is_plot_protected(plot):
            continue
        if isinstance(plot.get("points"), str):
            try:
                plot["points"] = _json.loads(plot["points"])
            except (TypeError, _json.JSONDecodeError):
                pass
        result.append(plot)
    return jsonify(result)


# ──────────────────────────────────────────────────────
# Boundary Vectors (villages are chief areas with a drawn boundary)
# ──────────────────────────────────────────────────────

@official_bp.route("/api/official/area-boundaries", methods=["GET"])
@token_required
def get_area_boundaries(current_user):
    """
    All chief areas that have a drawn boundary (villages, TAs, districts).
    Used by officials and chiefs to render vectors and auto-detect geography.
    """
    if not current_user.is_superuser and not current_user.is_official and current_user.role != 'chief':
        return jsonify({"error": "Unauthorized"}), 403
    areas = db.select("chief_areas", order="created_at DESC")
    result = []
    for area in areas:
        boundary = area.get('boundary')
        if not boundary:
            continue
        try:
            boundary = json.loads(boundary)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(boundary, list) or len(boundary) < 3:
            continue
        result.append({
            "id": area.get("id"),
            "area_type": area.get("area_type"),
            "area_id": area.get("area_id"),
            "area_name": area.get("area_name"),
            "district_id": area.get("district_id"),
            "chief_id": area.get("chief_id"),
            "villages": area.get("villages_json") or '[]',
            "boundary": boundary
        })
    return jsonify(result)

@official_bp.route("/api/public/area-boundaries", methods=["GET"])
def get_public_area_boundaries():
    """
    Public read-only boundary vectors (chief areas with drawn boundaries).
    Lets citizens auto-detect their village/district while registering a plot
    without needing an account-level token.
    """
    areas = db.select("chief_areas", order="created_at DESC")
    result = []
    for area in areas:
        boundary = area.get('boundary')
        if not boundary:
            continue
        try:
            boundary = json.loads(boundary)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(boundary, list) or len(boundary) < 3:
            continue
        villages = area.get("villages_json") or '[]'
        try:
            villages = json.loads(villages)
        except (TypeError, json.JSONDecodeError):
            villages = []
        result.append({
            "id": area.get("id"),
            "area_type": area.get("area_type"),
            "area_id": area.get("area_id"),
            "area_name": area.get("area_name"),
            "district_id": area.get("district_id"),
            "villages": villages,
            "boundary": boundary
        })
    return jsonify(result)

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
        "traditional_authorities": {district["id"]: get_traditional_authorities(district["id"]) for district in get_all_districts()},
        "villages": {
            f'{district["id"]}:{ta["id"]}': get_villages(district["id"], ta["id"])
            for district in get_all_districts()
            for ta in get_traditional_authorities(district["id"])
        }
    })
