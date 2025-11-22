# backend/utils/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from flask import jsonify
from functools import wraps
from config import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except JWTError:
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