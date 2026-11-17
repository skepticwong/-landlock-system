# backend/models/user.py
from datetime import datetime
from db.sqlite_db import db
from utils.security import get_password_hash, verify_password

class User:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.hashed_password = kwargs.get('hashed_password')
        self.full_name = kwargs.get('full_name')
        self.phone = kwargs.get('phone')
        self.is_active = kwargs.get('is_active', True)
        self.role = kwargs.get('role', 'citizen')
        admin_access = kwargs.get('admin_access')
        if admin_access is None:
            admin_access = bool(kwargs.get('is_superuser', False)) and self.role != 'official'
        self.is_superuser = bool(admin_access)
        self.identity_status = kwargs.get('identity_status', 'unverified')
        self.must_change_password = kwargs.get('must_change_password', False)
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())

    @property
    def is_official(self):
        """True for both superusers and users with role='official'."""
        return bool(self.is_superuser) or self.role == 'official'

    @property
    def is_staff(self):
        """Alias for is_official – kept for compatibility with frontend checks."""
        return self.is_official

    @classmethod
    def from_db(cls, data):
        if not data:
            return None
        if isinstance(data, list):
            return [cls(**user) for user in data]
        return cls(**data)

    @classmethod
    def get_by_id(cls, user_id: str):
        result = db.select("users", eq={"id": user_id})
        return cls.from_db(result[0] if result else None)

    @classmethod
    def get_by_username(cls, username: str):
        result = db.select("users", eq={"username": username})
        return cls.from_db(result[0] if result else None)

    @classmethod
    def get_by_email(cls, email: str):
        result = db.select("users", eq={"email": email})
        return cls.from_db(result[0] if result else None)

    @classmethod
    def create(cls, user_data: dict):
        # Hash password
        user_data['hashed_password'] = get_password_hash(user_data.pop('password'))
        user_data['created_at'] = datetime.utcnow().isoformat()
        user_data['updated_at'] = datetime.utcnow().isoformat()
        
        result = db.insert("users", [user_data])
        return cls.from_db(result[0] if result else None)

    def update(self, update_data: dict):
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        result = db.update(
            "users",
            update_data,
            eq={"id": self.id}
        )
        if result:
            for key, value in update_data.items():
                setattr(self, key, value)
        return bool(result)

    def verify_password(self, password: str) -> bool:
        return verify_password(password, self.hashed_password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "admin_access": self.is_superuser,
            "role": self.role,
            "identity_status": self.identity_status,
            "must_change_password": self.must_change_password,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }