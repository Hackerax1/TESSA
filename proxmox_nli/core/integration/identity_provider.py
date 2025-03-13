"""
Identity Provider integration module for managing authentication and identity services.
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import time

logger = logging.getLogger(__name__)

class IdentityBackendBase(ABC):
    """Abstract base class for identity backend implementations"""
    
    @abstractmethod
    def configure(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the identity backend"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the identity backend"""
        pass
    
    @abstractmethod
    def authenticate_user(self, username: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate a user with the backend"""
        pass
    
    @abstractmethod
    def get_user_groups(self, username: str) -> Dict[str, Any]:
        """Get groups for a user"""
        pass
    
    @abstractmethod
    def sync_users(self) -> Dict[str, Any]:
        """Sync users from the backend"""
        pass

class IdentityProvider:
    """Main class for managing identity provider integrations"""
    
    def __init__(self, config_dir: str = None):
        """Initialize with optional config directory path"""
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, 'identity_providers.json')
        self.backends: Dict[str, IdentityBackendBase] = {}
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load identity provider configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading identity provider config: {str(e)}")
        
        return {
            "backends": {
                "ldap": {
                    "enabled": False,
                    "settings": {
                        "url": "ldap://localhost:389",
                        "bind_dn": "",
                        "bind_password": "",
                        "base_dn": "",
                        "user_filter": "(objectClass=person)",
                        "group_filter": "(objectClass=group)",
                        "ssl": False
                    }
                },
                "oauth": {
                    "enabled": False,
                    "settings": {
                        "provider": "generic",  # or github, google, etc.
                        "client_id": "",
                        "client_secret": "",
                        "auth_url": "",
                        "token_url": "",
                        "scopes": ["openid", "profile", "email"]
                    }
                },
                "local": {
                    "enabled": True,
                    "settings": {
                        "hash_algorithm": "bcrypt",
                        "min_password_length": 8,
                        "require_special_chars": True,
                        "password_expiry_days": 90
                    }
                }
            },
            "sync_settings": {
                "auto_sync": True,
                "sync_interval": 3600,  # 1 hour
                "user_attributes": ["email", "full_name", "groups"],
                "group_attributes": ["description", "members"]
            },
            "mappings": {
                "groups": {},
                "roles": {}
            },
            "cache": {
                "enabled": True,
                "ttl": 300  # 5 minutes
            }
        }
    
    def _save_config(self) -> None:
        """Save identity provider configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving identity provider config: {str(e)}")
    
    def configure_backend(self, backend: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Configure an identity backend with settings"""
        try:
            if backend not in self.config["backends"]:
                return {
                    "success": False,
                    "message": f"Unsupported backend: {backend}"
                }
            
            # Update settings
            self.config["backends"][backend]["settings"].update(settings)
            self.config["backends"][backend]["enabled"] = True
            self._save_config()
            
            # Initialize backend if available
            if backend in self.backends:
                return self.backends[backend].configure(settings)
            
            return {
                "success": True,
                "message": f"Successfully configured {backend} backend"
            }
        except Exception as e:
            logger.error(f"Error configuring backend {backend}: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring backend: {str(e)}"
            }
    
    def add_group_mapping(self, external_group: str, local_group: str, backend: str) -> Dict[str, Any]:
        """Add a mapping between external and local groups"""
        try:
            if backend not in self.config["backends"]:
                return {
                    "success": False,
                    "message": f"Unknown backend: {backend}"
                }
            
            mapping_key = f"{backend}:{external_group}"
            self.config["mappings"]["groups"][mapping_key] = local_group
            self._save_config()
            
            return {
                "success": True,
                "message": f"Successfully mapped {external_group} to {local_group}"
            }
        except Exception as e:
            logger.error(f"Error adding group mapping: {str(e)}")
            return {
                "success": False,
                "message": f"Error adding group mapping: {str(e)}"
            }
    
    def authenticate(self, username: str, credentials: Dict[str, Any], backend: str = None) -> Dict[str, Any]:
        """Authenticate a user with specified or all enabled backends"""
        try:
            if backend:
                if backend not in self.backends or not self.config["backends"][backend]["enabled"]:
                    return {
                        "success": False,
                        "message": f"Backend {backend} not available"
                    }
                return self.backends[backend].authenticate_user(username, credentials)
            
            # Try each enabled backend until successful
            for backend_name, backend_obj in self.backends.items():
                if self.config["backends"][backend_name]["enabled"]:
                    try:
                        result = backend_obj.authenticate_user(username, credentials)
                        if result["success"]:
                            result["backend"] = backend_name
                            return result
                    except Exception as e:
                        logger.debug(f"Authentication failed with {backend_name}: {str(e)}")
            
            return {
                "success": False,
                "message": "Authentication failed with all backends"
            }
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return {
                "success": False,
                "message": f"Error during authentication: {str(e)}"
            }
    
    def sync_users(self, backend: str = None) -> Dict[str, Any]:
        """Sync users from specified or all enabled backends"""
        try:
            results = {
                "success": True,
                "synced": [],
                "failed": []
            }
            
            backends_to_sync = (
                [backend] if backend 
                else [name for name, config in self.config["backends"].items() if config["enabled"]]
            )
            
            for b in backends_to_sync:
                if b not in self.backends:
                    results["failed"].append({
                        "backend": b,
                        "error": "Backend not initialized"
                    })
                    continue
                
                try:
                    sync_result = self.backends[b].sync_users()
                    if sync_result["success"]:
                        results["synced"].append({
                            "backend": b,
                            "users": sync_result.get("user_count", 0),
                            "groups": sync_result.get("group_count", 0)
                        })
                    else:
                        results["failed"].append({
                            "backend": b,
                            "error": sync_result["message"]
                        })
                except Exception as e:
                    results["failed"].append({
                        "backend": b,
                        "error": str(e)
                    })
            
            if results["failed"]:
                results["success"] = False
            
            return results
        
        except Exception as e:
            logger.error(f"Error syncing users: {str(e)}")
            return {
                "success": False,
                "message": f"Error syncing users: {str(e)}"
            }
    
    def get_user_info(self, username: str, backend: str = None) -> Dict[str, Any]:
        """Get user information from specified or default backend"""
        try:
            if backend:
                if backend not in self.backends or not self.config["backends"][backend]["enabled"]:
                    return {
                        "success": False,
                        "message": f"Backend {backend} not available"
                    }
                return self.backends[backend].get_user_groups(username)
            
            # Get from first enabled backend that has the user
            for backend_name, backend_obj in self.backends.items():
                if self.config["backends"][backend_name]["enabled"]:
                    try:
                        result = backend_obj.get_user_groups(username)
                        if result["success"]:
                            result["backend"] = backend_name
                            return result
                    except Exception as e:
                        logger.debug(f"Failed to get user info from {backend_name}: {str(e)}")
            
            return {
                "success": False,
                "message": "User not found in any backend"
            }
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting user info: {str(e)}"
            }
    
    def test_backend(self, backend: str) -> Dict[str, Any]:
        """Test connection to an identity backend"""
        try:
            if backend not in self.backends or not self.config["backends"][backend]["enabled"]:
                return {
                    "success": False,
                    "message": f"Backend {backend} not available"
                }
            
            return self.backends[backend].test_connection()
        except Exception as e:
            logger.error(f"Error testing backend {backend}: {str(e)}")
            return {
                "success": False,
                "message": f"Error testing backend: {str(e)}"
            }