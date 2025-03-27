# network_manager

Network management module for Proxmox NLI.
Handles network configuration, VLANs, firewall rules, and security.

**Module Path**: `proxmox_nli.core.network.network_manager`

## Classes

### NetworkSegment

### NetworkManager

#### __init__(api)

#### setup_network_segmentation()

Set up initial network segmentation with VLANs

**Returns**: `Dict`

#### create_network_segment(segment: NetworkSegment)

Create a new network segment with VLAN

**Returns**: `Dict`

#### get_network_recommendations(service_type: str)

Get network configuration recommendations for a service

**Returns**: `Dict`

#### configure_service_network(service_id: str, service_type: str, vm_id: str)

Configure network for a service

**Returns**: `Dict`

#### analyze_network_security()

Analyze network security and provide recommendations

**Returns**: `Dict`

