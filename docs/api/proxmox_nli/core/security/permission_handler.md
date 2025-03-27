# permission_handler

Permission handler for role-based access control.

**Module Path**: `proxmox_nli.core.security.permission_handler`

## Classes

### PermissionHandler

#### __init__()

#### has_permission(roles: List[str], required_permission: str)

Check if any of the user's roles have the required permission

**Returns**: `bool`

#### get_role_permissions(role: str)

Get all permissions for a specific role

**Returns**: `List[str]`

#### add_role_permission(role: str, permission: str)

Add a permission to a role

**Returns**: `bool`

#### remove_role_permission(role: str, permission: str)

Remove a permission from a role

**Returns**: `bool`

