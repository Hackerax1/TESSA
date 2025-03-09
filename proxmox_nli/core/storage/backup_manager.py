"""
Backup management module for Proxmox NLI.
Handles automated backups, verification, and disaster recovery.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import subprocess

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, api, base_dir=None):
        self.api = api
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(self.base_dir, 'config', 'backup_config.json')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load backup configuration"""
        if not os.path.exists(self.config_path):
            default_config = {
                "backup_locations": {
                    "local": os.path.join(self.base_dir, "backups"),
                    "remote": []
                },
                "retention": {
                    "hourly": 24,
                    "daily": 7,
                    "weekly": 4,
                    "monthly": 3
                },
                "verification": {
                    "enabled": True,
                    "frequency": "weekly"
                },
                "vms": {}
            }
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _save_config(self):
        """Save backup configuration"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def configure_backup(self, vm_id: str, schedule: Dict = None, location: str = "local") -> Dict:
        """Configure automated backups for a VM"""
        if schedule is None:
            schedule = {
                "frequency": "daily",
                "time": "02:00",
                "retention": self.config["retention"]
            }
            
        # Validate VM exists
        vm_info = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
        if not vm_info['success'] or not vm_info['data']:
            return {
                "success": False,
                "message": f"VM {vm_id} not found"
            }
            
        # Update configuration
        self.config["vms"][vm_id] = {
            "schedule": schedule,
            "location": location,
            "last_backup": None,
            "last_verification": None
        }
        self._save_config()
        
        return {
            "success": True,
            "message": f"Backup configured for VM {vm_id}",
            "config": self.config["vms"][vm_id]
        }
    
    def create_backup(self, vm_id: str, mode: str = "snapshot") -> Dict:
        """Create a backup of a VM"""
        try:
            # Get VM info
            vm_info = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
            if not vm_info['success'] or not vm_info['data']:
                return {
                    "success": False,
                    "message": f"VM {vm_id} not found"
                }
                
            # Determine backup location
            backup_config = self.config["vms"].get(vm_id, {})
            location = backup_config.get("location", "local")
            backup_path = self.config["backup_locations"][location]
            
            # Create backup directory if needed
            os.makedirs(backup_path, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_path, f'vm_{vm_id}_{timestamp}.vma.gz')
            
            # Create backup using vzdump
            result = self.api.api_request('POST', f'nodes/{vm_info["data"][0]["node"]}/vzdump', {
                'vmid': vm_id,
                'compress': 'gzip',
                'mode': mode,
                'storage': 'local',
                'remove': 0
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Backup failed: {result.get('message', 'Unknown error')}"
                }
                
            # Update backup history
            if vm_id not in self.config["vms"]:
                self.config["vms"][vm_id] = {
                    "schedule": {
                        "frequency": "daily",
                        "time": "02:00"
                    },
                    "location": location
                }
            
            self.config["vms"][vm_id]["last_backup"] = {
                "timestamp": timestamp,
                "file": backup_file,
                "size": os.path.getsize(backup_file),
                "checksum": self._calculate_checksum(backup_file)
            }
            self._save_config()
            
            # Verify backup if enabled
            if self.config["verification"]["enabled"]:
                verification = self.verify_backup(vm_id, backup_file)
                if not verification["success"]:
                    return {
                        "success": False,
                        "message": f"Backup created but verification failed: {verification['message']}"
                    }
            
            return {
                "success": True,
                "message": f"Backup created successfully: {backup_file}",
                "backup_info": self.config["vms"][vm_id]["last_backup"]
            }
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating backup: {str(e)}"
            }
    
    def verify_backup(self, vm_id: str, backup_file: str = None) -> Dict:
        """Verify a backup's integrity"""
        try:
            if not backup_file:
                # Use latest backup
                vm_config = self.config["vms"].get(vm_id, {})
                if not vm_config or "last_backup" not in vm_config:
                    return {
                        "success": False,
                        "message": "No backup found for verification"
                    }
                backup_file = vm_config["last_backup"]["file"]
            
            if not os.path.exists(backup_file):
                return {
                    "success": False,
                    "message": f"Backup file not found: {backup_file}"
                }
            
            # Calculate current checksum
            current_checksum = self._calculate_checksum(backup_file)
            
            # Compare with stored checksum
            stored_checksum = None
            for vm_config in self.config["vms"].values():
                if "last_backup" in vm_config and vm_config["last_backup"]["file"] == backup_file:
                    stored_checksum = vm_config["last_backup"]["checksum"]
                    break
            
            if stored_checksum and current_checksum != stored_checksum:
                return {
                    "success": False,
                    "message": "Backup verification failed: checksum mismatch"
                }
            
            # Test backup integrity
            result = subprocess.run(['qemu-img', 'check', backup_file], 
                                 capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Backup verification failed: {result.stderr}"
                }
            
            # Update verification timestamp
            if vm_id in self.config["vms"]:
                self.config["vms"][vm_id]["last_verification"] = datetime.now().isoformat()
                self._save_config()
            
            return {
                "success": True,
                "message": "Backup verification successful",
                "checksum": current_checksum
            }
            
        except Exception as e:
            logger.error(f"Error verifying backup: {str(e)}")
            return {
                "success": False,
                "message": f"Error verifying backup: {str(e)}"
            }
    
    def restore_backup(self, vm_id: str, backup_file: str = None, target_node: str = None) -> Dict:
        """Restore a VM from backup"""
        try:
            if not backup_file:
                # Use latest backup
                vm_config = self.config["vms"].get(vm_id, {})
                if not vm_config or "last_backup" not in vm_config:
                    return {
                        "success": False,
                        "message": "No backup found for restoration"
                    }
                backup_file = vm_config["last_backup"]["file"]
            
            if not os.path.exists(backup_file):
                return {
                    "success": False,
                    "message": f"Backup file not found: {backup_file}"
                }
            
            # Verify backup before restoration
            verification = self.verify_backup(vm_id, backup_file)
            if not verification["success"]:
                return {
                    "success": False,
                    "message": f"Backup verification failed: {verification['message']}"
                }
            
            # Determine target node
            if not target_node:
                nodes_result = self.api.api_request('GET', 'nodes')
                if not nodes_result['success'] or not nodes_result['data']:
                    return {
                        "success": False,
                        "message": "No nodes available for restoration"
                    }
                target_node = nodes_result['data'][0]['node']
            
            # Restore the VM
            result = self.api.api_request('POST', f'nodes/{target_node}/qmrestore', {
                'vmid': vm_id,
                'archive': backup_file,
                'force': 1
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Restoration failed: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"VM {vm_id} restored successfully from {backup_file}",
                "target_node": target_node
            }
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            return {
                "success": False,
                "message": f"Error restoring backup: {str(e)}"
            }
    
    def configure_remote_storage(self, storage_type: str, config: Dict) -> Dict:
        """Configure remote backup storage (S3, B2, etc.)"""
        try:
            # Validate storage configuration
            if storage_type not in ["s3", "b2", "sftp", "nfs"]:
                return {
                    "success": False,
                    "message": f"Unsupported storage type: {storage_type}"
                }
            
            # Add remote storage configuration
            remote_config = {
                "type": storage_type,
                "config": config,
                "enabled": True
            }
            
            self.config["backup_locations"]["remote"].append(remote_config)
            self._save_config()
            
            return {
                "success": True,
                "message": f"Remote storage ({storage_type}) configured successfully"
            }
            
        except Exception as e:
            logger.error(f"Error configuring remote storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring remote storage: {str(e)}"
            }
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_backup_status(self, vm_id: str = None) -> Dict:
        """Get backup status for VMs"""
        try:
            if vm_id:
                if vm_id not in self.config["vms"]:
                    return {
                        "success": False,
                        "message": f"No backup configuration found for VM {vm_id}"
                    }
                return {
                    "success": True,
                    "vm_id": vm_id,
                    "backup_info": self.config["vms"][vm_id]
                }
            
            # Get status for all VMs
            return {
                "success": True,
                "backup_configs": self.config["vms"]
            }
            
        except Exception as e:
            logger.error(f"Error getting backup status: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting backup status: {str(e)}"
            }
    
    def cleanup_old_backups(self) -> Dict:
        """Clean up old backups based on retention policy"""
        try:
            cleaned_up = []
            for vm_id, vm_config in self.config["vms"].items():
                if "last_backup" not in vm_config:
                    continue
                
                backup_dir = os.path.dirname(vm_config["last_backup"]["file"])
                retention = vm_config.get("schedule", {}).get("retention", self.config["retention"])
                
                # Get all backups for this VM
                backups = []
                for f in os.listdir(backup_dir):
                    if f.startswith(f'vm_{vm_id}_') and f.endswith('.vma.gz'):
                        backup_path = os.path.join(backup_dir, f)
                        timestamp = datetime.strptime(f.split('_')[2].split('.')[0], '%Y%m%d_%H%M%S')
                        backups.append((backup_path, timestamp))
                
                # Sort backups by timestamp
                backups.sort(key=lambda x: x[1], reverse=True)
                
                # Keep required backups based on retention policy
                to_keep = set()
                now = datetime.now()
                
                # Keep hourly backups
                hourly_cutoff = now - timedelta(hours=retention["hourly"])
                hourly = [b for b in backups if b[1] > hourly_cutoff]
                to_keep.update(b[0] for b in hourly[:retention["hourly"]])
                
                # Keep daily backups
                daily_cutoff = now - timedelta(days=retention["daily"])
                daily = [b for b in backups if b[1] > daily_cutoff]
                to_keep.update(b[0] for b in daily[:retention["daily"]])
                
                # Keep weekly backups
                weekly_cutoff = now - timedelta(weeks=retention["weekly"])
                weekly = [b for b in backups if b[1] > weekly_cutoff]
                to_keep.update(b[0] for b in weekly[:retention["weekly"]])
                
                # Keep monthly backups
                monthly_cutoff = now - timedelta(days=30 * retention["monthly"])
                monthly = [b for b in backups if b[1] > monthly_cutoff]
                to_keep.update(b[0] for b in monthly[:retention["monthly"]])
                
                # Remove old backups
                for backup_path, _ in backups:
                    if backup_path not in to_keep:
                        try:
                            os.remove(backup_path)
                            cleaned_up.append(backup_path)
                        except Exception as e:
                            logger.warning(f"Failed to remove old backup {backup_path}: {str(e)}")
            
            return {
                "success": True,
                "message": f"Cleaned up {len(cleaned_up)} old backups",
                "removed": cleaned_up
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
            return {
                "success": False,
                "message": f"Error cleaning up old backups: {str(e)}"
            }