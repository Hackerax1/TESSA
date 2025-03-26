"""
Profile synchronization module for cross-device support.
"""
import os
import json
import sqlite3
import logging
from typing import Dict, List, Optional
from datetime import datetime
import threading
from queue import Queue, Empty  # Fix: Import Empty exception directly from queue module
import time

logger = logging.getLogger(__name__)

class ProfileSyncManager:
    """Manages synchronization of user profiles and preferences across devices."""
    
    def __init__(self, data_dir: str = None, dashboard_manager=None):
        """Initialize the profile sync manager.
        
        Args:
            data_dir: Directory to store sync data
            dashboard_manager: DashboardManager instance for dashboard sync
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.dashboard_manager = dashboard_manager
        self.sync_queue = Queue()
        self.sync_thread = None
        self._stop_sync = False
        
        # Initialize SQLite database for sync state
        self.db_path = os.path.join(self.data_dir, 'profile_sync.db')
        self._init_db()
        
    def _init_db(self):
        """Initialize the SQLite database for sync state tracking"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sync state table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_state (
                    user_id TEXT PRIMARY KEY,
                    last_sync TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    sync_enabled BOOLEAN DEFAULT 1
                )
            ''')
            
            # Device registrations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_registrations (
                    device_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES sync_state (user_id)
                )
            ''')
            
            conn.commit()
    
    def start_sync_service(self):
        """Start the background sync service"""
        if self.sync_thread and self.sync_thread.is_alive():
            return
            
        self._stop_sync = False
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        
    def stop_sync_service(self):
        """Stop the background sync service"""
        self._stop_sync = True
        if self.sync_thread:
            self.sync_thread.join()
            
    def _sync_worker(self):
        """Background worker for processing sync tasks"""
        while not self._stop_sync:
            try:
                sync_task = self.sync_queue.get(timeout=30)  # 30 second timeout
                self._process_sync_task(sync_task)
            except Empty:  # Fix: Use the directly imported Empty exception
                # Timeout occurred, check for any missed syncs
                self._check_pending_syncs()
                continue
            except Exception as e:
                logger.error(f"Error in sync worker: {e}")
                
    def _process_sync_task(self, task: Dict):
        """Process a sync task from the queue"""
        try:
            user_id = task.get('user_id')
            task_type = task.get('type')
            
            if not user_id or not task_type:
                return
                
            if task_type == 'dashboards':
                remote_dashboards = task.get('data', [])
                if remote_dashboards and self.dashboard_manager:
                    self.dashboard_manager.sync_user_dashboards(user_id, remote_dashboards)
                    
            elif task_type == 'preferences':
                preferences = task.get('data', {})
                if preferences:
                    self._sync_user_preferences(user_id, preferences)
                    
            # Update last sync time
            self._update_sync_state(user_id)
            
        except Exception as e:
            logger.error(f"Error processing sync task: {e}")
            
    def _sync_user_preferences(self, user_id: str, preferences: Dict):
        """Sync user preferences with remote data"""
        # Implementation will vary based on preferences structure
        pass
        
    def _update_sync_state(self, user_id: str):
        """Update the last sync time for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sync_state (user_id, last_sync, device_id, sync_enabled)
                    VALUES (?, ?, ?, (SELECT sync_enabled FROM sync_state WHERE user_id = ? OR 1))
                ''', (user_id, now, self._get_device_id(), user_id))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating sync state: {e}")
            
    def queue_sync_task(self, user_id: str, task_type: str, data: Dict):
        """Queue a sync task for processing
        
        Args:
            user_id: The user identifier
            task_type: Type of sync task ('dashboards', 'preferences', etc.)
            data: The data to sync
        """
        self.sync_queue.put({
            'user_id': user_id,
            'type': task_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
    def register_device(self, user_id: str, device_name: str) -> str:
        """Register a new device for sync
        
        Args:
            user_id: The user identifier
            device_name: Name of the device
            
        Returns:
            str: Device ID for the registered device
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                device_id = self._get_device_id()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO device_registrations
                    (device_id, user_id, device_name, last_seen, is_active)
                    VALUES (?, ?, ?, ?, 1)
                ''', (device_id, user_id, device_name, now))
                
                conn.commit()
                return device_id
                
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return None
            
    def _get_device_id(self) -> str:
        """Get or generate a unique device identifier"""
        config_file = os.path.join(self.data_dir, 'device_config.json')
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('device_id')
                    
            # Generate new device ID if none exists
            import uuid
            device_id = str(uuid.uuid4())
            
            with open(config_file, 'w') as f:
                json.dump({'device_id': device_id}, f)
                
            return device_id
            
        except Exception as e:
            logger.error(f"Error getting device ID: {e}")
            return None
            
    def _check_pending_syncs(self):
        """Check for any pending syncs that need to be processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get users with sync enabled
                cursor.execute('''
                    SELECT user_id, last_sync
                    FROM sync_state
                    WHERE sync_enabled = 1
                ''')
                
                now = datetime.now()
                for user_id, last_sync in cursor.fetchall():
                    try:
                        last_sync_time = datetime.fromisoformat(last_sync)
                        # If more than 5 minutes since last sync
                        if (now - last_sync_time).total_seconds() > 300:
                            # Queue sync tasks for this user
                            self.queue_sync_task(user_id, 'dashboards', None)
                            self.queue_sync_task(user_id, 'preferences', None)
                    except (ValueError, TypeError):
                        continue
                        
        except Exception as e:
            logger.error(f"Error checking pending syncs: {e}")
            
    def enable_sync(self, user_id: str, enabled: bool = True):
        """Enable or disable sync for a user
        
        Args:
            user_id: The user identifier
            enabled: Whether sync should be enabled
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sync_state (user_id, sync_enabled, last_sync, device_id)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, enabled, datetime.now().isoformat(), self._get_device_id()))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating sync enabled state: {e}")