"""
User preferences management module for Proxmox NLI.
Handles persistent storage of user environment preferences across sessions.
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class UserPreferencesManager:
    def __init__(self, data_dir: str = None):
        """Initialize the user preferences manager
        
        Args:
            data_dir: Directory to store user preferences data. If None,
                     defaults to the 'data' directory in the project root.
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize SQLite database for user preferences
        self.db_path = os.path.join(self.data_dir, 'user_preferences.db')
        self._init_db()
        
    def _init_db(self):
        """Initialize the SQLite database for user preferences"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, preference_key)
                )
            ''')
            
            # Favorite VMs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorite_vms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    vm_id TEXT NOT NULL,
                    vm_name TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, vm_id)
                )
            ''')
            
            # Favorite nodes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorite_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    node_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, node_name)
                )
            ''')
            
            # Frequently used commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS frequent_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    last_used TEXT NOT NULL,
                    UNIQUE(user_id, command)
                )
            ''')
            
            # Quick access services table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quick_access_services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    service_id TEXT NOT NULL,
                    vm_id TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, service_id, vm_id)
                )
            ''')
            
            conn.commit()
            
    def set_preference(self, user_id: str, key: str, value: Any) -> bool:
        """Set a user preference
        
        Args:
            user_id: The user identifier
            key: Preference key
            value: Preference value (will be JSON serialized)
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_preferences (user_id, preference_key, preference_value, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, preference_key) 
                    DO UPDATE SET preference_value = ?, updated_at = ?
                ''', (
                    user_id, key, json.dumps(value), now, now, 
                    json.dumps(value), now
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting user preference: {e}")
            return False
            
    def get_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get a user preference
        
        Args:
            user_id: The user identifier
            key: Preference key
            default: Default value if preference not found
            
        Returns:
            Any: The preference value or default if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT preference_value FROM user_preferences
                    WHERE user_id = ? AND preference_key = ?
                ''', (user_id, key))
                
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return default
        except Exception as e:
            logger.error(f"Error getting user preference: {e}")
            return default
            
    def get_all_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all preferences for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            Dict[str, Any]: Dictionary of all user preferences
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT preference_key, preference_value FROM user_preferences
                    WHERE user_id = ?
                ''', (user_id,))
                
                results = cursor.fetchall()
                return {row[0]: json.loads(row[1]) for row in results}
        except Exception as e:
            logger.error(f"Error getting all user preferences: {e}")
            return {}
            
    def delete_preference(self, user_id: str, key: str) -> bool:
        """Delete a user preference
        
        Args:
            user_id: The user identifier
            key: Preference key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM user_preferences
                    WHERE user_id = ? AND preference_key = ?
                ''', (user_id, key))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting user preference: {e}")
            return False
            
    def add_favorite_vm(self, user_id: str, vm_id: str, vm_name: Optional[str] = None) -> bool:
        """Add a VM to user favorites
        
        Args:
            user_id: The user identifier
            vm_id: The VM ID
            vm_name: Optional name of the VM
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO favorite_vms (user_id, vm_id, vm_name, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, vm_id) DO NOTHING
                ''', (user_id, vm_id, vm_name, now))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding favorite VM: {e}")
            return False
            
    def remove_favorite_vm(self, user_id: str, vm_id: str) -> bool:
        """Remove a VM from user favorites
        
        Args:
            user_id: The user identifier
            vm_id: The VM ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM favorite_vms
                    WHERE user_id = ? AND vm_id = ?
                ''', (user_id, vm_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing favorite VM: {e}")
            return False
            
    def get_favorite_vms(self, user_id: str) -> List[Dict[str, Any]]:
        """Get favorite VMs for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            List[Dict[str, Any]]: List of favorite VMs
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT vm_id, vm_name, created_at FROM favorite_vms
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                columns = ['vm_id', 'vm_name', 'created_at']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting favorite VMs: {e}")
            return []
            
    def add_favorite_node(self, user_id: str, node_name: str) -> bool:
        """Add a node to user favorites
        
        Args:
            user_id: The user identifier
            node_name: The node name
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO favorite_nodes (user_id, node_name, created_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, node_name) DO NOTHING
                ''', (user_id, node_name, now))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding favorite node: {e}")
            return False
            
    def get_favorite_nodes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get favorite nodes for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            List[Dict[str, Any]]: List of favorite nodes
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT node_name, created_at FROM favorite_nodes
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                columns = ['node_name', 'created_at']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting favorite nodes: {e}")
            return []
            
    def track_command_usage(self, user_id: str, command: str, intent: str) -> bool:
        """Track usage of a command
        
        Args:
            user_id: The user identifier
            command: The command string
            intent: The command intent
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO frequent_commands (user_id, command, intent, usage_count, last_used)
                    VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(user_id, command) 
                    DO UPDATE SET usage_count = usage_count + 1, last_used = ?
                ''', (user_id, command, intent, now, now))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error tracking command usage: {e}")
            return False
            
    def get_frequent_commands(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get frequently used commands for a user
        
        Args:
            user_id: The user identifier
            limit: Maximum number of commands to return
            
        Returns:
            List[Dict[str, Any]]: List of frequent commands
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT command, intent, usage_count, last_used FROM frequent_commands
                    WHERE user_id = ?
                    ORDER BY usage_count DESC, last_used DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                columns = ['command', 'intent', 'usage_count', 'last_used']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting frequent commands: {e}")
            return []
            
    def add_quick_access_service(self, user_id: str, service_id: str, vm_id: Optional[str] = None) -> bool:
        """Add a service to quick access list
        
        Args:
            user_id: The user identifier
            service_id: The service ID
            vm_id: Optional VM ID where the service is deployed
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO quick_access_services (user_id, service_id, vm_id, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, service_id, vm_id) DO NOTHING
                ''', (user_id, service_id, vm_id, now))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding quick access service: {e}")
            return False
            
    def get_quick_access_services(self, user_id: str) -> List[Dict[str, Any]]:
        """Get quick access services for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            List[Dict[str, Any]]: List of quick access services
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT service_id, vm_id, created_at FROM quick_access_services
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                columns = ['service_id', 'vm_id', 'created_at']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting quick access services: {e}")
            return []