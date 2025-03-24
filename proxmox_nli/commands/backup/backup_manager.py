"""
Backup management operations for Proxmox NLI.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

class BackupManager:
    def __init__(self, api):
        self.api = api

    def create_backup(self, vm_id: str, mode: str = 'snapshot', 
                     storage: str = None, compression: str = 'zstd', 
                     notes: str = None) -> Dict[str, Any]:
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
        # First get VM location
        vm_info = self._get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
            
        node = vm_info['node']
        
        # Prepare backup parameters
        backup_params = {
            'vmid': vm_id,
            'mode': mode,
            'compress': compression
        }
        
        if storage:
            backup_params['storage'] = storage
            
        if notes:
            backup_params['notes'] = notes
            
        # Create backup
        result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/snapshot', backup_params)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Created backup of VM {vm_id}",
                "backup_id": result['data'].get('backup_id')
            }
        return result

    def restore_backup(self, vm_id: str, backup_file: str, 
                      target_storage: str = None, 
                      restore_options: Dict = None) -> Dict[str, Any]:
        """Restore a VM from backup
        
        Args:
            vm_id: VM ID
            backup_file: Backup file path
            target_storage: Target storage location
            restore_options: Additional restore options
        
        Returns:
            Dict with operation result
        """
        # Get VM location
        vm_info = self._get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
            
        node = vm_info['node']
        
        # Prepare restore parameters
        restore_params = {
            'archive': backup_file
        }
        
        if target_storage:
            restore_params['storage'] = target_storage
            
        if restore_options:
            restore_params.update(restore_options)
            
        # Restore backup
        result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/snapshot/rollback', restore_params)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Restored VM {vm_id} from backup"
            }
        return result

    def list_backups(self, vm_id: str = None) -> Dict[str, Any]:
        """List available backups
        
        Args:
            vm_id: Optional VM ID to filter backups
        
        Returns:
            Dict with backup list
        """
        if vm_id:
            # Get VM location
            vm_info = self._get_vm_location(vm_id)
            if not vm_info['success']:
                return vm_info
                
            node = vm_info['node']
            
            # Get backups for specific VM
            result = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/snapshot')
        else:
            # Get all backups across cluster
            result = self.api.api_request('GET', 'cluster/backup')
            
        if result['success']:
            backups = []
            for backup in result['data']:
                backups.append({
                    'id': backup.get('vmid'),
                    'name': backup.get('name'),
                    'creation': backup.get('time'),
                    'size': backup.get('size'),
                    'type': backup.get('type')
                })
                
            return {
                "success": True,
                "message": "Available backups",
                "backups": backups
            }
        return result

    def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        """Delete a backup
        
        Args:
            backup_id: Backup ID
        
        Returns:
            Dict with operation result
        """
        # First get backup location
        backup_info = self._get_backup_location(backup_id)
        if not backup_info['success']:
            return backup_info
            
        node = backup_info['node']
        vm_id = backup_info['vmid']
        
        # Delete backup
        result = self.api.api_request('DELETE', f'nodes/{node}/qemu/{vm_id}/snapshot/{backup_id}')
        
        if result['success']:
            return {
                "success": True,
                "message": f"Deleted backup {backup_id}"
            }
        return result

    def verify_backup(self, vm_id: str, backup_file: str = None) -> Dict[str, Any]:
        """Verify a backup's integrity
        
        Args:
            vm_id: VM ID
            backup_file: Optional specific backup file to verify
        
        Returns:
            Dict with verification result
        """
        # Get VM location
        vm_info = self._get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
            
        node = vm_info['node']
        
        # Prepare verify parameters
        verify_params = {}
        if backup_file:
            verify_params['archive'] = backup_file
            
        # Verify backup
        result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/snapshot/verify', verify_params)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Verified backup for VM {vm_id}",
                "verification": result['data']
            }
        return result

    def configure_backup(self, vm_id: str, schedule: Dict = None) -> Dict[str, Any]:
        """Configure automated backups for a VM
        
        Args:
            vm_id: VM ID
            schedule: Schedule configuration with:
                - frequency: hourly, daily, weekly
                - time: Time to run
                - retention: Number of backups to keep
        
        Returns:
            Dict with operation result
        """
        # Get VM location
        vm_info = self._get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
            
        node = vm_info['node']
        
        # Update backup job configuration
        config_params = {
            'vmid': vm_id,
            'enabled': '1'
        }
        
        if schedule:
            if 'frequency' in schedule:
                config_params['schedule'] = schedule['frequency']
            if 'time' in schedule:
                config_params['starttime'] = schedule['time']
            if 'retention' in schedule:
                config_params['maxfiles'] = str(schedule['retention'])
                
        result = self.api.api_request('POST', f'nodes/{node}/storage/backup/job', config_params)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Configured backup schedule for VM {vm_id}"
            }
        return result

    def configure_recovery_testing(self, config: Dict) -> Dict[str, Any]:
        """Configure automated recovery testing
        
        Args:
            config: Recovery testing configuration with:
                - frequency: How often to test
                - vms: List of VMs to test
                - verify_method: How to verify recovery
        
        Returns:
            Dict with operation result
        """
        # Set up recovery testing job
        job_params = {
            'type': 'recovery-test',
            'enabled': '1'
        }
        
        if 'frequency' in config:
            job_params['schedule'] = config['frequency']
            
        if 'vms' in config:
            job_params['vmid'] = ','.join(config['vms'])
            
        if 'verify_method' in config:
            job_params['verify'] = config['verify_method']
            
        result = self.api.api_request('POST', 'cluster/jobs', job_params)
        
        if result['success']:
            return {
                "success": True,
                "message": "Configured recovery testing"
            }
        return result

    def configure_retention_policy(self, vm_id: str, policy: Dict) -> Dict[str, Any]:
        """Configure backup retention policy
        
        Args:
            vm_id: VM ID
            policy: Retention policy with:
                - keep_daily: Number of daily backups
                - keep_weekly: Number of weekly backups
                - keep_monthly: Number of monthly backups
        
        Returns:
            Dict with operation result
        """
        # Get VM location
        vm_info = self._get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
            
        node = vm_info['node']
        
        # Update retention policy
        policy_params = {
            'vmid': vm_id
        }
        
        if 'keep_daily' in policy:
            policy_params['keep-daily'] = str(policy['keep_daily'])
        if 'keep_weekly' in policy:
            policy_params['keep-weekly'] = str(policy['keep_weekly'])
        if 'keep_monthly' in policy:
            policy_params['keep-monthly'] = str(policy['keep_monthly'])
            
        result = self.api.api_request('POST', f'nodes/{node}/storage/backup/retention', policy_params)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Updated retention policy for VM {vm_id}"
            }
        return result

    def run_backup_now(self, vm_id: str) -> Dict[str, Any]:
        """Run a backup immediately
        
        Args:
            vm_id: VM ID
        
        Returns:
            Dict with operation result
        """
        return self.create_backup(vm_id, mode='snapshot')

    def run_recovery_test_now(self, vm_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run a recovery test immediately
        
        Args:
            vm_ids: Optional list of VM IDs to test
        
        Returns:
            Dict with operation result
        """
        # Prepare test parameters
        test_params = {
            'type': 'recovery-test'
        }
        
        if vm_ids:
            test_params['vmid'] = ','.join(vm_ids)
            
        result = self.api.api_request('POST', 'cluster/jobs/now', test_params)
        
        if result['success']:
            return {
                "success": True,
                "message": "Started recovery test"
            }
        return result

    def run_retention_enforcement_now(self) -> Dict[str, Any]:
        """Run retention policy enforcement immediately
        
        Returns:
            Dict with operation result
        """
        result = self.api.api_request('POST', 'cluster/backup/cleanup')
        
        if result['success']:
            return {
                "success": True,
                "message": "Started retention policy enforcement"
            }
        return result

    def run_deduplication_now(self) -> Dict[str, Any]:
        """Run data deduplication immediately
        
        Returns:
            Dict with operation result
        """
        result = self.api.api_request('POST', 'cluster/backup/dedup')
        
        if result['success']:
            return {
                "success": True,
                "message": "Started deduplication"
            }
        return result

    def configure_notifications(self, config: Dict) -> Dict[str, Any]:
        """Configure backup notifications
        
        Args:
            config: Notification configuration with:
                - email: Email addresses
                - events: Events to notify on
                - methods: Notification methods
        
        Returns:
            Dict with operation result
        """
        # Update notification configuration
        notify_params = {}
        
        if 'email' in config:
            notify_params['mail-to'] = ','.join(config['email'])
            
        if 'events' in config:
            notify_params['events'] = ','.join(config['events'])
            
        if 'methods' in config:
            notify_params['methods'] = ','.join(config['methods'])
            
        result = self.api.api_request('POST', 'cluster/notifications', notify_params)
        
        if result['success']:
            return {
                "success": True,
                "message": "Updated backup notifications"
            }
        return result

    def _get_vm_location(self, vm_id: str) -> Dict[str, Any]:
        """Get the node where a VM is located
        
        Args:
            vm_id: VM ID
        
        Returns:
            Dict with node information
        """
        result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not result['success']:
            return result
            
        for vm in result['data']:
            if str(vm['vmid']) == str(vm_id):
                return {
                    "success": True,
                    "node": vm['node']
                }
                
        return {
            "success": False,
            "message": f"VM {vm_id} not found"
        }

    def _get_backup_location(self, backup_id: str) -> Dict[str, Any]:
        """Get the location of a backup
        
        Args:
            backup_id: Backup ID
        
        Returns:
            Dict with backup location information
        """
        result = self.api.api_request('GET', 'cluster/backup')
        if not result['success']:
            return result
            
        for backup in result['data']:
            if backup.get('id') == backup_id:
                return {
                    "success": True,
                    "node": backup['node'],
                    "vmid": backup['vmid']
                }
                
        return {
            "success": False,
            "message": f"Backup {backup_id} not found"
        }