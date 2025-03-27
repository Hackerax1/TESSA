# vlan_manager

VLAN management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.network.vlan_manager`

## Classes

### VLANManager

#### __init__(api)

#### create_vlan(vlan_id: int, name: str, subnet: str, bridge: str)

Create a new VLAN

Args:
    vlan_id: VLAN ID (1-4094)
    name: Name of the VLAN
    subnet: Subnet in CIDR notation
    bridge: Bridge interface to attach VLAN to
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### list_vlans(node: Optional[str])

List all configured VLANs

Args:
    node: Optional node name to filter VLANs
    
Returns:
    Dict with list of VLANs

**Returns**: `Dict[(str, Any)]`

#### delete_vlan(vlan_id: int, bridge: str)

Delete a VLAN

Args:
    vlan_id: VLAN ID to delete
    bridge: Bridge interface
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### assign_vm_to_vlan(vm_id: str, vlan_id: int, bridge: str)

Assign a VM to a VLAN

Args:
    vm_id: ID of the VM
    vlan_id: ID of the VLAN
    bridge: Bridge interface
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

