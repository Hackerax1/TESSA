"""
Backup handler for service configurations and data.
"""
import logging
import os
import json
import yaml
import shutil
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ServiceBackupHandler:
    """Handler for backing up and restoring service configurations."""
    
    def __init__(self, backup_dir: str = None):
        """Initialize the backup handler.
        
        Args:
            backup_dir: Directory for storing backups. If None, uses default location.
        """
        if backup_dir is None:
            # Default to a backup directory in the user's home
            self.backup_dir = os.path.expanduser('~/proxmox-nli/backups')
        else:
            self.backup_dir = backup_dir
            
        # Create backup directory structure
        self.config_dir = os.path.join(self.backup_dir, 'configs')
        self.data_dir = os.path.join(self.backup_dir, 'data')
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
    def backup_service(self, service_def: Dict, vm_id: str, include_data: bool = False) -> Dict:
        """Create a backup of a service's configuration and optionally its data.
        
        Args:
            service_def: Service definition dictionary
            vm_id: VM ID where the service is running
            include_data: Whether to include service data in backup
            
        Returns:
            Backup result dictionary
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            service_id = service_def['id']
            
            # Create backup directory for this service
            backup_path = os.path.join(self.config_dir, f"{service_id}_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            # Save service definition
            with open(os.path.join(backup_path, 'service.yml'), 'w') as f:
                yaml.dump(service_def, f)
                
            # Save deployment info
            deployment_info = {
                'vm_id': vm_id,
                'timestamp': timestamp,
                'include_data': include_data
            }
            with open(os.path.join(backup_path, 'deployment.json'), 'w') as f:
                json.dump(deployment_info, f, indent=2)
                
            # Backup service data if requested
            if include_data:
                data_backup_path = os.path.join(self.data_dir, f"{service_id}_{timestamp}")
                os.makedirs(data_backup_path, exist_ok=True)
                
                # Let the deployment method handle data backup
                if service_def['deployment']['method'] == 'docker':
                    self._backup_docker_data(service_def, vm_id, data_backup_path)
                elif service_def['deployment']['method'] == 'script':
                    self._backup_script_data(service_def, vm_id, data_backup_path)
                
            return {
                "success": True,
                "message": f"Successfully backed up {service_def['name']}",
                "backup_id": f"{service_id}_{timestamp}",
                "config_path": backup_path,
                "data_path": data_backup_path if include_data else None
            }
            
        except Exception as e:
            logger.error(f"Error backing up service: {str(e)}")
            return {
                "success": False,
                "message": f"Error backing up service: {str(e)}"
            }
            
    def restore_service(self, backup_id: str, target_vm_id: Optional[str] = None) -> Dict:
        """Restore a service from backup.
        
        Args:
            backup_id: ID of the backup to restore
            target_vm_id: Optional VM ID to restore to. If None, uses original VM ID.
            
        Returns:
            Restore result dictionary
        """
        try:
            # Find backup directories
            config_path = os.path.join(self.config_dir, backup_id)
            data_path = os.path.join(self.data_dir, backup_id)
            
            if not os.path.exists(config_path):
                return {
                    "success": False,
                    "message": f"Backup {backup_id} not found"
                }
                
            # Load service definition
            with open(os.path.join(config_path, 'service.yml'), 'r') as f:
                service_def = yaml.safe_load(f)
                
            # Load deployment info
            with open(os.path.join(config_path, 'deployment.json'), 'r') as f:
                deployment_info = json.load(f)
                
            # Use original VM ID if none specified
            vm_id = target_vm_id or deployment_info['vm_id']
            
            # Restore service data if it was backed up
            if deployment_info.get('include_data') and os.path.exists(data_path):
                if service_def['deployment']['method'] == 'docker':
                    self._restore_docker_data(service_def, vm_id, data_path)
                elif service_def['deployment']['method'] == 'script':
                    self._restore_script_data(service_def, vm_id, data_path)
                
            return {
                "success": True,
                "message": f"Successfully restored {service_def['name']}",
                "service_def": service_def,
                "vm_id": vm_id
            }
            
        except Exception as e:
            logger.error(f"Error restoring service: {str(e)}")
            return {
                "success": False,
                "message": f"Error restoring service: {str(e)}"
            }
            
    def list_backups(self, service_id: Optional[str] = None) -> Dict:
        """List available backups.
        
        Args:
            service_id: Optional service ID to filter backups
            
        Returns:
            Dictionary with list of backups
        """
        try:
            backups = []
            
            # List all backup directories
            for backup_dir in os.listdir(self.config_dir):
                if service_id and not backup_dir.startswith(service_id):
                    continue
                    
                config_path = os.path.join(self.config_dir, backup_dir)
                if os.path.isdir(config_path):
                    try:
                        # Load backup info
                        with open(os.path.join(config_path, 'service.yml'), 'r') as f:
                            service_def = yaml.safe_load(f)
                        with open(os.path.join(config_path, 'deployment.json'), 'r') as f:
                            deployment_info = json.load(f)
                            
                        backups.append({
                            "backup_id": backup_dir,
                            "service_id": service_def['id'],
                            "service_name": service_def['name'],
                            "timestamp": deployment_info['timestamp'],
                            "vm_id": deployment_info['vm_id'],
                            "includes_data": deployment_info.get('include_data', False)
                        })
                    except Exception as e:
                        logger.warning(f"Error loading backup {backup_dir}: {str(e)}")
                        
            return {
                "success": True,
                "backups": sorted(backups, key=lambda x: x['timestamp'], reverse=True)
            }
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return {
                "success": False,
                "message": f"Error listing backups: {str(e)}"
            }
            
    def _backup_docker_data(self, service_def: Dict, vm_id: str, backup_path: str) -> None:
        """Backup Docker volume data.
        
        This is a placeholder - actual implementation would:
        1. Identify Docker volumes used by the service
        2. Create volume backups using docker commands
        3. Copy backups to the specified backup path
        """
        pass
        
    def _backup_script_data(self, service_def: Dict, vm_id: str, backup_path: str) -> None:
        """Backup script-based service data.
        
        This is a placeholder - actual implementation would:
        1. Execute any backup commands specified in service definition
        2. Copy specified data directories to backup location
        """
        pass
        
    def _restore_docker_data(self, service_def: Dict, vm_id: str, backup_path: str) -> None:
        """Restore Docker volume data.
        
        This is a placeholder - actual implementation would:
        1. Create Docker volumes if needed
        2. Restore volume data from backups
        """
        pass
        
    def _restore_script_data(self, service_def: Dict, vm_id: str, backup_path: str) -> None:
        """Restore script-based service data.
        
        This is a placeholder - actual implementation would:
        1. Create necessary directories
        2. Copy data from backup to appropriate locations
        3. Execute any restore commands specified in service definition
        """
        pass