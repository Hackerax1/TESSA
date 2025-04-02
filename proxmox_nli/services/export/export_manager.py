"""
Infrastructure as Code Export Manager for TESSA.

This module provides functionality to export Proxmox configurations to various
Infrastructure as Code formats like Terraform, Ansible, and supports version control integration.
"""
import logging
import os
import json
import yaml
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ...api.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class ExportManager:
    """Manager for exporting Proxmox configurations to Infrastructure as Code formats."""
    
    def __init__(self, api: ProxmoxAPI):
        """Initialize with Proxmox API connection."""
        self.api = api
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.export_config_path = os.path.join(self.config_dir, 'export_config.json')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration or create default."""
        if os.path.exists(self.export_config_path):
            try:
                with open(self.export_config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading export configuration: {str(e)}")
                
        # Default configuration
        default_config = {
            "terraform": {
                "enabled": True,
                "provider": "proxmox",
                "output_format": "hcl",
                "include_sensitive": False,
                "resource_types": ["vm", "lxc", "storage", "network"]
            },
            "ansible": {
                "enabled": True,
                "inventory_format": "yaml",
                "include_sensitive": False,
                "resource_types": ["vm", "lxc", "storage", "network"]
            },
            "version_control": {
                "enabled": False,
                "type": "git",
                "auto_commit": True,
                "remote": "",
                "branch": "main",
                "commit_message": "Update configuration via TESSA export"
            }
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config=None) -> None:
        """Save configuration to file."""
        if config is None:
            config = self.config
            
        with open(self.export_config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def update_config(self, new_config: Dict) -> Dict:
        """Update configuration with new settings."""
        try:
            # Deep merge configuration
            self._deep_merge(self.config, new_config)
            self._save_config()
            
            return {
                "success": True,
                "message": "Export configuration updated successfully",
                "config": self.config
            }
        except Exception as e:
            logger.error(f"Error updating export configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update export configuration: {str(e)}"
            }
    
    def _deep_merge(self, target: Dict, source: Dict) -> None:
        """Recursively merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def export_terraform(self, output_dir: Optional[str] = None, resource_types: Optional[List[str]] = None) -> Dict:
        """Export Proxmox configuration to Terraform format."""
        from .terraform_exporter import TerraformExporter
        
        try:
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="tessa_terraform_")
                
            if resource_types is None:
                resource_types = self.config["terraform"]["resource_types"]
            
            exporter = TerraformExporter(self.api)
            result = exporter.export(
                output_dir=output_dir,
                resource_types=resource_types,
                include_sensitive=self.config["terraform"]["include_sensitive"]
            )
            
            if self.config["version_control"]["enabled"] and self.config["version_control"]["auto_commit"]:
                from .vcs_integration import VersionControlIntegration
                vcs = VersionControlIntegration()
                vcs_result = vcs.add_to_repository(
                    directory=output_dir,
                    message=self.config["version_control"].get("commit_message", "Update Terraform configuration via TESSA export"),
                    branch=self.config["version_control"].get("branch")
                )
                result["vcs_integration"] = vcs_result
            
            return result
        except Exception as e:
            logger.error(f"Error exporting to Terraform: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export to Terraform: {str(e)}"
            }
    
    def export_ansible(self, output_dir: Optional[str] = None, resource_types: Optional[List[str]] = None) -> Dict:
        """Export Proxmox configuration to Ansible playbooks."""
        from .ansible_exporter import AnsibleExporter
        
        try:
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="tessa_ansible_")
                
            if resource_types is None:
                resource_types = self.config["ansible"]["resource_types"]
            
            exporter = AnsibleExporter(self.api)
            result = exporter.export(
                output_dir=output_dir,
                resource_types=resource_types,
                include_sensitive=self.config["ansible"].get("include_sensitive", False)
            )
            
            if self.config["version_control"]["enabled"] and self.config["version_control"]["auto_commit"]:
                from .vcs_integration import VersionControlIntegration
                vcs = VersionControlIntegration()
                vcs_result = vcs.add_to_repository(
                    directory=output_dir,
                    message=self.config["version_control"].get("commit_message", "Update Ansible configuration via TESSA export"),
                    branch=self.config["version_control"].get("branch")
                )
                result["vcs_integration"] = vcs_result
            
            return result
        except Exception as e:
            logger.error(f"Error exporting to Ansible: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export to Ansible: {str(e)}"
            }
    
    def setup_version_control(self, vcs_type: str, repository_url: str, branch: str = "main") -> Dict:
        """Set up version control integration for exported configurations."""
        try:
            from .vcs_integration import VersionControlIntegration
            
            vcs = VersionControlIntegration()
            result = vcs.setup_repository(
                vcs_type=vcs_type,
                repository_url=repository_url,
                branch=branch
            )
            
            if result["success"]:
                # Update configuration
                self.config["version_control"]["enabled"] = True
                self.config["version_control"]["type"] = vcs_type
                self.config["version_control"]["remote"] = repository_url
                self.config["version_control"]["branch"] = branch
                self._save_config()
            
            return result
        except Exception as e:
            logger.error(f"Error setting up version control: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to set up version control: {str(e)}"
            }
            
    def import_terraform(self, input_path: str) -> Dict:
        """Import Terraform configuration into Proxmox."""
        from .terraform_exporter import TerraformExporter
        
        try:
            importer = TerraformExporter(self.api)
            return importer.import_config(input_path)
        except Exception as e:
            logger.error(f"Error importing Terraform configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to import Terraform configuration: {str(e)}"
            }
    
    def import_ansible(self, input_path: str) -> Dict:
        """Import Ansible configuration into Proxmox."""
        from .ansible_exporter import AnsibleExporter
        
        try:
            importer = AnsibleExporter(self.api)
            return importer.import_config(input_path)
        except Exception as e:
            logger.error(f"Error importing Ansible configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to import Ansible configuration: {str(e)}"
            }
    
    def get_export_formats(self) -> Dict:
        """Get available export formats and their configuration."""
        return {
            "success": True,
            "formats": {
                "terraform": {
                    "enabled": self.config["terraform"]["enabled"],
                    "resource_types": self.config["terraform"]["resource_types"]
                },
                "ansible": {
                    "enabled": self.config["ansible"]["enabled"],
                    "resource_types": self.config["ansible"]["resource_types"]
                }
            },
            "version_control": {
                "enabled": self.config["version_control"]["enabled"],
                "type": self.config["version_control"]["type"] if self.config["version_control"]["enabled"] else None
            }
        }