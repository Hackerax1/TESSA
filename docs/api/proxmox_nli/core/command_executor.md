# command_executor

Command executor module handling execution of various Proxmox commands.
Provides centralized command routing, validation, and execution.

**Module Path**: `proxmox_nli.core.command_executor`

## Classes

### CommandExecutor

#### __init__(base_nli)

#### execute_command(command: str, args: Optional[Dict[(str, Any)]])

Execute a command with validation and proper routing

Args:
    command: Command to execute
    args: Optional command arguments
    
Returns:
    Dict containing command execution results

**Returns**: `Dict[(str, Any)]`

