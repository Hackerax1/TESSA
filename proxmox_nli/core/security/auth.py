"""
Authentication module for JWT-based user authentication.
"""
from datetime import datetime, timedelta
import jwt
import os
from typing import Dict, Optional

class AuthManager:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', os.urandom(32).hex())
        self.token_expiry = int(os.getenv('JWT_TOKEN_EXPIRY', 24)) # hours
        self.algorithm = 'HS256'

    def create_token(self, user_id: str, roles: list = None) -> str:
        """Create a new JWT token for a user"""
        payload = {
            'user_id': user_id,
            'roles': roles or ['user'],
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify a JWT token and return the payload if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def check_permission(self, token: str, required_roles: list) -> bool:
        """Check if the user has the required roles"""
        payload = self.verify_token(token)
        if not payload:
            return False
        user_roles = set(payload.get('roles', []))
        return bool(user_roles.intersection(required_roles))

    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh a valid token"""
        payload = self.verify_token(token)
        if payload:
            return self.create_token(payload['user_id'], payload['roles'])
        return None