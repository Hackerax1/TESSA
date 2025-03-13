"""
DNS Provider integration module for managing DNS configurations across different providers.
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DNSProviderBase(ABC):
    """Abstract base class for DNS provider implementations"""
    
    @abstractmethod
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with the DNS provider"""
        pass
    
    @abstractmethod
    def list_records(self, domain: str = None) -> Dict[str, Any]:
        """List DNS records for a domain"""
        pass
    
    @abstractmethod
    def add_record(self, domain: str, record_type: str, name: str, content: str, ttl: int = 3600) -> Dict[str, Any]:
        """Add a new DNS record"""
        pass
    
    @abstractmethod
    def update_record(self, record_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing DNS record"""
        pass
    
    @abstractmethod
    def delete_record(self, record_id: str) -> Dict[str, Any]:
        """Delete a DNS record"""
        pass

class DNSProvider:
    """Main class for managing DNS provider integrations"""
    
    def __init__(self, config_dir: str = None):
        """Initialize with optional config directory path"""
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, 'dns_providers.json')
        self.providers: Dict[str, DNSProviderBase] = {}
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load DNS provider configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading DNS provider config: {str(e)}")
        
        return {
            "providers": {
                "cloudflare": {"enabled": False, "credentials": {}},
                "route53": {"enabled": False, "credentials": {}},
                "digitalocean": {"enabled": False, "credentials": {}}
            },
            "zones": {},
            "auto_update": True,
            "ttl_settings": {
                "default": 3600,
                "minimum": 120,
                "maximum": 86400
            }
        }
    
    def _save_config(self) -> None:
        """Save DNS provider configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving DNS provider config: {str(e)}")
    
    def configure_provider(self, provider: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Configure a DNS provider with credentials"""
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
    
    def add_zone(self, domain: str, provider: str) -> Dict[str, Any]:
        """Add a new DNS zone configuration"""
        try:
            if provider not in self.config["providers"]:
                return {
                    "success": False,
                    "message": f"Unknown provider: {provider}"
                }
            
            if not self.config["providers"][provider]["enabled"]:
                return {
                    "success": False,
                    "message": f"Provider {provider} is not enabled"
                }
            
            self.config["zones"][domain] = {
                "provider": provider,
                "auto_update": True,
                "last_sync": None
            }
            self._save_config()
            
            return {
                "success": True,
                "message": f"Successfully added zone {domain}"
            }
        except Exception as e:
            logger.error(f"Error adding zone: {str(e)}")
            return {
                "success": False,
                "message": f"Error adding zone: {str(e)}"
            }
    
    def sync_records(self, domain: str = None) -> Dict[str, Any]:
        """Sync DNS records for specified domain or all configured zones"""
        try:
            results = {
                "success": True,
                "synced_zones": {},
                "failed_zones": {}
            }
            
            zones_to_sync = (
                [domain] if domain 
                else [zone for zone in self.config["zones"].keys()]
            )
            
            for zone in zones_to_sync:
                if zone not in self.config["zones"]:
                    results["failed_zones"][zone] = "Zone not configured"
                    continue
                
                provider = self.config["zones"][zone]["provider"]
                if provider not in self.providers:
                    results["failed_zones"][zone] = f"Provider {provider} not initialized"
                    continue
                
                try:
                    records = self.providers[provider].list_records(zone)
                    if records["success"]:
                        results["synced_zones"][zone] = {
                            "record_count": len(records["records"]),
                            "provider": provider
                        }
                    else:
                        results["failed_zones"][zone] = records["message"]
                except Exception as e:
                    results["failed_zones"][zone] = str(e)
            
            if results["failed_zones"]:
                results["success"] = False
            
            return results
        
        except Exception as e:
            logger.error(f"Error syncing DNS records: {str(e)}")
            return {
                "success": False,
                "message": f"Error syncing DNS records: {str(e)}"
            }
    
    def update_record(self, domain: str, record_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a DNS record"""
        try:
            if domain not in self.config["zones"]:
                return {
                    "success": False,
                    "message": f"Unknown zone: {domain}"
                }
            
            provider = self.config["zones"][domain]["provider"]
            if provider not in self.providers:
                return {
                    "success": False,
                    "message": f"Provider {provider} not initialized"
                }
            
            return self.providers[provider].update_record(record_id, updates)
        except Exception as e:
            logger.error(f"Error updating DNS record: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating DNS record: {str(e)}"
            }
    
    def add_record(self, domain: str, record_type: str, name: str, content: str, ttl: int = None) -> Dict[str, Any]:
        """Add a new DNS record"""
        try:
            if domain not in self.config["zones"]:
                return {
                    "success": False,
                    "message": f"Unknown zone: {domain}"
                }
            
            provider = self.config["zones"][domain]["provider"]
            if provider not in self.providers:
                return {
                    "success": False,
                    "message": f"Provider {provider} not initialized"
                }
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.config["ttl_settings"]["default"]
            
            # Validate TTL
            if ttl < self.config["ttl_settings"]["minimum"] or ttl > self.config["ttl_settings"]["maximum"]:
                return {
                    "success": False,
                    "message": f"TTL must be between {self.config['ttl_settings']['minimum']} and {self.config['ttl_settings']['maximum']}"
                }
            
            return self.providers[provider].add_record(domain, record_type, name, content, ttl)
        except Exception as e:
            logger.error(f"Error adding DNS record: {str(e)}")
            return {
                "success": False,
                "message": f"Error adding DNS record: {str(e)}"
            }
    
    def delete_record(self, domain: str, record_id: str) -> Dict[str, Any]:
        """Delete a DNS record"""
        try:
            if domain not in self.config["zones"]:
                return {
                    "success": False,
                    "message": f"Unknown zone: {domain}"
                }
            
            provider = self.config["zones"][domain]["provider"]
            if provider not in self.providers:
                return {
                    "success": False,
                    "message": f"Provider {provider} not initialized"
                }
            
            return self.providers[provider].delete_record(record_id)
        except Exception as e:
            logger.error(f"Error deleting DNS record: {str(e)}")
            return {
                "success": False,
                "message": f"Error deleting DNS record: {str(e)}"
            }