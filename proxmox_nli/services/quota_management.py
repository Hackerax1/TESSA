"""
Resource Quota Management Service.

This module provides functionality for managing resource quotas for users in Proxmox.
"""
import json
import os
import time
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class QuotaManagementService:
    """Service for managing resource quotas in Proxmox."""
    
    def __init__(self, proxmox_api=None):
        """Initialize the quota management service.
        
        Args:
            proxmox_api: The Proxmox API client instance
        """
        self.proxmox_api = proxmox_api
        self.quota_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      'data', 'quotas.json')
        self.quotas = self._load_quotas()
        
    def _load_quotas(self) -> Dict:
        """Load quotas from the quota file.
        
        Returns:
            Dict: The loaded quotas
        """
        if not os.path.exists(self.quota_file):
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
            return {
                "users": {},
                "groups": {},
                "defaults": {
                    "cpu": 2,
                    "memory": 2048,  # MB
                    "disk": 20,      # GB
                    "vm_count": 2,
                    "container_count": 2,
                    "backup_size": 50  # GB
                }
            }
        
        try:
            with open(self.quota_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading quotas: {str(e)}")
            return {
                "users": {},
                "groups": {},
                "defaults": {
                    "cpu": 2,
                    "memory": 2048,  # MB
                    "disk": 20,      # GB
                    "vm_count": 2,
                    "container_count": 2,
                    "backup_size": 50  # GB
                }
            }
    
    def _save_quotas(self) -> bool:
        """Save quotas to the quota file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.quota_file, 'w') as f:
                json.dump(self.quotas, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving quotas: {str(e)}")
            return False
    
    def get_user_quota(self, user_id: str) -> Dict:
        """Get the quota for a specific user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dict: The user's quota
        """
        if user_id not in self.quotas["users"]:
            # Return default quotas if user doesn't have specific quotas
            return self.quotas["defaults"].copy()
        
        # Merge user quotas with defaults for any missing values
        user_quota = self.quotas["users"][user_id].copy()
        for key, value in self.quotas["defaults"].items():
            if key not in user_quota:
                user_quota[key] = value
        
        return user_quota
    
    def set_user_quota(self, user_id: str, quota: Dict) -> bool:
        """Set the quota for a specific user.
        
        Args:
            user_id: The user ID
            quota: The quota to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate quota values
        for key, value in quota.items():
            if key not in self.quotas["defaults"]:
                return False
            
            if not isinstance(value, (int, float)) or value < 0:
                return False
        
        # Update or create user quota
        if user_id not in self.quotas["users"]:
            self.quotas["users"][user_id] = {}
        
        # Update only the provided quota values
        for key, value in quota.items():
            self.quotas["users"][user_id][key] = value
        
        return self._save_quotas()
    
    def delete_user_quota(self, user_id: str) -> bool:
        """Delete the quota for a specific user.
        
        Args:
            user_id: The user ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if user_id in self.quotas["users"]:
            del self.quotas["users"][user_id]
            return self._save_quotas()
        
        return True  # User didn't have quotas, so technically successful
    
    def get_group_quota(self, group_id: str) -> Dict:
        """Get the quota for a specific group.
        
        Args:
            group_id: The group ID
            
        Returns:
            Dict: The group's quota
        """
        if group_id not in self.quotas["groups"]:
            # Return default quotas if group doesn't have specific quotas
            return self.quotas["defaults"].copy()
        
        # Merge group quotas with defaults for any missing values
        group_quota = self.quotas["groups"][group_id].copy()
        for key, value in self.quotas["defaults"].items():
            if key not in group_quota:
                group_quota[key] = value
        
        return group_quota
    
    def set_group_quota(self, group_id: str, quota: Dict) -> bool:
        """Set the quota for a specific group.
        
        Args:
            group_id: The group ID
            quota: The quota to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate quota values
        for key, value in quota.items():
            if key not in self.quotas["defaults"]:
                return False
            
            if not isinstance(value, (int, float)) or value < 0:
                return False
        
        # Update or create group quota
        if group_id not in self.quotas["groups"]:
            self.quotas["groups"][group_id] = {}
        
        # Update only the provided quota values
        for key, value in quota.items():
            self.quotas["groups"][group_id][key] = value
        
        return self._save_quotas()
    
    def delete_group_quota(self, group_id: str) -> bool:
        """Delete the quota for a specific group.
        
        Args:
            group_id: The group ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if group_id in self.quotas["groups"]:
            del self.quotas["groups"][group_id]
            return self._save_quotas()
        
        return True  # Group didn't have quotas, so technically successful
    
    def get_default_quotas(self) -> Dict:
        """Get the default quotas.
        
        Returns:
            Dict: The default quotas
        """
        return self.quotas["defaults"].copy()
    
    def set_default_quotas(self, quotas: Dict) -> bool:
        """Set the default quotas.
        
        Args:
            quotas: The default quotas to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Validate quota values
        for key, value in quotas.items():
            if key not in self.quotas["defaults"]:
                return False
            
            if not isinstance(value, (int, float)) or value < 0:
                return False
        
        # Update default quotas
        for key, value in quotas.items():
            self.quotas["defaults"][key] = value
        
        return self._save_quotas()
    
    def get_all_quotas(self) -> Dict:
        """Get all quotas.
        
        Returns:
            Dict: All quotas
        """
        return self.quotas.copy()
    
    def check_quota_compliance(self, user_id: str) -> Tuple[bool, Dict]:
        """Check if a user is compliant with their quotas.
        
        Args:
            user_id: The user ID
            
        Returns:
            Tuple[bool, Dict]: Tuple containing compliance status and details
        """
        if not self.proxmox_api:
            return False, {"error": "Proxmox API not available"}
        
        user_quota = self.get_user_quota(user_id)
        
        # Get user's current resource usage
        try:
            # Get VMs owned by user
            vms = self._get_user_vms(user_id)
            
            # Calculate total resources used
            total_cpu = sum(vm.get('cpu', 0) for vm in vms)
            total_memory = sum(vm.get('memory', 0) for vm in vms)  # MB
            total_disk = sum(vm.get('disk', 0) for vm in vms)  # GB
            vm_count = sum(1 for vm in vms if vm.get('type') == 'qemu')
            container_count = sum(1 for vm in vms if vm.get('type') == 'lxc')
            
            # Get backup usage
            backup_size = self._get_user_backup_size(user_id)  # GB
            
            # Check compliance
            compliance = {
                "cpu": {
                    "used": total_cpu,
                    "limit": user_quota["cpu"],
                    "compliant": total_cpu <= user_quota["cpu"]
                },
                "memory": {
                    "used": total_memory,
                    "limit": user_quota["memory"],
                    "compliant": total_memory <= user_quota["memory"]
                },
                "disk": {
                    "used": total_disk,
                    "limit": user_quota["disk"],
                    "compliant": total_disk <= user_quota["disk"]
                },
                "vm_count": {
                    "used": vm_count,
                    "limit": user_quota["vm_count"],
                    "compliant": vm_count <= user_quota["vm_count"]
                },
                "container_count": {
                    "used": container_count,
                    "limit": user_quota["container_count"],
                    "compliant": container_count <= user_quota["container_count"]
                },
                "backup_size": {
                    "used": backup_size,
                    "limit": user_quota["backup_size"],
                    "compliant": backup_size <= user_quota["backup_size"]
                }
            }
            
            # Overall compliance
            is_compliant = all(item["compliant"] for item in compliance.values())
            
            return is_compliant, compliance
            
        except Exception as e:
            logger.error(f"Error checking quota compliance: {str(e)}")
            return False, {"error": str(e)}
    
    def _get_user_vms(self, user_id: str) -> List[Dict]:
        """Get VMs owned by a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List[Dict]: List of VMs owned by the user
        """
        # This is a simplified implementation
        # In a real implementation, you would query the Proxmox API
        # to get the VMs owned by the user
        
        if not self.proxmox_api:
            return []
        
        try:
            # Get all VMs and containers
            nodes = self.proxmox_api.nodes.get()
            
            user_vms = []
            for node in nodes:
                node_name = node['node']
                
                # Get VMs
                vms = self.proxmox_api.nodes(node_name).qemu.get()
                for vm in vms:
                    vm_id = vm['vmid']
                    config = self.proxmox_api.nodes(node_name).qemu(vm_id).config.get()
                    
                    # Check if VM belongs to user
                    # This depends on how you track ownership in your Proxmox setup
                    # For example, you might use a custom property or description
                    if 'description' in config and f"owner:{user_id}" in config['description']:
                        user_vms.append({
                            'id': vm_id,
                            'name': vm.get('name', f"VM {vm_id}"),
                            'type': 'qemu',
                            'node': node_name,
                            'cpu': config.get('cores', 1) * config.get('sockets', 1),
                            'memory': config.get('memory', 512),  # MB
                            'disk': self._calculate_vm_disk_size(node_name, vm_id, 'qemu')  # GB
                        })
                
                # Get containers
                containers = self.proxmox_api.nodes(node_name).lxc.get()
                for container in containers:
                    container_id = container['vmid']
                    config = self.proxmox_api.nodes(node_name).lxc(container_id).config.get()
                    
                    # Check if container belongs to user
                    if 'description' in config and f"owner:{user_id}" in config['description']:
                        user_vms.append({
                            'id': container_id,
                            'name': container.get('name', f"CT {container_id}"),
                            'type': 'lxc',
                            'node': node_name,
                            'cpu': config.get('cores', 1),
                            'memory': config.get('memory', 512),  # MB
                            'disk': self._calculate_vm_disk_size(node_name, container_id, 'lxc')  # GB
                        })
            
            return user_vms
        except Exception as e:
            logger.error(f"Error getting user VMs: {str(e)}")
            return []
    
    def _calculate_vm_disk_size(self, node: str, vm_id: int, vm_type: str) -> float:
        """Calculate the total disk size for a VM or container.
        
        Args:
            node: The node name
            vm_id: The VM or container ID
            vm_type: The VM type ('qemu' or 'lxc')
            
        Returns:
            float: The total disk size in GB
        """
        if not self.proxmox_api:
            return 0
        
        try:
            # Get disk configuration
            if vm_type == 'qemu':
                config = self.proxmox_api.nodes(node).qemu(vm_id).config.get()
            else:  # lxc
                config = self.proxmox_api.nodes(node).lxc(vm_id).config.get()
            
            # Calculate total disk size
            total_size = 0
            for key, value in config.items():
                if key.startswith('scsi') or key.startswith('virtio') or key.startswith('ide') or key.startswith('sata') or key.startswith('rootfs'):
                    # Extract size from disk configuration
                    # Format is typically: storage:size,format=raw
                    if isinstance(value, str) and ':' in value:
                        size_part = value.split(':')[1].split(',')[0]
                        if size_part.endswith('G'):
                            total_size += float(size_part[:-1])
                        elif size_part.endswith('M'):
                            total_size += float(size_part[:-1]) / 1024
                        elif size_part.endswith('T'):
                            total_size += float(size_part[:-1]) * 1024
            
            return total_size
        except Exception as e:
            logger.error(f"Error calculating VM disk size: {str(e)}")
            return 0
    
    def _get_user_backup_size(self, user_id: str) -> float:
        """Get the total backup size for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            float: The total backup size in GB
        """
        if not self.proxmox_api:
            return 0
        
        try:
            # Get user's VMs
            user_vms = self._get_user_vms(user_id)
            vm_ids = [vm['id'] for vm in user_vms]
            
            # Get all backups
            total_size = 0
            storages = self.proxmox_api.storage.get()
            
            for storage in storages:
                storage_id = storage['storage']
                
                # Check if storage is used for backups
                if 'backup' in storage.get('content', ''):
                    # Get backup list
                    backups = self.proxmox_api.storage(storage_id).content.get()
                    
                    # Filter backups for user's VMs
                    for backup in backups:
                        if 'volid' in backup and any(f"vm-{vm_id}-" in backup['volid'] for vm_id in vm_ids):
                            total_size += backup.get('size', 0) / (1024 * 1024 * 1024)  # Convert to GB
            
            return total_size
        except Exception as e:
            logger.error(f"Error getting user backup size: {str(e)}")
            return 0
    
    def enforce_quotas(self, user_id: str) -> Tuple[bool, Dict]:
        """Enforce quotas for a user.
        
        This is a more advanced feature that would require careful implementation
        in a production environment. It could potentially stop VMs or prevent
        new resource allocation if quotas are exceeded.
        
        Args:
            user_id: The user ID
            
        Returns:
            Tuple[bool, Dict]: Tuple containing success status and details
        """
        # Check quota compliance
        is_compliant, compliance = self.check_quota_compliance(user_id)
        
        if is_compliant:
            return True, {"message": "User is compliant with quotas"}
        
        # For now, we'll just return the non-compliant resources
        # In a real implementation, you might take action to enforce quotas
        non_compliant = {
            key: value for key, value in compliance.items() 
            if isinstance(value, dict) and not value.get("compliant", True)
        }
        
        return False, {
            "message": "User exceeds quota limits",
            "non_compliant": non_compliant
        }
    
    def get_quota_usage_report(self, user_id: str = None) -> Dict:
        """Get a report of quota usage.
        
        Args:
            user_id: Optional user ID to filter report
            
        Returns:
            Dict: The quota usage report
        """
        if user_id:
            # Get report for specific user
            is_compliant, compliance = self.check_quota_compliance(user_id)
            
            return {
                "user_id": user_id,
                "is_compliant": is_compliant,
                "compliance": compliance,
                "quota": self.get_user_quota(user_id)
            }
        else:
            # Get report for all users
            report = {
                "users": {},
                "groups": {},
                "defaults": self.get_default_quotas()
            }
            
            # Get user reports
            for user_id in self.quotas["users"]:
                is_compliant, compliance = self.check_quota_compliance(user_id)
                
                report["users"][user_id] = {
                    "is_compliant": is_compliant,
                    "compliance": compliance,
                    "quota": self.get_user_quota(user_id)
                }
            
            # Group reports would be similar but require group membership info
            
            return report

# Initialize the quota management service
quota_management_service = QuotaManagementService()
