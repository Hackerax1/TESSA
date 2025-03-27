# security_manager

Security Manager for Proxmox NLI.
Provides natural language interfaces for security management.

**Module Path**: `proxmox_nli.core.security.security_manager`

## Classes

### SecurityManager

Central manager for security-related functionality with natural language interfaces

#### __init__(api, base_nli)

Initialize the security manager

Args:
    api: Proxmox API client
    base_nli: Base NLI instance for accessing other components

#### run_security_audit(scope: str)

Run a security audit and generate a report

Args:
    scope: Audit scope (full, firewall, permissions, certificates, updates)
    
Returns:
    Dictionary with audit results

**Returns**: `Dict[(str, Any)]`

#### interpret_permission_command(command: str)

Interpret a natural language permission command

Args:
    command: Natural language command for permission management
    
Returns:
    Dictionary with interpreted command and parameters

**Returns**: `Dict[(str, Any)]`

#### interpret_firewall_command(command: str)

Interpret a natural language firewall command

Args:
    command: Natural language command for firewall management
    
Returns:
    Dictionary with interpreted command and parameters

**Returns**: `Dict[(str, Any)]`

