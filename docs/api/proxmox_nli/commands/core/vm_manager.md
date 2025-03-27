# vm_manager

Core VM management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.core.vm_manager`

## Classes

### VMManager

#### __init__(api)

#### list_vms()

Get a list of all VMs with their status

**Returns**: `Dict[(str, Any)]`

#### start_vm(vm_id: str)

Start a VM

**Returns**: `Dict[(str, Any)]`

#### stop_vm(vm_id: str)

Stop a VM

**Returns**: `Dict[(str, Any)]`

#### restart_vm(vm_id: str)

Restart a VM

**Returns**: `Dict[(str, Any)]`

#### get_vm_status(vm_id: str)

Get the status of a VM

**Returns**: `Dict[(str, Any)]`

#### create_vm(params: Dict[(str, Any)])

Create a new VM with the given parameters

**Returns**: `Dict[(str, Any)]`

#### delete_vm(vm_id: str)

Delete a VM

**Returns**: `Dict[(str, Any)]`

#### get_vm_location(vm_id: str)

Get the node where a VM is located

**Returns**: `Dict[(str, Any)]`

