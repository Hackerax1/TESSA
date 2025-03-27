# audit_logger

Audit logging module for Proxmox NLI.
Handles logging of all commands and their results for security and compliance.

**Module Path**: `proxmox_nli.core.events.audit_logger`

## Classes

### AuditLogger

#### __init__(log_dir: str)

Initialize the audit logger

#### log_command(query: str, intent: str, entities: Dict[(str, Any)], result: Dict[(str, Any)], user: str, source: str = None, ip_address: str = 'cli')

Log a command execution with all relevant details

Args:
    query: The original natural language query
    intent: The identified intent
    entities: Extracted entities from the query
    result: The result of command execution
    user: The user who executed the command
    source: Source of the command (cli/web)
    ip_address: IP address for web requests

#### get_recent_logs(limit: int)

Get recent audit logs from the database

**Returns**: `list`

#### get_user_activity(user: str, limit: int)

Get recent activity for a specific user

**Returns**: `list`

#### get_failed_commands(limit: int)

Get recent failed command executions

**Returns**: `list`

