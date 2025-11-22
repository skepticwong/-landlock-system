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
import jwt

# Initialize Flask app first
app = Flask(__name__)

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Supabase Configuration
SUPABASE_URL = "https://cisgwziqcfyjbohpxeyo.supabase.co"
SUPABASE_KEY = "your-supabase-key"  # Consider moving to environment variables
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Health Check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "db": "supabase"}), 200

# Auth routes
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json
    if not all(k in data for k in ['username', 'email', 'password', 'phone']):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user exists
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/users?select=id&or=(username.eq.{data['username']},email.eq.{data['email']},phone.eq.{data['phone']})",
        headers=HEADERS
    )
    
    if response.status_code == 200 and response.json():
        return jsonify({"error": "User with this username, email, or phone already exists"}), 400

    # Create new user
    user_data = {
        "username": data['username'],
        "email": data['email'],
        "phone": data['phone'],
        "password_hash": get_password_hash(data['password']),
        "is_active": True,
        "is_superuser": False
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/users",
        json=user_data,
        headers=HEADERS
    )

    if response.status_code in [200, 201]:
        user = response.json()[0]
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

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    if not all(k in data for k in ['username', 'password']):
        return jsonify({"error": "Username and password are required"}), 400

    # Find user by username
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/users?username=eq.{data['username']}",
        headers=HEADERS
    )

    if response.status_code != 200 or not response.json():
        return jsonify({"error": "Invalid username or password"}), 401

    user = response.json()[0]
    
    if not verify_password(data['password'], user.get('password_hash', '')):
        return jsonify({"error": "Invalid username or password"}), 401

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
        "user_id": current_user['id'],
        "created_at": datetime.now().isoformat()
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/plots",
        json=plot_data,
        headers=HEADERS
    )

    if response.status_code in [200, 201]:
        return jsonify(response.json()[0]), 201
    else:
        return jsonify({"error": "Failed to create plot"}), 500

@app.route("/api/plots", methods=["GET"])
@token_required
def get_user_plots(current_user):
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/plots?user_id=eq.{current_user['id']}",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch plots"}), 500

if __name__ == "__main__":
    print("🚀 Starting LandLock Backend Server...")
    print("📍 Server running at: http://localhost:5000")
    print("🔧 CORS enabled for all origins")
    app.run(host="0.0.0.0", port=5000, debug=True)