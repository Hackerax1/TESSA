"""
Backup-related commands for Proxmox NLI.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .backup_scheduler_commands import BackupSchedulerCommands

class BackupCommands:
    """Handles all backup-related commands for Proxmox NLI."""
    
    def __init__(self, api):
        """Initialize backup commands with API access.
        
        Args:
            api: Proxmox API client
        """
        self.api = api
        self.backup_scheduler = BackupSchedulerCommands(api)
    
    def create_backup(self, vm_id: str, mode: str = 'snapshot', 
                    storage: str = None, compression: str = 'zstd', 
                    notes: str = None) -> Dict:
        """Create a backup of a VM.
        
        Args:
            vm_id: VM ID
            mode: Backup mode (snapshot or suspend)
            storage: Storage location
            compression: Compression algorithm
            notes: Backup notes
            
        Returns:
            Dict: Result of the operation
        """
        from ..core.storage.backup_manager import BackupManager
        backup_manager = BackupManager(self.api)
        return backup_manager.create_backup(vm_id, mode, storage, compression, notes)
    
    def restore_backup(self, vm_id: str, backup_file: str, 
                      target_storage: str = None, 
                      restore_options: Dict = None) -> Dict:
        """Restore a VM from backup.
        
        Args:
            vm_id: VM ID
            backup_file: Backup file path
            target_storage: Target storage location
            restore_options: Additional restore options
            
        Returns:
            Dict: Result of the operation
        """
        from ..core.storage.backup_manager import BackupManager
        backup_manager = BackupManager(self.api)
        return backup_manager.restore_backup(vm_id, backup_file, target_storage, restore_options)
    
    def list_backups(self, vm_id: str = None) -> Dict:
        """List available backups.
        
        Args:
            vm_id: Optional VM ID to filter backups
            
        Returns:
            Dict: List of backups
        """
        from ..core.storage.backup_manager import BackupManager
        backup_manager = BackupManager(self.api)
        return backup_manager.list_backups(vm_id)
    
    def delete_backup(self, backup_id: str) -> Dict:
        """Delete a backup.
        
        Args:
            backup_id: Backup ID
            
        Returns:
            Dict: Result of the operation
        """
        from ..core.storage.backup_manager import BackupManager
        backup_manager = BackupManager(self.api)
        return backup_manager.delete_backup(backup_id)
    
    def verify_backup(self, vm_id: str, backup_file: str = None) -> Dict:
        """Verify a backup's integrity.
        
        Args:
            vm_id: VM ID
            backup_file: Optional backup file path
            
        Returns:
            Dict: Verification result
        """
        from ..core.storage.backup_manager import BackupManager
        backup_manager = BackupManager(self.api)
        return backup_manager.verify_backup(vm_id, backup_file)
    
    # Backup Scheduler Methods
    def start_backup_scheduler(self) -> Dict:
        """Start the backup scheduler service.
        
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.start_scheduler()
    
    def stop_backup_scheduler(self) -> Dict:
        """Stop the backup scheduler service.
        
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.stop_scheduler()
    
    def get_scheduler_status(self) -> Dict:
        """Get the status of the backup scheduler.
        
        Returns:
            Dict: Scheduler status information
        """
        return self.backup_scheduler.get_scheduler_status()
    
    def schedule_backup(self, vm_id: str, schedule: Dict) -> Dict:
        """Configure backup schedule for a VM.
        
        Args:
            vm_id: VM ID
            schedule: Schedule configuration with frequency, time, etc.
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.configure_backup_schedule(vm_id, schedule)
    
    def configure_recovery_testing(self, config: Dict) -> Dict:
        """Configure automated recovery testing.
        
        Args:
            config: Recovery testing configuration
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.configure_recovery_testing(config)
    
    def configure_retention_policy(self, vm_id: str, policy: Dict) -> Dict:
        """Configure backup retention policy for a VM.
        
        Args:
            vm_id: VM ID
            policy: Retention policy configuration
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.configure_retention_policy(vm_id, policy)
    
    def run_backup_now(self, vm_id: str) -> Dict:
        """Run a backup immediately.
        
        Args:
            vm_id: VM ID
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.run_backup_now(vm_id)
    
    def run_recovery_test_now(self, vm_ids: Optional[List[str]] = None) -> Dict:
        """Run a recovery test immediately.
        
        Args:
            vm_ids: Optional list of VM IDs to test
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.run_recovery_testing_now(vm_ids)
    
    def run_retention_enforcement_now(self) -> Dict:
        """Run retention policy enforcement immediately.
        
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.run_retention_enforcement_now()
    
    def run_deduplication_now(self) -> Dict:
        """Run data deduplication immediately.
        
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.run_deduplication_now()
    
    def configure_notifications(self, config: Dict) -> Dict:
        """Configure backup notifications.
        
        Args:
            config: Notification configuration
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.configure_notifications(config)
