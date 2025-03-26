"""
Dashboard management module for user-configurable dashboards.
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class DashboardManager:
    def __init__(self, data_dir: str = None):
        """Initialize the dashboard manager
        
        Args:
            data_dir: Directory to store dashboard data. If None,
                     defaults to the 'data' directory in the project root.
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize SQLite database for user dashboards
        self.db_path = os.path.join(self.data_dir, 'user_preferences.db')
        self._init_db()
        
    def _init_db(self):
        """Initialize the SQLite database for dashboard tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # User dashboards table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_dashboards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    layout TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(user_id, name)
                )
            ''')
            
            # Dashboard panels table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dashboard_panels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dashboard_id INTEGER NOT NULL,
                    panel_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    config TEXT,
                    position_x INTEGER DEFAULT 0,
                    position_y INTEGER DEFAULT 0,
                    width INTEGER DEFAULT 6,
                    height INTEGER DEFAULT 4,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (dashboard_id) REFERENCES user_dashboards (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            
    def create_dashboard(self, user_id: str, name: str, is_default: bool = False, layout: str = "grid") -> Optional[int]:
        """Create a new dashboard
        
        Args:
            user_id: The user identifier
            name: Dashboard name
            is_default: Whether this is the default dashboard
            layout: Dashboard layout type ("grid", "free", etc.)
            
        Returns:
            Optional[int]: Dashboard ID if successful, None otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # If setting as default, clear any existing default first
                if is_default:
                    cursor.execute('''
                        UPDATE user_dashboards
                        SET is_default = 0
                        WHERE user_id = ?
                    ''', (user_id,))
                
                # Insert new dashboard
                cursor.execute('''
                    INSERT INTO user_dashboards
                    (user_id, name, is_default, layout, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, name, is_default, layout, now, now))
                
                dashboard_id = cursor.lastrowid
                conn.commit()
                return dashboard_id
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return None
            
    def get_dashboards(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all dashboards for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            List[Dict[str, Any]]: List of dashboard objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, name, is_default, layout, created_at, updated_at
                    FROM user_dashboards
                    WHERE user_id = ?
                    ORDER BY is_default DESC, name ASC
                ''', (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting dashboards: {e}")
            return []
            
    def get_dashboard(self, dashboard_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific dashboard by ID
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            Optional[Dict[str, Any]]: Dashboard object if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, user_id, name, is_default, layout, created_at, updated_at
                    FROM user_dashboards
                    WHERE id = ?
                ''', (dashboard_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                dashboard = dict(row)
                
                # Get panels for this dashboard
                cursor.execute('''
                    SELECT id, panel_type, title, config, position_x, position_y, 
                           width, height, created_at, updated_at
                    FROM dashboard_panels
                    WHERE dashboard_id = ?
                    ORDER BY position_y, position_x
                ''', (dashboard_id,))
                
                panels = []
                for panel_row in cursor.fetchall():
                    panel = dict(panel_row)
                    # Parse panel config from JSON
                    if panel['config']:
                        try:
                            panel['config'] = json.loads(panel['config'])
                        except:
                            panel['config'] = {}
                    panels.append(panel)
                
                dashboard['panels'] = panels
                return dashboard
        except Exception as e:
            logger.error(f"Error getting dashboard: {e}")
            return None
            
    def update_dashboard(self, dashboard_id: int, name: str = None, is_default: bool = None, layout: str = None) -> bool:
        """Update dashboard properties
        
        Args:
            dashboard_id: Dashboard ID
            name: Optional new dashboard name
            is_default: Optional default status
            layout: Optional new layout
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if dashboard exists and get user_id
                cursor.execute("SELECT user_id FROM user_dashboards WHERE id = ?", (dashboard_id,))
                result = cursor.fetchone()
                if not result:
                    return False
                
                user_id = result[0]
                updates = []
                params = []
                
                if name is not None:
                    updates.append("name = ?")
                    params.append(name)
                    
                if layout is not None:
                    updates.append("layout = ?")
                    params.append(layout)
                
                if is_default is not None:
                    if is_default:
                        # Clear existing default first
                        cursor.execute('''
                            UPDATE user_dashboards
                            SET is_default = 0
                            WHERE user_id = ?
                        ''', (user_id,))
                    
                    updates.append("is_default = ?")
                    params.append(is_default)
                
                if not updates:
                    return True  # Nothing to update
                
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(dashboard_id)
                
                cursor.execute(f'''
                    UPDATE user_dashboards
                    SET {", ".join(updates)}
                    WHERE id = ?
                ''', params)
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return False
            
    def delete_dashboard(self, dashboard_id: int) -> bool:
        """Delete a dashboard
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete dashboard (cascade will delete panels)
                cursor.execute("DELETE FROM user_dashboards WHERE id = ?", (dashboard_id,))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting dashboard: {e}")
            return False
    
    def add_panel(self, dashboard_id: int, panel_type: str, title: str, 
                  config: Dict = None, position_x: int = 0, position_y: int = 0,
                  width: int = 6, height: int = 4) -> Optional[int]:
        """Add a new panel to a dashboard
        
        Args:
            dashboard_id: Dashboard ID
            panel_type: Panel type (chart, metrics, vm_list, etc.)
            title: Panel title
            config: Panel configuration
            position_x: X position in grid
            position_y: Y position in grid
            width: Panel width (grid units)
            height: Panel height (grid units)
            
        Returns:
            Optional[int]: Panel ID if successful, None otherwise
        """
        now = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if dashboard exists
                cursor.execute("SELECT id FROM user_dashboards WHERE id = ?", (dashboard_id,))
                if not cursor.fetchone():
                    return None
                
                config_json = json.dumps(config) if config else None
                
                cursor.execute('''
                    INSERT INTO dashboard_panels
                    (dashboard_id, panel_type, title, config, position_x, position_y, 
                     width, height, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (dashboard_id, panel_type, title, config_json, position_x, position_y, 
                      width, height, now, now))
                
                panel_id = cursor.lastrowid
                conn.commit()
                return panel_id
        except Exception as e:
            logger.error(f"Error adding panel: {e}")
            return None
    
    def update_panel(self, panel_id: int, title: str = None, config: Dict = None,
                    position_x: int = None, position_y: int = None, 
                    width: int = None, height: int = None) -> bool:
        """Update panel properties
        
        Args:
            panel_id: Panel ID
            title: Optional new title
            config: Optional new config
            position_x: Optional new X position
            position_y: Optional new Y position
            width: Optional new width
            height: Optional new height
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                updates = []
                params = []
                
                if title is not None:
                    updates.append("title = ?")
                    params.append(title)
                    
                if config is not None:
                    updates.append("config = ?")
                    params.append(json.dumps(config))
                
                if position_x is not None:
                    updates.append("position_x = ?")
                    params.append(position_x)
                    
                if position_y is not None:
                    updates.append("position_y = ?")
                    params.append(position_y)
                    
                if width is not None:
                    updates.append("width = ?")
                    params.append(width)
                    
                if height is not None:
                    updates.append("height = ?")
                    params.append(height)
                
                if not updates:
                    return True  # Nothing to update
                
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(panel_id)
                
                cursor.execute(f'''
                    UPDATE dashboard_panels
                    SET {", ".join(updates)}
                    WHERE id = ?
                ''', params)
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating panel: {e}")
            return False
    
    def delete_panel(self, panel_id: int) -> bool:
        """Delete a panel
        
        Args:
            panel_id: Panel ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM dashboard_panels WHERE id = ?", (panel_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting panel: {e}")
            return False
            
    def initialize_default_dashboard(self, user_id: str) -> Optional[int]:
        """Create a default dashboard for a user
        
        Args:
            user_id: The user identifier
            
        Returns:
            Optional[int]: Dashboard ID if successful, None otherwise
        """
        try:
            # Create a new dashboard
            dashboard_id = self.create_dashboard(
                user_id=user_id,
                name="Default Dashboard",
                is_default=True,
                layout="grid"
            )
            
            if not dashboard_id:
                return None
            
            # Add some default panels
            self.add_panel(
                dashboard_id=dashboard_id,
                panel_type="vm_status",
                title="VM Status",
                config={"show_resource_usage": True, "limit": 5},
                position_x=0,
                position_y=0,
                width=6,
                height=4
            )
            
            self.add_panel(
                dashboard_id=dashboard_id,
                panel_type="system_metrics",
                title="System Metrics",
                config={"metrics": ["cpu", "memory", "storage"]},
                position_x=6,
                position_y=0,
                width=6,
                height=4
            )
            
            self.add_panel(
                dashboard_id=dashboard_id,
                panel_type="recent_commands",
                title="Recent Commands",
                config={"limit": 5, "show_timestamp": True},
                position_x=0,
                position_y=4,
                width=6,
                height=3
            )
            
            self.add_panel(
                dashboard_id=dashboard_id,
                panel_type="favorite_commands",
                title="Favorite Commands",
                config={"show_description": True},
                position_x=6,
                position_y=4,
                width=6,
                height=3
            )
            
            return dashboard_id
        except Exception as e:
            logger.error(f"Error initializing default dashboard: {e}")
            return None

    def sync_user_dashboards(self, user_id: str, remote_dashboards: List[Dict]) -> bool:
        """Sync dashboards with remote data for cross-device support.
        
        Args:
            user_id: The user identifier
            remote_dashboards: List of dashboard configurations from remote
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get local dashboard IDs
                cursor.execute('SELECT id FROM user_dashboards WHERE user_id = ?', (user_id,))
                local_ids = set(row[0] for row in cursor.fetchall())
                remote_ids = set(d['id'] for d in remote_dashboards)
                
                # Handle deletions (dashboards that exist locally but not in remote)
                for dashboard_id in local_ids - remote_ids:
                    self.delete_dashboard(dashboard_id)
                
                # Handle updates and additions
                for dashboard in remote_dashboards:
                    if dashboard['id'] in local_ids:
                        # Update existing dashboard
                        self.update_dashboard(
                            dashboard_id=dashboard['id'],
                            name=dashboard.get('name'),
                            is_default=dashboard.get('is_default', False),
                            layout=dashboard.get('layout', 'grid')
                        )
                        
                        # Update panels
                        cursor.execute('DELETE FROM dashboard_panels WHERE dashboard_id = ?', (dashboard['id'],))
                        for panel in dashboard.get('panels', []):
                            self.add_panel(
                                dashboard_id=dashboard['id'],
                                panel_type=panel['panel_type'],
                                title=panel['title'],
                                config=panel.get('config'),
                                position_x=panel.get('position_x', 0),
                                position_y=panel.get('position_y', 0),
                                width=panel.get('width', 6),
                                height=panel.get('height', 4)
                            )
                    else:
                        # Create new dashboard
                        new_id = self.create_dashboard(
                            user_id=user_id,
                            name=dashboard['name'],
                            is_default=dashboard.get('is_default', False),
                            layout=dashboard.get('layout', 'grid')
                        )
                        
                        if new_id:
                            for panel in dashboard.get('panels', []):
                                self.add_panel(
                                    dashboard_id=new_id,
                                    panel_type=panel['panel_type'],
                                    title=panel['title'],
                                    config=panel.get('config'),
                                    position_x=panel.get('position_x', 0),
                                    position_y=panel.get('position_y', 0),
                                    width=panel.get('width', 6),
                                    height=panel.get('height', 4)
                                )
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error syncing dashboards: {e}")
            return False