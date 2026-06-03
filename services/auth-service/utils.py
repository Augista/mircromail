import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from config import settings
import uuid


class PasswordManager:
    """Password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))


class JWTManager:
    """JWT token generation and validation"""
    
    @staticmethod
    def create_access_token(user_id: str, email: str) -> str:
        """Create access token"""
        payload = {
            'sub': str(user_id),
            'email': email,
            'type': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return token
    
    @staticmethod
    def create_refresh_token(user_id: str, email: str) -> str:
        """Create refresh token"""
        payload = {
            'sub': str(user_id),
            'email': email,
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS),
            'jti': str(uuid.uuid4())  # Unique token ID for revocation
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def get_token_expiration_seconds(token_type: str = 'access') -> int:
        """Get token expiration in seconds"""
        if token_type == 'refresh':
            return settings.JWT_REFRESH_EXPIRATION_DAYS * 24 * 3600
        return settings.JWT_EXPIRATION_HOURS * 3600
