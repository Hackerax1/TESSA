"""
Cloud Provider integration module for connecting TESSA with major cloud providers.
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class CloudProviderBase(ABC):
    """Abstract base class for cloud provider implementations"""
    
    @abstractmethod
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with the cloud provider"""
        pass
    
    @abstractmethod
    def list_resources(self) -> Dict[str, Any]:
        """List available cloud resources"""
        pass
    
    @abstractmethod
    def import_resources(self, resources: List[Dict]) -> Dict[str, Any]:
        """Import selected cloud resources"""
        pass
    
    @abstractmethod
    def sync_status(self) -> Dict[str, Any]:
        """Get sync status between cloud and local resources"""
        pass

class CloudProvider:
    """Main class for managing cloud provider integrations"""
    
    def __init__(self, config_dir: str = None):
        """Initialize with optional config directory path"""
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, 'cloud_providers.json')
        self.providers: Dict[str, CloudProviderBase] = {}
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load cloud provider configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cloud provider config: {str(e)}")
        
        return {
            "providers": {
                "aws": {"enabled": False, "credentials": {}},
                "azure": {"enabled": False, "credentials": {}},
                "gcp": {"enabled": False, "credentials": {}}
            },
            "sync_settings": {
                "auto_sync": False,
                "sync_interval": 3600,
                "conflict_resolution": "ask"
            }
        }
    
    def _save_config(self) -> None:
        """Save cloud provider configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cloud provider config: {str(e)}")
    
    def configure_provider(self, provider: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Configure a cloud provider with credentials"""
        try:
            if provider not in self.config["providers"]:
                return {
                    "success": False,
                    "message": f"Unsupported provider: {provider}"
                }
            
            self.config["providers"][provider]["credentials"] = credentials
            self.config["providers"][provider]["enabled"] = True
            self._save_config()
            
            return {
                "success": True,
                "message": f"Successfully configured {provider} provider"
            }
        except Exception as e:
            logger.error(f"Error configuring provider {provider}: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring provider: {str(e)}"
            }
    
    def get_provider_status(self, provider: str = None) -> Dict[str, Any]:
        """Get status of configured providers"""
        try:
            if provider:
                if provider not in self.config["providers"]:
                    return {
                        "success": False,
                        "message": f"Unknown provider: {provider}"
                    }
                return {
                    "success": True,
                    "status": {
                        "enabled": self.config["providers"][provider]["enabled"],
                        "configured": bool(self.config["providers"][provider]["credentials"])
                    }
                }
            else:
                return {
                    "success": True,
                    "providers": {
                        name: {
                            "enabled": config["enabled"],
                            "configured": bool(config["credentials"])
                        } for name, config in self.config["providers"].items()
                    }
                }
        except Exception as e:
            logger.error(f"Error getting provider status: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting provider status: {str(e)}"
            }
    
    def sync_cloud_resources(self, provider: str = None) -> Dict[str, Any]:
        """Sync resources with specified cloud provider or all enabled providers"""
        try:
            results = {
                "success": True,
                "synced_providers": {},
                "failed_providers": {}
            }
            
            providers_to_sync = (
                [provider] if provider 
                else [p for p, c in self.config["providers"].items() if c["enabled"]]
            )
            
            for p in providers_to_sync:
                if p not in self.providers:
                    results["failed_providers"][p] = "Provider not initialized"
                    continue
                
                try:
                    sync_result = self.providers[p].sync_status()
                    if sync_result["success"]:
                        results["synced_providers"][p] = sync_result["status"]
                    else:
                        results["failed_providers"][p] = sync_result["message"]
                except Exception as e:
                    results["failed_providers"][p] = str(e)
            
            if results["failed_providers"]:
                results["success"] = False
            
            return results
        
        except Exception as e:
            logger.error(f"Error syncing cloud resources: {str(e)}")
            return {
                "success": False,
                "message": f"Error syncing cloud resources: {str(e)}"
            }
    
    def import_cloud_resources(self, provider: str, resources: List[Dict]) -> Dict[str, Any]:
        """Import specific resources from a cloud provider"""
        try:
            if provider not in self.config["providers"]:
                return {
                    "success": False,
                    "message": f"Unknown provider: {provider}"
                }
            
            if provider not in self.providers:
                return {
                    "success": False,
                    "message": f"Provider {provider} not initialized"
                }
            
            return self.providers[provider].import_resources(resources)
        
        except Exception as e:
            logger.error(f"Error importing cloud resources: {str(e)}")
            return {
                "success": False,
                "message": f"Error importing cloud resources: {str(e)}"
            }
    
    def update_sync_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update cloud synchronization settings"""
        try:
            self.config["sync_settings"].update(settings)
            self._save_config()
            
            return {
                "success": True,
                "message": "Successfully updated sync settings"
            }
        except Exception as e:
            logger.error(f"Error updating sync settings: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating sync settings: {str(e)}"
            }