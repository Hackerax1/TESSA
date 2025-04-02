"""
Storage Mapper Utility for Migration Services

This module provides utilities for mapping storage resources between different
platforms, handling storage pool conversion, dataset migration, and storage
configuration translation.
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Tuple, Union

from proxmox_nli.services.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class StorageMapper:
    """Storage mapper for cross-platform migrations"""
    
    def __init__(self, proxmox_api: ProxmoxAPI):
        """
        Initialize storage mapper
        
        Args:
            proxmox_api: Instance of ProxmoxAPI for interacting with Proxmox
        """
        self.proxmox_api = proxmox_api
    
    def get_proxmox_storage_types(self) -> Dict[str, Dict]:
        """
        Get available Proxmox storage types with their capabilities
        
        Returns:
            Dict of storage types and their capabilities
        """
        return {
            "dir": {
                "description": "Directory",
                "can_store": ["images", "iso", "backup", "snippets", "rootdir"],
                "features": ["shared"]
            },
            "lvm": {
                "description": "LVM",
                "can_store": ["images", "rootdir"],
                "features": ["snapshots"]
            },
            "lvmthin": {
                "description": "LVM-Thin",
                "can_store": ["images", "rootdir"],
                "features": ["snapshots", "thin"]
            },
            "zfspool": {
                "description": "ZFS Pool",
                "can_store": ["images", "rootdir"],
                "features": ["snapshots", "clone", "thin"]
            },
            "cifs": {
                "description": "CIFS",
                "can_store": ["images", "iso", "backup", "snippets"],
                "features": ["shared"]
            },
            "nfs": {
                "description": "NFS",
                "can_store": ["images", "iso", "backup", "snippets"],
                "features": ["shared"]
            },
            "glusterfs": {
                "description": "GlusterFS",
                "can_store": ["images", "iso", "backup", "snippets"],
                "features": ["shared"]
            },
            "cephfs": {
                "description": "CephFS",
                "can_store": ["images", "iso", "backup", "snippets"],
                "features": ["shared"]
            },
            "rbd": {
                "description": "Ceph RBD",
                "can_store": ["images"],
                "features": ["snapshots", "clone", "thin", "shared"]
            },
            "iscsi": {
                "description": "iSCSI",
                "can_store": ["images"],
                "features": []
            },
            "drbd": {
                "description": "DRBD",
                "can_store": ["images"],
                "features": ["shared"]
            }
        }
    
    def get_proxmox_storages(self, node: str) -> List[Dict]:
        """
        Get available storages on Proxmox node
        
        Args:
            node: Proxmox node name
            
        Returns:
            List of storage configurations
        """
        try:
            result = self.proxmox_api.get_node_storages(node)
            
            if not result.get("success", False):
                logger.error(f"Failed to get storages: {result.get('message', 'Unknown error')}")
                return []
            
            return result.get("data", [])
            
        except Exception as e:
            logger.error(f"Error getting storages: {str(e)}")
            return []
    
    def find_best_storage_for_vms(self, node: str) -> Optional[str]:
        """
        Find the best storage for VM images on a node
        
        Args:
            node: Proxmox node name
            
        Returns:
            Storage ID or None if not found
        """
        storages = self.get_proxmox_storages(node)
        
        # Preferred storage types for VMs in order of preference
        preferred_types = ["zfspool", "rbd", "lvmthin", "lvm", "dir"]
        
        # First, look for storages that can store VM images
        vm_storages = [s for s in storages if "images" in s.get("content", [])]
        
        if not vm_storages:
            return None
        
        # Then, find the best storage based on type preference
        for storage_type in preferred_types:
            for storage in vm_storages:
                if storage.get("type") == storage_type:
                    return storage.get("storage")
        
        # If no preferred type found, return the first VM storage
        return vm_storages[0].get("storage")
    
    def find_best_storage_for_containers(self, node: str) -> Optional[str]:
        """
        Find the best storage for container templates on a node
        
        Args:
            node: Proxmox node name
            
        Returns:
            Storage ID or None if not found
        """
        storages = self.get_proxmox_storages(node)
        
        # Look for storages that can store container templates
        ct_storages = [s for s in storages if "vztmpl" in s.get("content", [])]
        
        if not ct_storages:
            # Fall back to storages that can store rootdirs
            ct_storages = [s for s in storages if "rootdir" in s.get("content", [])]
            
            if not ct_storages:
                return None
        
        # Prefer local storage for containers
        for storage in ct_storages:
            if storage.get("storage") == "local":
                return "local"
        
        # Otherwise, return the first container storage
        return ct_storages[0].get("storage")
    
    def map_unraid_share_to_proxmox(self, share_config: Dict, node: str) -> Dict:
        """
        Map Unraid share to Proxmox storage
        
        Args:
            share_config: Unraid share configuration
            node: Target Proxmox node
            
        Returns:
            Dict with mapping results
        """
        share_name = share_config.get("name", "")
        share_path = share_config.get("path", "")
        
        if not share_name or not share_path:
            return {
                "success": False,
                "message": "Invalid share configuration"
            }
        
        # Check if storage already exists
        storages = self.get_proxmox_storages(node)
        for storage in storages:
            if storage.get("storage") == share_name:
                return {
                    "success": True,
                    "message": f"Storage {share_name} already exists",
                    "storage_id": share_name,
                    "already_exists": True
                }
        
        # Create new storage
        storage_config = {
            "storage": share_name,
            "type": "dir",
            "path": f"/mnt/unraid_shares/{share_name}",
            "content": "images,iso,backup",
            "nodes": node,
            "shared": 0
        }
        
        try:
            # Create the directory on the node
            mkdir_cmd = ["ssh", node, f"mkdir -p {storage_config['path']}"]
            subprocess.run(mkdir_cmd, check=True, capture_output=True)
            
            # Create the storage
            result = self.proxmox_api.create_storage(storage_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create storage: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created storage {share_name}",
                "storage_id": share_name,
                "already_exists": False
            }
            
        except Exception as e:
            logger.error(f"Error creating storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating storage: {str(e)}"
            }
    
    def map_truenas_dataset_to_proxmox(self, dataset_config: Dict, node: str) -> Dict:
        """
        Map TrueNAS ZFS dataset to Proxmox storage
        
        Args:
            dataset_config: TrueNAS dataset configuration
            node: Target Proxmox node
            
        Returns:
            Dict with mapping results
        """
        dataset_name = dataset_config.get("name", "")
        dataset_path = dataset_config.get("mountpoint", "")
        
        if not dataset_name or not dataset_path:
            return {
                "success": False,
                "message": "Invalid dataset configuration"
            }
        
        # Extract the last part of the dataset name for storage ID
        storage_name = dataset_name.split("/")[-1]
        
        # Check if storage already exists
        storages = self.get_proxmox_storages(node)
        for storage in storages:
            if storage.get("storage") == storage_name:
                return {
                    "success": True,
                    "message": f"Storage {storage_name} already exists",
                    "storage_id": storage_name,
                    "already_exists": True
                }
        
        # Determine if we should create a ZFS pool or NFS storage
        if dataset_config.get("type") == "zfs" and dataset_config.get("available_locally", False):
            # Create ZFS pool storage
            storage_config = {
                "storage": storage_name,
                "type": "zfspool",
                "pool": dataset_name,
                "content": "images,rootdir",
                "nodes": node,
                "sparse": 1
            }
        else:
            # Create NFS storage
            storage_config = {
                "storage": storage_name,
                "type": "nfs",
                "server": dataset_config.get("server_ip", ""),
                "export": dataset_path,
                "content": "images,iso,backup",
                "nodes": node,
                "shared": 1
            }
        
        try:
            # Create the storage
            result = self.proxmox_api.create_storage(storage_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create storage: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created storage {storage_name}",
                "storage_id": storage_name,
                "already_exists": False
            }
            
        except Exception as e:
            logger.error(f"Error creating storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating storage: {str(e)}"
            }
    
    def map_esxi_datastore_to_proxmox(self, datastore_config: Dict, node: str) -> Dict:
        """
        Map ESXi datastore to Proxmox storage
        
        Args:
            datastore_config: ESXi datastore configuration
            node: Target Proxmox node
            
        Returns:
            Dict with mapping results
        """
        datastore_name = datastore_config.get("name", "")
        datastore_type = datastore_config.get("type", "").lower()
        
        if not datastore_name:
            return {
                "success": False,
                "message": "Invalid datastore configuration"
            }
        
        # Create storage name from datastore name
        storage_name = f"esxi_{datastore_name.lower().replace(' ', '_')}"
        
        # Check if storage already exists
        storages = self.get_proxmox_storages(node)
        for storage in storages:
            if storage.get("storage") == storage_name:
                return {
                    "success": True,
                    "message": f"Storage {storage_name} already exists",
                    "storage_id": storage_name,
                    "already_exists": True
                }
        
        # Map datastore type to Proxmox storage type
        if datastore_type == "vmfs":
            # For local VMFS datastores, create a directory storage
            storage_config = {
                "storage": storage_name,
                "type": "dir",
                "path": f"/mnt/esxi_datastores/{datastore_name}",
                "content": "images,iso,backup",
                "nodes": node,
                "shared": 0
            }
        elif datastore_type == "nfs":
            # For NFS datastores, create NFS storage
            storage_config = {
                "storage": storage_name,
                "type": "nfs",
                "server": datastore_config.get("server", ""),
                "export": datastore_config.get("path", ""),
                "content": "images,iso,backup",
                "nodes": node,
                "shared": 1
            }
        elif datastore_type == "vsan":
            # For vSAN datastores, create a directory storage (limited support)
            storage_config = {
                "storage": storage_name,
                "type": "dir",
                "path": f"/mnt/esxi_datastores/{datastore_name}",
                "content": "images,iso,backup",
                "nodes": node,
                "shared": 0
            }
        else:
            # Default to directory storage
            storage_config = {
                "storage": storage_name,
                "type": "dir",
                "path": f"/mnt/esxi_datastores/{datastore_name}",
                "content": "images,iso,backup",
                "nodes": node,
                "shared": 0
            }
        
        try:
            # Create the directory on the node if needed
            if storage_config["type"] == "dir":
                mkdir_cmd = ["ssh", node, f"mkdir -p {storage_config['path']}"]
                subprocess.run(mkdir_cmd, check=True, capture_output=True)
            
            # Create the storage
            result = self.proxmox_api.create_storage(storage_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create storage: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created storage {storage_name}",
                "storage_id": storage_name,
                "already_exists": False
            }
            
        except Exception as e:
            logger.error(f"Error creating storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating storage: {str(e)}"
            }
    
    def setup_zfs_replication(self, source_config: Dict, target_node: str) -> Dict:
        """
        Set up ZFS replication from source to Proxmox
        
        Args:
            source_config: Source ZFS configuration
            target_node: Target Proxmox node
            
        Returns:
            Dict with setup results
        """
        source_dataset = source_config.get("dataset", "")
        source_host = source_config.get("host", "")
        source_user = source_config.get("user", "root")
        target_pool = source_config.get("target_pool", "")
        
        if not source_dataset or not source_host or not target_pool:
            return {
                "success": False,
                "message": "Missing required ZFS replication parameters"
            }
        
        try:
            # Check if target pool exists
            check_pool_cmd = ["ssh", target_node, f"zpool list {target_pool}"]
            pool_result = subprocess.run(check_pool_cmd, capture_output=True, text=True)
            
            if pool_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Target pool {target_pool} does not exist on node {target_node}"
                }
            
            # Create ZFS replication script
            script_content = f"""#!/bin/bash
# ZFS replication from {source_host}:{source_dataset} to {target_node}:{target_pool}

# Create initial snapshot if needed
ssh {source_user}@{source_host} "zfs snapshot {source_dataset}@initial 2>/dev/null || true"

# Send initial snapshot
ssh {source_user}@{source_host} "zfs send {source_dataset}@initial" | zfs receive {target_pool}/{source_dataset.split('/')[-1]}

# Create replication cron job
echo "0 2 * * * root ssh {source_user}@{source_host} 'zfs snapshot {source_dataset}@daily-\$(date +\\%Y\\%m\\%d) && zfs send -i \$(zfs list -H -o name -t snapshot {source_dataset} | grep -v daily-\$(date +\\%Y\\%m\\%d) | tail -1) {source_dataset}@daily-\$(date +\\%Y\\%m\\%d)' | zfs receive {target_pool}/{source_dataset.split('/')[-1]}" > /etc/cron.d/zfs_replication_{source_dataset.split('/')[-1]}
"""
            
            # Save script to node
            script_path = f"/root/zfs_replication_{source_dataset.split('/')[-1]}.sh"
            script_cmd = ["ssh", target_node, f"cat > {script_path} << 'EOF'\n{script_content}\nEOF\nchmod +x {script_path}"]
            subprocess.run(script_cmd, check=True, shell=True)
            
            return {
                "success": True,
                "message": f"ZFS replication set up for {source_dataset} to {target_pool}",
                "script_path": script_path
            }
            
        except Exception as e:
            logger.error(f"Error setting up ZFS replication: {str(e)}")
            return {
                "success": False,
                "message": f"Error setting up ZFS replication: {str(e)}"
            }
    
    def create_backup_job(self, storage_id: str, node: str, schedule: str = "0 0 * * *") -> Dict:
        """
        Create a backup job for a storage
        
        Args:
            storage_id: Storage ID to back up
            node: Proxmox node
            schedule: Cron schedule for backup
            
        Returns:
            Dict with job creation results
        """
        try:
            # Find a suitable backup storage
            storages = self.get_proxmox_storages(node)
            backup_storages = [s for s in storages if "backup" in s.get("content", [])]
            
            if not backup_storages:
                return {
                    "success": False,
                    "message": "No backup storage available"
                }
            
            backup_storage = backup_storages[0].get("storage")
            
            # Create backup job configuration
            job_id = f"backup-{storage_id}"
            job_config = {
                "id": job_id,
                "node": node,
                "storage": backup_storage,
                "mode": "snapshot",
                "compress": "zstd",
                "schedule": schedule,
                "all": 0,
                "enabled": 1,
                "comment": f"Auto-created backup job for migrated storage {storage_id}"
            }
            
            # Create backup job
            result = self.proxmox_api.create_backup_job(job_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create backup job: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created backup job for storage {storage_id}",
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"Error creating backup job: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating backup job: {str(e)}"
            }
