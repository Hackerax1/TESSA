# auth_manager

Authentication module for JWT-based user authentication.

**Module Path**: `proxmox_nli.core.security.auth_manager`

## Classes

### AuthManager

#### __init__()

#### create_token(user_id: str, roles: List[str])

Create a new JWT token for a user

**Returns**: `str`

#### verify_token(token: str)

Verify a JWT token and return the payload if valid

**Returns**: `Optional[Dict]`

#### check_permission(token: str, required_roles: List[str])

Check if the user has the required roles

**Returns**: `bool`

#### refresh_token(token: str)

Refresh a valid token

**Returns**: `Optional[str]`

#### revoke_token(token: str)

Revoke a token

**Returns**: `bool`

#### get_active_sessions(user_id: str)

Get all active sessions for a user

**Returns**: `Dict[(str, Dict)]`

