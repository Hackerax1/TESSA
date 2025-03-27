# vlan_handler

VLAN management module for Proxmox NLI.
Handles VLAN creation and management.

**Module Path**: `proxmox_nli.core.network.vlan_handler`

## Classes

### VLANHandler

#### __init__(api)

#### create_vlan(vlan_id: int, name: str, subnet: str, bridge: str)

Create a new VLAN

Args:
    vlan_id: VLAN ID (1-4094)
    name: VLAN name
    subnet: Subnet CIDR (e.g. 192.168.1.0/24)
    bridge: Bridge interface to attach VLAN to
    
Returns:
    dict: Result of operation

**Returns**: `dict`

#### delete_vlan(vlan_id: int, bridge: str)

Delete a VLAN by ID

Args:
    vlan_id: VLAN ID to delete
    bridge: Bridge interface the VLAN is attached to
    
Returns:
    dict: Result of operation

**Returns**: `dict`

#### list_vlans()

List all VLANs

Returns:
    dict: List of VLANs

**Returns**: `dict`

#### assign_vm_to_vlan(vm_id: int, vlan_id: int, bridge: str)

Assign a VM to a VLAN

Args:
    vm_id: VM ID to assign
    vlan_id: VLAN ID to assign VM to
    bridge: Bridge interface
    
Returns:
    dict: Result of operation

**Returns**: `dict`

