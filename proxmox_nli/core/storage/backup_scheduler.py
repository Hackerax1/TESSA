"""
Backup scheduler module for Proxmox NLI.
Handles automated backup scheduling, recovery testing, and retention policy enforcement.
"""
import logging
import os
import json
import threading
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

from .backup_manager import BackupManager

logger = logging.getLogger(__name__)

class BackupScheduler:
    """Scheduler for automated backups, testing, and maintenance."""
    
    def __init__(self, api, backup_manager=None):
        """Initialize the backup scheduler.
        
        Args:
            api: Proxmox API client
            backup_manager: Optional existing BackupManager instance
        """
        self.api = api
        self.backup_manager = backup_manager or BackupManager(api)
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                      'config', 'backup_schedule.json')
        self.config = self._load_config()
        self.scheduler_thread = None
        self.running = False
        
    def _load_config(self) -> Dict:
        """Load scheduler configuration"""
        if not os.path.exists(self.config_path):
            default_config = {
                "enabled": True,
                "backup_schedule": {
                    "daily": "02:00",
                    "weekly": "Sunday 03:00",
                    "monthly": "1 04:00"  # 1st day of month
                },
                "recovery_testing": {
                    "enabled": True,
                    "frequency": "weekly",  # daily, weekly, monthly
                    "schedule": "Saturday 05:00",
                    "vms": []  # empty means all VMs with backups
                },
                "retention_enforcement": {
                    "schedule": "daily 06:00"
                },
                "deduplication": {
                    "enabled": True,
                    "schedule": "weekly Sunday 07:00"
                },
                "notification": {
                    "enabled": True,
                    "on_success": False,
                    "on_failure": True,
                    "email": ""
                }
            }
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _save_config(self):
        """Save scheduler configuration"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def update_config(self, new_config: Dict) -> Dict:
        """Update scheduler configuration.
        
        Args:
            new_config: New configuration dictionary
            
        Returns:
            Update result dictionary
        """
        try:
            # Validate configuration
            if not isinstance(new_config, dict):
                return {
                    "success": False,
                    "message": "Configuration must be a dictionary"
                }
                
            # Update configuration
            for key, value in new_config.items():
                if key in self.config:
                    if isinstance(value, dict) and isinstance(self.config[key], dict):
                        # Merge dictionaries
                        self.config[key].update(value)
                    else:
                        # Replace value
                        self.config[key] = value
                        
            self._save_config()
            
            # Restart scheduler if running
            if self.running:
                self.stop()
                self.start()
                
            return {
                "success": True,
                "message": "Scheduler configuration updated successfully",
                "config": self.config
            }
            
        except Exception as e:
            logger.error(f"Error updating scheduler configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating scheduler configuration: {str(e)}"
            }
            
    def start(self) -> Dict:
        """Start the backup scheduler.
        
        Returns:
            Start result dictionary
        """
        try:
            if self.running:
                return {
                    "success": False,
                    "message": "Scheduler is already running"
                }
                
            if not self.config["enabled"]:
                return {
                    "success": False,
                    "message": "Scheduler is disabled in configuration"
                }
                
            # Clear existing schedule
            schedule.clear()
            
            # Schedule backups
            self._schedule_backups()
            
            # Schedule recovery testing
            if self.config["recovery_testing"]["enabled"]:
                self._schedule_recovery_testing()
                
            # Schedule retention enforcement
            self._schedule_retention_enforcement()
            
            # Schedule deduplication
            if self.config["deduplication"]["enabled"]:
                self._schedule_deduplication()
                
            # Start scheduler thread
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("Backup scheduler started")
            return {
                "success": True,
                "message": "Backup scheduler started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting backup scheduler: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting backup scheduler: {str(e)}"
            }
            
    def stop(self) -> Dict:
        """Stop the backup scheduler.
        
        Returns:
            Stop result dictionary
        """
        try:
            if not self.running:
                return {
                    "success": False,
                    "message": "Scheduler is not running"
                }
                
            # Set running flag to False
            self.running = False
            
            # Clear schedule
            schedule.clear()
            
            # Wait for thread to terminate
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
                
            logger.info("Backup scheduler stopped")
            return {
                "success": True,
                "message": "Backup scheduler stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"Error stopping backup scheduler: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping backup scheduler: {str(e)}"
            }
            
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
            
    def _schedule_backups(self):
        """Schedule automated backups"""
        # Get all VMs with backup configurations
        vms_with_backups = self.backup_manager.config["vms"]
        
        for vm_id, vm_config in vms_with_backups.items():
            if "schedule" not in vm_config:
                continue
                
            # Get backup schedule
            backup_schedule = vm_config["schedule"]
            frequency = backup_schedule.get("frequency", "daily")
            backup_time = backup_schedule.get("time", "02:00")
            
            # Schedule based on frequency
            if frequency == "hourly":
                schedule.every().hour.at(":00").do(self._run_backup, vm_id)
            elif frequency == "daily":
                schedule.every().day.at(backup_time).do(self._run_backup, vm_id)
            elif frequency == "weekly":
                day = backup_schedule.get("day", "Sunday")
                getattr(schedule.every(), day.lower()).at(backup_time).do(self._run_backup, vm_id)
            elif frequency == "monthly":
                day = backup_schedule.get("day", "1")
                schedule.every().month.at(f"{day} {backup_time}").do(self._run_backup, vm_id)
                
    def _schedule_recovery_testing(self):
        """Schedule automated recovery testing"""
        testing_config = self.config["recovery_testing"]
        frequency = testing_config.get("frequency", "weekly")
        test_schedule = testing_config.get("schedule", "Saturday 05:00")
        
        if frequency == "daily":
            schedule.every().day.at(test_schedule).do(self._run_recovery_testing)
        elif frequency == "weekly":
            day, time = test_schedule.split()
            getattr(schedule.every(), day.lower()).at(time).do(self._run_recovery_testing)
        elif frequency == "monthly":
            day, time = test_schedule.split()
            schedule.every().month.at(f"{day} {time}").do(self._run_recovery_testing)
            
    def _schedule_retention_enforcement(self):
        """Schedule retention policy enforcement"""
        retention_config = self.config["retention_enforcement"]
        retention_schedule = retention_config.get("schedule", "daily 06:00")
        
        if retention_schedule.startswith("daily"):
            _, time = retention_schedule.split()
            schedule.every().day.at(time).do(self._run_retention_enforcement)
        elif retention_schedule.startswith("weekly"):
            _, day, time = retention_schedule.split()
            getattr(schedule.every(), day.lower()).at(time).do(self._run_retention_enforcement)
            
    def _schedule_deduplication(self):
        """Schedule data deduplication"""
        dedup_config = self.config["deduplication"]
        dedup_schedule = dedup_config.get("schedule", "weekly Sunday 07:00")
        
        if dedup_schedule.startswith("daily"):
            _, time = dedup_schedule.split()
            schedule.every().day.at(time).do(self._run_deduplication)
        elif dedup_schedule.startswith("weekly"):
            _, day, time = dedup_schedule.split()
            getattr(schedule.every(), day.lower()).at(time).do(self._run_deduplication)
            
    def _run_backup(self, vm_id: str):
        """Run backup for a VM"""
        try:
            logger.info(f"Running scheduled backup for VM {vm_id}")
            result = self.backup_manager.create_backup(vm_id)
            
            # Send notification if configured
            if self.config["notification"]["enabled"]:
                if not result["success"] or self.config["notification"]["on_success"]:
                    self._send_notification(
                        f"Backup {'failed' if not result['success'] else 'succeeded'} for VM {vm_id}",
                        result["message"]
                    )
                    
            return result
            
        except Exception as e:
            logger.error(f"Error running scheduled backup for VM {vm_id}: {str(e)}")
            
            # Send notification
            if self.config["notification"]["enabled"] and self.config["notification"]["on_failure"]:
                self._send_notification(
                    f"Backup failed for VM {vm_id}",
                    f"Error: {str(e)}"
                )
                
            return {
                "success": False,
                "message": f"Error running scheduled backup: {str(e)}"
            }
            
    def _run_recovery_testing(self):
        """Run automated recovery testing"""
        try:
            logger.info("Running scheduled recovery testing")
            
            # Get VMs to test
            vms_to_test = self.config["recovery_testing"]["vms"]
            if not vms_to_test:
                # Test all VMs with backups
                vms_to_test = list(self.backup_manager.config["vms"].keys())
                
            results = {}
            for vm_id in vms_to_test:
                logger.info(f"Testing recovery for VM {vm_id}")
                result = self.backup_manager.test_backup_recovery(vm_id)
                results[vm_id] = result
                
                # Send notification if configured
                if self.config["notification"]["enabled"]:
                    if not result["success"] or self.config["notification"]["on_success"]:
                        self._send_notification(
                            f"Recovery test {'failed' if not result['success'] else 'succeeded'} for VM {vm_id}",
                            result["message"]
                        )
                
            return {
                "success": True,
                "message": f"Recovery testing completed for {len(results)} VMs",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error running scheduled recovery testing: {str(e)}")
            
            # Send notification
            if self.config["notification"]["enabled"] and self.config["notification"]["on_failure"]:
                self._send_notification(
                    "Recovery testing failed",
                    f"Error: {str(e)}"
                )
                
            return {
                "success": False,
                "message": f"Error running scheduled recovery testing: {str(e)}"
            }
            
    def _run_retention_enforcement(self):
        """Run retention policy enforcement"""
        try:
            logger.info("Running scheduled retention policy enforcement")
            result = self.backup_manager.cleanup_old_backups()
            
            # Send notification if configured
            if self.config["notification"]["enabled"]:
                if not result["success"] or self.config["notification"]["on_success"]:
                    self._send_notification(
                        f"Retention policy enforcement {'failed' if not result['success'] else 'succeeded'}",
                        result["message"]
                    )
                    
            return result
            
        except Exception as e:
            logger.error(f"Error running scheduled retention policy enforcement: {str(e)}")
            
            # Send notification
            if self.config["notification"]["enabled"] and self.config["notification"]["on_failure"]:
                self._send_notification(
                    "Retention policy enforcement failed",
                    f"Error: {str(e)}"
                )
                
            return {
                "success": False,
                "message": f"Error running scheduled retention policy enforcement: {str(e)}"
            }
            
    def _run_deduplication(self):
        """Run data deduplication"""
        try:
            logger.info("Running scheduled data deduplication")
            result = self.backup_manager.implement_data_deduplication()
            
            # Send notification if configured
            if self.config["notification"]["enabled"]:
                if not result["success"] or self.config["notification"]["on_success"]:
                    self._send_notification(
                        f"Data deduplication {'failed' if not result['success'] else 'succeeded'}",
                        result["message"]
                    )
                    
            return result
            
        except Exception as e:
            logger.error(f"Error running scheduled data deduplication: {str(e)}")
            
            # Send notification
            if self.config["notification"]["enabled"] and self.config["notification"]["on_failure"]:
                self._send_notification(
                    "Data deduplication failed",
                    f"Error: {str(e)}"
                )
                
            return {
                "success": False,
                "message": f"Error running scheduled data deduplication: {str(e)}"
            }
            
    def _send_notification(self, subject: str, message: str):
        """Send notification.
        
        Args:
            subject: Notification subject
            message: Notification message
        """
        try:
            if not self.config["notification"]["enabled"]:
                return
                
            email = self.config["notification"]["email"]
            if not email:
                # Log only if no email configured
                logger.info(f"Notification: {subject} - {message}")
                return
                
            # In a real implementation, you would send an email here
            # For now, just log the notification
            logger.info(f"Notification to {email}: {subject} - {message}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            
    def get_status(self) -> Dict:
        """Get scheduler status.
        
        Returns:
            Status dictionary
        """
        try:
            # Get all scheduled jobs
            jobs = []
            for job in schedule.jobs:
                jobs.append({
                    "job": str(job),
                    "next_run": job.next_run.isoformat() if job.next_run else None,
                    "last_run": job.last_run.isoformat() if job.last_run else None
                })
                
            return {
                "success": True,
                "running": self.running,
                "enabled": self.config["enabled"],
                "jobs": jobs,
                "config": self.config
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting scheduler status: {str(e)}"
            }
