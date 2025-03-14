"""
Profile synchronization module for managing user profiles across devices.
"""
import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ProfileSyncManager:
    def __init__(self, data_dir: str = None):
        """Initialize the profile synchronization manager
        
        Args:
            data_dir: Directory to store sync data. If None,
                     defaults to the 'data' directory in the project root.
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize SQLite database for user devices
        self.db_path = os.path.join(self.data_dir, 'user_preferences.db')
        self._init_db()
        
    def _init_db(self):
        """Initialize the SQLite database for profile sync tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    device_type TEXT NOT NULL,
                    last_sync TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, device_id)
                )
            ''')
            
            # Profile sync data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profile_sync_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    sync_token TEXT NOT NULL,
                    sync_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, sync_token)
                )
            ''')
            
            conn.commit()
            
    def register_device(self, user_id: str, device_id: str, device_name: str, device_type: str) -> bool:
        """Register a device for profile synchronization
        
        Args:
            user_id: The user identifier
            device_id: Unique device identifier
            device_name: Human-readable device name
            device_type: Type of device (desktop, mobile, tablet, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO user_devices
                    (user_id, device_id, device_name, device_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, device_id) 
                    DO UPDATE SET device_name = ?, device_type = ?, updated_at = ?
                ''', (user_id, device_id, device_name, device_type, now, now, 
                      device_name, device_type, now))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return False
            
    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all devices registered for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            List[Dict[str, Any]]: List of device objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT device_id, device_name, device_type, last_sync, created_at, updated_at
                    FROM user_devices
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                ''', (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user devices: {e}")
            return []
            
    def remove_device(self, user_id: str, device_id: str) -> bool:
        """Remove a device from synchronization
        
        Args:
            user_id: The user identifier
            device_id: Device identifier to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove device
                cursor.execute('''
                    DELETE FROM user_devices
                    WHERE user_id = ? AND device_id = ?
                ''', (user_id, device_id))
                
                # Also clean up any sync data for this device
                cursor.execute('''
                    DELETE FROM profile_sync_data
                    WHERE user_id = ? AND device_id = ?
                ''', (user_id, device_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing device: {e}")
            return False
            
    def update_sync_data(self, user_id: str, device_id: str, sync_data: Dict[str, Any]) -> bool:
        """Update profile sync data
        
        Args:
            user_id: The user identifier
            device_id: Device identifier
            sync_data: Profile data to synchronize
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        sync_token = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store sync data
                cursor.execute('''
                    INSERT INTO profile_sync_data
                    (user_id, device_id, sync_token, sync_data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, device_id, sync_token, json.dumps(sync_data), now))
                
                # Update device last sync time
                cursor.execute('''
                    UPDATE user_devices
                    SET last_sync = ?, updated_at = ?
                    WHERE user_id = ? AND device_id = ?
                ''', (now, now, user_id, device_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating sync data: {e}")
            return False
            
    def get_latest_sync_data(self, user_id: str, device_id: str = None) -> Optional[Dict[str, Any]]:
        """Get latest profile sync data
        
        Args:
            user_id: The user identifier
            device_id: Optional device identifier to filter by
            
        Returns:
            Optional[Dict[str, Any]]: Latest sync data if available, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get latest sync data for this user
                if device_id:
                    # Get most recent sync data from OTHER devices (not the requesting device)
                    cursor.execute('''
                        SELECT sync_data, created_at
                        FROM profile_sync_data
                        WHERE user_id = ? AND device_id != ?
                        ORDER BY created_at DESC
                        LIMIT 1
                    ''', (user_id, device_id))
                else:
                    # Get most recent sync data for any device
                    cursor.execute('''
                        SELECT sync_data, created_at
                        FROM profile_sync_data
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                    ''', (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                try:
                    sync_data = json.loads(row['sync_data'])
                    return {
                        "data": sync_data,
                        "last_sync": row['created_at']
                    }
                except Exception as e:
                    logger.error(f"Error parsing sync data: {e}")
                    return None
        except Exception as e:
            logger.error(f"Error getting latest sync data: {e}")
            return None
            
    def get_sync_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sync history for a user
        
        Args:
            user_id: The user identifier
            limit: Maximum number of history items
            
        Returns:
            List[Dict[str, Any]]: Sync history items
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT d.device_name, p.device_id, p.sync_token, p.created_at
                    FROM profile_sync_data p
                    JOIN user_devices d ON p.user_id = d.user_id AND p.device_id = d.device_id
                    WHERE p.user_id = ?
                    ORDER BY p.created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting sync history: {e}")
            return []
            
    def clean_old_sync_data(self, user_id: str = None, days: int = 30) -> bool:
        """Clean up old sync data
        
        Args:
            user_id: Optional user identifier to clean data for
            days: Number of days to keep data for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cutoff_date = (datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute('''
                        DELETE FROM profile_sync_data
                        WHERE user_id = ? AND created_at < ?
                    ''', (user_id, cutoff_date))
                else:
                    cursor.execute('''
                        DELETE FROM profile_sync_data
                        WHERE created_at < ?
                    ''', (cutoff_date,))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error cleaning old sync data: {e}")
            return False