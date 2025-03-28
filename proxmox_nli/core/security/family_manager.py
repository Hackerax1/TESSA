"""
Family manager module for multi-tenancy support.
Handles family member accounts and role-based access control.
"""
import os
import json
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .resource_manager import ResourceManager

logger = logging.getLogger(__name__)

class FamilyManager:
    """Manages family member accounts and access control."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the family manager.
        
        Args:
            data_dir: Directory to store family data. If None,
                     defaults to the 'data' directory in the project root.
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize SQLite database for family management
        self.db_path = os.path.join(self.data_dir, 'family_management.db')
        self._init_db()
        
        # Initialize resource manager
        self.resource_manager = ResourceManager(self.data_dir)
    
    def _init_db(self):
        """Initialize the SQLite database for family management."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create family members table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                relationship TEXT,
                age INTEGER,
                profile_image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
            ''')
            
            # Create family groups table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name)
            )
            ''')
            
            # Create family group members table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_group_members (
                group_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, user_id),
                FOREIGN KEY (group_id) REFERENCES family_groups(id) ON DELETE CASCADE
            )
            ''')
            
            # Create family access policies table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_access_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                policy_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name)
            )
            ''')
            
            # Create family member policies table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_member_policies (
                user_id TEXT NOT NULL,
                policy_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, policy_id),
                FOREIGN KEY (policy_id) REFERENCES family_access_policies(id) ON DELETE CASCADE
            )
            ''')
            
            # Create default family groups and policies
            self._create_default_family_groups(cursor)
            self._create_default_access_policies(cursor)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing family management database: {e}")
            raise
    
    def _create_default_family_groups(self, cursor):
        """Create default family groups if they don't exist."""
        # Check if groups already exist
        cursor.execute("SELECT COUNT(*) FROM family_groups")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert default groups
            groups = [
                ("Parents", "Parent/guardian group with administrative access"),
                ("Children", "Children with limited access"),
                ("Teens", "Teenagers with moderate access"),
                ("Guests", "Guest users with minimal access")
            ]
            
            for group in groups:
                cursor.execute(
                    "INSERT INTO family_groups (name, description) VALUES (?, ?)",
                    group
                )
    
    def _create_default_access_policies(self, cursor):
        """Create default access policies if they don't exist."""
        # Check if policies already exist
        cursor.execute("SELECT COUNT(*) FROM family_access_policies")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create parent policy
            parent_policy = json.dumps({
                "content_restrictions": {
                    "adult_content": False,
                    "violence": False,
                    "explicit_language": False
                },
                "time_restrictions": {
                    "enabled": False,
                    "weekday_hours": {"start": "00:00", "end": "23:59"},
                    "weekend_hours": {"start": "00:00", "end": "23:59"}
                },
                "resource_restrictions": {
                    "vm_creation": True,
                    "container_creation": True,
                    "storage_allocation": True,
                    "network_configuration": True,
                    "system_updates": True
                },
                "usage_quotas": {
                    "vm_count": -1,  # Unlimited
                    "container_count": -1,  # Unlimited
                    "storage_gb": -1,  # Unlimited
                    "backup_count": -1  # Unlimited
                }
            })
            
            # Create teen policy
            teen_policy = json.dumps({
                "content_restrictions": {
                    "adult_content": True,
                    "violence": False,
                    "explicit_language": False
                },
                "time_restrictions": {
                    "enabled": True,
                    "weekday_hours": {"start": "15:00", "end": "22:00"},
                    "weekend_hours": {"start": "09:00", "end": "23:00"}
                },
                "resource_restrictions": {
                    "vm_creation": True,
                    "container_creation": True,
                    "storage_allocation": False,
                    "network_configuration": False,
                    "system_updates": False
                },
                "usage_quotas": {
                    "vm_count": 3,
                    "container_count": 5,
                    "storage_gb": 100,
                    "backup_count": 10
                }
            })
            
            # Create child policy
            child_policy = json.dumps({
                "content_restrictions": {
                    "adult_content": True,
                    "violence": True,
                    "explicit_language": True
                },
                "time_restrictions": {
                    "enabled": True,
                    "weekday_hours": {"start": "15:00", "end": "20:00"},
                    "weekend_hours": {"start": "09:00", "end": "21:00"}
                },
                "resource_restrictions": {
                    "vm_creation": False,
                    "container_creation": False,
                    "storage_allocation": False,
                    "network_configuration": False,
                    "system_updates": False
                },
                "usage_quotas": {
                    "vm_count": 1,
                    "container_count": 2,
                    "storage_gb": 20,
                    "backup_count": 5
                }
            })
            
            # Create guest policy
            guest_policy = json.dumps({
                "content_restrictions": {
                    "adult_content": True,
                    "violence": True,
                    "explicit_language": True
                },
                "time_restrictions": {
                    "enabled": True,
                    "weekday_hours": {"start": "09:00", "end": "21:00"},
                    "weekend_hours": {"start": "09:00", "end": "21:00"}
                },
                "resource_restrictions": {
                    "vm_creation": False,
                    "container_creation": False,
                    "storage_allocation": False,
                    "network_configuration": False,
                    "system_updates": False
                },
                "usage_quotas": {
                    "vm_count": 0,
                    "container_count": 1,
                    "storage_gb": 5,
                    "backup_count": 1
                }
            })
            
            # Insert policies
            policies = [
                ("Parent", "Full access policy for parents/guardians", parent_policy),
                ("Teen", "Moderate access policy for teenagers", teen_policy),
                ("Child", "Limited access policy for children", child_policy),
                ("Guest", "Minimal access policy for guests", guest_policy)
            ]
            
            for policy in policies:
                cursor.execute(
                    "INSERT INTO family_access_policies (name, description, policy_data) VALUES (?, ?, ?)",
                    policy
                )
    
    def add_family_member(self, user_id: str, name: str, relationship: Optional[str] = None, 
                         age: Optional[int] = None, profile_image: Optional[str] = None) -> Dict:
        """Add a family member.
        
        Args:
            user_id: User ID
            name: Family member's name
            relationship: Optional relationship to primary account (parent, child, etc.)
            age: Optional age
            profile_image: Optional profile image path
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            # Check if member already exists
            cursor.execute("SELECT id FROM family_members WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                # Update existing member
                cursor.execute(
                    """UPDATE family_members 
                       SET name = ?, relationship = ?, age = ?, profile_image = ?, updated_at = ? 
                       WHERE id = ?""",
                    (name, relationship, age, profile_image, current_time, result[0])
                )
                message = f"Updated family member {name}"
            else:
                # Add new member
                cursor.execute(
                    """INSERT INTO family_members 
                       (user_id, name, relationship, age, profile_image) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, name, relationship, age, profile_image)
                )
                message = f"Added family member {name}"
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error adding family member: {e}")
            return {
                "success": False,
                "message": f"Error adding family member: {str(e)}"
            }
    
    def get_family_members(self) -> Dict:
        """Get all family members.
        
        Returns:
            Dict: Response with success status and members
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT user_id, name, relationship, age, profile_image FROM family_members"
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            members = []
            for row in rows:
                members.append({
                    "user_id": row[0],
                    "name": row[1],
                    "relationship": row[2],
                    "age": row[3],
                    "profile_image": row[4]
                })
            
            return {
                "success": True,
                "members": members
            }
            
        except Exception as e:
            logger.error(f"Error getting family members: {e}")
            return {
                "success": False,
                "message": f"Error getting family members: {str(e)}"
            }
    
    def get_family_member(self, user_id: str) -> Dict:
        """Get a specific family member.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Response with success status and member data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT user_id, name, relationship, age, profile_image FROM family_members WHERE user_id = ?",
                (user_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {
                    "success": False,
                    "message": f"Family member with user ID {user_id} not found"
                }
            
            member = {
                "user_id": row[0],
                "name": row[1],
                "relationship": row[2],
                "age": row[3],
                "profile_image": row[4]
            }
            
            return {
                "success": True,
                "member": member
            }
            
        except Exception as e:
            logger.error(f"Error getting family member: {e}")
            return {
                "success": False,
                "message": f"Error getting family member: {str(e)}"
            }
    
    def add_member_to_group(self, user_id: str, group_name: str) -> Dict:
        """Add a family member to a group.
        
        Args:
            user_id: User ID
            group_name: Group name
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get group ID
            cursor.execute("SELECT id FROM family_groups WHERE name = ?", (group_name,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return {
                    "success": False,
                    "message": f"Group '{group_name}' does not exist"
                }
            
            group_id = result[0]
            
            # Check if member is already in the group
            cursor.execute(
                "SELECT 1 FROM family_group_members WHERE group_id = ? AND user_id = ?",
                (group_id, user_id)
            )
            
            if cursor.fetchone():
                conn.close()
                return {
                    "success": False,
                    "message": f"Member is already in group '{group_name}'"
                }
            
            # Add member to group
            cursor.execute(
                "INSERT INTO family_group_members (group_id, user_id) VALUES (?, ?)",
                (group_id, user_id)
            )
            
            conn.commit()
            conn.close()
            
            # Assign appropriate role based on group
            role_mapping = {
                "Parents": "admin",
                "Teens": "power_user",
                "Children": "user",
                "Guests": "guest"
            }
            
            if group_name in role_mapping:
                self.resource_manager.assign_role_to_user(user_id, role_mapping[group_name])
            
            return {
                "success": True,
                "message": f"Added member to group '{group_name}'"
            }
            
        except Exception as e:
            logger.error(f"Error adding member to group: {e}")
            return {
                "success": False,
                "message": f"Error adding member to group: {str(e)}"
            }
    
    def get_member_groups(self, user_id: str) -> Dict:
        """Get groups that a family member belongs to.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Response with success status and groups
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT g.id, g.name, g.description
                FROM family_groups g
                JOIN family_group_members m ON g.id = m.group_id
                WHERE m.user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            groups = []
            for row in rows:
                groups.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2]
                })
            
            return {
                "success": True,
                "groups": groups
            }
            
        except Exception as e:
            logger.error(f"Error getting member groups: {e}")
            return {
                "success": False,
                "message": f"Error getting member groups: {str(e)}"
            }
    
    def apply_access_policy(self, user_id: str, policy_name: str) -> Dict:
        """Apply an access policy to a family member.
        
        Args:
            user_id: User ID
            policy_name: Policy name
            
        Returns:
            Dict: Response with success status and message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get policy ID
            cursor.execute("SELECT id, policy_data FROM family_access_policies WHERE name = ?", (policy_name,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return {
                    "success": False,
                    "message": f"Policy '{policy_name}' does not exist"
                }
            
            policy_id = result[0]
            policy_data = json.loads(result[1])
            
            # Check if policy is already applied
            cursor.execute(
                "SELECT 1 FROM family_member_policies WHERE user_id = ? AND policy_id = ?",
                (user_id, policy_id)
            )
            
            if cursor.fetchone():
                # Policy already applied, update it
                pass
            else:
                # Apply new policy
                cursor.execute(
                    "INSERT INTO family_member_policies (user_id, policy_id) VALUES (?, ?)",
                    (user_id, policy_id)
                )
            
            conn.commit()
            conn.close()
            
            # Apply resource quotas from the policy
            quotas = policy_data.get("usage_quotas", {})
            for resource_type, limit in quotas.items():
                if limit >= 0:  # Only set quotas for non-unlimited values
                    self.resource_manager.set_user_quota(user_id, resource_type, limit)
            
            # Apply role based on policy
            role_mapping = {
                "Parent": "admin",
                "Teen": "power_user",
                "Child": "user",
                "Guest": "guest"
            }
            
            if policy_name in role_mapping:
                self.resource_manager.assign_role_to_user(user_id, role_mapping[policy_name])
            
            return {
                "success": True,
                "message": f"Applied access policy '{policy_name}' to user"
            }
            
        except Exception as e:
            logger.error(f"Error applying access policy: {e}")
            return {
                "success": False,
                "message": f"Error applying access policy: {str(e)}"
            }
    
    def get_member_policies(self, user_id: str) -> Dict:
        """Get access policies applied to a family member.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Response with success status and policies
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.policy_data
                FROM family_access_policies p
                JOIN family_member_policies mp ON p.id = mp.policy_id
                WHERE mp.user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            policies = []
            for row in rows:
                policies.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "policy_data": json.loads(row[3])
                })
            
            return {
                "success": True,
                "policies": policies
            }
            
        except Exception as e:
            logger.error(f"Error getting member policies: {e}")
            return {
                "success": False,
                "message": f"Error getting member policies: {str(e)}"
            }
    
    def check_access_time_restriction(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Check if a user is allowed to access the system based on time restrictions.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple[bool, Optional[str]]: (allowed, message)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all policies for the user
            cursor.execute("""
                SELECT p.policy_data
                FROM family_access_policies p
                JOIN family_member_policies mp ON p.id = mp.policy_id
                WHERE mp.user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                # No policies, allow by default
                return True, None
            
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            is_weekend = now.weekday() >= 5  # 5 = Saturday, 6 = Sunday
            
            # Check each policy
            for row in rows:
                policy_data = json.loads(row[0])
                time_restrictions = policy_data.get("time_restrictions", {})
                
                if not time_restrictions.get("enabled", False):
                    # Time restrictions not enabled in this policy
                    continue
                
                if is_weekend:
                    hours = time_restrictions.get("weekend_hours", {})
                else:
                    hours = time_restrictions.get("weekday_hours", {})
                
                start_time = hours.get("start", "00:00")
                end_time = hours.get("end", "23:59")
                
                if start_time <= current_time <= end_time:
                    # Within allowed time
                    continue
                else:
                    day_type = "weekend" if is_weekend else "weekday"
                    return False, f"Access not allowed at this time. Allowed {day_type} hours: {start_time} - {end_time}"
            
            # If we get here, all policies allow access
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking access time restriction: {e}")
            return False, f"Error checking access time restriction: {str(e)}"
    
    def check_content_restriction(self, user_id: str, content_type: str) -> Tuple[bool, Optional[str]]:
        """Check if a user is allowed to access specific content types.
        
        Args:
            user_id: User ID
            content_type: Type of content (adult_content, violence, explicit_language)
            
        Returns:
            Tuple[bool, Optional[str]]: (allowed, message)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all policies for the user
            cursor.execute("""
                SELECT p.policy_data
                FROM family_access_policies p
                JOIN family_member_policies mp ON p.id = mp.policy_id
                WHERE mp.user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                # No policies, allow by default
                return True, None
            
            # Check each policy
            for row in rows:
                policy_data = json.loads(row[0])
                content_restrictions = policy_data.get("content_restrictions", {})
                
                if content_restrictions.get(content_type, False):
                    # Content is restricted
                    return False, f"Access to {content_type.replace('_', ' ')} is restricted"
            
            # If we get here, all policies allow access
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking content restriction: {e}")
            return False, f"Error checking content restriction: {str(e)}"
    
    def check_resource_restriction(self, user_id: str, action: str) -> Tuple[bool, Optional[str]]:
        """Check if a user is allowed to perform a specific resource action.
        
        Args:
            user_id: User ID
            action: Resource action (vm_creation, container_creation, etc.)
            
        Returns:
            Tuple[bool, Optional[str]]: (allowed, message)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all policies for the user
            cursor.execute("""
                SELECT p.policy_data
                FROM family_access_policies p
                JOIN family_member_policies mp ON p.id = mp.policy_id
                WHERE mp.user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                # No policies, allow by default
                return True, None
            
            # Check each policy
            for row in rows:
                policy_data = json.loads(row[0])
                resource_restrictions = policy_data.get("resource_restrictions", {})
                
                if not resource_restrictions.get(action, True):
                    # Action is restricted
                    return False, f"Action {action.replace('_', ' ')} is restricted"
            
            # If we get here, all policies allow the action
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking resource restriction: {e}")
            return False, f"Error checking resource restriction: {str(e)}"
