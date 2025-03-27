# container_manager

Container management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.core.container_manager`

## Classes

### ContainerManager

#### __init__(api)

#### list_containers()

List all LXC containers

**Returns**: `Dict[(str, Any)]`

#### create_container(params: Dict[(str, Any)])

Create a new LXC container

**Returns**: `Dict[(str, Any)]`

#### start_container(ct_id: str)

Start a container

**Returns**: `Dict[(str, Any)]`

#### stop_container(ct_id: str)

Stop a container

**Returns**: `Dict[(str, Any)]`

#### delete_container(ct_id: str)

Delete a container

**Returns**: `Dict[(str, Any)]`

#### get_container_status(ct_id: str)

Get status of a container

**Returns**: `Dict[(str, Any)]`

