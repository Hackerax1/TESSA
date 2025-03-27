# ssh_commands

SSH Device Commands module for Proxmox NLI.
Provides commands for managing SSH connections to devices on the network.

**Module Path**: `proxmox_nli.commands.ssh_commands`

## Classes

### SSHCommands

Commands for managing SSH devices on the network

#### __init__(api)

#### scan_network(subnet: str)

Scan network for SSH-accessible devices

Args:
    subnet (str, optional): Subnet to scan in CIDR notation. Defaults to local subnet.

Returns:
    dict: Scan results

**Returns**: `dict`

#### discover_devices(subnet: str, username: str = None, password: str = 'root')

Discover and add SSH devices on the network

Args:
    subnet (str, optional): Subnet to scan in CIDR notation. Defaults to local subnet.
    username (str, optional): Default username for connections. Defaults to "root".
    password (str, optional): Default password for connections. Defaults to None.

Returns:
    dict: Discovery results

**Returns**: `dict`

#### list_devices(device_type: str)

List all SSH devices or devices of a specific type

Args:
    device_type (str, optional): Filter by device type. Defaults to None.

Returns:
    dict: List of devices

**Returns**: `dict`

#### get_device_groups()

Get devices grouped by their type

Returns:
    dict: Device groups

**Returns**: `dict`

#### add_device(hostname: str, name: str, username: str = None, password: str = 'root', port: int = None, description: str = 22, tags: List[str] = '')

Add an SSH device manually

Args:
    hostname (str): IP or hostname of the device
    name (str, optional): User-friendly name. Defaults to hostname.
    username (str, optional): Username for SSH. Defaults to "root".
    password (str, optional): Password for SSH. Defaults to None.
    port (int, optional): SSH port. Defaults to 22.
    description (str, optional): Description of the device. Defaults to "".
    tags (List[str], optional): Tags for the device. Defaults to None.

Returns:
    dict: Result of operation

**Returns**: `dict`

#### update_device(hostname: str, name: str, username: str = None, password: str = None, port: int = None, description: str = None, tags: List[str] = None)

Update an existing SSH device

Args:
    hostname (str): IP or hostname of the device
    name (str, optional): User-friendly name. Defaults to None.
    username (str, optional): Username for SSH. Defaults to None.
    password (str, optional): Password for SSH. Defaults to None.
    port (int, optional): SSH port. Defaults to None.
    description (str, optional): Description of the device. Defaults to None.
    tags (List[str], optional): Tags for the device. Defaults to None.

Returns:
    dict: Result of operation

**Returns**: `dict`

#### remove_device(hostname: str)

Remove an SSH device

Args:
    hostname (str): IP or hostname of the device

Returns:
    dict: Result of operation

**Returns**: `dict`

#### execute_command(hostname: str, command: str)

Execute a command on a device

Args:
    hostname (str): IP or hostname of the device
    command (str): Command to execute

Returns:
    dict: Command execution results

**Returns**: `dict`

#### execute_command_on_multiple(hostnames: List[str], command: str)

Execute a command on multiple devices

Args:
    hostnames (List[str]): List of hostnames to execute on
    command (str): Command to execute

Returns:
    dict: Command execution results for each device

**Returns**: `dict`

#### execute_command_on_group(group_name: str, command: str)

Execute a command on a group of devices

Args:
    group_name (str): Group name (device type)
    command (str): Command to execute

Returns:
    dict: Command execution results for each device

**Returns**: `dict`

#### setup_ssh_keys(hostnames: List[str], key_path: str)

Set up SSH key authentication for multiple devices

Args:
    hostnames (List[str]): List of hostnames to set up
    key_path (str, optional): Path to existing SSH key. Defaults to None.

Returns:
    dict: Results of key setup

**Returns**: `dict`

#### setup_ssh_keys_for_group(group_name: str, key_path: str)

Set up SSH key authentication for a group of devices

Args:
    group_name (str): Group name (device type)
    key_path (str, optional): Path to existing SSH key. Defaults to None.

Returns:
    dict: Results of key setup

**Returns**: `dict`

#### upload_file(hostname: str, local_path: str, remote_path: str)

Upload a file to a device

Args:
    hostname (str): IP or hostname of the device
    local_path (str): Local file path
    remote_path (str): Remote file path

Returns:
    dict: Upload result

**Returns**: `dict`

#### download_file(hostname: str, remote_path: str, local_path: str)

Download a file from a device

Args:
    hostname (str): IP or hostname of the device
    remote_path (str): Remote file path
    local_path (str): Local file path

Returns:
    dict: Download result

**Returns**: `dict`

