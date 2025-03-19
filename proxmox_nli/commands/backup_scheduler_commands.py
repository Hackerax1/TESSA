"""
Backup scheduler command handlers for Proxmox NLI.
"""
import logging
from typing import Dict, List, Optional

from ..core.storage.backup_scheduler import BackupScheduler

logger = logging.getLogger(__name__)

class BackupSchedulerCommands:
    """Command handlers for backup scheduler operations."""
    
    def __init__(self, api, backup_manager=None):
        """Initialize the backup scheduler commands.
        
        Args:
            api: Proxmox API client
            backup_manager: Optional existing BackupManager instance
        """
        self.api = api
        self.scheduler = BackupScheduler(api, backup_manager)
        
    def start_scheduler(self) -> Dict:
        """Start the backup scheduler.
        
        Returns:
            Start result dictionary
        """
        return self.scheduler.start()
        
    def stop_scheduler(self) -> Dict:
        """Stop the backup scheduler.
        
        Returns:
            Stop result dictionary
        """
        return self.scheduler.stop()
        
    def get_scheduler_status(self) -> Dict:
        """Get scheduler status.
        
        Returns:
            Status dictionary
        """
        return self.scheduler.get_status()
        
    def update_scheduler_config(self, config: Dict) -> Dict:
        """Update scheduler configuration.
        
        Args:
            config: New configuration dictionary
            
        Returns:
            Update result dictionary
        """
        return self.scheduler.update_config(config)
        
    def configure_backup_schedule(self, vm_id: str, schedule: Dict) -> Dict:
        """Configure backup schedule for a VM.
        
        Args:
            vm_id: VM ID
            schedule: Schedule configuration
            
        Returns:
            Configuration result dictionary
        """
        try:
            # Validate schedule
            if not isinstance(schedule, dict):
                return {
                    "success": False,
                    "message": "Schedule must be a dictionary"
                }
                
            # Get VM configuration
            vm_config = self.scheduler.backup_manager.config["vms"].get(vm_id, {})
            if not vm_config:
                # Create VM configuration
                self.scheduler.backup_manager.config["vms"][vm_id] = {
                    "schedule": schedule
                }
            else:
                # Update VM configuration
                vm_config["schedule"] = schedule
                
            # Save configuration
            self.scheduler.backup_manager._save_config()
            
            # Restart scheduler if running
            if self.scheduler.running:
                self.scheduler.stop()
                self.scheduler.start()
                
            return {
                "success": True,
                "message": f"Backup schedule configured for VM {vm_id}",
                "schedule": schedule
            }
            
        except Exception as e:
            logger.error(f"Error configuring backup schedule: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring backup schedule: {str(e)}"
            }
            
    def configure_recovery_testing(self, config: Dict) -> Dict:
        """Configure recovery testing.
        
        Args:
            config: Recovery testing configuration
            
        Returns:
            Configuration result dictionary
        """
        try:
            # Validate configuration
            if not isinstance(config, dict):
                return {
                    "success": False,
                    "message": "Configuration must be a dictionary"
                }
                
            # Update configuration
            self.scheduler.config["recovery_testing"].update(config)
            self.scheduler._save_config()
            
            # Restart scheduler if running
            if self.scheduler.running:
                self.scheduler.stop()
                self.scheduler.start()
                
            return {
                "success": True,
                "message": "Recovery testing configuration updated",
                "config": self.scheduler.config["recovery_testing"]
            }
            
        except Exception as e:
            logger.error(f"Error configuring recovery testing: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring recovery testing: {str(e)}"
            }
            
    def configure_retention_policy(self, vm_id: str, policy: Dict) -> Dict:
        """Configure retention policy for a VM.
        
        Args:
            vm_id: VM ID
            policy: Retention policy configuration
            
        Returns:
            Configuration result dictionary
        """
        try:
            # Validate policy
            if not isinstance(policy, dict):
                return {
                    "success": False,
                    "message": "Policy must be a dictionary"
                }
                
            # Get VM configuration
            vm_config = self.scheduler.backup_manager.config["vms"].get(vm_id, {})
            if not vm_config:
                # Create VM configuration
                self.scheduler.backup_manager.config["vms"][vm_id] = {
                    "retention_policy": policy
                }
            else:
                # Update VM configuration
                vm_config["retention_policy"] = policy
                
            # Save configuration
            self.scheduler.backup_manager._save_config()
            
            return {
                "success": True,
                "message": f"Retention policy configured for VM {vm_id}",
                "policy": policy
            }
            
        except Exception as e:
            logger.error(f"Error configuring retention policy: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring retention policy: {str(e)}"
            }
            
    def configure_notifications(self, config: Dict) -> Dict:
        """Configure notifications.
        
        Args:
            config: Notification configuration
            
        Returns:
            Configuration result dictionary
        """
        try:
            # Validate configuration
            if not isinstance(config, dict):
                return {
                    "success": False,
                    "message": "Configuration must be a dictionary"
                }
                
            # Update configuration
            self.scheduler.config["notification"].update(config)
            self.scheduler._save_config()
            
            return {
                "success": True,
                "message": "Notification configuration updated",
                "config": self.scheduler.config["notification"]
            }
            
        except Exception as e:
            logger.error(f"Error configuring notifications: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring notifications: {str(e)}"
            }
            
    def run_backup_now(self, vm_id: str) -> Dict:
        """Run backup immediately.
        
        Args:
            vm_id: VM ID
            
        Returns:
            Backup result dictionary
        """
        try:
            logger.info(f"Running immediate backup for VM {vm_id}")
            return self.scheduler._run_backup(vm_id)
            
        except Exception as e:
            logger.error(f"Error running immediate backup: {str(e)}")
            return {
                "success": False,
                "message": f"Error running immediate backup: {str(e)}"
            }
            
    def run_recovery_testing_now(self, vm_ids: Optional[List[str]] = None) -> Dict:
        """Run recovery testing immediately.
        
        Args:
            vm_ids: Optional list of VM IDs to test
            
        Returns:
            Testing result dictionary
        """
        try:
            logger.info("Running immediate recovery testing")
            
            # Override VMs to test if specified
            if vm_ids:
                original_vms = self.scheduler.config["recovery_testing"]["vms"]
                self.scheduler.config["recovery_testing"]["vms"] = vm_ids
                
                # Run testing
                result = self.scheduler._run_recovery_testing()
                
                # Restore original configuration
                self.scheduler.config["recovery_testing"]["vms"] = original_vms
                
                return result
            else:
                # Run testing with configured VMs
                return self.scheduler._run_recovery_testing()
            
        except Exception as e:
            logger.error(f"Error running immediate recovery testing: {str(e)}")
            return {
                "success": False,
                "message": f"Error running immediate recovery testing: {str(e)}"
            }
            
    def run_retention_enforcement_now(self) -> Dict:
        """Run retention policy enforcement immediately.
        
        Returns:
            Enforcement result dictionary
        """
        try:
            logger.info("Running immediate retention policy enforcement")
            return self.scheduler._run_retention_enforcement()
            
        except Exception as e:
            logger.error(f"Error running immediate retention enforcement: {str(e)}")
            return {
                "success": False,
                "message": f"Error running immediate retention enforcement: {str(e)}"
            }
            
    def run_deduplication_now(self) -> Dict:
        """Run data deduplication immediately.
        
        Returns:
            Deduplication result dictionary
        """
        try:
            logger.info("Running immediate data deduplication")
            return self.scheduler._run_deduplication()
            
        except Exception as e:
            logger.error(f"Error running immediate deduplication: {str(e)}")
            return {
                "success": False,
                "message": f"Error running immediate deduplication: {str(e)}"
            }
