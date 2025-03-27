# auto_configurator

Automated Proxmox initial configuration module.
Handles initial setup of network and storage configurations for Proxmox nodes.

**Module Path**: `proxmox_nli.core.automation.auto_configurator`

## Classes

### NetworkConfig

Network configuration data class

### ProxmoxAutoConfigurator

Automated configuration for Proxmox nodes

#### __init__(api: ProxmoxAPI)

Initialize with Proxmox API connection

#### configure_networking(node: str)

Configure networking based on configuration and auto-detection

**Returns**: `Dict`

#### setup_network_segmentation(node: str)

Set up network segmentation based on configuration

**Returns**: `Dict`

#### setup_storage(node: str)

Set up storage configuration based on configuration

**Returns**: `Dict`

#### update_config(new_config: Dict)

Update the configuration with new settings

**Returns**: `Dict`

#### auto_configure(node: str)

Run automatic configuration for a node or all nodes

**Returns**: `Dict`

#### set_network_profile(profile_name: str)

Set the default network profile to use

**Returns**: `Dict`

#### toggle_dhcp(use_dhcp: bool)

Toggle between DHCP and static IP configuration

**Returns**: `Dict`

#### create_network_profile(name: str, subnet: str, gateway: str, dns_servers: List[str])

Create a new network profile

**Returns**: `Dict`

