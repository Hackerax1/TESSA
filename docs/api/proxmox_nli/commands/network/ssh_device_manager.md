# ssh_device_manager

SSH device management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.network.ssh_device_manager`

## Classes

### SSHDeviceManager

#### __init__(api)

#### scan_network(subnet: Optional[str])

Scan network for SSH-accessible devices

Args:
    subnet: Optional subnet in CIDR notation to scan
    
Returns:
    Dict with scan results

**Returns**: `Dict[(str, Any)]`

#### discover_devices(subnet: Optional[str], username: str = None, password: Optional[str] = 'root')

Discover and add SSH devices

Args:
    subnet: Optional subnet to scan
    username: Default username for connections
    password: Default password for connections
    
Returns:
    Dict with discovery results

**Returns**: `Dict[(str, Any)]`

#### add_device(hostname: str, name: Optional[str], username: str = None, password: Optional[str] = 'root', port: int = None, description: str = 22, tags: Optional[List[str]] = '')

Add an SSH device manually

Args:
    hostname: IP or hostname of device
    name: User-friendly name
    username: SSH username
    password: Optional SSH password
    port: SSH port
    description: Device description
    tags: Optional tags for device
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### remove_device(hostname: str)

Remove an SSH device

Args:
    hostname: IP or hostname of device
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### list_devices(device_type: Optional[str])

List all SSH devices

Args:
    device_type: Optional device type to filter by
    
Returns:
    Dict with list of devices

**Returns**: `Dict[(str, Any)]`

#### get_device_groups()

Get devices grouped by type

Returns:
    Dict with device groups

**Returns**: `Dict[(str, Any)]`

#### execute_command(hostname: str, command: str)

Execute command on an SSH device

Args:
    hostname: IP or hostname of device
    command: Command to execute
    
Returns:
    Dict with command result

**Returns**: `Dict[(str, Any)]`

#### execute_command_on_multiple(hostnames: List[str], command: str)

Execute command on multiple devices

Args:
    hostnames: List of device hostnames
    command: Command to execute
    
Returns:
    Dict with command results

**Returns**: `Dict[(str, Any)]`

#### execute_command_on_group(group_name: str, command: str)

Execute command on a device group

Args:
    group_name: Device group/type
    command: Command to execute
    
Returns:
    Dict with command results

**Returns**: `Dict[(str, Any)]`

#### setup_ssh_keys(hostnames: List[str], key_path: Optional[str])

Set up SSH key authentication

Args:
    hostnames: List of device hostnames
    key_path: Optional path to existing SSH key
    
Returns:
    Dict with setup results

**Returns**: `Dict[(str, Any)]`

#### setup_ssh_keys_for_group(group_name: str, key_path: Optional[str])

Set up SSH key authentication for a device group

Args:
    group_name: Device group/type
    key_path: Optional path to existing SSH key
    
Returns:
    Dict with setup results

**Returns**: `Dict[(str, Any)]`

