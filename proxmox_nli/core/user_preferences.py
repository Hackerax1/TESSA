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
            
            # Command history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    intent TEXT,
                    entities TEXT,
                    timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL
                )
            ''')
            
            # Favorite commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorite_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    command_text TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, command_text)
                )
            ''')
            
            # Notification preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, event_type, channel)
                )
            ''')
            
            # User shortcuts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_shortcuts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    command_text TEXT NOT NULL,
                    description TEXT,
                    shortcut_key TEXT,
                    category TEXT,
                    icon TEXT,
                    position INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, name)
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

    # Command history methods
    def add_to_command_history(self, user_id: str, command: str, intent: str = None, 
                             entities: Dict = None, success: bool = True) -> bool:
        """Add a command to the user's command history
        
        Args:
            user_id: The user identifier
            command: The command text
            intent: Identified intent
            entities: Extracted entities
            success: Whether the command executed successfully
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        entities_json = json.dumps(entities) if entities else None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO command_history
                    (user_id, command, intent, entities, timestamp, success)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, command, intent, entities_json, now, success))
                conn.commit()
                
                # Also update the frequent commands table
                if success and intent:
                    self.track_command_usage(user_id, command, intent)
                    
                return True
        except Exception as e:
            logger.error(f"Error adding to command history: {e}")
            return False
    
    def get_command_history(self, user_id: str, limit: int = 50, 
                          successful_only: bool = False) -> List[Dict[str, Any]]:
        """Get command history for a user
        
        Args:
            user_id: The user identifier
            limit: Maximum number of history items to return
            successful_only: Whether to return only successful commands
            
        Returns:
            List[Dict[str, Any]]: List of command history items
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, command, intent, entities, timestamp, success 
                    FROM command_history
                    WHERE user_id = ?
                '''
                
                params = [user_id]
                
                if successful_only:
                    query += " AND success = 1"
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                columns = ['id', 'command', 'intent', 'entities', 'timestamp', 'success']
                results = []
                
                for row in cursor.fetchall():
                    item = dict(zip(columns, row))
                    if item['entities'] and isinstance(item['entities'], str):
                        try:
                            item['entities'] = json.loads(item['entities'])
                        except:
                            item['entities'] = {}
                    results.append(item)
                
                return results
        except Exception as e:
            logger.error(f"Error getting command history: {e}")
            return []
    
    def clear_command_history(self, user_id: str) -> bool:
        """Clear command history for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM command_history
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing command history: {e}")
            return False
    
    # Favorite commands methods
    def add_favorite_command(self, user_id: str, command_text: str, description: str = None) -> bool:
        """Add a command to the user's favorites
        
        Args:
            user_id: The user identifier
            command_text: The command text
            description: Optional description for the command
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO favorite_commands
                    (user_id, command_text, description, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, command_text) 
                    DO UPDATE SET description = ?, created_at = ?
                ''', (user_id, command_text, description, now, description, now))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding favorite command: {e}")
            return False
    
    def get_favorite_commands(self, user_id: str) -> List[Dict[str, Any]]:
        """Get favorite commands for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            List[Dict[str, Any]]: List of favorite commands
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, command_text, description, created_at
                    FROM favorite_commands
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
                
                columns = ['id', 'command_text', 'description', 'created_at']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting favorite commands: {e}")
            return []
    
    def remove_favorite_command(self, user_id: str, command_id: int) -> bool:
        """Remove a command from the user's favorites
        
        Args:
            user_id: The user identifier
            command_id: The favorite command ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM favorite_commands
                    WHERE user_id = ? AND id = ?
                ''', (user_id, command_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing favorite command: {e}")
            return False
            
    # Notification preferences methods
    def set_notification_preference(self, user_id: str, event_type: str, channel: str, enabled: bool) -> bool:
        """Set notification preference for a specific event and channel
        
        Args:
            user_id: The user identifier
            event_type: The event type (e.g., vm_state_change, backup_complete, security_alert)
            channel: The notification channel (e.g., web, email, sms)
            enabled: Whether notifications are enabled for this event/channel
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notification_preferences
                    (user_id, event_type, channel, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, event_type, channel) 
                    DO UPDATE SET enabled = ?, updated_at = ?
                ''', (user_id, event_type, channel, enabled, now, now, enabled, now))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting notification preference: {e}")
            return False
    
    def get_notification_preferences(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all notification preferences for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            List[Dict[str, Any]]: List of notification preferences
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT event_type, channel, enabled, created_at, updated_at
                    FROM notification_preferences
                    WHERE user_id = ?
                    ORDER BY event_type, channel
                ''', (user_id,))
                
                columns = ['event_type', 'channel', 'enabled', 'created_at', 'updated_at']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            return []
    
    def get_notification_preference(self, user_id: str, event_type: str, channel: str) -> Optional[bool]:
        """Get a specific notification preference
        
        Args:
            user_id: The user identifier
            event_type: The event type
            channel: The notification channel
            
        Returns:
            Optional[bool]: Whether the notification is enabled, or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT enabled FROM notification_preferences
                    WHERE user_id = ? AND event_type = ? AND channel = ?
                ''', (user_id, event_type, channel))
                
                result = cursor.fetchone()
                if result is not None:
                    return bool(result[0])
                return None
        except Exception as e:
            logger.error(f"Error getting notification preference: {e}")
            return None
    
    def get_notification_channels_for_event(self, user_id: str, event_type: str) -> List[str]:
        """Get enabled notification channels for a specific event
        
        Args:
            user_id: The user identifier
            event_type: The event type
            
        Returns:
            List[str]: List of enabled notification channels for this event
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT channel FROM notification_preferences
                    WHERE user_id = ? AND event_type = ? AND enabled = 1
                ''', (user_id, event_type))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting notification channels: {e}")
            return []
    
    def initialize_default_notification_preferences(self, user_id: str) -> bool:
        """Initialize default notification preferences for a new user
        
        Args:
            user_id: The user identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Define default notification configuration
            # Format: (event_type, channel, enabled)
            default_preferences = [
                # VM events
                ("vm_state_change", "web", True),
                ("vm_state_change", "email", False),
                ("vm_creation", "web", True),
                ("vm_deletion", "web", True),
                ("vm_error", "web", True),
                ("vm_error", "email", True),
                
                # Backup events
                ("backup_start", "web", False),
                ("backup_complete", "web", True),
                ("backup_error", "web", True),
                ("backup_error", "email", True),
                
                # Security events
                ("security_alert", "web", True),
                ("security_alert", "email", True),
                ("login_failure", "web", True),
                ("login_success", "web", False),
                
                # System events
                ("system_update", "web", True),
                ("resource_warning", "web", True),
                ("resource_warning", "email", False),
                ("disk_space_low", "web", True),
                ("disk_space_low", "email", True),
                
                # Service events
                ("service_start", "web", False),
                ("service_stop", "web", False),
                ("service_error", "web", True),
                ("service_error", "email", True),
            ]
            
            # Insert default preferences
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                for event_type, channel, enabled in default_preferences:
                    cursor.execute('''
                        INSERT INTO notification_preferences
                        (user_id, event_type, channel, enabled, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(user_id, event_type, channel) DO NOTHING
                    ''', (user_id, event_type, channel, enabled, now, now))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error initializing default notification preferences: {e}")
            return False
    
    def delete_notification_preferences(self, user_id: str) -> bool:
        """Delete all notification preferences for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM notification_preferences
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting notification preferences: {e}")
            return False

    # User shortcuts methods
    def add_shortcut(self, user_id: str, name: str, command_text: str, 
                     description: str = None, shortcut_key: str = None,
                     category: str = None, icon: str = None, position: int = None) -> bool:
        """Add or update a shortcut for a user
        
        Args:
            user_id: The user identifier
            name: The name of the shortcut
            command_text: The command text to execute
            description: Optional description of the shortcut
            shortcut_key: Optional keyboard shortcut (e.g., 'Ctrl+Alt+S')
            category: Optional category for organizing shortcuts
            icon: Optional icon name (e.g., 'bi-star' for Bootstrap icons)
            position: Optional position for display order
            
        Returns:
            bool: True if successful, False otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if shortcut already exists
                cursor.execute('''
                    SELECT id FROM user_shortcuts 
                    WHERE user_id = ? AND name = ?
                ''', (user_id, name))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing shortcut
                    cursor.execute('''
                        UPDATE user_shortcuts
                        SET command_text = ?, description = ?, shortcut_key = ?,
                            category = ?, icon = ?, position = ?, updated_at = ?
                        WHERE user_id = ? AND name = ?
                    ''', (command_text, description, shortcut_key, category, 
                          icon, position, now, user_id, name))
                else:
                    # Insert new shortcut
                    cursor.execute('''
                        INSERT INTO user_shortcuts
                        (user_id, name, command_text, description, shortcut_key,
                         category, icon, position, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, name, command_text, description, shortcut_key,
                         category, icon, position, now, now))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding shortcut: {e}")
            return False
    
    def get_shortcuts(self, user_id: str, category: str = None) -> List[Dict[str, Any]]:
        """Get shortcuts for a user
        
        Args:
            user_id: The user identifier
            category: Optional category filter
            
        Returns:
            List[Dict[str, Any]]: List of shortcuts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute('''
                        SELECT id, name, command_text, description, shortcut_key,
                               category, icon, position, created_at, updated_at
                        FROM user_shortcuts
                        WHERE user_id = ? AND category = ?
                        ORDER BY COALESCE(position, 999), name
                    ''', (user_id, category))
                else:
                    cursor.execute('''
                        SELECT id, name, command_text, description, shortcut_key,
                               category, icon, position, created_at, updated_at
                        FROM user_shortcuts
                        WHERE user_id = ?
                        ORDER BY COALESCE(position, 999), name
                    ''', (user_id,))
                
                columns = ['id', 'name', 'command_text', 'description', 'shortcut_key',
                          'category', 'icon', 'position', 'created_at', 'updated_at']
                
                shortcuts = []
                for row in cursor.fetchall():
                    shortcut = dict(zip(columns, row))
                    shortcuts.append(shortcut)
                
                return shortcuts
        except Exception as e:
            logger.error(f"Error getting shortcuts: {e}")
            return []
    
    def get_shortcut(self, user_id: str, shortcut_id: int = None, name: str = None) -> Optional[Dict[str, Any]]:
        """Get a specific shortcut by ID or name
        
        Args:
            user_id: The user identifier
            shortcut_id: The shortcut ID (optional if name is provided)
            name: The shortcut name (optional if shortcut_id is provided)
            
        Returns:
            Optional[Dict[str, Any]]: The shortcut or None if not found
        """
        if not shortcut_id and not name:
            return None
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if shortcut_id:
                    cursor.execute('''
                        SELECT id, name, command_text, description, shortcut_key,
                               category, icon, position, created_at, updated_at
                        FROM user_shortcuts
                        WHERE user_id = ? AND id = ?
                    ''', (user_id, shortcut_id))
                else:
                    cursor.execute('''
                        SELECT id, name, command_text, description, shortcut_key,
                               category, icon, position, created_at, updated_at
                        FROM user_shortcuts
                        WHERE user_id = ? AND name = ?
                    ''', (user_id, name))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                columns = ['id', 'name', 'command_text', 'description', 'shortcut_key',
                          'category', 'icon', 'position', 'created_at', 'updated_at']
                
                return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Error getting shortcut: {e}")
            return None
    
    def delete_shortcut(self, user_id: str, shortcut_id: int = None, name: str = None) -> bool:
        """Delete a shortcut
        
        Args:
            user_id: The user identifier
            shortcut_id: The shortcut ID (optional if name is provided)
            name: The shortcut name (optional if shortcut_id is provided)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not shortcut_id and not name:
            return False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if shortcut_id:
                    cursor.execute('''
                        DELETE FROM user_shortcuts
                        WHERE user_id = ? AND id = ?
                    ''', (user_id, shortcut_id))
                else:
                    cursor.execute('''
                        DELETE FROM user_shortcuts
                        WHERE user_id = ? AND name = ?
                    ''', (user_id, name))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting shortcut: {e}")
            return False
    
    def get_shortcut_categories(self, user_id: str) -> List[str]:
        """Get all shortcut categories for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            List[str]: List of category names
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT category
                    FROM user_shortcuts
                    WHERE user_id = ? AND category IS NOT NULL
                    ORDER BY category
                ''', (user_id,))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting shortcut categories: {e}")
            return []
    
    def update_shortcut_position(self, user_id: str, shortcut_id: int, position: int) -> bool:
        """Update the position of a shortcut
        
        Args:
            user_id: The user identifier
            shortcut_id: The shortcut ID
            position: The new position
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update the position
                cursor.execute('''
                    UPDATE user_shortcuts
                    SET position = ?, updated_at = ?
                    WHERE user_id = ? AND id = ?
                ''', (position, datetime.now().isoformat(), user_id, shortcut_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating shortcut position: {e}")
            return False
    
    def initialize_default_shortcuts(self, user_id: str) -> bool:
        """Initialize default shortcuts for a new user
        
        Args:
            user_id: The user identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Define default shortcuts
            default_shortcuts = [
                # VM Management shortcuts
                {
                    'name': 'List all VMs',
                    'command_text': 'list all virtual machines',
                    'description': 'Show all virtual machines in the system',
                    'category': 'VM Management',
                    'icon': 'bi-hdd',
                    'position': 1
                },
                {
                    'name': 'VM Status',
                    'command_text': 'show vm status',
                    'description': 'Display the status of all VMs',
                    'category': 'VM Management',
                    'icon': 'bi-info-circle',
                    'position': 2
                },
                {
                    'name': 'Start VM',
                    'command_text': 'start vm {{vm_id}}',
                    'description': 'Start a virtual machine by ID',
                    'category': 'VM Management',
                    'icon': 'bi-play-circle',
                    'position': 3
                },
                {
                    'name': 'Stop VM',
                    'command_text': 'stop vm {{vm_id}}',
                    'description': 'Stop a virtual machine by ID',
                    'category': 'VM Management',
                    'icon': 'bi-stop-circle',
                    'position': 4
                },
                
                # Backup shortcuts
                {
                    'name': 'Backup VM',
                    'command_text': 'backup vm {{vm_id}}',
                    'description': 'Create a backup of a virtual machine',
                    'category': 'Backups',
                    'icon': 'bi-cloud-arrow-up',
                    'position': 1
                },
                {
                    'name': 'List Backups',
                    'command_text': 'list backups',
                    'description': 'Show all available backups',
                    'category': 'Backups',
                    'icon': 'bi-list',
                    'position': 2
                },
                
                # System shortcuts
                {
                    'name': 'System Status',
                    'command_text': 'system status',
                    'description': 'Show overall system status',
                    'category': 'System',
                    'icon': 'bi-pc-display',
                    'position': 1
                },
                {
                    'name': 'Node Status',
                    'command_text': 'node status',
                    'description': 'Show status of all nodes',
                    'category': 'System',
                    'icon': 'bi-diagram-3',
                    'position': 2
                },
                {
                    'name': 'Resource Usage',
                    'command_text': 'show resource usage',
                    'description': 'Display current resource utilization',
                    'category': 'System',
                    'icon': 'bi-graph-up',
                    'position': 3
                }
            ]
            
            # Add default shortcuts
            for shortcut in default_shortcuts:
                self.add_shortcut(
                    user_id=user_id,
                    name=shortcut['name'],
                    command_text=shortcut['command_text'],
                    description=shortcut['description'],
                    category=shortcut['category'],
                    icon=shortcut['icon'],
                    position=shortcut['position']
                )
            
            return True
        except Exception as e:
            logger.error(f"Error initializing default shortcuts: {e}")
            return False

class UserManager:
    def __init__(self, base_nli_or_data_dir=None):
        """Initialize the user manager
        
        Args:
            base_nli_or_data_dir: Either the base NLI instance or a directory to store user data.
                                 If None, defaults to the 'data' directory in the project root.
        """
        # Handle different types of initialization parameters
        if base_nli_or_data_dir is None:
            # Use default data directory
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        elif isinstance(base_nli_or_data_dir, str):
            # Already a path string
            data_dir = base_nli_or_data_dir
        else:
            # Assume it's a base_nli instance
            self.base_nli = base_nli_or_data_dir
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        
        self.preferences_manager = UserPreferencesManager(data_dir)
        
    # ... existing methods ...
    
    # User shortcuts methods
    def add_shortcut(self, user_id: str, name: str, command_text: str, description: str = None, 
                    shortcut_key: str = None, category: str = None, icon: str = None, position: int = None) -> Dict:
        """Add a shortcut for a user
        
        Args:
            user_id: The user ID
            name: Name of the shortcut
            command_text: Command text (can include placeholders like {{param}})
            description: Optional description
            shortcut_key: Optional keyboard shortcut
            category: Optional category for grouping
            icon: Optional icon identifier
            position: Optional display position
            
        Returns:
            Dict: Response with success status and message
        """
        success = self.preferences_manager.add_shortcut(
            user_id, name, command_text, description, shortcut_key, category, icon, position
        )
        
        if success:
            return {
                'success': True,
                'message': f"Shortcut '{name}' added successfully"
            }
        else:
            return {
                'success': False,
                'message': f"Failed to add shortcut '{name}'"
            }
    
    def get_shortcuts(self, user_id: str, category: str = None) -> Dict:
        """Get shortcuts for a user
        
        Args:
            user_id: The user ID
            category: Optional category filter
            
        Returns:
            Dict: Response with shortcuts data
        """
        shortcuts = self.preferences_manager.get_shortcuts(user_id, category)
        
        # Group shortcuts by category
        if shortcuts:
            grouped_shortcuts = {}
            for shortcut in shortcuts:
                cat = shortcut.get('category') or 'Uncategorized'
                if cat not in grouped_shortcuts:
                    grouped_shortcuts[cat] = []
                grouped_shortcuts[cat].append(shortcut)
            
            return {
                'success': True,
                'message': f"Found {len(shortcuts)} shortcuts",
                'shortcuts': shortcuts,
                'grouped_shortcuts': grouped_shortcuts
            }
        else:
            return {
                'success': True,
                'message': "No shortcuts found",
                'shortcuts': [],
                'grouped_shortcuts': {}
            }
    
    def get_shortcut(self, user_id: str, shortcut_id: int = None, name: str = None) -> Dict:
        """Get a specific shortcut
        
        Args:
            user_id: The user ID
            shortcut_id: Optional shortcut ID
            name: Optional shortcut name (if ID not provided)
            
        Returns:
            Dict: Response with shortcut data
        """
        shortcut = self.preferences_manager.get_shortcut(user_id, shortcut_id, name)
        
        if shortcut:
            return {
                'success': True,
                'message': f"Found shortcut '{shortcut['name']}'",
                'shortcut': shortcut
            }
        else:
            return {
                'success': False,
                'message': "Shortcut not found"
            }
    
    def delete_shortcut(self, user_id: str, shortcut_id: int = None, name: str = None) -> Dict:
        """Delete a shortcut
        
        Args:
            user_id: The user ID
            shortcut_id: Optional shortcut ID
            name: Optional shortcut name (if ID not provided)
            
        Returns:
            Dict: Response with success status
        """
        success = self.preferences_manager.delete_shortcut(user_id, shortcut_id, name)
        
        if success:
            return {
                'success': True,
                'message': "Shortcut deleted successfully"
            }
        else:
            return {
                'success': False,
                'message': "Failed to delete shortcut or shortcut not found"
            }
    
    def update_shortcut_position(self, user_id: str, shortcut_id: int, position: int) -> Dict:
        """Update position of a shortcut
        
        Args:
            user_id: The user ID
            shortcut_id: The shortcut ID
            position: New position value
            
        Returns:
            Dict: Response with success status
        """
        success = self.preferences_manager.update_shortcut_position(user_id, shortcut_id, position)
        
        if success:
            return {
                'success': True,
                'message': "Shortcut position updated"
            }
        else:
            return {
                'success': False,
                'message': "Failed to update shortcut position"
            }
    
    def initialize_default_shortcuts(self, user_id: str) -> Dict:
        """Initialize default shortcuts for a user
        
        Args:
            user_id: The user ID
            
        Returns:
            Dict: Response with success status
        """
        success = self.preferences_manager.initialize_default_shortcuts(user_id)
        
        if success:
            return {
                'success': True,
                'message': "Default shortcuts initialized"
            }
        else:
            return {
                'success': False,
                'message': "Failed to initialize default shortcuts"
            }
    
    def get_shortcut_categories(self, user_id: str) -> Dict:
        """Get all shortcut categories for a user
        
        Args:
            user_id: The user ID
            
        Returns:
            Dict: Response with list of categories
        """
        categories = self.preferences_manager.get_shortcut_categories(user_id)
        
        return {
            'success': True,
            'message': f"Found {len(categories)} categories",
            'categories': categories
        }