"""
Automated Proxmox initial configuration module.
Handles initial setup of network and storage configurations for Proxmox nodes.
"""
import logging
import os
import json
import ipaddress
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from ...api.proxmox_api import ProxmoxAPI
from ..network.network_manager import NetworkManager, NetworkSegment
from ...commands.proxmox_commands import ProxmoxCommands

logger = logging.getLogger(__name__)

@dataclass
class NetworkConfig:
    """Network configuration data class"""
    name: str  # Interface name
    type: str  # Type: bond, bridge, etc.
    address: Optional[str] = None  # IP address with CIDR notation
    gateway: Optional[str] = None  # Gateway IP
    bond_slaves: Optional[List[str]] = None  # For bond interfaces
    bridge_ports: Optional[List[str]] = None  # For bridge interfaces
    vlan_id: Optional[int] = None  # For VLAN interfaces
    mtu: Optional[int] = None  # MTU size
    netmask: Optional[str] = None  # Subnet mask
    autostart: bool = True  # Start on boot
    use_dhcp: bool = False  # Use DHCP instead of static
    dns_servers: Optional[List[str]] = None  # DNS servers

class ProxmoxAutoConfigurator:
    """Automated configuration for Proxmox nodes"""
    
    def __init__(self, api: ProxmoxAPI):
        """Initialize with Proxmox API connection"""
        self.api = api
        self.network_manager = NetworkManager(api)
        self.proxmox_commands = ProxmoxCommands(api)
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, 'auto_config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
        
        # Default configuration
        return {
            "network": {
                "enabled": True,
                "auto_detect": True,
                "use_dhcp": True,
                "primary_interface": "",  # Will be auto-detected
                "default_network_profile": "home",  # home, office, datacenter
                "network_profiles": {
                    "home": {
                        "subnet": "192.168.1.0/24",
                        "gateway": "192.168.1.1",
                        "dns_servers": ["1.1.1.1", "8.8.8.8"]
                    },
                    "office": {
                        "subnet": "10.0.0.0/24", 
                        "gateway": "10.0.0.1",
                        "dns_servers": ["10.0.0.1", "1.1.1.1"]
                    },
                    "datacenter": {
                        "subnet": "10.10.10.0/24",
                        "gateway": "10.10.10.1", 
                        "dns_servers": ["10.10.10.2", "10.10.10.3"]
                    },
                    "custom": {
                        "subnet": "192.168.0.0/24",
                        "gateway": "192.168.0.1",
                        "dns_servers": ["1.1.1.1", "8.8.8.8"]
                    }
                },
                "segments": [
                    {
                        "name": "management",
                        "vlan_id": 1,
                        "subnet": "10.0.0.0/24",
                        "purpose": "Proxmox management network",
                        "security_level": "high",
                        "allowed_services": ["ssh", "https"]
                    },
                    {
                        "name": "storage",
                        "vlan_id": 2,
                        "subnet": "10.0.1.0/24",
                        "purpose": "Storage network for backups and replication",
                        "security_level": "high",
                        "allowed_services": ["nfs", "iscsi"]
                    },
                    {
                        "name": "services",
                        "vlan_id": 10,
                        "subnet": "10.0.10.0/24",
                        "purpose": "Internal services network",
                        "security_level": "medium",
                        "allowed_services": ["http", "https", "dns"]
                    },
                    {
                        "name": "dmz",
                        "vlan_id": 20,
                        "subnet": "10.0.20.0/24",
                        "purpose": "DMZ for external-facing services",
                        "security_level": "high",
                        "allowed_services": ["http", "https"]
                    }
                ],
                "additional_settings": {
                    "ipv6_enabled": False,
                    "create_vmbr_bridges": True,
                    "configure_firewall": True
                }
            },
            "storage": {
                "enabled": True,
                "detect_disks": True,
                "zfs_pools": [
                    {
                        "name": "tank",
                        "raid_level": "mirror", 
                        "auto_detect": True,
                        "disk_pattern": "sd[a-z]",  # Pattern for disk selection
                        "exclude_system_disk": True,
                        "datasets": [
                            {
                                "name": "vm",
                                "properties": {
                                    "compression": "lz4",
                                    "recordsize": "16k"
                                }
                            },
                            {
                                "name": "backup",
                                "properties": {
                                    "compression": "zstd",
                                    "recordsize": "1M"
                                }
                            },
                            {
                                "name": "media",
                                "properties": {
                                    "compression": "lz4",
                                    "recordsize": "1M",
                                    "atime": "off"
                                },
                                "subdatasets": [
                                    {"name": "movies"},
                                    {"name": "tv"},
                                    {"name": "music"},
                                    {"name": "downloads"}
                                ]
                            }
                        ]
                    }
                ],
                "directories": [
                    {
                        "name": "local",
                        "path": "/var/lib/vz",
                        "content": ["images", "rootdir"]
                    },
                    {
                        "name": "templates",
                        "path": "/var/lib/vz/template",
                        "content": ["iso", "vztmpl"]
                    }
                ]
            }
        }
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _detect_system_disk(self, node: str) -> str:
        """Detect the system disk to exclude from ZFS pools"""
        # Try to determine the system disk by checking mount points
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': "lsblk -o NAME,MOUNTPOINT -J"
        })
        
        if not result['success']:
            return ""
        
        try:
            blockdevices = json.loads(result['data']['stdout'])['blockdevices']
            for device in blockdevices:
                # Look for root mount point
                if 'children' in device:
                    for child in device['children']:
                        if child.get('mountpoint') == '/':
                            return f"/dev/{device['name']}"
            
            # Fallback: assume the first disk is the system disk
            if blockdevices:
                return f"/dev/{blockdevices[0]['name']}"
        except Exception as e:
            logger.error(f"Error parsing lsblk output: {str(e)}")
        
        return ""
    
    def _detect_available_disks(self, node: str, exclude_system_disk: bool = True) -> List[str]:
        """Detect available disks for ZFS pools"""
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': "lsblk -d -o NAME,TYPE,SIZE -J"
        })
        
        if not result['success']:
            return []
        
        disks = []
        try:
            system_disk = self._detect_system_disk(node) if exclude_system_disk else ""
            system_disk_name = os.path.basename(system_disk) if system_disk else ""
            
            blockdevices = json.loads(result['data']['stdout'])['blockdevices']
            for device in blockdevices:
                if device['type'] == 'disk' and device['name'] != system_disk_name:
                    disks.append(f"/dev/{device['name']}")
        except Exception as e:
            logger.error(f"Error parsing lsblk output: {str(e)}")
        
        return disks
    
    def _detect_network_interfaces(self, node: str) -> List[Dict]:
        """Detect available network interfaces on a node"""
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': "ip -j addr show"
        })
        
        if not result['success']:
            return []
        
        interfaces = []
        try:
            ifaces_data = json.loads(result['data']['stdout'])
            for iface in ifaces_data:
                # Skip loopback
                if iface['ifname'] == 'lo':
                    continue
                
                # Create an interface record
                interface = {
                    'name': iface['ifname'],
                    'mac': iface.get('address', ''),
                    'type': 'physical',  # Default to physical
                    'state': 'UP' if 'UP' in iface.get('flags', []) else 'DOWN'
                }
                
                # Check for VLANs
                if '.' in iface['ifname']:
                    base_name, vlan = iface['ifname'].split('.')
                    try:
                        vlan_id = int(vlan)
                        interface['type'] = 'vlan'
                        interface['vlan_id'] = vlan_id
                        interface['base_interface'] = base_name
                    except ValueError:
                        pass
                
                # Check if it's a bridge
                if iface['ifname'].startswith('vmbr'):
                    interface['type'] = 'bridge'
                
                # Get IP info if available
                interface['addresses'] = []
                if 'addr_info' in iface:
                    for addr in iface['addr_info']:
                        if addr.get('family') == 'inet':  # IPv4
                            interface['addresses'].append({
                                'address': addr['local'],
                                'prefix': addr['prefixlen'],
                                'family': 'inet'
                            })
                        elif addr.get('family') == 'inet6':  # IPv6
                            interface['addresses'].append({
                                'address': addr['local'],
                                'prefix': addr['prefixlen'],
                                'family': 'inet6'
                            })
                
                interfaces.append(interface)
        except Exception as e:
            logger.error(f"Error parsing network interfaces: {str(e)}")
        
        return interfaces
    
    def _detect_primary_interface(self, node: str) -> Dict:
        """Detect the primary network interface (with default route)"""
        # Get interfaces
        interfaces = self._detect_network_interfaces(node)
        if not interfaces:
            return {}
        
        # Get default route to determine primary interface
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': "ip -j route show default"
        })
        
        if not result['success'] or not result['data'].get('stdout'):
            # No default route, use first active interface
            for iface in interfaces:
                if iface['state'] == 'UP' and iface['type'] == 'physical' and len(iface.get('addresses', [])) > 0:
                    return iface
            # If no active interface with IP, return first physical
            for iface in interfaces:
                if iface['type'] == 'physical':
                    return iface
            return interfaces[0]  # Last resort
        
        try:
            routes = json.loads(result['data']['stdout'])
            if routes and 'dev' in routes[0]:
                primary_iface_name = routes[0]['dev']
                for iface in interfaces:
                    if iface['name'] == primary_iface_name:
                        return iface
        except Exception as e:
            logger.error(f"Error detecting primary interface: {str(e)}")
        
        # Fallback to first interface
        return interfaces[0] if interfaces else {}
    
    def _detect_current_network_profile(self, node: str) -> str:
        """Try to detect current network profile based on IP range"""
        primary = self._detect_primary_interface(node)
        if not primary or not primary.get('addresses'):
            return self.config['network']['default_network_profile']
        
        # Get first IPv4 address
        ipv4_address = None
        for addr in primary.get('addresses', []):
            if addr.get('family') == 'inet':
                ipv4_address = addr['address']
                break
        
        if not ipv4_address:
            return self.config['network']['default_network_profile']
        
        # Check which profile subnet contains this IP
        for profile_name, profile in self.config['network']['network_profiles'].items():
            try:
                subnet = ipaddress.ip_network(profile['subnet'])
                if ipaddress.ip_address(ipv4_address) in subnet:
                    return profile_name
            except Exception:
                pass
        
        return self.config['network']['default_network_profile']
    
    def _get_network_profile_settings(self) -> Dict:
        """Get the current network profile settings"""
        profile_name = self.config['network'].get('default_network_profile', 'home')
        return self.config['network']['network_profiles'].get(profile_name, self.config['network']['network_profiles']['home'])
    
    def _generate_static_ip(self, subnet: str, node_id: int = 1) -> str:
        """Generate a static IP address from subnet based on node_id
        
        For example, for subnet 192.168.1.0/24:
        - node_id 1 -> 192.168.1.10
        - node_id 2 -> 192.168.1.11
        """
        try:
            network = ipaddress.ip_network(subnet)
            base_address = network.network_address
            # Convert to integer and add starting offset (10) + node_id - 1
            new_address_int = int(base_address) + 9 + node_id  # Starting from .10
            # Ensure we're not exceeding the subnet range or using .0 or .255
            if new_address_int >= int(network.broadcast_address) or new_address_int <= int(base_address):
                # Fallback to a simpler scheme
                new_address_int = int(base_address) + 100 + node_id
            
            # Convert back to an IP address
            new_ip = ipaddress.ip_address(new_address_int)
            return str(new_ip)
        except Exception as e:
            logger.error(f"Error generating static IP: {str(e)}")
            # Fallback: return a standard IP in the typical home network range
            return f"192.168.1.{10 + node_id}"
    
    def configure_networking(self, node: str) -> Dict:
        """Configure networking based on configuration and auto-detection"""
        if not self.config['network']['enabled']:
            return {"success": True, "message": "Network configuration is disabled", "skipped": True}
        
        try:
            # Auto-detect interfaces if enabled
            if self.config['network']['auto_detect']:
                interfaces = self._detect_network_interfaces(node)
                primary = self._detect_primary_interface(node)
                
                if not primary:
                    return {
                        "success": False, 
                        "message": "Failed to detect primary network interface"
                    }
                
                # Update primary interface in config
                self.config['network']['primary_interface'] = primary.get('name', '')
                self._save_config()
                
                # Detect current network profile
                profile_name = self._detect_current_network_profile(node)
                profile = self.config['network']['network_profiles'][profile_name]
                
                # Get node ID/number from node name
                node_id = 1
                match = re.search(r'(\d+)', node)
                if match:
                    try:
                        node_id = int(match.group(1))
                    except:
                        pass
                
                # Determine if we should use DHCP or static
                use_dhcp = self.config['network']['use_dhcp']
                
                # Prepare network configuration
                network_config = NetworkConfig(
                    name=primary['name'],
                    type='eth',
                    use_dhcp=use_dhcp,
                    autostart=True
                )
                
                if not use_dhcp:
                    # Generate static IP configuration
                    static_ip = self._generate_static_ip(profile['subnet'], node_id)
                    prefix_len = profile['subnet'].split('/')[1]
                    network_config.address = f"{static_ip}/{prefix_len}"
                    network_config.gateway = profile['gateway']
                    network_config.dns_servers = profile['dns_servers']
                
                # Apply network configuration
                config_result = self._apply_network_config(node, network_config)
                if not config_result['success']:
                    return config_result
                
                return {
                    "success": True,
                    "message": f"Successfully configured networking using {profile_name} profile with {'DHCP' if use_dhcp else 'static IP'}",
                    "interface": primary['name'],
                    "profile": profile_name,
                    "config": {
                        "use_dhcp": use_dhcp,
                        "address": network_config.address if not use_dhcp else "DHCP",
                        "gateway": network_config.gateway if not use_dhcp else "DHCP",
                        "dns_servers": network_config.dns_servers if not use_dhcp else ["DHCP"]
                    }
                }
            else:
                # Use manual configuration from config file
                return {"success": True, "message": "Manual network configuration is not implemented yet", "skipped": True}
            
        except Exception as e:
            logger.error(f"Error configuring networking: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring networking: {str(e)}"
            }
    
    def _apply_network_config(self, node: str, config: NetworkConfig) -> Dict:
        """Apply network configuration to a node"""
        try:
            # Get current network config
            ifaces_result = self.api.api_request('GET', f'nodes/{node}/network')
            if not ifaces_result['success']:
                return ifaces_result
            
            existing_ifaces = {iface['iface']: iface for iface in ifaces_result['data']}
            
            # Prepare network configuration
            network_config = {
                'type': config.type,
                'iface': config.name,
                'autostart': 1 if config.autostart else 0
            }
            
            if config.use_dhcp:
                network_config['method'] = 'dhcp'
            else:
                network_config['method'] = 'static'
                network_config['cidr'] = config.address
                network_config['gateway'] = config.gateway
                
                if config.dns_servers:
                    network_config['nameserver'] = ' '.join(config.dns_servers)
            
            # Add interface-specific settings
            if config.type == 'bridge' and config.bridge_ports:
                network_config['bridge_ports'] = ' '.join(config.bridge_ports)
            
            if config.type == 'bond' and config.bond_slaves:
                network_config['slaves'] = ' '.join(config.bond_slaves)
                # Add bond-specific settings
                network_config['bond_mode'] = 'balance-rr'  # Default mode
            
            if config.vlan_id is not None:
                network_config['vlan-id'] = config.vlan_id
            
            if config.mtu is not None:
                network_config['mtu'] = config.mtu
            
            # Check if the interface exists
            if config.name in existing_ifaces:
                # Update existing interface
                result = self.api.api_request('PUT', f'nodes/{node}/network/{config.name}', network_config)
            else:
                # Create new interface
                result = self.api.api_request('POST', f'nodes/{node}/network', network_config)
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to configure interface {config.name}: {result.get('message', 'Unknown error')}"
                }
            
            # Apply network configuration
            apply_result = self.api.api_request('PUT', f'nodes/{node}/network', {
                'digest': ifaces_result['data']['digest'],
                'method': 'apply'
            })
            
            if not apply_result['success']:
                return {
                    "success": False,
                    "message": f"Failed to apply network configuration: {apply_result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Successfully configured interface {config.name}"
            }
        except Exception as e:
            logger.error(f"Error applying network configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error applying network configuration: {str(e)}"
            }
    
    def setup_network_segmentation(self, node: str) -> Dict:
        """Set up network segmentation based on configuration"""
        if not self.config['network']['enabled']:
            return {"success": True, "message": "Network configuration is disabled", "skipped": True}
        
        try:
            # Get existing interfaces
            ifaces_result = self.api.api_request('GET', f'nodes/{node}/network')
            if not ifaces_result['success']:
                return ifaces_result
            
            existing_ifaces = {iface['iface']: iface for iface in ifaces_result['data']}
            
            # Configure each network segment
            results = []
            for segment_config in self.config['network']['segments']:
                segment = NetworkSegment(
                    name=segment_config['name'],
                    vlan_id=segment_config['vlan_id'],
                    subnet=segment_config['subnet'],
                    purpose=segment_config['purpose'],
                    security_level=segment_config['security_level'],
                    allowed_services=segment_config['allowed_services']
                )
                
                # Create bridge if needed
                bridge_name = f"vmbr{segment.vlan_id}"
                if self.config['network']['additional_settings']['create_vmbr_bridges']:
                    if bridge_name not in existing_ifaces:
                        # Create bridge interface
                        bridge_config = {
                            'type': 'bridge',
                            'iface': bridge_name,
                            'cidr': segment.subnet.split('/')[0] + '/24',  # First IP in subnet
                            'bridge_ports': 'none',  # No physical ports yet
                            'autostart': 1
                        }
                        
                        bridge_result = self.api.api_request('POST', f'nodes/{node}/network', bridge_config)
                        
                        if not bridge_result['success']:
                            results.append({
                                "segment": segment.name,
                                "success": False,
                                "message": f"Failed to create bridge {bridge_name}: {bridge_result.get('message', 'Unknown error')}"
                            })
                            continue
                        
                        results.append({
                            "segment": segment.name,
                            "success": True,
                            "message": f"Created bridge {bridge_name} for {segment.name} network"
                        })
                
                # Configure firewall for this segment if enabled
                if self.config['network']['additional_settings']['configure_firewall']:
                    # Basic firewall configuration logic
                    fw_cmds = [
                        f"echo 'Configuring firewall for {segment.name} network'",
                        f"pve-firewall compile"
                    ]
                    
                    for cmd in fw_cmds:
                        fw_result = self.api.api_request('POST', f'nodes/{node}/execute', {
                            'command': cmd
                        })
                        
                        if not fw_result['success']:
                            results.append({
                                "segment": segment.name,
                                "success": False,
                                "message": f"Failed to configure firewall: {fw_result.get('message', 'Unknown error')}"
                            })
            
            # Apply network configuration
            apply_result = self.api.api_request('POST', f'nodes/{node}/network', {
                'command': 'apply'
            })
            
            if not apply_result['success']:
                return {
                    "success": False,
                    "message": f"Failed to apply network configuration: {apply_result.get('message', 'Unknown error')}",
                    "results": results
                }
            
            return {
                "success": True,
                "message": "Network segmentation configured successfully",
                "results": results
            }
        except Exception as e:
            logger.error(f"Error setting up network segmentation: {str(e)}")
            return {
                "success": False,
                "message": f"Error setting up network segmentation: {str(e)}"
            }
    
    def setup_storage(self, node: str) -> Dict:
        """Set up storage configuration based on configuration"""
        if not self.config['storage']['enabled']:
            return {"success": True, "message": "Storage configuration is disabled", "skipped": True}
        
        try:
            results = []
            
            # Set up ZFS pools
            for pool_config in self.config['storage']['zfs_pools']:
                pool_name = pool_config['name']
                raid_level = pool_config['raid_level']
                
                # Auto detect disks if configured
                if pool_config['auto_detect'] and self.config['storage']['detect_disks']:
                    disks = self._detect_available_disks(
                        node, 
                        exclude_system_disk=pool_config['exclude_system_disk']
                    )
                    
                    # Filter disks by pattern if provided
                    if 'disk_pattern' in pool_config and pool_config['disk_pattern']:
                        import re
                        pattern = re.compile(pool_config['disk_pattern'])
                        disks = [disk for disk in disks if pattern.search(os.path.basename(disk))]
                    
                    # Ensure we have enough disks for the RAID level
                    min_disks = 2 if raid_level in ['mirror', 'raidz'] else 3  # Minimum requirements
                    if len(disks) < min_disks:
                        results.append({
                            "pool": pool_name,
                            "success": False,
                            "message": f"Insufficient disks for {raid_level}. Found {len(disks)}, need at least {min_disks}"
                        })
                        continue
                else:
                    # Use manually specified disks
                    disks = pool_config.get('disks', [])
                
                # Check if pool already exists
                check_result = self.api.api_request('POST', f'nodes/{node}/execute', {
                    'command': f"zpool list {pool_name}"
                })
                
                if check_result['success'] and check_result['data'].get('exitcode', -1) == 0:
                    # Pool exists, skip creation
                    results.append({
                        "pool": pool_name,
                        "success": True,
                        "message": f"ZFS pool {pool_name} already exists, skipping creation",
                        "skipped": True
                    })
                else:
                    # Create the pool
                    pool_result = self.proxmox_commands.create_zfs_pool(
                        node=node,
                        name=pool_name,
                        devices=disks,
                        raid_level=raid_level
                    )
                    
                    if not pool_result['success']:
                        results.append({
                            "pool": pool_name,
                            "success": False,
                            "message": f"Failed to create ZFS pool: {pool_result.get('message', 'Unknown error')}"
                        })
                        continue
                    
                    results.append({
                        "pool": pool_name,
                        "success": True,
                        "message": f"Created ZFS pool {pool_name} with {len(disks)} disks in {raid_level} configuration"
                    })
                
                # Create datasets
                for dataset_config in pool_config.get('datasets', []):
                    dataset_name = f"{pool_name}/{dataset_config['name']}"
                    dataset_result = self.proxmox_commands.create_zfs_dataset(
                        node=node,
                        name=dataset_name,
                        options=dataset_config.get('properties', {})
                    )
                    
                    if not dataset_result['success']:
                        results.append({
                            "dataset": dataset_name,
                            "success": False,
                            "message": f"Failed to create ZFS dataset: {dataset_result.get('message', 'Unknown error')}"
                        })
                        continue
                    
                    results.append({
                        "dataset": dataset_name,
                        "success": True,
                        "message": f"Created ZFS dataset {dataset_name}"
                    })
                    
                    # Set up auto snapshots
                    snapshot_result = self.proxmox_commands.setup_auto_snapshots(
                        node=node,
                        dataset=dataset_name,
                        schedule='true'
                    )
                    
                    if snapshot_result['success']:
                        results.append({
                            "dataset": dataset_name,
                            "success": True,
                            "message": f"Configured automatic snapshots for {dataset_name}"
                        })
                    
                    # Create subdatasets
                    for subdataset_config in dataset_config.get('subdatasets', []):
                        subdataset_name = f"{dataset_name}/{subdataset_config['name']}"
                        subdataset_result = self.proxmox_commands.create_zfs_dataset(
                            node=node,
                            name=subdataset_name,
                            options=subdataset_config.get('properties', {})
                        )
                        
                        if subdataset_result['success']:
                            results.append({
                                "dataset": subdataset_name,
                                "success": True,
                                "message": f"Created ZFS dataset {subdataset_name}"
                            })
            
            # Create storage directories (non-ZFS)
            for dir_config in self.config['storage'].get('directories', []):
                dir_name = dir_config['name']
                dir_path = dir_config['path']
                content_types = dir_config['content']
                
                # Create the directory if it doesn't exist
                mkdir_result = self.api.api_request('POST', f'nodes/{node}/execute', {
                    'command': f"mkdir -p {dir_path}"
                })
                
                if not mkdir_result['success']:
                    results.append({
                        "directory": dir_name,
                        "success": False,
                        "message": f"Failed to create directory: {mkdir_result.get('message', 'Unknown error')}"
                    })
                    continue
                
                # Add storage to Proxmox
                storage_config = {
                    'storage': dir_name,
                    'type': 'dir',
                    'path': dir_path,
                    'content': ','.join(content_types)
                }
                
                # Check if storage already exists
                storage_check = self.api.api_request('GET', 'storage')
                if storage_check['success']:
                    if any(s['storage'] == dir_name for s in storage_check['data']):
                        results.append({
                            "storage": dir_name,
                            "success": True,
                            "message": f"Storage {dir_name} already exists, skipping",
                            "skipped": True
                        })
                        continue
                
                storage_result = self.api.api_request('POST', 'storage', storage_config)
                
                if not storage_result['success']:
                    results.append({
                        "storage": dir_name,
                        "success": False,
                        "message": f"Failed to add storage: {storage_result.get('message', 'Unknown error')}"
                    })
                    continue
                
                results.append({
                    "storage": dir_name,
                    "success": True,
                    "message": f"Added directory storage {dir_name} at {dir_path}"
                })
            
            # Add ZFS storage to Proxmox
            for pool_config in self.config['storage']['zfs_pools']:
                zfs_storage_name = f"zfs_{pool_config['name']}"
                zfs_pool_name = pool_config['name']
                
                # Check if storage already exists
                storage_check = self.api.api_request('GET', 'storage')
                if storage_check['success']:
                    if any(s['storage'] == zfs_storage_name for s in storage_check['data']):
                        results.append({
                            "storage": zfs_storage_name,
                            "success": True,
                            "message": f"ZFS storage {zfs_storage_name} already exists, skipping",
                            "skipped": True
                        })
                        continue
                
                # Add ZFS storage
                zfs_storage_config = {
                    'storage': zfs_storage_name,
                    'type': 'zfspool',
                    'pool': zfs_pool_name,
                    'content': 'images,rootdir',
                    'sparse': 1
                }
                
                zfs_storage_result = self.api.api_request('POST', 'storage', zfs_storage_config)
                
                if not zfs_storage_result['success']:
                    results.append({
                        "storage": zfs_storage_name,
                        "success": False,
                        "message": f"Failed to add ZFS storage: {zfs_storage_result.get('message', 'Unknown error')}"
                    })
                    continue
                
                results.append({
                    "storage": zfs_storage_name,
                    "success": True,
                    "message": f"Added ZFS storage {zfs_storage_name} using pool {zfs_pool_name}"
                })
            
            return {
                "success": True,
                "message": "Storage configuration completed successfully",
                "results": results
            }
        except Exception as e:
            logger.error(f"Error setting up storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error setting up storage: {str(e)}"
            }
    
    def update_config(self, new_config: Dict) -> Dict:
        """Update the configuration with new settings"""
        try:
            # Validate the new config structure
            if 'network' not in new_config and 'storage' not in new_config:
                return {
                    "success": False,
                    "message": "Invalid configuration: must contain 'network' or 'storage' sections"
                }
            
            # Update network config if provided
            if 'network' in new_config:
                self.config['network'] = new_config['network']
            
            # Update storage config if provided
            if 'storage' in new_config:
                self.config['storage'] = new_config['storage']
            
            # Save updated config
            self._save_config()
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "config": self.config
            }
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating configuration: {str(e)}"
            }
    
    def auto_configure(self, node: str = None) -> Dict:
        """Run automatic configuration for a node or all nodes"""
        try:
            if node:
                # Configure a specific node
                nodes = [node]
            else:
                # Get all nodes
                nodes_result = self.api.api_request('GET', 'nodes')
                if not nodes_result['success']:
                    return nodes_result
                
                nodes = [n['node'] for n in nodes_result['data']]
            
            results = []
            
            for current_node in nodes:
                # Configure networking first
                network_result = self.configure_networking(current_node)
                
                # Configure network segments
                segmentation_result = self.setup_network_segmentation(current_node)
                
                # Configure storage
                storage_result = self.setup_storage(current_node)
                
                results.append({
                    "node": current_node,
                    "networking": network_result,
                    "segmentation": segmentation_result,
                    "storage": storage_result
                })
            
            return {
                "success": True,
                "message": f"Automatic configuration completed for {len(nodes)} node(s)",
                "results": results
            }
        except Exception as e:
            logger.error(f"Error during automatic configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error during automatic configuration: {str(e)}"
            }
            
    def set_network_profile(self, profile_name: str) -> Dict:
        """Set the default network profile to use"""
        if profile_name not in self.config['network']['network_profiles']:
            return {
                "success": False,
                "message": f"Invalid profile name: {profile_name}. Valid profiles: {', '.join(self.config['network']['network_profiles'].keys())}"
            }
        
        self.config['network']['default_network_profile'] = profile_name
        self._save_config()
        
        return {
            "success": True,
            "message": f"Network profile set to {profile_name}",
            "profile": self.config['network']['network_profiles'][profile_name]
        }
    
    def toggle_dhcp(self, use_dhcp: bool) -> Dict:
        """Toggle between DHCP and static IP configuration"""
        self.config['network']['use_dhcp'] = use_dhcp
        self._save_config()
        
        return {
            "success": True,
            "message": f"Network configuration set to {'DHCP' if use_dhcp else 'static IP'}"
        }
    
    def create_network_profile(self, name: str, subnet: str, gateway: str, dns_servers: List[str]) -> Dict:
        """Create a new network profile"""
        if name in self.config['network']['network_profiles']:
            return {
                "success": False,
                "message": f"Profile {name} already exists"
            }
        
        # Validate subnet format
        try:
            ipaddress.ip_network(subnet)
        except ValueError:
            return {
                "success": False,
                "message": f"Invalid subnet format: {subnet}. Expected format: 192.168.1.0/24"
            }
        
        # Validate gateway
        try:
            gateway_ip = ipaddress.ip_address(gateway)
            network = ipaddress.ip_network(subnet)
            if gateway_ip not in network:
                return {
                    "success": False,
                    "message": f"Gateway {gateway} is not within subnet {subnet}"
                }
        except ValueError:
            return {
                "success": False,
                "message": f"Invalid gateway format: {gateway}"
            }
        
        # Create the profile
        self.config['network']['network_profiles'][name] = {
            "subnet": subnet,
            "gateway": gateway,
            "dns_servers": dns_servers
        }
        
        self._save_config()
        
        return {
            "success": True,
            "message": f"Network profile {name} created successfully"
        }