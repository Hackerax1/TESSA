"""
Base Migration Service Module

This module provides the foundation for all migration services, defining common
interfaces and functionality for migrating from various platforms to Proxmox.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple

from proxmox_nli.services.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class MigrationBase(ABC):
    """Base class for all migration services"""
    
    def __init__(self, proxmox_api: ProxmoxAPI, config: Optional[Dict] = None):
        """
        Initialize the migration service
        
        Args:
            proxmox_api: Instance of ProxmoxAPI for interacting with Proxmox
            config: Optional configuration dictionary
        """
        self.proxmox_api = proxmox_api
        self.config = config or {}
        self.migration_data = {}
        self.source_platform = "unknown"
        self.migration_id = None
        self.migration_status = "not_started"
        self.errors = []
        self.warnings = []
        
    @abstractmethod
    def validate_source_credentials(self, credentials: Dict) -> Dict:
        """
        Validate credentials for the source platform
        
        Args:
            credentials: Dictionary containing credentials for the source platform
            
        Returns:
            Dict with validation results
        """
        pass
    
    @abstractmethod
    def analyze_source_environment(self, credentials: Dict) -> Dict:
        """
        Analyze the source environment to identify resources for migration
        
        Args:
            credentials: Dictionary containing credentials for the source platform
            
        Returns:
            Dict with analysis results
        """
        pass
    
    @abstractmethod
    def create_migration_plan(self, source_resources: Dict, target_node: str) -> Dict:
        """
        Create a migration plan based on source resources and target node
        
        Args:
            source_resources: Dictionary of resources from the source platform
            target_node: Target Proxmox node for migration
            
        Returns:
            Dict with migration plan
        """
        pass
    
    @abstractmethod
    def execute_migration(self, migration_plan: Dict, progress_callback=None) -> Dict:
        """
        Execute the migration plan
        
        Args:
            migration_plan: Dictionary containing the migration plan
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict with migration results
        """
        pass
    
    def save_migration_state(self, state_dir: Optional[str] = None) -> str:
        """
        Save the current migration state to a file
        
        Args:
            state_dir: Optional directory to save state file
            
        Returns:
            Path to the saved state file
        """
        if not state_dir:
            state_dir = os.path.join(os.path.dirname(__file__), "migration_states")
        
        os.makedirs(state_dir, exist_ok=True)
        
        if not self.migration_id:
            import uuid
            self.migration_id = str(uuid.uuid4())
        
        state_file = os.path.join(state_dir, f"{self.source_platform}_{self.migration_id}.json")
        
        state = {
            "migration_id": self.migration_id,
            "source_platform": self.source_platform,
            "status": self.migration_status,
            "data": self.migration_data,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        return state_file
    
    def load_migration_state(self, migration_id: str, state_dir: Optional[str] = None) -> Dict:
        """
        Load a migration state from a file
        
        Args:
            migration_id: ID of the migration to load
            state_dir: Optional directory to load state file from
            
        Returns:
            Dict with loaded state
        """
        if not state_dir:
            state_dir = os.path.join(os.path.dirname(__file__), "migration_states")
        
        state_file = os.path.join(state_dir, f"{self.source_platform}_{migration_id}.json")
        
        if not os.path.exists(state_file):
            raise FileNotFoundError(f"Migration state file not found: {state_file}")
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        self.migration_id = state.get("migration_id")
        self.migration_status = state.get("status")
        self.migration_data = state.get("data", {})
        self.errors = state.get("errors", [])
        self.warnings = state.get("warnings", [])
        
        return state
    
    def list_migrations(self, state_dir: Optional[str] = None) -> List[Dict]:
        """
        List all migrations for the current platform
        
        Args:
            state_dir: Optional directory to look for state files
            
        Returns:
            List of migration states
        """
        if not state_dir:
            state_dir = os.path.join(os.path.dirname(__file__), "migration_states")
        
        if not os.path.exists(state_dir):
            return []
        
        migrations = []
        
        for filename in os.listdir(state_dir):
            if filename.startswith(f"{self.source_platform}_") and filename.endswith(".json"):
                try:
                    with open(os.path.join(state_dir, filename), 'r') as f:
                        state = json.load(f)
                        migrations.append({
                            "migration_id": state.get("migration_id"),
                            "source_platform": state.get("source_platform"),
                            "status": state.get("status"),
                            "created_at": state.get("data", {}).get("created_at"),
                            "updated_at": state.get("data", {}).get("updated_at")
                        })
                except Exception as e:
                    logger.error(f"Error loading migration state file {filename}: {str(e)}")
        
        return migrations
    
    def validate_target_environment(self, node: str) -> Tuple[bool, List[str]]:
        """
        Validate the target Proxmox environment for migration
        
        Args:
            node: Target Proxmox node
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if node exists
        try:
            node_status = self.proxmox_api.get_node_status(node)
            if not node_status.get("success", False):
                issues.append(f"Node {node} not found or not accessible")
                return False, issues
        except Exception as e:
            issues.append(f"Error checking node status: {str(e)}")
            return False, issues
        
        # Check if node is online
        if node_status.get("data", {}).get("status") != "online":
            issues.append(f"Node {node} is not online")
        
        # Check storage availability
        try:
            storages = self.proxmox_api.get_node_storages(node)
            if not storages.get("success", False) or not storages.get("data"):
                issues.append("No storage available on target node")
        except Exception as e:
            issues.append(f"Error checking storage availability: {str(e)}")
        
        # Check network availability
        try:
            networks = self.proxmox_api.get_node_networks(node)
            if not networks.get("success", False) or not networks.get("data"):
                issues.append("No networks available on target node")
        except Exception as e:
            issues.append(f"Error checking network availability: {str(e)}")
        
        return len(issues) == 0, issues
    
    def estimate_migration_resources(self, source_resources: Dict) -> Dict:
        """
        Estimate resources needed for migration
        
        Args:
            source_resources: Dictionary of resources from source platform
            
        Returns:
            Dict with resource estimates
        """
        # Default implementation - override in platform-specific classes for better estimates
        vms = source_resources.get("vms", [])
        containers = source_resources.get("containers", [])
        storage = source_resources.get("storage", [])
        
        total_memory = sum(vm.get("memory", 0) for vm in vms)
        total_memory += sum(container.get("memory", 0) for container in containers)
        
        total_storage = sum(vm.get("disk_size", 0) for vm in vms)
        total_storage += sum(container.get("disk_size", 0) for container in containers)
        total_storage += sum(vol.get("size", 0) for vol in storage)
        
        total_vcpus = sum(vm.get("vcpus", 0) for vm in vms)
        total_vcpus += sum(container.get("vcpus", 0) for container in containers)
        
        return {
            "memory_required_mb": total_memory,
            "storage_required_bytes": total_storage,
            "vcpus_required": total_vcpus,
            "estimated_migration_time_seconds": self._estimate_migration_time(total_storage),
            "vm_count": len(vms),
            "container_count": len(containers),
            "storage_volume_count": len(storage)
        }
    
    def _estimate_migration_time(self, total_bytes: int) -> int:
        """
        Estimate migration time based on total bytes to transfer
        
        Args:
            total_bytes: Total bytes to transfer
            
        Returns:
            Estimated seconds for migration
        """
        # Assume 50 MB/s transfer rate as a conservative estimate
        transfer_rate_bytes_per_second = 50 * 1024 * 1024
        
        # Add 20% overhead for processing
        return int((total_bytes / transfer_rate_bytes_per_second) * 1.2)
    
    def generate_migration_report(self) -> Dict:
        """
        Generate a report of the migration
        
        Returns:
            Dict with migration report
        """
        if not self.migration_data:
            return {
                "success": False,
                "message": "No migration data available"
            }
        
        report = {
            "migration_id": self.migration_id,
            "source_platform": self.source_platform,
            "status": self.migration_status,
            "start_time": self.migration_data.get("start_time"),
            "end_time": self.migration_data.get("end_time"),
            "duration_seconds": None,
            "resources_migrated": {
                "vms": [],
                "containers": [],
                "storage": []
            },
            "success_rate": 0,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        # Calculate duration if start and end times are available
        if report["start_time"] and report["end_time"]:
            from datetime import datetime
            start = datetime.fromisoformat(report["start_time"])
            end = datetime.fromisoformat(report["end_time"])
            report["duration_seconds"] = (end - start).total_seconds()
        
        # Add migrated resources
        migrated_vms = self.migration_data.get("migrated_vms", [])
        migrated_containers = self.migration_data.get("migrated_containers", [])
        migrated_storage = self.migration_data.get("migrated_storage", [])
        
        report["resources_migrated"]["vms"] = migrated_vms
        report["resources_migrated"]["containers"] = migrated_containers
        report["resources_migrated"]["storage"] = migrated_storage
        
        # Calculate success rate
        total_resources = len(migrated_vms) + len(migrated_containers) + len(migrated_storage)
        successful_resources = sum(1 for vm in migrated_vms if vm.get("success", False))
        successful_resources += sum(1 for container in migrated_containers if container.get("success", False))
        successful_resources += sum(1 for storage in migrated_storage if storage.get("success", False))
        
        if total_resources > 0:
            report["success_rate"] = (successful_resources / total_resources) * 100
        
        return report
