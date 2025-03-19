"""
Test script for the backup scheduler functionality.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from proxmox_nli.core.storage.backup_scheduler import BackupScheduler
from proxmox_nli.commands.backup_scheduler_commands import BackupSchedulerCommands

class TestBackupScheduler(unittest.TestCase):
    """Test cases for the BackupScheduler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_mock = MagicMock()
        self.backup_manager_mock = MagicMock()
        
        # Mock the config path to use a temporary file
        with patch('os.path.join', return_value='test_backup_schedule.json'):
            self.scheduler = BackupScheduler(self.api_mock, self.backup_manager_mock)
        
        # Mock the _load_config method to return a test configuration
        self.test_config = {
            "enabled": True,
            "backup_schedule": {
                "daily": "02:00",
                "weekly": "Sunday 03:00",
                "monthly": "1 04:00"
            },
            "recovery_testing": {
                "enabled": True,
                "frequency": "weekly",
                "schedule": "Saturday 05:00",
                "vms": []
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
        self.scheduler.config = self.test_config
        
        # Mock the _save_config method
        self.scheduler._save_config = MagicMock()
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the test config file if it exists
        if os.path.exists('test_backup_schedule.json'):
            os.remove('test_backup_schedule.json')
    
    def test_init(self):
        """Test initialization of the BackupScheduler."""
        self.assertEqual(self.scheduler.api, self.api_mock)
        self.assertEqual(self.scheduler.backup_manager, self.backup_manager_mock)
        self.assertEqual(self.scheduler.config, self.test_config)
        self.assertFalse(self.scheduler.running)
        
    def test_update_config(self):
        """Test updating the scheduler configuration."""
        new_config = {
            "enabled": False,
            "backup_schedule": {
                "daily": "03:00"
            }
        }
        
        result = self.scheduler.update_config(new_config)
        
        self.assertTrue(result["success"])
        self.assertEqual(self.scheduler.config["enabled"], False)
        self.assertEqual(self.scheduler.config["backup_schedule"]["daily"], "03:00")
        self.assertEqual(self.scheduler.config["backup_schedule"]["weekly"], "Sunday 03:00")
        self.scheduler._save_config.assert_called_once()
        
    @patch('threading.Thread')
    @patch('schedule.every')
    def test_start(self, mock_schedule, mock_thread):
        """Test starting the scheduler."""
        # Mock the schedule methods
        mock_schedule.day.at.return_value.do.return_value = None
        
        # Mock the thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        result = self.scheduler.start()
        
        self.assertTrue(result["success"])
        self.assertTrue(self.scheduler.running)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
    def test_stop(self):
        """Test stopping the scheduler."""
        # Set up a running scheduler
        self.scheduler.running = True
        self.scheduler.scheduler_thread = MagicMock()
        
        result = self.scheduler.stop()
        
        self.assertTrue(result["success"])
        self.assertFalse(self.scheduler.running)
        
    @patch('schedule.run_pending')
    def test_run_scheduler(self, mock_run_pending):
        """Test the scheduler loop."""
        # Set up to run only once
        self.scheduler.running = True
        
        def stop_after_one_iteration():
            self.scheduler.running = False
            
        mock_run_pending.side_effect = stop_after_one_iteration
        
        self.scheduler._run_scheduler()
        
        mock_run_pending.assert_called_once()
        
    def test_run_backup(self):
        """Test running a backup."""
        vm_id = "100"
        self.backup_manager_mock.create_backup.return_value = {
            "success": True,
            "message": "Backup created successfully"
        }
        
        result = self.scheduler._run_backup(vm_id)
        
        self.assertTrue(result["success"])
        self.backup_manager_mock.create_backup.assert_called_once_with(vm_id)
        
    def test_run_recovery_testing(self):
        """Test running recovery testing."""
        # Set up test VMs
        self.scheduler.config["recovery_testing"]["vms"] = ["100", "101"]
        
        # Mock the test_backup_recovery method
        self.backup_manager_mock.test_backup_recovery.return_value = {
            "success": True,
            "message": "Recovery test successful"
        }
        
        result = self.scheduler._run_recovery_testing()
        
        self.assertTrue(result["success"])
        self.assertEqual(self.backup_manager_mock.test_backup_recovery.call_count, 2)
        
    def test_run_retention_enforcement(self):
        """Test running retention policy enforcement."""
        self.backup_manager_mock.cleanup_old_backups.return_value = {
            "success": True,
            "message": "Retention policy enforced"
        }
        
        result = self.scheduler._run_retention_enforcement()
        
        self.assertTrue(result["success"])
        self.backup_manager_mock.cleanup_old_backups.assert_called_once()
        
    def test_run_deduplication(self):
        """Test running data deduplication."""
        self.backup_manager_mock.implement_data_deduplication.return_value = {
            "success": True,
            "message": "Deduplication completed"
        }
        
        result = self.scheduler._run_deduplication()
        
        self.assertTrue(result["success"])
        self.backup_manager_mock.implement_data_deduplication.assert_called_once()
        
    def test_get_status(self):
        """Test getting scheduler status."""
        # Set up a mock schedule
        with patch('schedule.jobs', [MagicMock()]):
            result = self.scheduler.get_status()
            
            self.assertTrue(result["success"])
            self.assertFalse(result["running"])
            self.assertTrue(result["enabled"])
            self.assertIn("jobs", result)
            self.assertIn("config", result)


class TestBackupSchedulerCommands(unittest.TestCase):
    """Test cases for the BackupSchedulerCommands class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_mock = MagicMock()
        self.backup_manager_mock = MagicMock()
        
        # Mock the BackupScheduler
        self.scheduler_mock = MagicMock()
        
        # Create the commands instance
        self.commands = BackupSchedulerCommands(self.api_mock, self.backup_manager_mock)
        
        # Replace the scheduler with our mock
        self.commands.scheduler = self.scheduler_mock
        
    def test_start_scheduler(self):
        """Test starting the scheduler."""
        self.scheduler_mock.start.return_value = {
            "success": True,
            "message": "Scheduler started"
        }
        
        result = self.commands.start_scheduler()
        
        self.assertTrue(result["success"])
        self.scheduler_mock.start.assert_called_once()
        
    def test_stop_scheduler(self):
        """Test stopping the scheduler."""
        self.scheduler_mock.stop.return_value = {
            "success": True,
            "message": "Scheduler stopped"
        }
        
        result = self.commands.stop_scheduler()
        
        self.assertTrue(result["success"])
        self.scheduler_mock.stop.assert_called_once()
        
    def test_get_scheduler_status(self):
        """Test getting scheduler status."""
        self.scheduler_mock.get_status.return_value = {
            "success": True,
            "running": False,
            "enabled": True,
            "jobs": [],
            "config": {}
        }
        
        result = self.commands.get_scheduler_status()
        
        self.assertTrue(result["success"])
        self.scheduler_mock.get_status.assert_called_once()
        
    def test_configure_backup_schedule(self):
        """Test configuring backup schedule."""
        vm_id = "100"
        schedule = {
            "frequency": "daily",
            "time": "03:00"
        }
        
        self.scheduler_mock.backup_manager.config = {"vms": {}}
        
        result = self.commands.configure_backup_schedule(vm_id, schedule)
        
        self.scheduler_mock.backup_manager._save_config.assert_called_once()
        
    def test_run_backup_now(self):
        """Test running a backup immediately."""
        vm_id = "100"
        self.scheduler_mock._run_backup.return_value = {
            "success": True,
            "message": "Backup created"
        }
        
        result = self.commands.run_backup_now(vm_id)
        
        self.assertTrue(result["success"])
        self.scheduler_mock._run_backup.assert_called_once_with(vm_id)


if __name__ == '__main__':
    unittest.main()
