#!/usr/bin/env python3
"""
Configuration Validation and Rollback System
Provides validation and rollback capabilities for TESSA configurations
"""

import logging
import json
import os
import time
import shutil
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigValidator:
    """
    A system for validating configurations and providing rollback capabilities
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the configuration validator
        
        Args:
            config_dir: Directory where configurations are stored
        """
        self.config_dir = config_dir or os.path.join(os.path.expanduser("~"), ".tessa", "configs")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        self.validation_rules = self._load_validation_rules()
        
        # Create directories if they don't exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def _load_validation_rules(self) -> Dict:
        """
        Load validation rules from built-in definitions
        
        Returns:
            Dictionary of validation rules
        """
        # Define validation rules for different configuration types
        return {
            "vm": {
                "required_fields": ["name", "memory", "cores", "disk"],
                "constraints": {
                    "memory": {"min": 512, "max": 1024 * 1024},  # 512MB to 1TB
                    "cores": {"min": 1, "max": 128},
                    "disk": {"min": 1, "max": 64 * 1024}  # 1GB to 64TB
                },
                "dependencies": [
                    {"if": {"field": "template", "equals": True}, "then": {"required": ["template_id"]}}
                ]
            },
            "container": {
                "required_fields": ["name", "memory", "cores", "rootfs"],
                "constraints": {
                    "memory": {"min": 64, "max": 512 * 1024},  # 64MB to 512GB
                    "cores": {"min": 1, "max": 64},
                    "rootfs": {"min": 1, "max": 1024}  # 1GB to 1TB
                }
            },
            "network": {
                "required_fields": ["name", "type", "bridge"],
                "constraints": {
                    "type": {"enum": ["bridge", "bond", "vlan"]},
                    "vlan": {"min": 1, "max": 4094}
                },
                "dependencies": [
                    {"if": {"field": "type", "equals": "vlan"}, "then": {"required": ["vlan_id", "parent"]}}
                ]
            },
            "storage": {
                "required_fields": ["name", "type", "path"],
                "constraints": {
                    "type": {"enum": ["dir", "lvm", "zfs", "cifs", "nfs"]},
                    "size": {"min": 1, "max": 1024 * 1024}  # 1GB to 1PB
                },
                "dependencies": [
                    {"if": {"field": "type", "equals": "cifs"}, "then": {"required": ["server", "share"]}},
                    {"if": {"field": "type", "equals": "nfs"}, "then": {"required": ["server", "export"]}}
                ]
            },
            "backup": {
                "required_fields": ["name", "target", "schedule"],
                "constraints": {
                    "retention": {"min": 1, "max": 365}  # 1 day to 1 year
                }
            },
            "user": {
                "required_fields": ["username", "email"],
                "constraints": {
                    "username": {"pattern": "^[a-zA-Z0-9_-]{3,32}$"},
                    "email": {"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
                }
            },
            "service": {
                "required_fields": ["name", "type", "version"],
                "constraints": {
                    "port": {"min": 1, "max": 65535}
                },
                "dependencies": [
                    {"if": {"field": "type", "equals": "web"}, "then": {"required": ["port", "domain"]}}
                ]
            }
        }
        
    def backup_config(self, config_type: str, config_id: str, config_data: Dict) -> str:
        """
        Create a backup of a configuration
        
        Args:
            config_type: Type of configuration (vm, container, etc.)
            config_id: ID of the configuration
            config_data: Configuration data
            
        Returns:
            Backup ID
        """
        # Create backup ID
        timestamp = int(time.time())
        backup_id = f"{config_type}_{config_id}_{timestamp}"
        
        # Create backup directory
        backup_path = os.path.join(self.backup_dir, backup_id)
        os.makedirs(backup_path, exist_ok=True)
        
        # Save configuration data
        with open(os.path.join(backup_path, "config.json"), "w") as f:
            json.dump(config_data, f, indent=2)
            
        # Save metadata
        metadata = {
            "config_type": config_type,
            "config_id": config_id,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "checksum": hashlib.sha256(json.dumps(config_data).encode()).hexdigest()
        }
        
        with open(os.path.join(backup_path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Created backup {backup_id} for {config_type} {config_id}")
        
        return backup_id
        
    def validate_config(self, config_type: str, config_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a configuration against rules
        
        Args:
            config_type: Type of configuration (vm, container, etc.)
            config_data: Configuration data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if config_type not in self.validation_rules:
            return False, [f"Unknown configuration type: {config_type}"]
            
        rules = self.validation_rules[config_type]
        errors = []
        
        # Check required fields
        for field in rules.get("required_fields", []):
            if field not in config_data:
                errors.append(f"Missing required field: {field}")
                
        # Check constraints
        for field, constraint in rules.get("constraints", {}).items():
            if field in config_data:
                value = config_data[field]
                
                # Check min/max constraints
                if "min" in constraint and value < constraint["min"]:
                    errors.append(f"Field {field} value {value} is less than minimum {constraint['min']}")
                    
                if "max" in constraint and value > constraint["max"]:
                    errors.append(f"Field {field} value {value} is greater than maximum {constraint['max']}")
                    
                # Check enum constraints
                if "enum" in constraint and value not in constraint["enum"]:
                    errors.append(f"Field {field} value {value} is not one of {constraint['enum']}")
                    
                # Check pattern constraints
                if "pattern" in constraint:
                    import re
                    if not re.match(constraint["pattern"], value):
                        errors.append(f"Field {field} value {value} does not match pattern {constraint['pattern']}")
                        
        # Check dependencies
        for dependency in rules.get("dependencies", []):
            condition_field = dependency["if"]["field"]
            condition_value = dependency["if"]["equals"]
            
            if condition_field in config_data and config_data[condition_field] == condition_value:
                for required_field in dependency["then"]["required"]:
                    if required_field not in config_data:
                        errors.append(f"Field {required_field} is required when {condition_field} is {condition_value}")
                        
        return len(errors) == 0, errors
        
    def validate_and_backup(self, config_type: str, config_id: str, config_data: Dict) -> Tuple[bool, List[str], Optional[str]]:
        """
        Validate a configuration and create a backup if valid
        
        Args:
            config_type: Type of configuration (vm, container, etc.)
            config_id: ID of the configuration
            config_data: Configuration data
            
        Returns:
            Tuple of (is_valid, error_messages, backup_id)
        """
        is_valid, errors = self.validate_config(config_type, config_data)
        
        if is_valid:
            backup_id = self.backup_config(config_type, config_id, config_data)
            return True, [], backup_id
        else:
            return False, errors, None
            
    def list_backups(self, config_type: str = None, config_id: str = None) -> List[Dict]:
        """
        List available backups
        
        Args:
            config_type: Optional type of configuration to filter by
            config_id: Optional ID of configuration to filter by
            
        Returns:
            List of backup metadata
        """
        backups = []
        
        for backup_id in os.listdir(self.backup_dir):
            metadata_path = os.path.join(self.backup_dir, backup_id, "metadata.json")
            
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    
                # Apply filters
                if config_type and metadata["config_type"] != config_type:
                    continue
                    
                if config_id and metadata["config_id"] != config_id:
                    continue
                    
                backups.append({
                    "backup_id": backup_id,
                    **metadata
                })
                
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return backups
        
    def get_backup(self, backup_id: str) -> Optional[Dict]:
        """
        Get a backup by ID
        
        Args:
            backup_id: ID of the backup
            
        Returns:
            Backup data or None if not found
        """
        backup_path = os.path.join(self.backup_dir, backup_id)
        
        if not os.path.exists(backup_path):
            return None
            
        # Load metadata
        metadata_path = os.path.join(backup_path, "metadata.json")
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            
        # Load configuration data
        config_path = os.path.join(backup_path, "config.json")
        with open(config_path, "r") as f:
            config_data = json.load(f)
            
        return {
            "backup_id": backup_id,
            "metadata": metadata,
            "config": config_data
        }
        
    def rollback_config(self, backup_id: str) -> Tuple[bool, str]:
        """
        Rollback to a previous configuration
        
        Args:
            backup_id: ID of the backup to rollback to
            
        Returns:
            Tuple of (success, message)
        """
        backup = self.get_backup(backup_id)
        
        if not backup:
            return False, f"Backup {backup_id} not found"
            
        config_type = backup["metadata"]["config_type"]
        config_id = backup["metadata"]["config_id"]
        config_data = backup["config"]
        
        # Save current configuration as a new backup
        current_config_path = os.path.join(self.config_dir, f"{config_type}_{config_id}.json")
        
        if os.path.exists(current_config_path):
            with open(current_config_path, "r") as f:
                current_config = json.load(f)
                
            # Create backup of current configuration before rollback
            self.backup_config(config_type, config_id, current_config)
            
        # Write rollback configuration
        with open(current_config_path, "w") as f:
            json.dump(config_data, f, indent=2)
            
        logger.info(f"Rolled back {config_type} {config_id} to backup {backup_id}")
        
        return True, f"Successfully rolled back {config_type} {config_id} to backup {backup_id}"
        
    def compare_configs(self, config1: Dict, config2: Dict) -> Dict:
        """
        Compare two configurations and return differences
        
        Args:
            config1: First configuration
            config2: Second configuration
            
        Returns:
            Dictionary of differences
        """
        differences = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        # Find added and changed fields
        for key, value in config2.items():
            if key not in config1:
                differences["added"][key] = value
            elif config1[key] != value:
                differences["changed"][key] = {
                    "from": config1[key],
                    "to": value
                }
                
        # Find removed fields
        for key, value in config1.items():
            if key not in config2:
                differences["removed"][key] = value
                
        return differences
        
    def compare_with_backup(self, config_type: str, config_id: str, backup_id: str) -> Dict:
        """
        Compare current configuration with a backup
        
        Args:
            config_type: Type of configuration
            config_id: ID of the configuration
            backup_id: ID of the backup to compare with
            
        Returns:
            Dictionary of differences
        """
        # Get backup configuration
        backup = self.get_backup(backup_id)
        
        if not backup:
            return {"error": f"Backup {backup_id} not found"}
            
        backup_config = backup["config"]
        
        # Get current configuration
        current_config_path = os.path.join(self.config_dir, f"{config_type}_{config_id}.json")
        
        if not os.path.exists(current_config_path):
            return {"error": f"Current configuration {config_type}_{config_id} not found"}
            
        with open(current_config_path, "r") as f:
            current_config = json.load(f)
            
        # Compare configurations
        return self.compare_configs(backup_config, current_config)
        
    def validate_dependencies(self, config_type: str, config_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate dependencies between configurations
        
        Args:
            config_type: Type of configuration
            config_data: Configuration data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Define dependency validation rules
        dependency_rules = {
            "vm": {
                "storage": lambda vm, storage: all(
                    self._check_storage_exists(disk["storage"])
                    for disk in vm.get("disks", [])
                ),
                "network": lambda vm, network: all(
                    self._check_network_exists(nic["bridge"])
                    for nic in vm.get("net", [])
                )
            },
            "container": {
                "storage": lambda ct, storage: self._check_storage_exists(ct.get("rootfs", {}).get("storage")),
                "network": lambda ct, network: all(
                    self._check_network_exists(nic["bridge"])
                    for nic in ct.get("net", [])
                )
            },
            "service": {
                "vm": lambda service, vm: service.get("vm_id") is None or self._check_vm_exists(service.get("vm_id")),
                "container": lambda service, ct: service.get("ct_id") is None or self._check_container_exists(service.get("ct_id"))
            }
        }
        
        # Check dependencies for this config type
        if config_type in dependency_rules:
            for dep_type, validator in dependency_rules[config_type].items():
                if not validator(config_data, None):
                    errors.append(f"Invalid dependency on {dep_type}")
                    
        return len(errors) == 0, errors
        
    def _check_storage_exists(self, storage_id: str) -> bool:
        """Check if a storage exists"""
        storage_path = os.path.join(self.config_dir, f"storage_{storage_id}.json")
        return os.path.exists(storage_path)
        
    def _check_network_exists(self, network_id: str) -> bool:
        """Check if a network exists"""
        network_path = os.path.join(self.config_dir, f"network_{network_id}.json")
        return os.path.exists(network_path)
        
    def _check_vm_exists(self, vm_id: str) -> bool:
        """Check if a VM exists"""
        vm_path = os.path.join(self.config_dir, f"vm_{vm_id}.json")
        return os.path.exists(vm_path)
        
    def _check_container_exists(self, ct_id: str) -> bool:
        """Check if a container exists"""
        ct_path = os.path.join(self.config_dir, f"container_{ct_id}.json")
        return os.path.exists(ct_path)
        
    def get_config_history(self, config_type: str, config_id: str) -> List[Dict]:
        """
        Get the history of changes for a configuration
        
        Args:
            config_type: Type of configuration
            config_id: ID of the configuration
            
        Returns:
            List of historical changes
        """
        # Get all backups for this configuration
        backups = self.list_backups(config_type, config_id)
        
        if len(backups) <= 1:
            return []
            
        history = []
        
        # Compare each backup with the previous one
        for i in range(1, len(backups)):
            current = self.get_backup(backups[i]["backup_id"])
            previous = self.get_backup(backups[i-1]["backup_id"])
            
            if current and previous:
                differences = self.compare_configs(previous["config"], current["config"])
                
                history.append({
                    "timestamp": current["metadata"]["timestamp"],
                    "created_at": current["metadata"]["created_at"],
                    "backup_id": current["backup_id"],
                    "differences": differences
                })
                
        return history
        
    def cleanup_old_backups(self, max_age_days: int = 30, max_per_config: int = 10) -> int:
        """
        Clean up old backups
        
        Args:
            max_age_days: Maximum age of backups in days
            max_per_config: Maximum number of backups per configuration
            
        Returns:
            Number of backups removed
        """
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        removed_count = 0
        
        # Group backups by config type and id
        backups_by_config = {}
        
        for backup in self.list_backups():
            config_key = f"{backup['config_type']}_{backup['config_id']}"
            
            if config_key not in backups_by_config:
                backups_by_config[config_key] = []
                
            backups_by_config[config_key].append(backup)
            
        # Process each configuration
        for config_key, backups in backups_by_config.items():
            # Remove old backups
            for backup in backups:
                if now - backup["timestamp"] > max_age_seconds:
                    backup_path = os.path.join(self.backup_dir, backup["backup_id"])
                    shutil.rmtree(backup_path)
                    removed_count += 1
                    
            # Keep only the most recent backups if there are too many
            if len(backups) > max_per_config:
                # Sort by timestamp (newest first)
                backups.sort(key=lambda x: x["timestamp"], reverse=True)
                
                # Remove excess backups
                for backup in backups[max_per_config:]:
                    backup_path = os.path.join(self.backup_dir, backup["backup_id"])
                    shutil.rmtree(backup_path)
                    removed_count += 1
                    
        return removed_count
