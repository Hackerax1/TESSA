"""
Service configuration management module for Proxmox NLI.

Handles saving, loading and merging of service configurations.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ServiceConfig:
    """
    Service configuration management for the Proxmox NLI system.
    
    Handles:
    - Loading and saving service configurations
    - Merging default configs with user preferences
    - Validating configurations against service requirements
    """
    
    def __init__(self, base_nli):
        """Initialize the service configuration manager"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_dir = os.path.join(self.base_dir, 'config', 'services')
        self.service_catalog = base_nli.service_catalog if hasattr(base_nli, 'service_catalog') else None
        self.user_preferences = base_nli.user_preferences if hasattr(base_nli, 'user_preferences') else None
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
    
    def get_service_config(self, service_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a service, combining defaults with user preferences
        
        Args:
            service_id: ID of the service to get configuration for
            user_id: Optional user ID to get user-specific preferences
            
        Returns:
            Combined service configuration
        """
        # Start with default configuration
        config = self._load_default_config(service_id)
        
        # Load saved service configuration
        saved_config = self._load_saved_config(service_id)
        if saved_config:
            config = self._merge_configs(config, saved_config)
        
        # Apply user preferences if available
        if self.user_preferences and user_id:
            user_prefs = self.user_preferences.get_service_preferences(service_id, user_id)
            if user_prefs:
                config = self._merge_configs(config, user_prefs)
                
        return config
    
    def save_service_config(self, service_id: str, config: Dict[str, Any]) -> bool:
        """
        Save configuration for a service
        
        Args:
            service_id: ID of the service
            config: Configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_file = os.path.join(self.config_dir, f"{service_id}.json")
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving service config for {service_id}: {str(e)}")
            return False
    
    def validate_config(self, service_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate service configuration against service requirements
        
        Args:
            service_id: ID of the service
            config: Configuration to validate
            
        Returns:
            Validation result with any validation errors
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not self.service_catalog:
            result["valid"] = False
            result["errors"].append("No service catalog available")
            return result
            
        # Get service definition
        service_def = self.service_catalog.get_service(service_id)
        if not service_def:
            result["valid"] = False
            result["errors"].append(f"Service {service_id} not found in catalog")
            return result
        
        # Check VM requirements
        if 'vm_requirements' in service_def and 'vm' in config:
            vm_reqs = service_def['vm_requirements']
            vm_config = config['vm']
            
            # Check memory
            if 'memory' in vm_reqs and vm_config.get('memory', 0) < vm_reqs['memory']:
                result["valid"] = False
                result["errors"].append(f"Memory requirement not met: needs at least {vm_reqs['memory']}MB")
            
            # Check cores
            if 'cores' in vm_reqs and vm_config.get('cores', 0) < vm_reqs['cores']:
                result["valid"] = False
                result["errors"].append(f"CPU requirement not met: needs at least {vm_reqs['cores']} cores")
            
            # Check disk
            if 'disk' in vm_reqs and vm_config.get('disk', 0) < vm_reqs['disk']:
                result["valid"] = False
                result["errors"].append(f"Disk requirement not met: needs at least {vm_reqs['disk']}GB")
        
        # Check required fields based on deployment method
        if 'deployment' in service_def:
            method = service_def['deployment'].get('method', 'docker')
            
            if method == 'docker':
                if 'docker_port_mappings' in config and not isinstance(config['docker_port_mappings'], list):
                    result["valid"] = False
                    result["errors"].append("docker_port_mappings must be a list")
                    
            elif method == 'script':
                if 'script_vars' in config and not isinstance(config['script_vars'], dict):
                    result["valid"] = False
                    result["errors"].append("script_vars must be a dictionary")
        
        return result
    
    def _load_default_config(self, service_id: str) -> Dict[str, Any]:
        """
        Load default configuration for a service from its definition
        
        Args:
            service_id: ID of the service
            
        Returns:
            Default configuration
        """
        default_config = {
            "vm": {
                "memory": 1024,  # Default 1GB
                "cores": 1,
                "disk": 10       # Default 10GB
            },
            "network": {
                "type": "internal",
                "ports": []
            },
            "backup": {
                "enabled": True,
                "schedule": "daily",
                "retention": 7
            }
        }
        
        # Add service-specific defaults if service catalog available
        if self.service_catalog:
            service_def = self.service_catalog.get_service(service_id)
            if service_def:
                # Use VM requirements
                if 'vm_requirements' in service_def:
                    vm_reqs = service_def['vm_requirements']
                    default_config["vm"]["memory"] = vm_reqs.get("memory", default_config["vm"]["memory"])
                    default_config["vm"]["cores"] = vm_reqs.get("cores", default_config["vm"]["cores"])
                    default_config["vm"]["disk"] = vm_reqs.get("disk", default_config["vm"]["disk"])
                
                # Add deployment method specific configuration
                if 'deployment' in service_def:
                    method = service_def['deployment'].get('method', 'docker')
                    
                    if method == 'docker':
                        default_config["docker"] = {
                            "image": service_def['deployment'].get('docker_image', ''),
                            "port_mappings": []
                        }
                        
                    elif method == 'script':
                        default_config["script"] = {
                            "vars": {}
                        }
        
        return default_config
    
    def _load_saved_config(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Load saved configuration for a service
        
        Args:
            service_id: ID of the service
            
        Returns:
            Saved configuration or None if not found
        """
        config_file = os.path.join(self.config_dir, f"{service_id}.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading saved config for {service_id}: {str(e)}")
        
        return None
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configurations, with override_config taking precedence
        
        Args:
            base_config: Base configuration
            override_config: Configuration to override base with
            
        Returns:
            Merged configuration
        """
        result = base_config.copy()
        
        # Iterate through override config
        for key, value in override_config.items():
            # If key exists in base and both are dictionaries, merge recursively
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                # Otherwise just override
                result[key] = value
                
        return result