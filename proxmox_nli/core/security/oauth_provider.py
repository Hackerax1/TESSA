"""
OAuth provider integration for federated identity management.
Supports authentication with external identity providers like Google, GitHub, Microsoft, etc.
"""
import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import secrets
import hashlib
import base64
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class OAuthProvider:
    """Provider for OAuth-based authentication with external identity providers."""
    
    def __init__(self, config_path=None):
        """Initialize the OAuth provider.
        
        Args:
            config_path: Optional path to OAuth configuration file
        """
        self.providers = {}
        self.states = {}  # Store state tokens for CSRF protection
        self.mapping_config = {
            'auto_create_users': False,
            'default_role': 'user'
        }
        
        # Load configuration
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        else:
            # Default configuration path
            default_config = os.path.join(os.path.dirname(__file__), 'oauth_config.json')
            if os.path.exists(default_config):
                self._load_config(default_config)
            else:
                # Create empty configuration
                self._create_default_config()
                
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'oauth')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load user mappings
        self.user_mappings = {}
        self._load_user_mappings()
    
    def _load_config(self, config_path: str):
        """Load OAuth configuration from a file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.providers = config.get('providers', {})
                logger.info(f"Loaded {len(self.providers)} OAuth providers")
        except Exception as e:
            logger.error(f"Error loading OAuth configuration: {str(e)}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default OAuth configuration."""
        self.providers = {
            'google': {
                'name': 'Google',
                'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
                'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'userinfo_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
                'scope': 'openid email profile',
                'enabled': False
            },
            'github': {
                'name': 'GitHub',
                'client_id': os.getenv('GITHUB_CLIENT_ID', ''),
                'client_secret': os.getenv('GITHUB_CLIENT_SECRET', ''),
                'authorize_url': 'https://github.com/login/oauth/authorize',
                'token_url': 'https://github.com/login/oauth/access_token',
                'userinfo_url': 'https://api.github.com/user',
                'scope': 'read:user user:email',
                'enabled': False
            },
            'microsoft': {
                'name': 'Microsoft',
                'client_id': os.getenv('MICROSOFT_CLIENT_ID', ''),
                'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET', ''),
                'authorize_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
                'scope': 'openid email profile User.Read',
                'enabled': False
            }
        }
        
        # Save the default configuration
        self._save_config()
    
    def _save_config(self):
        """Save the OAuth configuration to a file."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'oauth_config.json')
            with open(config_path, 'w') as f:
                json.dump({'providers': self.providers}, f, indent=2)
            logger.info("Saved OAuth configuration")
        except Exception as e:
            logger.error(f"Error saving OAuth configuration: {str(e)}")
    
    def _load_user_mappings(self):
        """Load user mappings from disk."""
        try:
            mappings_file = os.path.join(self.data_dir, 'user_mappings.json')
            if os.path.exists(mappings_file):
                with open(mappings_file, 'r') as f:
                    self.user_mappings = json.load(f)
                logger.info(f"Loaded {len(self.user_mappings)} OAuth user mappings")
        except Exception as e:
            logger.error(f"Error loading OAuth user mappings: {str(e)}")
            self.user_mappings = {}
    
    def _save_user_mappings(self):
        """Save user mappings to disk."""
        try:
            mappings_file = os.path.join(self.data_dir, 'user_mappings.json')
            with open(mappings_file, 'w') as f:
                json.dump(self.user_mappings, f, indent=2)
            logger.debug("Saved OAuth user mappings")
        except Exception as e:
            logger.error(f"Error saving OAuth user mappings: {str(e)}")
    
    def get_providers(self) -> Dict:
        """Get all configured OAuth providers.
        
        Returns:
            Dictionary with provider information
        """
        # Return only enabled providers with public information
        public_providers = {}
        for provider_id, provider in self.providers.items():
            if provider.get('enabled', False):
                public_providers[provider_id] = {
                    'name': provider.get('name', provider_id),
                    'authorize_url': provider.get('authorize_url', ''),
                    'scope': provider.get('scope', '')
                }
                
        return {
            'success': True,
            'message': f'Found {len(public_providers)} enabled OAuth providers',
            'providers': public_providers
        }
    
    def configure_provider(self, provider_id: str, config: Dict) -> Dict:
        """Configure an OAuth provider.
        
        Args:
            provider_id: ID of the provider to configure
            config: Provider configuration
            
        Returns:
            Dictionary with configuration result
        """
        if provider_id not in self.providers:
            return {
                'success': False,
                'message': f'Unknown provider: {provider_id}'
            }
            
        # Update provider configuration
        provider = self.providers[provider_id]
        for key, value in config.items():
            if key in ['client_id', 'client_secret', 'scope', 'enabled']:
                provider[key] = value
                
        # Save the configuration
        self._save_config()
        
        return {
            'success': True,
            'message': f'Provider {provider_id} configured successfully',
            'provider': {k: v for k, v in provider.items() if k != 'client_secret'}
        }
    
    def generate_authorization_url(self, provider_id: str, redirect_uri: str) -> Dict:
        """Generate an authorization URL for an OAuth provider.
        
        Args:
            provider_id: ID of the provider to use
            redirect_uri: Redirect URI for the OAuth flow
            
        Returns:
            Dictionary with authorization URL
        """
        if provider_id not in self.providers:
            return {
                'success': False,
                'message': f'Unknown provider: {provider_id}'
            }
            
        provider = self.providers[provider_id]
        if not provider.get('enabled', False):
            return {
                'success': False,
                'message': f'Provider {provider_id} is not enabled'
            }
            
        # Generate a state token for CSRF protection
        state = secrets.token_urlsafe(32)
        self.states[state] = {
            'provider_id': provider_id,
            'redirect_uri': redirect_uri,
            'created_at': datetime.now().isoformat()
        }
        
        # Clean up old state tokens
        self._cleanup_states()
        
        # Build the authorization URL
        params = {
            'client_id': provider['client_id'],
            'redirect_uri': redirect_uri,
            'scope': provider['scope'],
            'response_type': 'code',
            'state': state
        }
        
        auth_url = f"{provider['authorize_url']}?{urlencode(params)}"
        
        return {
            'success': True,
            'message': f'Generated authorization URL for {provider_id}',
            'auth_url': auth_url,
            'state': state
        }
    
    def handle_callback(self, code: str, state: str) -> Dict:
        """Handle the OAuth callback and exchange the code for tokens.
        
        Args:
            code: Authorization code from the OAuth provider
            state: State token for CSRF protection
            
        Returns:
            Dictionary with authentication result
        """
        if state not in self.states:
            return {
                'success': False,
                'message': 'Invalid state token'
            }
            
        state_data = self.states.pop(state)
        provider_id = state_data['provider_id']
        redirect_uri = state_data['redirect_uri']
        
        if provider_id not in self.providers:
            return {
                'success': False,
                'message': f'Unknown provider: {provider_id}'
            }
            
        provider = self.providers[provider_id]
        
        # Exchange the code for tokens
        token_data = self._exchange_code_for_tokens(provider, code, redirect_uri)
        if not token_data.get('success', False):
            return token_data
            
        # Get user information
        userinfo_data = self._get_user_info(provider, token_data['access_token'])
        if not userinfo_data.get('success', False):
            return userinfo_data
            
        # Create or update user mapping
        user_id = self._create_or_update_user_mapping(provider_id, userinfo_data['userinfo'])
        
        return {
            'success': True,
            'message': f'Successfully authenticated with {provider_id}',
            'user_id': user_id,
            'provider_id': provider_id,
            'userinfo': userinfo_data['userinfo']
        }
    
    def _exchange_code_for_tokens(self, provider: Dict, code: str, redirect_uri: str) -> Dict:
        """Exchange an authorization code for access and refresh tokens.
        
        Args:
            provider: Provider configuration
            code: Authorization code
            redirect_uri: Redirect URI used in the authorization request
            
        Returns:
            Dictionary with token exchange result
        """
        try:
            # Prepare the token request
            data = {
                'client_id': provider['client_id'],
                'client_secret': provider['client_secret'],
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            headers = {
                'Accept': 'application/json'
            }
            
            # Make the token request
            response = requests.post(provider['token_url'], data=data, headers=headers)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Token request failed: HTTP {response.status_code}',
                    'response': response.text
                }
                
            # Parse the response
            try:
                token_data = response.json()
            except ValueError:
                # Some providers (like GitHub) might return form-encoded data
                if 'application/x-www-form-urlencoded' in response.headers.get('Content-Type', ''):
                    token_data = {}
                    for pair in response.text.split('&'):
                        key, value = pair.split('=')
                        token_data[key] = value
                else:
                    return {
                        'success': False,
                        'message': 'Invalid token response format',
                        'response': response.text
                    }
            
            if 'access_token' not in token_data:
                return {
                    'success': False,
                    'message': 'Access token not found in response',
                    'response': token_data
                }
                
            return {
                'success': True,
                'message': 'Successfully exchanged code for tokens',
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'id_token': token_data.get('id_token'),
                'expires_in': token_data.get('expires_in')
            }
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            return {
                'success': False,
                'message': f'Error exchanging code for tokens: {str(e)}'
            }
    
    def _get_user_info(self, provider: Dict, access_token: str) -> Dict:
        """Get user information from the OAuth provider.
        
        Args:
            provider: Provider configuration
            access_token: Access token
            
        Returns:
            Dictionary with user information
        """
        try:
            # Prepare the userinfo request
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            # Make the userinfo request
            response = requests.get(provider['userinfo_url'], headers=headers)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Userinfo request failed: HTTP {response.status_code}',
                    'response': response.text
                }
                
            # Parse the response
            userinfo = response.json()
            
            # Extract and normalize user information
            normalized_info = self._normalize_user_info(provider, userinfo)
            
            return {
                'success': True,
                'message': 'Successfully retrieved user information',
                'userinfo': normalized_info
            }
        except Exception as e:
            logger.error(f"Error getting user information: {str(e)}")
            return {
                'success': False,
                'message': f'Error getting user information: {str(e)}'
            }
    
    def _normalize_user_info(self, provider: Dict, userinfo: Dict) -> Dict:
        """Normalize user information from different providers.
        
        Args:
            provider: Provider configuration
            userinfo: Raw user information
            
        Returns:
            Normalized user information
        """
        provider_id = next((pid for pid, p in self.providers.items() if p == provider), 'unknown')
        
        # Default normalized structure
        normalized = {
            'provider_id': provider_id,
            'provider_user_id': '',
            'email': '',
            'name': '',
            'picture': '',
            'raw': userinfo
        }
        
        # Provider-specific normalization
        if provider_id == 'google':
            normalized.update({
                'provider_user_id': userinfo.get('sub', ''),
                'email': userinfo.get('email', ''),
                'name': userinfo.get('name', ''),
                'picture': userinfo.get('picture', '')
            })
        elif provider_id == 'github':
            normalized.update({
                'provider_user_id': str(userinfo.get('id', '')),
                'email': userinfo.get('email', ''),
                'name': userinfo.get('name', userinfo.get('login', '')),
                'picture': userinfo.get('avatar_url', '')
            })
            
            # GitHub might not return email in the initial response
            if not normalized['email'] and 'email_url' in provider:
                try:
                    email_response = requests.get(
                        provider['email_url'],
                        headers={'Authorization': f'Bearer {userinfo.get("access_token")}'}
                    )
                    if email_response.status_code == 200:
                        emails = email_response.json()
                        primary_email = next((e for e in emails if e.get('primary')), None)
                        if primary_email:
                            normalized['email'] = primary_email.get('email', '')
                except Exception as e:
                    logger.error(f"Error getting GitHub email: {str(e)}")
        elif provider_id == 'microsoft':
            normalized.update({
                'provider_user_id': userinfo.get('id', ''),
                'email': userinfo.get('mail', userinfo.get('userPrincipalName', '')),
                'name': userinfo.get('displayName', ''),
                'picture': ''  # Microsoft Graph API doesn't provide picture URL directly
            })
        
        return normalized
    
    def _create_or_update_user_mapping(self, provider_id: str, userinfo: Dict) -> str:
        """Create or update a user mapping for an OAuth user.
        
        Args:
            provider_id: ID of the OAuth provider
            userinfo: Normalized user information
            
        Returns:
            Internal user ID
        """
        # Create a unique identifier for this OAuth user
        provider_user_id = userinfo['provider_user_id']
        oauth_id = f"{provider_id}:{provider_user_id}"
        
        # Check if this OAuth user is already mapped
        for user_id, mappings in self.user_mappings.items():
            if oauth_id in mappings.get('oauth_ids', []):
                # Update the mapping with the latest user info
                mappings['userinfo'] = userinfo
                mappings['last_login'] = datetime.now().isoformat()
                self._save_user_mappings()
                return user_id
        
        # Create a new user ID
        user_id = f"oauth_user_{secrets.token_hex(8)}"
        
        # Create a new mapping
        self.user_mappings[user_id] = {
            'oauth_ids': [oauth_id],
            'userinfo': userinfo,
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat()
        }
        
        self._save_user_mappings()
        return user_id
    
    def get_user_by_oauth_id(self, provider_id: str, provider_user_id: str) -> Optional[Dict]:
        """Get a user by their OAuth ID.
        
        Args:
            provider_id: ID of the OAuth provider
            provider_user_id: User ID from the provider
            
        Returns:
            User information or None if not found
        """
        oauth_id = f"{provider_id}:{provider_user_id}"
        
        for user_id, mappings in self.user_mappings.items():
            if oauth_id in mappings.get('oauth_ids', []):
                return {
                    'user_id': user_id,
                    'oauth_ids': mappings.get('oauth_ids', []),
                    'userinfo': mappings.get('userinfo', {}),
                    'created_at': mappings.get('created_at'),
                    'last_login': mappings.get('last_login')
                }
                
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get a user by their internal user ID.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            User information or None if not found
        """
        if user_id in self.user_mappings:
            mappings = self.user_mappings[user_id]
            return {
                'user_id': user_id,
                'oauth_ids': mappings.get('oauth_ids', []),
                'userinfo': mappings.get('userinfo', {}),
                'created_at': mappings.get('created_at'),
                'last_login': mappings.get('last_login')
            }
            
        return None
    
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
        if user_id not in self.user_mappings:
            return {
                'success': False,
                'message': f'User {user_id} not found'
            }
            
        oauth_id = f"{provider_id}:{provider_user_id}"
        
        # Check if this OAuth account is already linked to another user
        for uid, mappings in self.user_mappings.items():
            if uid != user_id and oauth_id in mappings.get('oauth_ids', []):
                return {
                    'success': False,
                    'message': f'OAuth account is already linked to user {uid}'
                }
        
        # Add the OAuth ID to the user's mappings
        mappings = self.user_mappings[user_id]
        if 'oauth_ids' not in mappings:
            mappings['oauth_ids'] = []
            
        if oauth_id not in mappings['oauth_ids']:
            mappings['oauth_ids'].append(oauth_id)
            
        # Update user info
        mappings['userinfo'] = userinfo
        mappings['last_login'] = datetime.now().isoformat()
        
        self._save_user_mappings()
        
        return {
            'success': True,
            'message': f'OAuth account linked to user {user_id}',
            'user_id': user_id,
            'oauth_ids': mappings['oauth_ids']
        }
    
    def unlink_oauth_account(self, user_id: str, provider_id: str, provider_user_id: str) -> Dict:
        """Unlink an OAuth account from a user.
        
        Args:
            user_id: Internal user ID
            provider_id: ID of the OAuth provider
            provider_user_id: User ID from the provider
            
        Returns:
            Dictionary with unlinking result
        """
        if user_id not in self.user_mappings:
            return {
                'success': False,
                'message': f'User {user_id} not found'
            }
            
        oauth_id = f"{provider_id}:{provider_user_id}"
        
        # Remove the OAuth ID from the user's mappings
        mappings = self.user_mappings[user_id]
        if 'oauth_ids' in mappings and oauth_id in mappings['oauth_ids']:
            mappings['oauth_ids'].remove(oauth_id)
            self._save_user_mappings()
            
            return {
                'success': True,
                'message': f'OAuth account unlinked from user {user_id}',
                'user_id': user_id,
                'oauth_ids': mappings['oauth_ids']
            }
        else:
            return {
                'success': False,
                'message': f'OAuth account not linked to user {user_id}'
            }
    
    def _cleanup_states(self):
        """Clean up expired state tokens."""
        now = datetime.now()
        expired_states = []
        
        for state, data in self.states.items():
            created_at = datetime.fromisoformat(data['created_at'])
            if now - created_at > timedelta(minutes=10):
                expired_states.append(state)
                
        for state in expired_states:
            self.states.pop(state, None)
            
    def configure_mapping(self, config: Dict) -> Dict:
        """Configure OAuth user mapping settings.
        
        Args:
            config: Mapping configuration
            
        Returns:
            Dictionary with configuration result
        """
        # Validate the configuration
        if 'auto_create_users' not in config:
            return {
                'success': False,
                'message': 'Missing auto_create_users setting'
            }
            
        if 'default_role' not in config:
            return {
                'success': False,
                'message': 'Missing default_role setting'
            }
            
        # Update the mapping configuration
        self.mapping_config = {
            'auto_create_users': config.get('auto_create_users', False),
            'default_role': config.get('default_role', 'user')
        }
        
        # Save the configuration to the database
        self._save_config()
        
        return {
            'success': True,
            'message': 'Mapping configuration updated successfully',
            'config': self.mapping_config
        }
