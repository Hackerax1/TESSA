# security_auditor

Security Auditor for Proxmox NLI.
Provides security auditing and reporting functionality.

**Module Path**: `proxmox_nli.core.security.security_auditor`

## Classes

### SecurityAuditor

Performs security audits and generates reports

#### __init__(api, base_nli)

Initialize the security auditor

Args:
    api: Proxmox API client
    base_nli: Base NLI instance for accessing other components

#### run_full_audit()

Run a comprehensive security audit

Returns:
    Dictionary with audit results

**Returns**: `Dict[(str, Any)]`

#### get_audit_history(limit: int)

Get audit history

Args:
    limit: Maximum number of audit results to return
    
Returns:
    Dictionary with audit history

**Returns**: `Dict[(str, Any)]`

#### interpret_audit_command(command: str)

Interpret a natural language audit command

Args:
    command: Natural language command for security audit
    
Returns:
    Dictionary with interpreted command and parameters

**Returns**: `Dict[(str, Any)]`

