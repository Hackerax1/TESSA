"""
Network Planning Service

This module provides services for network planning and topology design.
It allows users to create, save, and manage network plans for their Proxmox environment.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from proxmox_nli.utils.config import get_config_dir
from proxmox_nli.services.network_planning.templates import (
    get_vlan_templates, get_subnet_templates,
    apply_vlan_template, apply_subnet_template
)

class NetworkPlanningService:
    """Service for network planning and topology design."""

    def __init__(self):
        """Initialize the network planning service."""
        self.plans_dir = os.path.join(get_config_dir(), "network_plans")
        os.makedirs(self.plans_dir, exist_ok=True)

    def get_plans(self) -> List[Dict[str, Any]]:
        """
        Get all network plans.

        Returns:
            List[Dict[str, Any]]: List of network plans metadata
        """
        plans = []
        for filename in os.listdir(self.plans_dir):
            if filename.endswith(".json"):
                plan_path = os.path.join(self.plans_dir, filename)
                try:
                    with open(plan_path, "r") as f:
                        plan = json.load(f)
                        plans.append({
                            "id": plan.get("id", os.path.splitext(filename)[0]),
                            "name": plan.get("name", "Unnamed Plan"),
                            "description": plan.get("description", ""),
                            "created_at": plan.get("created_at", ""),
                            "updated_at": plan.get("updated_at", ""),
                            "node_count": len(plan.get("nodes", [])),
                            "network_count": len(plan.get("networks", [])),
                        })
                except Exception as e:
                    print(f"Error loading plan {filename}: {str(e)}")
        
        # Sort by updated_at (newest first)
        plans.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return plans

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a network plan by ID.

        Args:
            plan_id (str): Plan ID

        Returns:
            Optional[Dict[str, Any]]: Network plan or None if not found
        """
        plan_path = os.path.join(self.plans_dir, f"{plan_id}.json")
        if not os.path.exists(plan_path):
            return None
        
        try:
            with open(plan_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading plan {plan_id}: {str(e)}")
            return None

    def create_plan(self, name: str, description: str = "", template: str = "empty") -> Dict[str, Any]:
        """
        Create a new network plan.

        Args:
            name (str): Plan name
            description (str): Plan description
            template (str): Template to use (empty, small, medium, large)

        Returns:
            Dict[str, Any]: Created network plan
        """
        plan_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Create basic plan structure
        plan = {
            "id": plan_id,
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now,
            "nodes": [],
            "networks": [],
            "connections": [],
            "settings": {
                "default_subnet_mask": "255.255.255.0",
                "default_gateway": "",
                "dns_servers": ["8.8.8.8", "1.1.1.1"],
                "domain": "local"
            }
        }
        
        # Apply template if specified
        if template != "empty":
            plan = self._apply_template(plan, template)
        
        # Save the plan
        self._save_plan(plan)
        
        return plan

    def update_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a network plan.

        Args:
            plan_id (str): Plan ID
            plan_data (Dict[str, Any]): Updated plan data

        Returns:
            Optional[Dict[str, Any]]: Updated network plan or None if not found
        """
        existing_plan = self.get_plan(plan_id)
        if not existing_plan:
            return None
        
        # Update plan data
        plan_data["id"] = plan_id  # Ensure ID doesn't change
        plan_data["created_at"] = existing_plan.get("created_at")  # Preserve creation time
        plan_data["updated_at"] = datetime.now().isoformat()
        
        # Save the updated plan
        self._save_plan(plan_data)
        
        return plan_data

    def delete_plan(self, plan_id: str) -> bool:
        """
        Delete a network plan.

        Args:
            plan_id (str): Plan ID

        Returns:
            bool: True if deleted, False otherwise
        """
        plan_path = os.path.join(self.plans_dir, f"{plan_id}.json")
        if not os.path.exists(plan_path):
            return False
        
        try:
            os.remove(plan_path)
            return True
        except Exception as e:
            print(f"Error deleting plan {plan_id}: {str(e)}")
            return False

    def validate_plan(self, plan: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a network plan.

        Args:
            plan (Dict[str, Any]): Network plan

        Returns:
            Tuple[bool, List[str]]: (is_valid, list of validation errors)
        """
        errors = []
        
        # Check for required fields
        required_fields = ["id", "name", "nodes", "networks", "connections"]
        for field in required_fields:
            if field not in plan:
                errors.append(f"Missing required field: {field}")
        
        # Validate nodes
        nodes = plan.get("nodes", [])
        node_ids = set()
        for i, node in enumerate(nodes):
            if "id" not in node:
                errors.append(f"Node at index {i} is missing an ID")
            else:
                if node["id"] in node_ids:
                    errors.append(f"Duplicate node ID: {node['id']}")
                node_ids.add(node["id"])
            
            if "name" not in node:
                errors.append(f"Node {node.get('id', f'at index {i}')} is missing a name")
            
            if "type" not in node:
                errors.append(f"Node {node.get('id', f'at index {i}')} is missing a type")
        
        # Validate networks
        networks = plan.get("networks", [])
        network_ids = set()
        for i, network in enumerate(networks):
            if "id" not in network:
                errors.append(f"Network at index {i} is missing an ID")
            else:
                if network["id"] in network_ids:
                    errors.append(f"Duplicate network ID: {network['id']}")
                network_ids.add(network["id"])
            
            if "name" not in network:
                errors.append(f"Network {network.get('id', f'at index {i}')} is missing a name")
            
            if "subnet" not in network:
                errors.append(f"Network {network.get('id', f'at index {i}')} is missing a subnet")
        
        # Validate connections
        connections = plan.get("connections", [])
        for i, connection in enumerate(connections):
            if "source" not in connection:
                errors.append(f"Connection at index {i} is missing a source")
            elif connection["source"] not in node_ids:
                errors.append(f"Connection at index {i} has an invalid source: {connection['source']}")
            
            if "target" not in connection:
                errors.append(f"Connection at index {i} is missing a target")
            elif connection["target"] not in network_ids:
                errors.append(f"Connection at index {i} has an invalid target: {connection['target']}")
        
        return len(errors) == 0, errors

    def generate_proxmox_network_config(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Proxmox network configuration from a network plan.

        Args:
            plan (Dict[str, Any]): Network plan

        Returns:
            Dict[str, Any]: Proxmox network configuration
        """
        # This is a simplified version - in a real implementation, this would
        # generate the actual network configuration for Proxmox nodes
        
        proxmox_config = {
            "nodes": {}
        }
        
        # Process each node
        for node in plan.get("nodes", []):
            node_id = node["id"]
            node_config = {
                "interfaces": {}
            }
            
            # Find connections for this node
            for conn in plan.get("connections", []):
                if conn["source"] == node_id:
                    # Find the network for this connection
                    network_id = conn["target"]
                    network = next((n for n in plan.get("networks", []) if n["id"] == network_id), None)
                    
                    if network:
                        interface_name = conn.get("interface", "eth0")
                        node_config["interfaces"][interface_name] = {
                            "name": interface_name,
                            "type": "bridge" if network.get("type") == "bridge" else "eth",
                            "subnet": network.get("subnet", ""),
                            "gateway": network.get("gateway", ""),
                            "vlan": network.get("vlan", None),
                            "mtu": network.get("mtu", 1500)
                        }
            
            proxmox_config["nodes"][node_id] = node_config
        
        return proxmox_config

    def get_vlan_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available VLAN templates.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of VLAN templates
        """
        return get_vlan_templates()
    
    def get_subnet_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available subnet templates.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of subnet templates
        """
        return get_subnet_templates()
    
    def apply_vlan_template(self, plan_id: str, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Apply a VLAN template to a network plan.
        
        Args:
            plan_id (str): Plan ID
            template_id (str): VLAN template ID
            
        Returns:
            Optional[Dict[str, Any]]: Updated network plan or None if not found
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        try:
            updated_plan = apply_vlan_template(plan, template_id)
            self._save_plan(updated_plan)
            return updated_plan
        except ValueError as e:
            print(f"Error applying VLAN template: {str(e)}")
            return None
    
    def apply_subnet_template(self, plan_id: str, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Apply a subnet template to a network plan.
        
        Args:
            plan_id (str): Plan ID
            template_id (str): Subnet template ID
            
        Returns:
            Optional[Dict[str, Any]]: Updated network plan or None if not found
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        
        try:
            updated_plan = apply_subnet_template(plan, template_id)
            self._save_plan(updated_plan)
            return updated_plan
        except ValueError as e:
            print(f"Error applying subnet template: {str(e)}")
            return None

    def _save_plan(self, plan: Dict[str, Any]) -> None:
        """
        Save a network plan to disk.

        Args:
            plan (Dict[str, Any]): Network plan
        """
        plan_path = os.path.join(self.plans_dir, f"{plan['id']}.json")
        with open(plan_path, "w") as f:
            json.dump(plan, f, indent=2)

    def _apply_template(self, plan: Dict[str, Any], template: str) -> Dict[str, Any]:
        """
        Apply a template to a network plan.

        Args:
            plan (Dict[str, Any]): Network plan
            template (str): Template name

        Returns:
            Dict[str, Any]: Network plan with template applied
        """
        if template == "small":
            # Small home network template
            plan["nodes"] = [
                {"id": "proxmox1", "name": "Proxmox Node 1", "type": "server", "x": 100, "y": 100},
                {"id": "router", "name": "Router", "type": "router", "x": 300, "y": 100}
            ]
            
            plan["networks"] = [
                {"id": "lan", "name": "LAN", "type": "bridge", "subnet": "192.168.1.0/24", "vlan": None, "x": 200, "y": 200}
            ]
            
            plan["connections"] = [
                {"source": "proxmox1", "target": "lan", "interface": "eth0"},
                {"source": "router", "target": "lan", "interface": "eth1"}
            ]
            
            plan["settings"]["default_gateway"] = "192.168.1.1"
            
        elif template == "medium":
            # Medium network with VLANs
            plan["nodes"] = [
                {"id": "proxmox1", "name": "Proxmox Node 1", "type": "server", "x": 100, "y": 100},
                {"id": "proxmox2", "name": "Proxmox Node 2", "type": "server", "x": 100, "y": 200},
                {"id": "router", "name": "Router", "type": "router", "x": 300, "y": 100},
                {"id": "switch", "name": "Managed Switch", "type": "switch", "x": 200, "y": 150}
            ]
            
            plan["networks"] = [
                {"id": "lan", "name": "LAN", "type": "bridge", "subnet": "192.168.1.0/24", "vlan": None, "x": 200, "y": 50},
                {"id": "servers", "name": "Servers VLAN", "type": "bridge", "subnet": "192.168.10.0/24", "vlan": 10, "x": 200, "y": 250},
                {"id": "storage", "name": "Storage VLAN", "type": "bridge", "subnet": "192.168.20.0/24", "vlan": 20, "x": 300, "y": 250}
            ]
            
            plan["connections"] = [
                {"source": "proxmox1", "target": "switch", "interface": "eth0"},
                {"source": "proxmox2", "target": "switch", "interface": "eth0"},
                {"source": "router", "target": "switch", "interface": "eth1"},
                {"source": "switch", "target": "lan", "interface": "eth0"},
                {"source": "switch", "target": "servers", "interface": "eth0.10"},
                {"source": "switch", "target": "storage", "interface": "eth0.20"}
            ]
            
            plan["settings"]["default_gateway"] = "192.168.1.1"
            
        elif template == "large":
            # Large network with multiple VLANs and redundancy
            plan["nodes"] = [
                {"id": "proxmox1", "name": "Proxmox Node 1", "type": "server", "x": 100, "y": 100},
                {"id": "proxmox2", "name": "Proxmox Node 2", "type": "server", "x": 100, "y": 200},
                {"id": "proxmox3", "name": "Proxmox Node 3", "type": "server", "x": 100, "y": 300},
                {"id": "router1", "name": "Primary Router", "type": "router", "x": 300, "y": 50},
                {"id": "router2", "name": "Backup Router", "type": "router", "x": 300, "y": 150},
                {"id": "switch1", "name": "Core Switch 1", "type": "switch", "x": 200, "y": 100},
                {"id": "switch2", "name": "Core Switch 2", "type": "switch", "x": 200, "y": 200}
            ]
            
            plan["networks"] = [
                {"id": "management", "name": "Management", "type": "bridge", "subnet": "10.0.0.0/24", "vlan": 1, "x": 400, "y": 50},
                {"id": "servers", "name": "Servers VLAN", "type": "bridge", "subnet": "10.0.10.0/24", "vlan": 10, "x": 400, "y": 100},
                {"id": "storage", "name": "Storage VLAN", "type": "bridge", "subnet": "10.0.20.0/24", "vlan": 20, "x": 400, "y": 150},
                {"id": "vmotion", "name": "vMotion VLAN", "type": "bridge", "subnet": "10.0.30.0/24", "vlan": 30, "x": 400, "y": 200},
                {"id": "wan", "name": "WAN", "type": "bridge", "subnet": "192.168.1.0/24", "vlan": None, "x": 400, "y": 250}
            ]
            
            # Add connections (simplified for brevity)
            plan["connections"] = [
                {"source": "proxmox1", "target": "switch1", "interface": "eth0"},
                {"source": "proxmox1", "target": "switch2", "interface": "eth1"},
                {"source": "proxmox2", "target": "switch1", "interface": "eth0"},
                {"source": "proxmox2", "target": "switch2", "interface": "eth1"},
                {"source": "proxmox3", "target": "switch1", "interface": "eth0"},
                {"source": "proxmox3", "target": "switch2", "interface": "eth1"},
                {"source": "router1", "target": "switch1", "interface": "eth1"},
                {"source": "router2", "target": "switch2", "interface": "eth1"},
                {"source": "router1", "target": "wan", "interface": "eth0"},
                {"source": "router2", "target": "wan", "interface": "eth0"},
                {"source": "switch1", "target": "management", "interface": "eth0.1"},
                {"source": "switch1", "target": "servers", "interface": "eth0.10"},
                {"source": "switch1", "target": "storage", "interface": "eth0.20"},
                {"source": "switch1", "target": "vmotion", "interface": "eth0.30"},
                {"source": "switch2", "target": "management", "interface": "eth0.1"},
                {"source": "switch2", "target": "servers", "interface": "eth0.10"},
                {"source": "switch2", "target": "storage", "interface": "eth0.20"},
                {"source": "switch2", "target": "vmotion", "interface": "eth0.30"}
            ]
            
            plan["settings"]["default_gateway"] = "10.0.0.1"
        
        return plan


# Create a singleton instance
network_planning_service = NetworkPlanningService()
