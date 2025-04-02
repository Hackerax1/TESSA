"""
Network Mapper Utility for Migration Services

This module provides utilities for mapping network configurations between different
platforms, handling network interface conversion, VLAN mapping, and bridge setup.
"""

import os
import json
import logging
import subprocess
import ipaddress
from typing import Dict, List, Optional, Tuple, Union

from proxmox_nli.services.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class NetworkMapper:
    """Network mapper for cross-platform migrations"""
    
    def __init__(self, proxmox_api: ProxmoxAPI):
        """
        Initialize network mapper
        
        Args:
            proxmox_api: Instance of ProxmoxAPI for interacting with Proxmox
        """
        self.proxmox_api = proxmox_api
    
    def get_proxmox_network_interfaces(self, node: str) -> List[Dict]:
        """
        Get network interfaces on Proxmox node
        
        Args:
            node: Proxmox node name
            
        Returns:
            List of network interface configurations
        """
        try:
            result = self.proxmox_api.get_node_networks(node)
            
            if not result.get("success", False):
                logger.error(f"Failed to get networks: {result.get('message', 'Unknown error')}")
                return []
            
            return result.get("data", [])
            
        except Exception as e:
            logger.error(f"Error getting networks: {str(e)}")
            return []
    
    def get_proxmox_bridges(self, node: str) -> List[Dict]:
        """
        Get network bridges on Proxmox node
        
        Args:
            node: Proxmox node name
            
        Returns:
            List of bridge configurations
        """
        interfaces = self.get_proxmox_network_interfaces(node)
        
        # Filter for bridge interfaces
        bridges = [iface for iface in interfaces if iface.get("type") == "bridge"]
        
        return bridges
    
    def find_default_bridge(self, node: str) -> Optional[str]:
        """
        Find the default bridge on a node
        
        Args:
            node: Proxmox node name
            
        Returns:
            Bridge name or None if not found
        """
        bridges = self.get_proxmox_bridges(node)
        
        if not bridges:
            return None
        
        # Look for vmbr0 first (common default)
        for bridge in bridges:
            if bridge.get("iface") == "vmbr0":
                return "vmbr0"
        
        # Otherwise return the first bridge
        return bridges[0].get("iface")
    
    def map_unraid_network_to_proxmox(self, network_config: Dict, node: str) -> Dict:
        """
        Map Unraid network configuration to Proxmox
        
        Args:
            network_config: Unraid network configuration
            node: Target Proxmox node
            
        Returns:
            Dict with mapping results
        """
        network_name = network_config.get("name", "")
        network_type = network_config.get("type", "").lower()
        
        if not network_name:
            return {
                "success": False,
                "message": "Invalid network configuration"
            }
        
        # Get existing bridges
        bridges = self.get_proxmox_bridges(node)
        bridge_names = [bridge.get("iface") for bridge in bridges]
        
        # Check if a bridge already exists for this network
        for bridge in bridges:
            if bridge.get("iface") == f"vmbr{network_config.get('id', 0)}":
                return {
                    "success": True,
                    "message": f"Bridge {bridge.get('iface')} already exists",
                    "bridge": bridge.get("iface"),
                    "already_exists": True
                }
        
        # Find next available bridge ID
        next_id = 0
        while f"vmbr{next_id}" in bridge_names:
            next_id += 1
        
        bridge_name = f"vmbr{next_id}"
        
        # Create bridge configuration
        bridge_config = {
            "iface": bridge_name,
            "type": "bridge",
            "autostart": 1
        }
        
        # Add IP configuration if available
        if network_config.get("ipv4_address") and network_config.get("ipv4_netmask"):
            bridge_config["address"] = network_config.get("ipv4_address")
            bridge_config["netmask"] = network_config.get("ipv4_netmask")
            
            # Add gateway if available
            if network_config.get("ipv4_gateway"):
                bridge_config["gateway"] = network_config.get("ipv4_gateway")
        else:
            # Default to DHCP
            bridge_config["address"] = "dhcp"
        
        # Add physical interface if available
        if network_config.get("physical_interface"):
            bridge_config["bridge_ports"] = network_config.get("physical_interface")
        
        # Add VLAN if available
        if network_config.get("vlan_id"):
            bridge_config["bridge_vlan_aware"] = 1
            bridge_config["bridge_vids"] = str(network_config.get("vlan_id"))
        
        try:
            # Create the bridge
            result = self.proxmox_api.create_network(node, bridge_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create bridge: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created bridge {bridge_name}",
                "bridge": bridge_name,
                "already_exists": False
            }
            
        except Exception as e:
            logger.error(f"Error creating bridge: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating bridge: {str(e)}"
            }
    
    def map_truenas_network_to_proxmox(self, network_config: Dict, node: str) -> Dict:
        """
        Map TrueNAS network configuration to Proxmox
        
        Args:
            network_config: TrueNAS network configuration
            node: Target Proxmox node
            
        Returns:
            Dict with mapping results
        """
        interface_name = network_config.get("name", "")
        interface_type = network_config.get("type", "").lower()
        
        if not interface_name:
            return {
                "success": False,
                "message": "Invalid network configuration"
            }
        
        # Get existing bridges
        bridges = self.get_proxmox_bridges(node)
        bridge_names = [bridge.get("iface") for bridge in bridges]
        
        # For TrueNAS, we'll create a bridge for each interface or VLAN
        if interface_type == "vlan":
            # For VLANs, use the VLAN ID in the bridge name
            vlan_id = network_config.get("vlan_id", 0)
            bridge_name = f"vmbr{vlan_id}"
            
            # Check if bridge already exists
            if bridge_name in bridge_names:
                return {
                    "success": True,
                    "message": f"Bridge {bridge_name} already exists",
                    "bridge": bridge_name,
                    "already_exists": True
                }
            
            # Create bridge configuration
            bridge_config = {
                "iface": bridge_name,
                "type": "bridge",
                "autostart": 1,
                "bridge_vlan_aware": 1,
                "bridge_vids": str(vlan_id)
            }
            
            # Add parent interface if available
            if network_config.get("parent_interface"):
                bridge_config["bridge_ports"] = network_config.get("parent_interface")
        else:
            # Find next available bridge ID
            next_id = 0
            while f"vmbr{next_id}" in bridge_names:
                next_id += 1
            
            bridge_name = f"vmbr{next_id}"
            
            # Create bridge configuration
            bridge_config = {
                "iface": bridge_name,
                "type": "bridge",
                "autostart": 1
            }
            
            # Add physical interface if available
            if interface_name:
                bridge_config["bridge_ports"] = interface_name
        
        # Add IP configuration if available
        if network_config.get("ipv4_address") and network_config.get("ipv4_netmask"):
            bridge_config["address"] = network_config.get("ipv4_address")
            bridge_config["netmask"] = network_config.get("ipv4_netmask")
            
            # Add gateway if available
            if network_config.get("ipv4_gateway"):
                bridge_config["gateway"] = network_config.get("ipv4_gateway")
        
        try:
            # Create the bridge
            result = self.proxmox_api.create_network(node, bridge_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create bridge: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created bridge {bridge_name}",
                "bridge": bridge_name,
                "already_exists": False
            }
            
        except Exception as e:
            logger.error(f"Error creating bridge: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating bridge: {str(e)}"
            }
    
    def map_esxi_network_to_proxmox(self, network_config: Dict, node: str) -> Dict:
        """
        Map ESXi network configuration to Proxmox
        
        Args:
            network_config: ESXi network configuration
            node: Target Proxmox node
            
        Returns:
            Dict with mapping results
        """
        network_name = network_config.get("name", "")
        network_type = network_config.get("type", "").lower()
        vlan_id = network_config.get("vlan_id")
        
        if not network_name:
            return {
                "success": False,
                "message": "Invalid network configuration"
            }
        
        # Get existing bridges
        bridges = self.get_proxmox_bridges(node)
        bridge_names = [bridge.get("iface") for bridge in bridges]
        
        # For ESXi, we'll map port groups to bridges
        # Standard port group naming: bridge name based on network name
        bridge_name = f"vmbr{len(bridges)}"
        
        # Check if bridge already exists
        for bridge in bridges:
            if bridge.get("comments", "").lower() == f"esxi:{network_name}".lower():
                return {
                    "success": True,
                    "message": f"Bridge {bridge.get('iface')} already exists for ESXi network {network_name}",
                    "bridge": bridge.get("iface"),
                    "already_exists": True
                }
        
        # Find next available bridge ID
        next_id = 0
        while f"vmbr{next_id}" in bridge_names:
            next_id += 1
        
        bridge_name = f"vmbr{next_id}"
        
        # Create bridge configuration
        bridge_config = {
            "iface": bridge_name,
            "type": "bridge",
            "autostart": 1,
            "comments": f"ESXi:{network_name}"
        }
        
        # Add physical interface
        # For ESXi, we'll use the first physical interface as the bridge port
        interfaces = self.get_proxmox_network_interfaces(node)
        physical_interfaces = [iface for iface in interfaces if iface.get("type") == "eth"]
        
        if physical_interfaces:
            bridge_config["bridge_ports"] = physical_interfaces[0].get("iface", "eth0")
        
        # Add VLAN if available
        if vlan_id:
            bridge_config["bridge_vlan_aware"] = 1
            bridge_config["bridge_vids"] = str(vlan_id)
        
        try:
            # Create the bridge
            result = self.proxmox_api.create_network(node, bridge_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create bridge: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created bridge {bridge_name} for ESXi network {network_name}",
                "bridge": bridge_name,
                "already_exists": False
            }
            
        except Exception as e:
            logger.error(f"Error creating bridge: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating bridge: {str(e)}"
            }
    
    def create_vlan_interface(self, node: str, parent_iface: str, vlan_id: int) -> Dict:
        """
        Create a VLAN interface on a Proxmox node
        
        Args:
            node: Proxmox node name
            parent_iface: Parent interface name
            vlan_id: VLAN ID
            
        Returns:
            Dict with creation results
        """
        # Check if interface already exists
        interfaces = self.get_proxmox_network_interfaces(node)
        vlan_iface_name = f"{parent_iface}.{vlan_id}"
        
        for iface in interfaces:
            if iface.get("iface") == vlan_iface_name:
                return {
                    "success": True,
                    "message": f"VLAN interface {vlan_iface_name} already exists",
                    "iface": vlan_iface_name,
                    "already_exists": True
                }
        
        # Create VLAN interface configuration
        vlan_config = {
            "iface": vlan_iface_name,
            "type": "vlan",
            "autostart": 1,
            "vlan-id": vlan_id,
            "vlan-raw-device": parent_iface
        }
        
        try:
            # Create the VLAN interface
            result = self.proxmox_api.create_network(node, vlan_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create VLAN interface: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created VLAN interface {vlan_iface_name}",
                "iface": vlan_iface_name,
                "already_exists": False
            }
            
        except Exception as e:
            logger.error(f"Error creating VLAN interface: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating VLAN interface: {str(e)}"
            }
    
    def create_bridge_for_vlan(self, node: str, vlan_iface: str) -> Dict:
        """
        Create a bridge for a VLAN interface
        
        Args:
            node: Proxmox node name
            vlan_iface: VLAN interface name
            
        Returns:
            Dict with creation results
        """
        # Extract VLAN ID from interface name
        vlan_id = vlan_iface.split(".")[-1]
        
        # Check if bridge already exists
        bridges = self.get_proxmox_bridges(node)
        bridge_names = [bridge.get("iface") for bridge in bridges]
        
        bridge_name = f"vmbr{vlan_id}"
        
        # If bridge name is taken, find next available
        if bridge_name in bridge_names:
            next_id = 0
            while f"vmbr{next_id}" in bridge_names:
                next_id += 1
            bridge_name = f"vmbr{next_id}"
        
        # Create bridge configuration
        bridge_config = {
            "iface": bridge_name,
            "type": "bridge",
            "autostart": 1,
            "bridge_ports": vlan_iface
        }
        
        try:
            # Create the bridge
            result = self.proxmox_api.create_network(node, bridge_config)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to create bridge: {result.get('message', 'Unknown error')}"
                }
            
            return {
                "success": True,
                "message": f"Created bridge {bridge_name} for VLAN interface {vlan_iface}",
                "bridge": bridge_name
            }
            
        except Exception as e:
            logger.error(f"Error creating bridge: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating bridge: {str(e)}"
            }
    
    def setup_nat_for_bridge(self, node: str, bridge: str, nat_network: str = "192.168.100.0/24") -> Dict:
        """
        Set up NAT for a bridge
        
        Args:
            node: Proxmox node name
            bridge: Bridge name
            nat_network: NAT network CIDR
            
        Returns:
            Dict with setup results
        """
        try:
            # Create NAT configuration script
            script_content = f"""#!/bin/bash
# NAT configuration for {bridge}

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf

# Set up NAT
iptables -t nat -A POSTROUTING -s {nat_network} -o eth0 -j MASQUERADE
iptables -A FORWARD -s {nat_network} -j ACCEPT
iptables -A FORWARD -d {nat_network} -j ACCEPT

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

# Create network configuration
cat > /etc/network/interfaces.d/{bridge}_nat << EOF
auto {bridge}
iface {bridge} inet static
    address $(echo {nat_network} | sed 's/0\/24/1\/24/')
    netmask 255.255.255.0
    bridge_ports none
    bridge_stp off
    bridge_fd 0
EOF

# Restart networking
systemctl restart networking
"""
            
            # Save script to node
            script_path = f"/root/setup_nat_{bridge}.sh"
            script_cmd = ["ssh", node, f"cat > {script_path} << 'EOF'\n{script_content}\nEOF\nchmod +x {script_path}"]
            subprocess.run(script_cmd, check=True, shell=True)
            
            # Execute script
            exec_cmd = ["ssh", node, f"bash {script_path}"]
            subprocess.run(exec_cmd, check=True)
            
            return {
                "success": True,
                "message": f"NAT set up for bridge {bridge}",
                "script_path": script_path
            }
            
        except Exception as e:
            logger.error(f"Error setting up NAT: {str(e)}")
            return {
                "success": False,
                "message": f"Error setting up NAT: {str(e)}"
            }
    
    def map_vm_networks(self, vm_networks: List[Dict], node: str) -> Dict[str, str]:
        """
        Map VM networks to Proxmox bridges
        
        Args:
            vm_networks: List of VM network configurations
            node: Target Proxmox node
            
        Returns:
            Dict mapping network names to bridge names
        """
        network_map = {}
        bridges = self.get_proxmox_bridges(node)
        
        # Get default bridge
        default_bridge = self.find_default_bridge(node) or "vmbr0"
        
        for network in vm_networks:
            network_name = network.get("name", "")
            vlan_id = network.get("vlan_id")
            
            # Try to find a matching bridge
            matched_bridge = None
            
            # First, look for bridges with matching VLAN
            if vlan_id:
                for bridge in bridges:
                    if bridge.get("bridge_vids") and str(vlan_id) in bridge.get("bridge_vids").split(","):
                        matched_bridge = bridge.get("iface")
                        break
            
            # If no VLAN match, look for bridges with matching name in comments
            if not matched_bridge and network_name:
                for bridge in bridges:
                    if network_name.lower() in bridge.get("comments", "").lower():
                        matched_bridge = bridge.get("iface")
                        break
            
            # If still no match, use default bridge
            if not matched_bridge:
                matched_bridge = default_bridge
            
            network_map[network_name] = matched_bridge
        
        return network_map
