# security_commands

Security Commands for Proxmox NLI.
Provides natural language command handling for security management.

**Module Path**: `proxmox_nli.core.security.security_commands`

## Classes

### SecurityCommands

Command handler for security-related natural language commands

#### __init__(api, base_nli)

Initialize the security commands handler

Args:
    api: Proxmox API client
    base_nli: Base NLI instance for accessing other components

#### handle_command(command: str)

Handle a natural language security command

Args:
    command: Natural language command
    
Returns:
    Dictionary with command result

**Returns**: `Dict[(str, Any)]`

