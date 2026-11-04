# backend/routes/chief.py
"""
Chief-specific routes for LandLock.

This module provides routes for chiefs to:
- View their dashboard statistics
- View pending claims in their jurisdiction
- View verified claims
- Manage land transactions requiring their approval
"""

from flask import Blueprint, request, jsonify
from utils.security import token_required
from db.sqlite_db import db
from datetime import datetime, timedelta
from models.chief_area import ChiefArea

chief_bp = Blueprint('chief', __name__)

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
# Chief Dashboard Statistics
# ──────────────────────────────────────────────────────

@chief_bp.route("/api/chief/dashboard-stats", methods=["GET"])
@token_required
def get_chief_dashboard_stats(current_user):
    """
    Get dashboard statistics for the current chief.
    
    Returns:
    - pending_claims: Number of pending land claims in chief's jurisdiction
    - verified_this_month: Number of claims verified this month
    - total_households: Total households in chief's jurisdiction
    - registration_rate: Percentage of households registered
    - pending_transactions: Number of transactions awaiting chief approval
    """
    # Only chiefs can access this
    if current_user.role != 'chief' and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized - chiefs only"}), 403
    
    # Get chief's assigned areas
    chief_areas = db.select("chief_areas", eq={"chief_id": current_user.id})
    
    if not chief_areas:
        return jsonify({
            "pending_claims": 0,
            "verified_this_month": 0,
            "total_households": 0,
            "registration_rate": 0,
            "pending_transactions": 0
        })
    
    # Get all plots in chief's jurisdiction
    plots = db.select("plots")
    plots_in_jurisdiction = []
    
    for plot in plots:
        for area in chief_areas:
            chief_area = ChiefArea(**area)
            if chief_area.contains_plot(plot):
                plots_in_jurisdiction.append(plot)
                break
    
    # Calculate statistics
    pending_claims = len([p for p in plots_in_jurisdiction if p.get('status') == 'pending'])
    
    # Verified this month
    this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    verified_this_month = len([
        p for p in plots_in_jurisdiction 
        if p.get('status') == 'verified' and datetime.fromisoformat(p.get('updated_at', '')) >= this_month_start
    ])
    
    # Total households (unique owners in jurisdiction)
    household_owners = set()
    for plot in plots_in_jurisdiction:
        if plot.get('owner_phone'):
            household_owners.add(plot.get('owner_phone'))
    total_households = len(household_owners)
    
    # Registration rate (verified plots / total plots in jurisdiction)
    total_plots = len(plots_in_jurisdiction)
    verified_plots = len([p for p in plots_in_jurisdiction if p.get('status') == 'verified'])
    registration_rate = (verified_plots / total_plots * 100) if total_plots > 0 else 0
    
    # Pending transactions awaiting chief approval
    transactions = db.select("transactions")
    pending_transactions = len([
        t for t in transactions 
        if t.get('chief_id') == current_user.id and t.get('status') in ['pending_chief', 'pending_witness']
    ])
    
    return jsonify({
        "pending_claims": pending_claims,
        "verified_this_month": verified_this_month,
        "total_households": total_households,
        "registration_rate": round(registration_rate, 1),
        "pending_transactions": pending_transactions
    })

@chief_bp.route("/api/chief/pending-claims", methods=["GET"])
@token_required
def get_chief_pending_claims(current_user):
    """
    Get pending land claims in chief's jurisdiction.
    """
    if current_user.role != 'chief' and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized - chiefs only"}), 403
    
    # Get chief's assigned areas
    chief_areas = db.select("chief_areas", eq={"chief_id": current_user.id})
    
    if not chief_areas:
        return jsonify([])
    
    # Get all plots in chief's jurisdiction
    plots = db.select("plots", order="created_at DESC")
    pending_claims = []
    
    for plot in plots:
        if plot.get('status') != 'pending':
            continue
        for area in chief_areas:
            chief_area = ChiefArea(**area)
            if chief_area.contains_plot(plot):
                pending_claims.append(plot)
                break
    
    return jsonify(pending_claims)

@chief_bp.route("/api/chief/claims/<int:claim_id>", methods=["GET"])
@token_required
def get_chief_claim_details(current_user, claim_id):
    if current_user.role != 'chief' and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized - chiefs only"}), 403

    plots = db.select("plots", eq={"id": claim_id})
    if not plots:
        return jsonify({"error": "Claim not found"}), 404

    plot = plots[0]
    chief_areas = db.select("chief_areas", eq={"chief_id": current_user.id})
    if not current_user.is_superuser:
        in_jurisdiction = False
        for area in chief_areas:
            if ChiefArea(**area).contains_plot(plot):
                in_jurisdiction = True
                break
        if not in_jurisdiction:
            return jsonify({"error": "Claim is outside your jurisdiction"}), 403

    import json
    if isinstance(plot.get('points'), str):
        try:
            plot['points'] = json.loads(plot['points'])
        except json.JSONDecodeError:
            plot['points'] = []
    if isinstance(plot.get('witnesses'), str):
        try:
            plot['witnesses'] = json.loads(plot['witnesses'])
        except json.JSONDecodeError:
            plot['witnesses'] = []

    owners = db.select("users", eq={"id": plot.get('user_id')}) if plot.get('user_id') else []
    plot['owner'] = owners[0] if owners else {}
    plot['media'] = db.select("plot_media", eq={"plot_id": claim_id}, order="created_at DESC")
    return jsonify(plot)

@chief_bp.route("/api/chief/verified-claims", methods=["GET"])
@token_required
def get_chief_verified_claims(current_user):
    """
    Get verified land claims in chief's jurisdiction.
    """
    if current_user.role != 'chief' and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized - chiefs only"}), 403
    
    # Get chief's assigned areas
    chief_areas = db.select("chief_areas", eq={"chief_id": current_user.id})
    
    if not chief_areas:
        return jsonify([])
    
    # Get all plots in chief's jurisdiction
    plots = db.select("plots", order="updated_at DESC")
    verified_claims = []
    
    for plot in plots:
        if plot.get('status') != 'verified':
            continue
        for area in chief_areas:
            chief_area = ChiefArea(**area)
            if chief_area.contains_plot(plot):
                verified_claims.append(plot)
                break
    
    return jsonify(verified_claims)

@chief_bp.route("/api/chief/disputed-claims", methods=["GET"])
@token_required
def get_chief_disputed_claims(current_user):
    if current_user.role != 'chief' and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized - chiefs only"}), 403

    chief_areas = db.select("chief_areas", eq={"chief_id": current_user.id})
    if not chief_areas:
        return jsonify([])

    disputed_claims = []
    for plot in db.select("plots", order="updated_at DESC"):
        if plot.get('status') != 'disputed':
            continue
        for area in chief_areas:
            if ChiefArea(**area).contains_plot(plot):
                disputed_claims.append(plot)
                break
    return jsonify(disputed_claims)

@chief_bp.route("/api/chief/pending-transactions", methods=["GET"])
@token_required
def get_chief_pending_transactions(current_user):
    """
    Get transactions awaiting chief's approval.
    """
    if current_user.role != 'chief' and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized - chiefs only"}), 403
    
    # Get transactions where this chief needs to approve
    transactions = db.select("transactions", order="created_at DESC")
    pending_transactions = [
        t for t in transactions 
        if t.get('chief_id') == current_user.id and t.get('status') in ['pending_chief', 'pending_witness']
    ]
    
    # Add plot details
    for tx in pending_transactions:
        plot = db.select("plots", eq={"id": tx.get('plot_id')})
        if plot:
            tx['plot'] = plot[0]
    
    return jsonify(pending_transactions)

@chief_bp.route("/api/chief/recent-activity", methods=["GET"])
@token_required
def get_chief_recent_activity(current_user):
    """
    Get recent activity in chief's jurisdiction.
    """
    if current_user.role != 'chief' and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized - chiefs only"}), 403
    
    # Get chief's assigned areas
    chief_areas = db.select("chief_areas", eq={"chief_id": current_user.id})
    
    if not chief_areas:
        return jsonify([])
    
    # Get recent plots in jurisdiction
    plots = db.select("plots", order="created_at DESC", limit=10)
    recent_activity = []
    
    for plot in plots:
        for area in chief_areas:
            chief_area = ChiefArea(**area)
            if chief_area.contains_plot(plot):
                # Get owner info
                owner = db.select("users", eq={"phone": plot.get('owner_phone')})
                owner_name = owner[0].get('full_name', 'Unknown') if owner else 'Unknown'
                
                recent_activity.append({
                    "type": "claim_submitted" if plot.get('status') == 'pending' else "claim_verified",
                    "plot_id": plot.get('id'),
                    "plot_name": plot.get('plot_name'),
                    "owner_name": owner_name,
                    "status": plot.get('status'),
                    "created_at": plot.get('created_at')
                })
                break
    
    return jsonify(recent_activity[:5])

@chief_bp.route("/api/chief/jurisdiction", methods=["GET"])
@token_required
def get_chief_jurisdiction(current_user):
    """
    Get chief's assigned jurisdiction areas.
    """
    if current_user.role != 'chief' and not current_user.is_superuser:
        return jsonify({"error": "Unauthorized - chiefs only"}), 403
    
    chief_areas = db.select("chief_areas", eq={"chief_id": current_user.id})
    
    return jsonify(chief_areas)
