# session_manager

Session manager for handling user sessions and access tracking.

**Module Path**: `proxmox_nli.core.security.session_manager`

## Classes

### SessionManager

#### __init__(session_timeout: int)

#### create_session(user_id: str, token: str)

Create a new session for a user

**Returns**: `Dict`

#### get_session(token: str)

Get session information for a token

**Returns**: `Optional[Dict]`

#### update_session(token: str, ip_address: str, user_agent: str = None)

Update session metadata

**Returns**: `bool`

#### end_session(token: str)

End a user session

**Returns**: `bool`

#### get_active_sessions(user_id: str)

Get all active sessions, optionally filtered by user_id

**Returns**: `Dict[(str, Dict)]`

