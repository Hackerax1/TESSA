"""
Ansible Playbook Export Module for TESSA.

This module provides functionality to export Proxmox configurations to Ansible playbook format.
"""
import logging
import os
import json
import yaml
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ...api.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class AnsibleExporter:
    """Exporter for Ansible playbooks."""
    
    def __init__(self, api: ProxmoxAPI):
        """Initialize with Proxmox API connection."""
        self.api = api
        
    def export(self, output_dir: str, resource_types: List[str], include_sensitive: bool = False) -> Dict:
        """
        Export Proxmox configuration to Ansible playbook format.
        
        Args:
            output_dir: Directory to write Ansible files to
            resource_types: List of resource types to export (e.g., ['vm', 'lxc', 'storage'])
            include_sensitive: Whether to include sensitive information (default: False)
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            exported_resources = []
            
            # Create inventory file
            inventory_content = self._generate_inventory()
            with open(os.path.join(output_dir, 'inventory.yml'), 'w') as f:
                f.write(inventory_content)
            
            # Create variables file
            variables_content = self._generate_variables(include_sensitive)
            os.makedirs(os.path.join(output_dir, 'group_vars', 'all'), exist_ok=True)
            with open(os.path.join(output_dir, 'group_vars', 'all', 'vars.yml'), 'w') as f:
                f.write(variables_content)
                
            # Create main playbook
            main_playbook = self._generate_main_playbook(resource_types)
            with open(os.path.join(output_dir, 'site.yml'), 'w') as f:
                f.write(main_playbook)
            
            # Create roles directory
            roles_dir = os.path.join(output_dir, 'roles')
            os.makedirs(roles_dir, exist_ok=True)
            
            # Export VMs
            if "vm" in resource_types:
                vm_result = self._export_vms(roles_dir)
                exported_resources.extend(vm_result.get("resources", []))
                
            # Export Containers (LXC)
            if "lxc" in resource_types:
                lxc_result = self._export_containers(roles_dir)
                exported_resources.extend(lxc_result.get("resources", []))
                
            # Export Storage
            if "storage" in resource_types:
                storage_result = self._export_storage(roles_dir)
                exported_resources.extend(storage_result.get("resources", []))
                
            # Export Network
            if "network" in resource_types:
                network_result = self._export_network(roles_dir)
                exported_resources.extend(network_result.get("resources", []))
                
            # Create README
            readme_content = self._generate_readme()
            with open(os.path.join(output_dir, 'README.md'), 'w') as f:
                f.write(readme_content)
            
            return {
                "success": True,
                "message": f"Successfully exported {len(exported_resources)} resources to Ansible playbook format",
                "resources": exported_resources,
                "output_dir": output_dir
            }
        except Exception as e:
            logger.error(f"Error exporting to Ansible: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export to Ansible: {str(e)}"
            }
    
    def _generate_inventory(self) -> str:
        """Generate Ansible inventory file."""
        inventory = {
            "all": {
                "hosts": {
                    "proxmox": {
                        "ansible_host": "{{ proxmox_host }}",
                        "ansible_user": "{{ proxmox_user }}",
                        "ansible_ssh_pass": "{{ proxmox_ssh_pass }}"
                    }
                },
                "children": {
                    "proxmox_hosts": {
                        "hosts": {
                            "proxmox": {}
                        }
                    }
                }
            }
        }
        
        return yaml.dump(inventory, default_flow_style=False)

    def _generate_variables(self, include_sensitive: bool) -> str:
        """Generate Ansible variables file."""
        variables = {
            "proxmox_host": "your_proxmox_host",
            "proxmox_user": "root",
            "proxmox_api_user": "root@pam",
            "proxmox_api_password": "your_password" if include_sensitive else "{{ vault_proxmox_api_password }}",
            "proxmox_ssh_pass": "your_ssh_password" if include_sensitive else "{{ vault_proxmox_ssh_pass }}",
            "proxmox_node": "pve",
            "proxmox_api_host": "https://{{ proxmox_host }}:8006"
        }
        
        return yaml.dump(variables, default_flow_style=False)

    def _generate_main_playbook(self, resource_types: List[str]) -> str:
        """Generate main Ansible playbook."""
        roles = []
        
        if "vm" in resource_types:
            roles.append("proxmox_vms")
        
        if "lxc" in resource_types:
            roles.append("proxmox_containers")
            
        if "storage" in resource_types:
            roles.append("proxmox_storage")
            
        if "network" in resource_types:
            roles.append("proxmox_network")
        
        playbook = [
            {
                "name": "Proxmox Configuration Playbook",
                "hosts": "proxmox_hosts",
                "become": True,
                "roles": roles
            }
        ]
        
        return yaml.dump(playbook, default_flow_style=False)
        
    def _export_vms(self, roles_dir: str) -> Dict:
        """
        Export VMs to Ansible role.
        
        Args:
            roles_dir: Directory to write role to
            
        Returns:
            Result dictionary with success status and resources
        """
        try:
            # Create role directory structure
            role_dir = os.path.join(roles_dir, "proxmox_vms")
            os.makedirs(os.path.join(role_dir, "tasks"), exist_ok=True)
            os.makedirs(os.path.join(role_dir, "defaults"), exist_ok=True)
            
            # Get VM data from API
            vms = self.api.get_all_vms()
            
            # Create defaults/main.yml with VM definitions
            vm_vars = {
                "proxmox_vms": []
            }
            
            for vm in vms:
                vm_config = {
                    "name": vm.get("name", f"vm-{vm.get('vmid')}"),
                    "vmid": vm.get("vmid"),
                    "node": vm.get("node", "{{ proxmox_node }}"),
                    "memory": vm.get("maxmem", 512) // (1024 * 1024),  # Convert to MB
                    "cores": vm.get("cpus", 1),
                    "sockets": vm.get("sockets", 1),
                    "state": "present"
                }
                
                # Add disks
                if "disks" in vm:
                    vm_config["disks"] = []
                    for disk in vm["disks"]:
                        vm_config["disks"].append({
                            "storage": disk.get("storage", "local-lvm"),
                            "size": disk.get("size", "8G"),
                            "format": disk.get("format", "raw")
                        })
                
                # Add networks
                if "net" in vm:
                    vm_config["networks"] = []
                    for net in vm["net"]:
                        vm_config["networks"].append({
                            "model": net.get("model", "virtio"),
                            "bridge": net.get("bridge", "vmbr0"),
                            "tag": net.get("tag")
                        })
                
                vm_vars["proxmox_vms"].append(vm_config)
            
            # Write defaults/main.yml
            with open(os.path.join(role_dir, "defaults", "main.yml"), 'w') as f:
                f.write(yaml.dump(vm_vars, default_flow_style=False))
            
            # Create tasks/main.yml
            tasks = [
                {
                    "name": "Ensure Proxmox VMs are created",
                    "community.general.proxmox_kvm": {
                        "api_host": "{{ proxmox_api_host }}",
                        "api_user": "{{ proxmox_api_user }}",
                        "api_password": "{{ proxmox_api_password }}",
                        "name": "{{ item.name }}",
                        "node": "{{ item.node }}",
                        "vmid": "{{ item.vmid }}",
                        "memory": "{{ item.memory }}",
                        "cores": "{{ item.cores }}",
                        "sockets": "{{ item.sockets }}",
                        "state": "{{ item.state }}"
                    },
                    "loop": "{{ proxmox_vms }}"
                }
            ]
            
            # Write tasks/main.yml
            with open(os.path.join(role_dir, "tasks", "main.yml"), 'w') as f:
                f.write(yaml.dump(tasks, default_flow_style=False))
            
            return {
                "success": True,
                "resources": [{"type": "vm", "id": vm.get("vmid")} for vm in vms]
            }
        except Exception as e:
            logger.error(f"Error exporting VMs to Ansible: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export VMs to Ansible: {str(e)}",
                "resources": []
            }
    
    def _export_containers(self, roles_dir: str) -> Dict:
        """
        Export LXC containers to Ansible role.
        
        Args:
            roles_dir: Directory to write role to
            
        Returns:
            Result dictionary with success status and resources
        """
        try:
            # Create role directory structure
            role_dir = os.path.join(roles_dir, "proxmox_containers")
            os.makedirs(os.path.join(role_dir, "tasks"), exist_ok=True)
            os.makedirs(os.path.join(role_dir, "defaults"), exist_ok=True)
            
            # Get container data from API
            containers = self.api.get_all_containers()
            
            # Create defaults/main.yml with container definitions
            container_vars = {
                "proxmox_containers": []
            }
            
            for container in containers:
                container_config = {
                    "name": container.get("name", f"ct-{container.get('vmid')}"),
                    "vmid": container.get("vmid"),
                    "node": container.get("node", "{{ proxmox_node }}"),
                    "memory": container.get("maxmem", 512) // (1024 * 1024),  # Convert to MB
                    "cores": container.get("cpus", 1),
                    "ostemplate": container.get("ostemplate", "local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz"),
                    "state": "present"
                }
                
                # Add storage
                if "rootfs" in container:
                    container_config["rootfs"] = {
                        "storage": container["rootfs"].get("storage", "local-lvm"),
                        "size": container["rootfs"].get("size", "8G")
                    }
                
                # Add networks
                if "net" in container:
                    container_config["networks"] = []
                    for net in container["net"]:
                        container_config["networks"].append({
                            "name": net.get("name", "eth0"),
                            "bridge": net.get("bridge", "vmbr0"),
                            "ip": net.get("ip", "dhcp"),
                            "tag": net.get("tag")
                        })
                
                container_vars["proxmox_containers"].append(container_config)
            
            # Write defaults/main.yml
            with open(os.path.join(role_dir, "defaults", "main.yml"), 'w') as f:
                f.write(yaml.dump(container_vars, default_flow_style=False))
            
            # Create tasks/main.yml
            tasks = [
                {
                    "name": "Ensure Proxmox containers are created",
                    "community.general.proxmox_lxc": {
                        "api_host": "{{ proxmox_api_host }}",
                        "api_user": "{{ proxmox_api_user }}",
                        "api_password": "{{ proxmox_api_password }}",
                        "hostname": "{{ item.name }}",
                        "node": "{{ item.node }}",
                        "vmid": "{{ item.vmid }}",
                        "memory": "{{ item.memory }}",
                        "cores": "{{ item.cores }}",
                        "ostemplate": "{{ item.ostemplate }}",
                        "state": "{{ item.state }}"
                    },
                    "loop": "{{ proxmox_containers }}"
                }
            ]
            
            # Write tasks/main.yml
            with open(os.path.join(role_dir, "tasks", "main.yml"), 'w') as f:
                f.write(yaml.dump(tasks, default_flow_style=False))
            
            return {
                "success": True,
                "resources": [{"type": "container", "id": container.get("vmid")} for container in containers]
            }
        except Exception as e:
            logger.error(f"Error exporting containers to Ansible: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export containers to Ansible: {str(e)}",
                "resources": []
            }
    
    def _export_storage(self, roles_dir: str) -> Dict:
        """
        Export storage configuration to Ansible role.
        
        Args:
            roles_dir: Directory to write role to
            
        Returns:
            Result dictionary with success status and resources
        """
        try:
            # Create role directory structure
            role_dir = os.path.join(roles_dir, "proxmox_storage")
            os.makedirs(os.path.join(role_dir, "tasks"), exist_ok=True)
            os.makedirs(os.path.join(role_dir, "defaults"), exist_ok=True)
            
            # Get storage data from API
            storages = self.api.get_storage_configuration()
            
            # Create defaults/main.yml with storage definitions
            storage_vars = {
                "proxmox_storages": []
            }
            
            for storage in storages:
                storage_config = {
                    "name": storage.get("storage"),
                    "type": storage.get("type"),
                    "content": storage.get("content", "images,rootdir"),
                    "state": "present"
                }
                
                # Add type-specific configuration
                if storage.get("type") == "lvm":
                    storage_config["vgname"] = storage.get("vgname")
                elif storage.get("type") == "nfs":
                    storage_config["server"] = storage.get("server")
                    storage_config["export"] = storage.get("export")
                elif storage.get("type") == "cifs":
                    storage_config["server"] = storage.get("server")
                    storage_config["share"] = storage.get("share")
                elif storage.get("type") == "dir":
                    storage_config["path"] = storage.get("path")
                
                storage_vars["proxmox_storages"].append(storage_config)
            
            # Write defaults/main.yml
            with open(os.path.join(role_dir, "defaults", "main.yml"), 'w') as f:
                f.write(yaml.dump(storage_vars, default_flow_style=False))
            
            # Create tasks/main.yml
            tasks = [
                {
                    "name": "Ensure Proxmox storage is configured",
                    "proxmox_storage": {
                        "api_host": "{{ proxmox_api_host }}",
                        "api_user": "{{ proxmox_api_user }}",
                        "api_password": "{{ proxmox_api_password }}",
                        "storage": "{{ item.name }}",
                        "type": "{{ item.type }}",
                        "content": "{{ item.content }}",
                        "state": "{{ item.state }}"
                    },
                    "loop": "{{ proxmox_storages }}"
                }
            ]
            
            # Write tasks/main.yml
            with open(os.path.join(role_dir, "tasks", "main.yml"), 'w') as f:
                f.write(yaml.dump(tasks, default_flow_style=False))
            
            return {
                "success": True,
                "resources": [{"type": "storage", "id": storage.get("storage")} for storage in storages]
            }
        except Exception as e:
            logger.error(f"Error exporting storage to Ansible: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export storage to Ansible: {str(e)}",
                "resources": []
            }
    
    def _export_network(self, roles_dir: str) -> Dict:
        """
        Export network configuration to Ansible role.
        
        Args:
            roles_dir: Directory to write role to
            
        Returns:
            Result dictionary with success status and resources
        """
        try:
            # Create role directory structure
            role_dir = os.path.join(roles_dir, "proxmox_network")
            os.makedirs(os.path.join(role_dir, "tasks"), exist_ok=True)
            os.makedirs(os.path.join(role_dir, "defaults"), exist_ok=True)
            
            # Get network data from API
            networks = self.api.get_network_configuration()
            
            # Create defaults/main.yml with network definitions
            network_vars = {
                "proxmox_networks": []
            }
            
            for network in networks:
                network_config = {
                    "name": network.get("iface"),
                    "type": network.get("type", "bridge"),
                    "node": network.get("node", "{{ proxmox_node }}"),
                    "state": "present"
                }
                
                # Add type-specific configuration
                if network.get("type") == "bridge":
                    network_config["bridge_ports"] = network.get("bridge_ports", "")
                    network_config["bridge_stp"] = network.get("bridge_stp", "off")
                elif network.get("type") == "bond":
                    network_config["bond_slaves"] = network.get("slaves", "")
                    network_config["bond_mode"] = network.get("bond_mode", "balance-rr")
                elif network.get("type") == "vlan":
                    network_config["vlan_id"] = network.get("vlan_id")
                    network_config["vlan_raw_device"] = network.get("vlan_raw_device")
                
                # Add IP configuration if available
                if "cidr" in network:
                    network_config["cidr"] = network.get("cidr")
                    network_config["gateway"] = network.get("gateway", "")
                
                network_vars["proxmox_networks"].append(network_config)
            
            # Write defaults/main.yml
            with open(os.path.join(role_dir, "defaults", "main.yml"), 'w') as f:
                f.write(yaml.dump(network_vars, default_flow_style=False))
            
            # Create tasks/main.yml
            tasks = [
                {
                    "name": "Ensure Proxmox network is configured",
                    "community.general.proxmox_network": {
                        "api_host": "{{ proxmox_api_host }}",
                        "api_user": "{{ proxmox_api_user }}",
                        "api_password": "{{ proxmox_api_password }}",
                        "node": "{{ item.node }}",
                        "iface": "{{ item.name }}",
                        "type": "{{ item.type }}",
                        "state": "{{ item.state }}"
                    },
                    "loop": "{{ proxmox_networks }}"
                }
            ]
            
            # Write tasks/main.yml
            with open(os.path.join(role_dir, "tasks", "main.yml"), 'w') as f:
                f.write(yaml.dump(tasks, default_flow_style=False))
            
            return {
                "success": True,
                "resources": [{"type": "network", "id": network.get("iface")} for network in networks]
            }
        except Exception as e:
            logger.error(f"Error exporting network to Ansible: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export network to Ansible: {str(e)}",
                "resources": []
            }
    
    def _generate_readme(self) -> str:
        """Generate README file for Ansible playbook."""
        return """# Proxmox Ansible Playbook

This Ansible playbook was generated by TESSA (The Extensible Self-hosted Services Assistant).

## Structure

- `inventory.yml`: Contains the inventory definition for Proxmox hosts
- `site.yml`: Main playbook that includes all roles
- `group_vars/all/vars.yml`: Variables for Proxmox configuration
- `roles/`: Contains roles for different resource types
  - `proxmox_vms/`: Role for VM configuration
  - `proxmox_containers/`: Role for LXC container configuration
  - `proxmox_storage/`: Role for storage configuration
  - `proxmox_network/`: Role for network configuration

## Usage

1. Edit the `group_vars/all/vars.yml` file to set your Proxmox connection details
2. For sensitive information, consider using Ansible Vault:
   ```
   ansible-vault create group_vars/all/vault.yml
   ```
3. Run the playbook:
   ```
   ansible-playbook -i inventory.yml site.yml
   ```

## Requirements

- Ansible 2.9 or higher
- community.general collection (for Proxmox modules)

Install required collections:
```
ansible-galaxy collection install community.general
```
"""
