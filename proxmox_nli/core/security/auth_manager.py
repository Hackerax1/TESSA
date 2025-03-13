"""
Authentication module for JWT-based user authentication.
"""
from datetime import datetime, timedelta
import jwt
import os
from typing import Dict, Optional, List
from .permission_handler import PermissionHandler
from .token_manager import TokenManager
from .session_manager import SessionManager

class AuthManager:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', os.urandom(32).hex())
        self.token_expiry = int(os.getenv('JWT_TOKEN_EXPIRY', 24))  # hours
        self.algorithm = 'HS256'
        
        self.permission_handler = PermissionHandler()
        self.token_manager = TokenManager()
        self.session_manager = SessionManager()

    def create_token(self, user_id: str, roles: List[str] = None) -> str:
        """Create a new JWT token for a user"""
        payload = {
            'user_id': user_id,
            'roles': roles or ['user'],
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry)
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Create a session for the token
        self.session_manager.create_session(user_id, token)
        return token

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify a JWT token and return the payload if valid"""
        if self.token_manager.is_token_revoked(token):
            return None
            
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # Update session last active time
            session = self.session_manager.get_session(token)
            if not session:
                return None
            return payload
        except jwt.ExpiredSignatureError:
            self.token_manager.revoke_token(token)
            self.session_manager.end_session(token)
            return None
        except jwt.InvalidTokenError:
            return None

    def check_permission(self, token: str, required_roles: List[str]) -> bool:
        """Check if the user has the required roles"""
        payload = self.verify_token(token)
        if not payload:
            return False
        user_roles = set(payload.get('roles', []))
        return bool(user_roles.intersection(required_roles))

    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh a valid token"""
        payload = self.verify_token(token)
        if not payload:
            return None
            
        # Create new token
        new_token = self.create_token(payload['user_id'], payload['roles'])
        
        # Revoke old token
        self.token_manager.revoke_token(token)
        self.session_manager.end_session(token)
        
        return new_token

    def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        self.token_manager.revoke_token(token)
        return self.session_manager.end_session(token)

    def get_active_sessions(self, user_id: str = None) -> Dict[str, Dict]:
        """Get all active sessions for a user"""
        return self.session_manager.get_active_sessions(user_id)