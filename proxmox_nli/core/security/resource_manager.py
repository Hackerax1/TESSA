"""
Resource manager module for multi-tenancy support.
Handles resource allocation and access control for multiple users.
"""
import os
import json
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ResourceManager:
    """Manages resource allocation and access control for multi-tenancy."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the resource manager.
        
        Args:
            data_dir: Directory to store resource data. If None,
                     defaults to the 'data' directory in the project root.
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize SQLite database for resource management
        self.db_path = os.path.join(self.data_dir, 'resource_management.db')
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database for resource management."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create resource allocation table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                permissions TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, resource_type, resource_id)
            )
            ''')
            
            # Create resource groups table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name)
            )
            ''')
            
            # Create group resources table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_resources (
                group_id INTEGER NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, resource_type, resource_id),
                FOREIGN KEY (group_id) REFERENCES resource_groups(id) ON DELETE CASCADE
            )
            ''')
            
            # Create user groups table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_groups (
                user_id TEXT NOT NULL,
                group_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, group_id),
                FOREIGN KEY (group_id) REFERENCES resource_groups(id) ON DELETE CASCADE
            )
            ''')
            
            # Create roles table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                permissions TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name)
            )
            ''')
            
            # Create user roles table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
            )
            ''')
            
            # Create quota table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                limit_value INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, resource_type)
            )
            ''')
            
            # Create default roles if they don't exist
            self._create_default_roles(cursor)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing resource management database: {e}")
            raise
    
    def _create_default_roles(self, cursor):
        """Create default roles if they don't exist."""
        # Check if roles already exist
        cursor.execute("SELECT COUNT(*) FROM roles")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create admin role
            admin_permissions = json.dumps({
                "vm": ["view", "create", "modify", "delete", "start", "stop", "backup", "restore", "migrate"],
                "container": ["view", "create", "modify", "delete", "start", "stop", "backup", "restore", "migrate"],
                "storage": ["view", "create", "modify", "delete", "allocate"],
                "network": ["view", "create", "modify", "delete"],
                "backup": ["view", "create", "modify", "delete", "restore"],
                "user": ["view", "create", "modify", "delete"],
                "system": ["view", "modify", "update"]
            })
            
            # Create power user role
            power_user_permissions = json.dumps({
                "vm": ["view", "create", "modify", "start", "stop", "backup"],
                "container": ["view", "create", "modify", "start", "stop", "backup"],
                "storage": ["view", "allocate"],
                "network": ["view"],
                "backup": ["view", "create", "restore"],
                "user": ["view"],
                "system": ["view"]
            })
            
            # Create standard user role
            user_permissions = json.dumps({
                "vm": ["view", "start", "stop"],
                "container": ["view", "start", "stop"],
                "storage": ["view"],
                "network": ["view"],
                "backup": ["view"],
                "user": ["view"],
                "system": ["view"]
            })
            
            # Create guest role
            guest_permissions = json.dumps({
                "vm": ["view"],
                "container": ["view"],
                "storage": ["view"],
                "network": ["view"],
                "backup": ["view"],
                "user": ["view"],
                "system": ["view"]
            })
            
            # Insert roles
            roles = [
                ("admin", "Administrator with full access to all resources", admin_permissions),
                ("power_user", "Power user with extended privileges", power_user_permissions),
                ("user", "Standard user with basic privileges", user_permissions),
                ("guest", "Guest user with view-only access", guest_permissions)
            ]
            
            for role in roles:
                cursor.execute(
                    "INSERT INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                    role
                )
    
    def allocate_resource(self, user_id: str, resource_type: str, resource_id: str, permissions: List[str]) -> Dict:
        """Allocate a resource to a user with specified permissions.
        
        Args:
            user_id: The user ID
            resource_type: Type of resource (vm, container, storage, etc.)
            resource_id: ID of the resource
            permissions: List of permissions (view, create, modify, delete, etc.)
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if allocation already exists
            cursor.execute(
                "SELECT id FROM resource_allocations WHERE user_id = ? AND resource_type = ? AND resource_id = ?",
                (user_id, resource_type, resource_id)
            )
            result = cursor.fetchone()
            
            permissions_json = json.dumps(permissions)
            current_time = datetime.now().isoformat()
            
            if result:
                # Update existing allocation
                cursor.execute(
                    "UPDATE resource_allocations SET permissions = ?, updated_at = ? WHERE id = ?",
                    (permissions_json, current_time, result[0])
                )
                message = f"Updated resource allocation for {resource_type} {resource_id}"
            else:
                # Create new allocation
                cursor.execute(
                    "INSERT INTO resource_allocations (user_id, resource_type, resource_id, permissions) VALUES (?, ?, ?, ?)",
                    (user_id, resource_type, resource_id, permissions_json)
                )
                message = f"Created resource allocation for {resource_type} {resource_id}"
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error allocating resource: {e}")
            return {
                "success": False,
                "message": f"Error allocating resource: {str(e)}"
            }
    
    def get_user_resources(self, user_id: str, resource_type: Optional[str] = None) -> Dict:
        """Get resources allocated to a user.
        
        Args:
            user_id: The user ID
            resource_type: Optional resource type filter
            
        Returns:
            Dict: Response with success status and resources
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if resource_type:
                cursor.execute(
                    "SELECT resource_type, resource_id, permissions FROM resource_allocations WHERE user_id = ? AND resource_type = ?",
                    (user_id, resource_type)
                )
            else:
                cursor.execute(
                    "SELECT resource_type, resource_id, permissions FROM resource_allocations WHERE user_id = ?",
                    (user_id,)
                )
            
            rows = cursor.fetchall()
            conn.close()
            
            resources = []
            for row in rows:
                resources.append({
                    "resource_type": row[0],
                    "resource_id": row[1],
                    "permissions": json.loads(row[2])
                })
            
            return {
                "success": True,
                "resources": resources
            }
            
        except Exception as e:
            logger.error(f"Error getting user resources: {e}")
            return {
                "success": False,
                "message": f"Error getting user resources: {str(e)}"
            }
    
    def check_permission(self, user_id: str, resource_type: str, resource_id: str, permission: str) -> bool:
        """Check if a user has a specific permission for a resource.
        
        Args:
            user_id: The user ID
            resource_type: Type of resource
            resource_id: ID of the resource
            permission: Permission to check
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check direct resource allocation
            cursor.execute(
                "SELECT permissions FROM resource_allocations WHERE user_id = ? AND resource_type = ? AND resource_id = ?",
                (user_id, resource_type, resource_id)
            )
            result = cursor.fetchone()
            
            if result:
                permissions = json.loads(result[0])
                if permission in permissions:
                    conn.close()
                    return True
            
            # Check group-based permissions
            cursor.execute("""
                SELECT r.permissions
                FROM user_groups ug
                JOIN group_resources gr ON ug.group_id = gr.group_id
                JOIN roles r ON ug.role = r.name
                WHERE ug.user_id = ? AND gr.resource_type = ? AND gr.resource_id = ?
            """, (user_id, resource_type, resource_id))
            
            group_results = cursor.fetchall()
            conn.close()
            
            for group_result in group_results:
                role_permissions = json.loads(group_result[0])
                resource_permissions = role_permissions.get(resource_type, [])
                if permission in resource_permissions:
                    return True
            
            # Check user roles for global permissions
            return self.check_role_permission(user_id, resource_type, permission)
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    def check_role_permission(self, user_id: str, resource_type: str, permission: str) -> bool:
        """Check if a user has a role-based permission for a resource type.
        
        Args:
            user_id: The user ID
            resource_type: Type of resource
            permission: Permission to check
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT r.permissions
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = ?
            """, (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            for result in results:
                role_permissions = json.loads(result[0])
                resource_permissions = role_permissions.get(resource_type, [])
                if permission in resource_permissions:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking role permission: {e}")
            return False
    
    def create_resource_group(self, name: str, description: Optional[str] = None) -> Dict:
        """Create a resource group.
        
        Args:
            name: Group name
            description: Optional group description
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO resource_groups (name, description) VALUES (?, ?)",
                (name, description)
            )
            
            group_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"Resource group '{name}' created successfully",
                "group_id": group_id
            }
            
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "message": f"Resource group '{name}' already exists"
            }
        except Exception as e:
            logger.error(f"Error creating resource group: {e}")
            return {
                "success": False,
                "message": f"Error creating resource group: {str(e)}"
            }
    
    def add_resource_to_group(self, group_id: int, resource_type: str, resource_id: str) -> Dict:
        """Add a resource to a group.
        
        Args:
            group_id: Group ID
            resource_type: Type of resource
            resource_id: ID of the resource
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO group_resources (group_id, resource_type, resource_id) VALUES (?, ?, ?)",
                (group_id, resource_type, resource_id)
            )
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"Resource {resource_type} {resource_id} added to group {group_id}"
            }
            
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "message": f"Resource {resource_type} {resource_id} already exists in group {group_id}"
            }
        except Exception as e:
            logger.error(f"Error adding resource to group: {e}")
            return {
                "success": False,
                "message": f"Error adding resource to group: {str(e)}"
            }
    
    def add_user_to_group(self, user_id: str, group_id: int, role: str = "user") -> Dict:
        """Add a user to a group with a specific role.
        
        Args:
            user_id: User ID
            group_id: Group ID
            role: Role name (admin, power_user, user, guest)
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verify role exists
            cursor.execute("SELECT id FROM roles WHERE name = ?", (role,))
            if not cursor.fetchone():
                conn.close()
                return {
                    "success": False,
                    "message": f"Role '{role}' does not exist"
                }
            
            cursor.execute(
                "INSERT INTO user_groups (user_id, group_id, role) VALUES (?, ?, ?)",
                (user_id, group_id, role)
            )
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"User {user_id} added to group {group_id} with role {role}"
            }
            
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "message": f"User {user_id} is already in group {group_id}"
            }
        except Exception as e:
            logger.error(f"Error adding user to group: {e}")
            return {
                "success": False,
                "message": f"Error adding user to group: {str(e)}"
            }
    
    def assign_role_to_user(self, user_id: str, role_name: str) -> Dict:
        """Assign a role to a user.
        
        Args:
            user_id: User ID
            role_name: Role name
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get role ID
            cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return {
                    "success": False,
                    "message": f"Role '{role_name}' does not exist"
                }
            
            role_id = result[0]
            
            # Check if user already has this role
            cursor.execute("SELECT 1 FROM user_roles WHERE user_id = ? AND role_id = ?", (user_id, role_id))
            if cursor.fetchone():
                conn.close()
                return {
                    "success": False,
                    "message": f"User {user_id} already has role '{role_name}'"
                }
            
            # Assign role to user
            cursor.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id)
            )
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": f"Role '{role_name}' assigned to user {user_id}"
            }
            
        except Exception as e:
            logger.error(f"Error assigning role to user: {e}")
            return {
                "success": False,
                "message": f"Error assigning role to user: {str(e)}"
            }
    
    def get_user_roles(self, user_id: str) -> Dict:
        """Get roles assigned to a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Response with success status and roles
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT r.name, r.description, r.permissions
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            roles = []
            for row in rows:
                roles.append({
                    "name": row[0],
                    "description": row[1],
                    "permissions": json.loads(row[2])
                })
            
            return {
                "success": True,
                "roles": roles
            }
            
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            return {
                "success": False,
                "message": f"Error getting user roles: {str(e)}"
            }
    
    def set_user_quota(self, user_id: str, resource_type: str, limit_value: int) -> Dict:
        """Set a quota limit for a user on a specific resource type.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            limit_value: Maximum allowed value
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if quota already exists
            cursor.execute(
                "SELECT id FROM quotas WHERE user_id = ? AND resource_type = ?",
                (user_id, resource_type)
            )
            result = cursor.fetchone()
            
            current_time = datetime.now().isoformat()
            
            if result:
                # Update existing quota
                cursor.execute(
                    "UPDATE quotas SET limit_value = ?, updated_at = ? WHERE id = ?",
                    (limit_value, current_time, result[0])
                )
                message = f"Updated quota for {resource_type} to {limit_value}"
            else:
                # Create new quota
                cursor.execute(
                    "INSERT INTO quotas (user_id, resource_type, limit_value) VALUES (?, ?, ?)",
                    (user_id, resource_type, limit_value)
                )
                message = f"Created quota for {resource_type} with limit {limit_value}"
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error setting user quota: {e}")
            return {
                "success": False,
                "message": f"Error setting user quota: {str(e)}"
            }
    
    def get_user_quotas(self, user_id: str) -> Dict:
        """Get quotas for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Response with success status and quotas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT resource_type, limit_value FROM quotas WHERE user_id = ?",
                (user_id,)
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            quotas = {}
            for row in rows:
                quotas[row[0]] = row[1]
            
            return {
                "success": True,
                "quotas": quotas
            }
            
        except Exception as e:
            logger.error(f"Error getting user quotas: {e}")
            return {
                "success": False,
                "message": f"Error getting user quotas: {str(e)}"
            }
    
    def check_quota(self, user_id: str, resource_type: str, requested_value: int = 1) -> Tuple[bool, Optional[str]]:
        """Check if a user has sufficient quota for a resource.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            requested_value: Value to check against quota
            
        Returns:
            Tuple[bool, Optional[str]]: (allowed, message)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get quota limit
            cursor.execute(
                "SELECT limit_value FROM quotas WHERE user_id = ? AND resource_type = ?",
                (user_id, resource_type)
            )
            result = cursor.fetchone()
            
            if not result:
                # No quota set, allow by default
                conn.close()
                return True, None
            
            limit_value = result[0]
            
            # Count current usage
            cursor.execute(
                "SELECT COUNT(*) FROM resource_allocations WHERE user_id = ? AND resource_type = ?",
                (user_id, resource_type)
            )
            current_usage = cursor.fetchone()[0]
            
            conn.close()
            
            if current_usage + requested_value <= limit_value:
                return True, None
            else:
                return False, f"Quota exceeded for {resource_type}. Limit: {limit_value}, Current: {current_usage}, Requested: {requested_value}"
            
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            return False, f"Error checking quota: {str(e)}"
