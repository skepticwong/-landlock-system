# backend/utils/security.py
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from flask import jsonify
from functools import wraps
from config import config


def get_jwt_secrets():
    configured = (config.JWT_SECRET_KEY or '').strip()
    legacy = os.getenv('LANDLOCK_JWT_SECRET') or 'landlock-legacy-secret'
    fallbacks = [configured, legacy, 'your-secret-key-here']
    seen = set()
    secrets = []
    for secret in fallbacks:
        if secret and secret not in seen:
            seen.add(secret)
            secrets.append(secret)
    return secrets

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    last_error = None
    for secret in get_jwt_secrets():
        try:
            return jwt.decode(token, secret, algorithms=[config.JWT_ALGORITHM])
        except JWTError as exc:
            last_error = exc
    return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request, jsonify
        from models.user import User
        
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            payload = decode_token(token)
            if payload is None:
                return jsonify({"message": "Invalid token!"}), 401
                
            user_id = payload.get("sub")
            if user_id is None:
                return jsonify({"message": "Invalid token payload!"}), 401
                
            current_user = User.get_by_id(user_id)
            if current_user is None:
                return jsonify({"message": "User not found!"}), 404
                
            return f(current_user, *args, **kwargs)
            
        except Exception as e:
            return jsonify({"message": str(e)}), 500

    return decorated

def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if not current_user.is_superuser:
            return jsonify({"message": "Admin access required!"}), 403
        return f(current_user, *args, **kwargs)
    return decorated