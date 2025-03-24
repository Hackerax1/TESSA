"""
Backup management operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

class BackupManager:
    def __init__(self, api):
        self.api = api

    def create_backup(self, vm_id: str, mode: str = 'snapshot', 
                     storage: Optional[str] = None, compression: str = 'zstd', 
                     notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a backup of a VM
        
        Args:
            vm_id: VM ID
            mode: Backup mode (snapshot or suspend)
            storage: Storage location
            compression: Compression algorithm
            notes: Backup notes
            
        Returns:
            Dict with operation result
        """
        # Find VM node
        vm_result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not vm_result['success']:
            return vm_result
        
        node = None
        for vm in vm_result['data']:
            if str(vm['vmid']) == str(vm_id):
                node = vm['node']
                break
        
        if not node:
            return {"success": False, "message": f"VM {vm_id} not found"}
        
        # If storage not specified, use local
        if not storage:
            storage = "local"
        
        # Create backup
        config = {
            'vmid': vm_id,
            'mode': mode,
            'storage': storage,
            'compress': compression
        }
        
        if notes:
            config['notes'] = notes
        
        result = self.api.api_request('POST', f'nodes/{node}/vzdump', config)
        if result['success']:
            return {
                "success": True,
                "message": f"Created backup of VM {vm_id}",
                "task_id": result['data']
            }
        return result

    def restore_backup(self, vm_id: str, backup_file: str,
                      target_storage: Optional[str] = None,
                      restore_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Restore a VM from backup
        
        Args:
            vm_id: VM ID
            backup_file: Backup file path
            target_storage: Target storage location
            restore_options: Additional restore options
            
        Returns:
            Dict with operation result
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        config = {
            'vmid': vm_id,
            'archive': backup_file
        }
        
        if target_storage:
            config['storage'] = target_storage
            
        if restore_options:
            config.update(restore_options)
        
        result = self.api.api_request('POST', f'nodes/{node}/qemu', config)
        if result['success']:
            return {
                "success": True,
                "message": f"Restored VM {vm_id} from backup",
                "task_id": result['data']
            }
        return result

    def list_backups(self, vm_id: Optional[str] = None) -> Dict[str, Any]:
        """List available backups
        
        Args:
            vm_id: Optional VM ID to filter backups
            
        Returns:
            Dict with list of backups
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Get backup list
        result = self.api.api_request('GET', f'nodes/{node}/storage/local/content')
        if not result['success']:
            return result
        
        backups = []
        for item in result['data']:
            if item['content'] == 'backup-image':
                if not vm_id or str(vm_id) in item['volid']:
                    backups.append({
                        'id': item['volid'],
                        'size': item['size'],
                        'date': item.get('ctime', ''),
                        'notes': item.get('notes', '')
                    })
        
        return {
            "success": True,
            "message": f"Found {len(backups)} backups",
            "backups": backups
        }

    def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        """Delete a backup
        
        Args:
            backup_id: Backup ID/volume ID
            
        Returns:
            Dict with operation result
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        result = self.api.api_request('DELETE', f'nodes/{node}/storage/local/content/{backup_id}')
        if result['success']:
            return {"success": True, "message": f"Deleted backup {backup_id}"}
        return result

    def verify_backup(self, vm_id: str, backup_file: Optional[str] = None) -> Dict[str, Any]:
        """Verify a backup's integrity
        
        Args:
            vm_id: VM ID
            backup_file: Optional specific backup file to verify
            
        Returns:
            Dict with verification result
        """
        # First list available backups
        backups_result = self.list_backups(vm_id)
        if not backups_result['success']:
            return backups_result
        
        if backup_file:
            backups = [b for b in backups_result['backups'] if b['id'] == backup_file]
        else:
            backups = backups_result['backups']
        
        if not backups:
            return {
                "success": False,
                "message": "No backups found to verify"
            }
        
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        results = []
        failed = []
        
        for backup in backups:
            # Check backup file integrity
            verify_result = self.api.api_request('POST', f'nodes/{node}/vzdump/verify', {
                'archive': backup['id']
            })
            
            if verify_result['success']:
                results.append({
                    'backup_id': backup['id'],
                    'status': 'verified'
                })
            else:
                failed.append({
                    'backup_id': backup['id'],
                    'error': verify_result.get('message', 'Unknown error')
                })
        
        return {
            "success": True,
            "message": f"Verified {len(results)} backups, {len(failed)} failed",
            "verified": results,
            "failed": failed
        }

    def configure_backup_schedule(self, vm_id: str, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Configure automated backup schedule
        
        Args:
            vm_id: VM ID
            schedule: Schedule configuration with:
                - dow: Day of week (1-7)
                - hour: Hour (0-23)
                - minute: Minute (0-59)
                - retention: Number of backups to keep
                
        Returns:
            Dict with configuration result
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        config = {
            'vmid': vm_id,
            'enabled': 1,
            'mode': 'snapshot',
            'storage': 'local',
            'compress': 'zstd'
        }
        
        config.update(schedule)
        
        result = self.api.api_request('POST', f'nodes/{node}/vzdump/schedule', config)
        if result['success']:
            return {
                "success": True,
                "message": f"Configured backup schedule for VM {vm_id}"
            }
        return result

    def get_backup_schedule(self, vm_id: Optional[str] = None) -> Dict[str, Any]:
        """Get backup schedule configuration
        
        Args:
            vm_id: Optional VM ID to filter schedules
            
        Returns:
            Dict with schedule configuration
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        result = self.api.api_request('GET', f'nodes/{node}/vzdump/schedule')
        if not result['success']:
            return result
        
        schedules = []
        for schedule in result['data']:
            if not vm_id or str(schedule.get('vmid', '')) == str(vm_id):
                schedules.append({
                    'vmid': schedule.get('vmid'),
                    'enabled': schedule.get('enabled', 0) == 1,
                    'dow': schedule.get('dow'),
                    'hour': schedule.get('hour'),
                    'minute': schedule.get('minute'),
                    'storage': schedule.get('storage'),
                    'mode': schedule.get('mode'),
                    'retention': schedule.get('retention')
                })
        
        return {
            "success": True,
            "message": f"Found {len(schedules)} backup schedules",
            "schedules": schedules
        }

    def remove_backup_schedule(self, vm_id: str) -> Dict[str, Any]:
        """Remove backup schedule
        
        Args:
            vm_id: VM ID
            
        Returns:
            Dict with operation result
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        result = self.api.api_request('DELETE', f'nodes/{node}/vzdump/schedule/{vm_id}')
        if result['success']:
            return {
                "success": True,
                "message": f"Removed backup schedule for VM {vm_id}"
            }
        return result