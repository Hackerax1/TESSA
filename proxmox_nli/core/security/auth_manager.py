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
from .oauth_provider import OAuthProvider

class AuthManager:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', os.urandom(32).hex())
        self.token_expiry = int(os.getenv('JWT_TOKEN_EXPIRY', 24))  # hours
        self.algorithm = 'HS256'
        
        self.permission_handler = PermissionHandler()
        self.token_manager = TokenManager()
        self.session_manager = SessionManager()
        self.oauth_provider = OAuthProvider()

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
        
    # OAuth integration methods
    
    def get_oauth_providers(self) -> Dict:
        """Get all configured OAuth providers.
        
        Returns:
            Dictionary with provider information
        """
        return self.oauth_provider.get_providers()
    
    def configure_oauth_provider(self, provider_id: str, config: Dict) -> Dict:
        """Configure an OAuth provider.
        
        Args:
            provider_id: ID of the provider to configure
            config: Provider configuration
            
        Returns:
            Dictionary with configuration result
        """
        return self.oauth_provider.configure_provider(provider_id, config)
    
    def generate_oauth_authorization_url(self, provider_id: str, redirect_uri: str) -> Dict:
        """Generate an authorization URL for an OAuth provider.
        
        Args:
            provider_id: ID of the provider to use
            redirect_uri: Redirect URI for the OAuth flow
            
        Returns:
            Dictionary with authorization URL
        """
        return self.oauth_provider.generate_authorization_url(provider_id, redirect_uri)
    
    def handle_oauth_callback(self, code: str, state: str) -> Dict:
        """Handle the OAuth callback and exchange the code for tokens.
        
        Args:
            code: Authorization code from the OAuth provider
            state: State token for CSRF protection
            
        Returns:
            Dictionary with authentication result and user token
        """
        # Process the OAuth callback
        result = self.oauth_provider.handle_callback(code, state)
        
        if not result.get('success', False):
            return result
            
        # Get the user ID from the result
        user_id = result.get('user_id')
        
        # Get user information to determine roles
        user_info = self.oauth_provider.get_user_by_id(user_id)
        
        # Determine user roles (could be based on user info, group membership, etc.)
        roles = ['user']  # Default role
        
        # Create a JWT token for the user
        token = self.create_token(user_id, roles)
        
        # Add the token to the result
        result['token'] = token
        
        return result
    
    def link_oauth_account(self, user_id: str, provider_id: str, provider_user_id: str, userinfo: Dict) -> Dict:
        """Link an OAuth account to an existing user.
        
        Args:
            user_id: Internal user ID
            provider_id: ID of the OAuth provider
            provider_user_id: User ID from the provider
            userinfo: User information from the provider
            
        Returns:
            Dictionary with linking result
        """
        return self.oauth_provider.link_oauth_account(user_id, provider_id, provider_user_id, userinfo)
    
    def unlink_oauth_account(self, user_id: str, provider_id: str, provider_user_id: str) -> Dict:
        """Unlink an OAuth account from a user.
        
        Args:
            user_id: Internal user ID
            provider_id: ID of the OAuth provider
            provider_user_id: User ID from the provider
            
        Returns:
            Dictionary with unlinking result
        """
        return self.oauth_provider.unlink_oauth_account(user_id, provider_id, provider_user_id)
    
    def get_user_oauth_accounts(self, user_id: str) -> Dict:
        """Get all OAuth accounts linked to a user.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Dictionary with linked OAuth accounts
        """
        user = self.oauth_provider.get_user_by_id(user_id)
        
        if not user:
            return {
                'success': False,
                'message': f'User {user_id} not found'
            }
            
        return {
            'success': True,
            'message': f'Found {len(user.get("oauth_ids", []))} linked OAuth accounts',
            'user_id': user_id,
            'oauth_ids': user.get('oauth_ids', []),
            'userinfo': user.get('userinfo', {})
        }