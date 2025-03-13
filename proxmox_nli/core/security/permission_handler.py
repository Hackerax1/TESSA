"""
Permission handler for role-based access control.
"""
from typing import List, Dict, Optional

class PermissionHandler:
    def __init__(self):
        self.role_permissions = {
            'admin': ['*'],  # Admin has all permissions
            'user': [
                'vm.view',
                'vm.start',
                'vm.stop',
                'vm.restart',
                'backup.view',
                'stats.view',
                'preferences.edit'
            ],
            'readonly': [
                'vm.view',
                'backup.view',
                'stats.view'
            ]
        }

    def has_permission(self, roles: List[str], required_permission: str) -> bool:
        """Check if any of the user's roles have the required permission"""
        for role in roles:
            permissions = self.role_permissions.get(role, [])
            if '*' in permissions or required_permission in permissions:
                return True
        return False

    def get_role_permissions(self, role: str) -> List[str]:
        """Get all permissions for a specific role"""
        return self.role_permissions.get(role, [])

    def add_role_permission(self, role: str, permission: str) -> bool:
        """Add a permission to a role"""
        if role not in self.role_permissions:
            self.role_permissions[role] = []
        if permission not in self.role_permissions[role]:
            self.role_permissions[role].append(permission)
            return True
        return False

    def remove_role_permission(self, role: str, permission: str) -> bool:
        """Remove a permission from a role"""
        if role in self.role_permissions and permission in self.role_permissions[role]:
            self.role_permissions[role].remove(permission)
            return True
        return False