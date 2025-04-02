"""
Network Planning Templates

This module provides templates for VLAN and subnet planning in network designs.
These templates can be applied to network plans to quickly set up common network configurations.
"""

from typing import Dict, List, Any

# VLAN Templates
VLAN_TEMPLATES = {
    "home": {
        "name": "Home Network",
        "description": "Simple home network with basic VLANs",
        "vlans": [
            {
                "id": 1,
                "name": "Management",
                "subnet": "10.0.1.0/24",
                "purpose": "Network management and infrastructure"
            },
            {
                "id": 10,
                "name": "LAN",
                "subnet": "192.168.10.0/24",
                "purpose": "Primary local network for computers and devices"
            },
            {
                "id": 20,
                "name": "IoT",
                "subnet": "192.168.20.0/24",
                "purpose": "Internet of Things devices"
            },
            {
                "id": 30,
                "name": "Guest",
                "subnet": "192.168.30.0/24",
                "purpose": "Guest network with internet access only"
            }
        ]
    },
    "homelab": {
        "name": "Homelab",
        "description": "Comprehensive homelab setup with multiple VLANs",
        "vlans": [
            {
                "id": 1,
                "name": "Management",
                "subnet": "10.0.1.0/24",
                "purpose": "Network management and infrastructure"
            },
            {
                "id": 10,
                "name": "LAN",
                "subnet": "192.168.10.0/24",
                "purpose": "Primary local network for computers and devices"
            },
            {
                "id": 20,
                "name": "IoT",
                "subnet": "192.168.20.0/24",
                "purpose": "Internet of Things devices"
            },
            {
                "id": 30,
                "name": "Guest",
                "subnet": "192.168.30.0/24",
                "purpose": "Guest network with internet access only"
            },
            {
                "id": 40,
                "name": "Storage",
                "subnet": "10.0.40.0/24",
                "purpose": "Storage network for NAS and backups"
            },
            {
                "id": 50,
                "name": "vMotion",
                "subnet": "10.0.50.0/24",
                "purpose": "VM migration network"
            },
            {
                "id": 60,
                "name": "DMZ",
                "subnet": "192.168.60.0/24",
                "purpose": "Demilitarized zone for public-facing services"
            }
        ]
    },
    "small_business": {
        "name": "Small Business",
        "description": "Small business network with security segregation",
        "vlans": [
            {
                "id": 1,
                "name": "Management",
                "subnet": "10.0.1.0/24",
                "purpose": "Network management and infrastructure"
            },
            {
                "id": 10,
                "name": "Staff",
                "subnet": "10.0.10.0/24",
                "purpose": "Staff workstations and laptops"
            },
            {
                "id": 20,
                "name": "Servers",
                "subnet": "10.0.20.0/24",
                "purpose": "Internal servers and services"
            },
            {
                "id": 30,
                "name": "Voice",
                "subnet": "10.0.30.0/24",
                "purpose": "VoIP phones and communication"
            },
            {
                "id": 40,
                "name": "Guest",
                "subnet": "10.0.40.0/24",
                "purpose": "Guest and visitor network"
            },
            {
                "id": 50,
                "name": "DMZ",
                "subnet": "192.168.50.0/24",
                "purpose": "Public-facing services"
            }
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "description": "Enterprise network with comprehensive segmentation",
        "vlans": [
            {
                "id": 1,
                "name": "Management",
                "subnet": "10.0.1.0/24",
                "purpose": "Network management and infrastructure"
            },
            {
                "id": 10,
                "name": "Staff",
                "subnet": "10.10.0.0/16",
                "purpose": "Staff workstations and laptops"
            },
            {
                "id": 20,
                "name": "Servers",
                "subnet": "10.20.0.0/16",
                "purpose": "Internal servers and services"
            },
            {
                "id": 30,
                "name": "Voice",
                "subnet": "10.30.0.0/16",
                "purpose": "VoIP phones and communication"
            },
            {
                "id": 40,
                "name": "IoT",
                "subnet": "10.40.0.0/16",
                "purpose": "Internet of Things devices"
            },
            {
                "id": 50,
                "name": "Guest",
                "subnet": "10.50.0.0/16",
                "purpose": "Guest and visitor network"
            },
            {
                "id": 60,
                "name": "DMZ",
                "subnet": "192.168.0.0/16",
                "purpose": "Public-facing services"
            },
            {
                "id": 70,
                "name": "Storage",
                "subnet": "10.70.0.0/16",
                "purpose": "Storage network for SAN and NAS"
            },
            {
                "id": 80,
                "name": "vMotion",
                "subnet": "10.80.0.0/16",
                "purpose": "VM migration network"
            },
            {
                "id": 90,
                "name": "Backup",
                "subnet": "10.90.0.0/16",
                "purpose": "Backup network"
            }
        ]
    }
}

# Subnet Planning Templates
SUBNET_TEMPLATES = {
    "class_c": {
        "name": "Class C Network",
        "description": "Traditional Class C private network (192.168.x.0/24)",
        "base_network": "192.168.0.0/16",
        "subnet_size": "/24",
        "allocation_strategy": "sequential",
        "reserved_ranges": [
            {"start": "192.168.0.0", "end": "192.168.0.255", "purpose": "Reserved"}
        ]
    },
    "class_b": {
        "name": "Class B Network",
        "description": "Traditional Class B private network (172.16.0.0/12)",
        "base_network": "172.16.0.0/12",
        "subnet_size": "/24",
        "allocation_strategy": "sequential",
        "reserved_ranges": [
            {"start": "172.16.0.0", "end": "172.16.0.255", "purpose": "Reserved"}
        ]
    },
    "class_a": {
        "name": "Class A Network",
        "description": "Traditional Class A private network (10.0.0.0/8)",
        "base_network": "10.0.0.0/8",
        "subnet_size": "/24",
        "allocation_strategy": "vlan_mapped",
        "reserved_ranges": [
            {"start": "10.0.0.0", "end": "10.0.0.255", "purpose": "Reserved"}
        ]
    },
    "rfc1918_mixed": {
        "name": "RFC1918 Mixed",
        "description": "Mixed RFC1918 address space with purpose-based allocation",
        "base_networks": [
            {"network": "10.0.0.0/8", "purpose": "Internal infrastructure"},
            {"network": "172.16.0.0/12", "purpose": "Client VPNs and temporary networks"},
            {"network": "192.168.0.0/16", "purpose": "DMZ and public-facing services"}
        ],
        "subnet_size": "variable",
        "allocation_strategy": "purpose_based"
    }
}


def get_vlan_templates() -> Dict[str, Dict[str, Any]]:
    """
    Get all available VLAN templates.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of VLAN templates
    """
    return VLAN_TEMPLATES


def get_subnet_templates() -> Dict[str, Dict[str, Any]]:
    """
    Get all available subnet templates.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of subnet templates
    """
    return SUBNET_TEMPLATES


def apply_vlan_template(plan: Dict[str, Any], template_id: str) -> Dict[str, Any]:
    """
    Apply a VLAN template to a network plan.
    
    Args:
        plan (Dict[str, Any]): Network plan
        template_id (str): VLAN template ID
        
    Returns:
        Dict[str, Any]: Updated network plan
    
    Raises:
        ValueError: If template_id is not found
    """
    if template_id not in VLAN_TEMPLATES:
        raise ValueError(f"VLAN template '{template_id}' not found")
    
    template = VLAN_TEMPLATES[template_id]
    
    # Create networks for each VLAN
    for vlan in template["vlans"]:
        # Generate a unique ID for the network
        network_id = f"network-vlan-{vlan['id']}"
        
        # Check if this VLAN already exists
        existing_network = next((n for n in plan.get("networks", []) 
                               if n.get("vlan") == vlan["id"]), None)
        
        if existing_network:
            # Update existing network
            existing_network.update({
                "name": vlan["name"],
                "subnet": vlan["subnet"],
                "vlan": vlan["id"],
                "purpose": vlan["purpose"],
                "networkType": "vlan"
            })
        else:
            # Create new network
            network = {
                "id": network_id,
                "name": vlan["name"],
                "type": "network",
                "networkType": "vlan",
                "subnet": vlan["subnet"],
                "vlan": vlan["id"],
                "purpose": vlan["purpose"],
                "x": 400,  # Default position
                "y": 100 + (vlan["id"] * 50)  # Stagger vertically
            }
            
            # Add to plan
            if "networks" not in plan:
                plan["networks"] = []
            
            plan["networks"].append(network)
    
    return plan


def apply_subnet_template(plan: Dict[str, Any], template_id: str) -> Dict[str, Any]:
    """
    Apply a subnet template to a network plan.
    
    Args:
        plan (Dict[str, Any]): Network plan
        template_id (str): Subnet template ID
        
    Returns:
        Dict[str, Any]: Updated network plan
    
    Raises:
        ValueError: If template_id is not found
    """
    if template_id not in SUBNET_TEMPLATES:
        raise ValueError(f"Subnet template '{template_id}' not found")
    
    template = SUBNET_TEMPLATES[template_id]
    
    # Add subnet planning information to the plan
    if "subnet_planning" not in plan:
        plan["subnet_planning"] = {}
    
    plan["subnet_planning"].update({
        "template": template_id,
        "name": template["name"],
        "description": template["description"]
    })
    
    # For simple templates with a single base network
    if "base_network" in template:
        plan["subnet_planning"]["base_network"] = template["base_network"]
        plan["subnet_planning"]["subnet_size"] = template["subnet_size"]
        plan["subnet_planning"]["allocation_strategy"] = template["allocation_strategy"]
        plan["subnet_planning"]["reserved_ranges"] = template["reserved_ranges"]
    
    # For complex templates with multiple base networks
    elif "base_networks" in template:
        plan["subnet_planning"]["base_networks"] = template["base_networks"]
        plan["subnet_planning"]["subnet_size"] = template["subnet_size"]
        plan["subnet_planning"]["allocation_strategy"] = template["allocation_strategy"]
    
    # Update existing networks with appropriate subnets based on the template
    _assign_subnets_to_networks(plan)
    
    return plan


def _assign_subnets_to_networks(plan: Dict[str, Any]) -> None:
    """
    Assign subnets to networks based on the subnet planning template.
    
    Args:
        plan (Dict[str, Any]): Network plan
    """
    subnet_planning = plan.get("subnet_planning", {})
    if not subnet_planning:
        return
    
    networks = plan.get("networks", [])
    if not networks:
        return
    
    allocation_strategy = subnet_planning.get("allocation_strategy")
    
    if allocation_strategy == "sequential":
        _assign_sequential_subnets(networks, subnet_planning)
    elif allocation_strategy == "vlan_mapped":
        _assign_vlan_mapped_subnets(networks, subnet_planning)
    elif allocation_strategy == "purpose_based":
        _assign_purpose_based_subnets(networks, subnet_planning)


def _assign_sequential_subnets(networks: List[Dict[str, Any]], subnet_planning: Dict[str, Any]) -> None:
    """
    Assign subnets sequentially from the base network.
    
    Args:
        networks (List[Dict[str, Any]]): List of networks
        subnet_planning (Dict[str, Any]): Subnet planning configuration
    """
    import ipaddress
    
    base_network = subnet_planning.get("base_network")
    subnet_size = subnet_planning.get("subnet_size")
    reserved_ranges = subnet_planning.get("reserved_ranges", [])
    
    if not base_network or not subnet_size:
        return
    
    # Parse base network
    try:
        base = ipaddress.ip_network(base_network)
    except ValueError:
        return
    
    # Get subnet size as integer
    try:
        subnet_prefix = int(subnet_size.strip('/'))
    except ValueError:
        return
    
    # Generate subnets
    subnets = list(base.subnets(new_prefix=subnet_prefix))
    
    # Skip reserved ranges
    reserved_networks = []
    for reserved in reserved_ranges:
        try:
            start = ipaddress.ip_address(reserved["start"])
            end = ipaddress.ip_address(reserved["end"])
            
            for subnet in subnets:
                if (start in subnet or end in subnet or
                    (subnet.network_address <= start and subnet.broadcast_address >= end)):
                    reserved_networks.append(subnet)
        except ValueError:
            continue
    
    available_subnets = [s for s in subnets if s not in reserved_networks]
    
    # Assign subnets to networks that don't already have one
    subnet_index = 0
    for network in networks:
        if not network.get("subnet") and subnet_index < len(available_subnets):
            network["subnet"] = str(available_subnets[subnet_index])
            subnet_index += 1


def _assign_vlan_mapped_subnets(networks: List[Dict[str, Any]], subnet_planning: Dict[str, Any]) -> None:
    """
    Assign subnets based on VLAN ID.
    
    Args:
        networks (List[Dict[str, Any]]): List of networks
        subnet_planning (Dict[str, Any]): Subnet planning configuration
    """
    import ipaddress
    
    base_network = subnet_planning.get("base_network")
    subnet_size = subnet_planning.get("subnet_size")
    
    if not base_network or not subnet_size:
        return
    
    # Parse base network
    try:
        base = ipaddress.ip_network(base_network)
    except ValueError:
        return
    
    # Get subnet size as integer
    try:
        subnet_prefix = int(subnet_size.strip('/'))
    except ValueError:
        return
    
    # Assign subnets based on VLAN ID
    for network in networks:
        vlan_id = network.get("vlan")
        if vlan_id is not None and not network.get("subnet"):
            # Use VLAN ID to determine the third octet
            if base.version == 4 and subnet_prefix == 24:
                # For IPv4 with /24 subnets
                base_parts = str(base.network_address).split('.')
                if len(base_parts) == 4:
                    network["subnet"] = f"{base_parts[0]}.{base_parts[1]}.{vlan_id}.0/24"


def _assign_purpose_based_subnets(networks: List[Dict[str, Any]], subnet_planning: Dict[str, Any]) -> None:
    """
    Assign subnets based on network purpose.
    
    Args:
        networks (List[Dict[str, Any]]): List of networks
        subnet_planning (Dict[str, Any]): Subnet planning configuration
    """
    base_networks = subnet_planning.get("base_networks", [])
    
    if not base_networks:
        return
    
    # Create purpose to base network mapping
    purpose_map = {bn["purpose"].lower(): bn["network"] for bn in base_networks}
    
    # Default to first base network
    default_base = base_networks[0]["network"] if base_networks else None
    
    # Assign subnets based on purpose
    for network in networks:
        if network.get("subnet"):
            continue
            
        purpose = network.get("purpose", "").lower()
        
        # Find the most appropriate base network
        best_match = None
        for p, bn in purpose_map.items():
            if purpose and p in purpose:
                best_match = bn
                break
        
        if not best_match and default_base:
            best_match = default_base
            
        if best_match:
            # Assign a subnet from the base network
            import ipaddress
            try:
                base = ipaddress.ip_network(best_match)
                
                # Use a hash of the network ID to get a deterministic subnet
                import hashlib
                network_id = network.get("id", "")
                hash_val = int(hashlib.md5(network_id.encode()).hexdigest(), 16)
                
                # For IPv4 with /24 subnets
                if base.version == 4 and base.prefixlen <= 16:
                    third_octet = (hash_val % 254) + 1
                    fourth_octet = 0
                    
                    base_parts = str(base.network_address).split('.')
                    if len(base_parts) == 4:
                        network["subnet"] = f"{base_parts[0]}.{base_parts[1]}.{third_octet}.{fourth_octet}/24"
            except (ValueError, TypeError):
                continue
