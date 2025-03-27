# ssh_device_manager

SSH Device Manager module for Proxmox NLI.
Handles discovery, connection, and management of SSH-enabled devices on the network.

**Module Path**: `proxmox_nli.core.ssh_device_manager`

## Classes

### SSHDevice

Represents an SSH-accessible device on the network

#### to_dict()

Convert to dictionary, excluding sensitive fields

**Returns**: `Dict[(str, Any)]`

### SSHDeviceManager

Manages SSH connections to network devices

#### __init__(config_dir: str, api = None)

#### load_devices()

Load devices from the JSON file

**Returns**: `None`

#### save_devices()

Save devices to the JSON file

**Returns**: `bool`

#### add_device(device: SSHDevice)

Add or update a device in the manager

**Returns**: `Dict[(str, Any)]`

#### remove_device(hostname: str)

Remove a device from the manager

**Returns**: `Dict[(str, Any)]`

#### get_device(hostname: str)

Get a device by hostname or IP

**Returns**: `Optional[SSHDevice]`

#### get_all_devices()

Get all devices as dictionaries

**Returns**: `List[Dict[(str, Any)]]`

#### scan_network(subnet: str, timeout: int = '192.168.1.0/24')

Scan the network for SSH-accessible devices

**Returns**: `Dict[(str, Any)]`

#### discover_and_add_devices(subnet: str, username: str = '192.168.1.0/24', password: str = 'root', key_path: str = None)

Scan network and add discovered SSH devices

**Returns**: `Dict[(str, Any)]`

#### test_connection(device: SSHDevice)

Test connection to a device and gather basic system info

**Returns**: `Dict[(str, Any)]`

#### execute_command(hostname: str, command: str)

Execute a command on a device

**Returns**: `Dict[(str, Any)]`

#### execute_command_on_multiple(hostnames: List[str], command: str)

Execute a command on multiple devices in parallel

**Returns**: `Dict[(str, Any)]`

#### get_device_groups()

Get devices grouped by type

**Returns**: `Dict[(str, List[str])]`

#### setup_ssh_keys(hostnames: List[str], key_path: str)

Set up SSH key authentication for multiple devices

**Returns**: `Dict[(str, Any)]`

#### upload_file(hostname: str, local_path: str, remote_path: str)

Upload a file to a device

**Returns**: `Dict[(str, Any)]`

#### download_file(hostname: str, remote_path: str, local_path: str)

Download a file from a device

**Returns**: `Dict[(str, Any)]`

