"""
VM Converter Utility for Migration Services

This module provides utilities for converting virtual machines between different
platforms, handling disk image conversion, configuration translation, and VM
import/export operations.
"""

import os
import json
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple, Union, BinaryIO

from proxmox_nli.services.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class VMConverter:
    """Virtual machine converter for cross-platform migrations"""
    
    def __init__(self, proxmox_api: ProxmoxAPI, temp_dir: Optional[str] = None):
        """
        Initialize VM converter
        
        Args:
            proxmox_api: Instance of ProxmoxAPI for interacting with Proxmox
            temp_dir: Optional temporary directory for conversion operations
        """
        self.proxmox_api = proxmox_api
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def convert_disk_image(self, source_path: str, target_path: str, 
                          source_format: str, target_format: str) -> bool:
        """
        Convert disk image from one format to another using qemu-img
        
        Args:
            source_path: Path to source disk image
            target_path: Path to save converted disk image
            source_format: Source disk image format (raw, qcow2, vmdk, vdi, etc.)
            target_format: Target disk image format (raw, qcow2, vmdk, vdi, etc.)
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Create target directory if it doesn't exist
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Build qemu-img command
            cmd = [
                'qemu-img', 'convert',
                '-f', source_format,
                '-O', target_format,
                source_path,
                target_path
            ]
            
            # Execute command
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Disk conversion failed: {result.stderr}")
                return False
            
            return os.path.exists(target_path)
            
        except Exception as e:
            logger.error(f"Disk conversion error: {str(e)}")
            return False
    
    def create_proxmox_vm(self, node: str, vm_config: Dict) -> Dict:
        """
        Create a new VM in Proxmox based on configuration
        
        Args:
            node: Target Proxmox node
            vm_config: VM configuration dictionary
            
        Returns:
            Dict with creation results
        """
        try:
            # Create VM
            result = self.proxmox_api.create_vm(node, vm_config)
            
            if not result.get("success", False):
                logger.error(f"VM creation failed: {result.get('message', 'Unknown error')}")
                return result
            
            return result
            
        except Exception as e:
            logger.error(f"VM creation error: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def import_disk_to_proxmox(self, node: str, storage: str, disk_path: str, 
                             format: str, vm_id: int) -> Dict:
        """
        Import disk image to Proxmox storage
        
        Args:
            node: Target Proxmox node
            storage: Target storage ID
            disk_path: Path to disk image
            format: Disk image format
            vm_id: Target VM ID
            
        Returns:
            Dict with import results
        """
        try:
            # Check if disk exists
            if not os.path.exists(disk_path):
                return {"success": False, "message": f"Disk image not found: {disk_path}"}
            
            # Import disk to storage
            result = self.proxmox_api.import_disk(node, storage, disk_path, format, vm_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Disk import error: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def map_network_devices(self, source_networks: List[Dict], 
                          target_networks: List[Dict]) -> List[Dict]:
        """
        Map network devices from source to target
        
        Args:
            source_networks: List of source network device configurations
            target_networks: List of available target networks
            
        Returns:
            List of mapped network configurations for Proxmox
        """
        mapped_networks = []
        
        # Simple mapping based on network names and types
        for source_net in source_networks:
            best_match = None
            best_score = 0
            
            for target_net in target_networks:
                score = 0
                
                # Match by name (partial match)
                if source_net.get("name", "").lower() in target_net.get("name", "").lower():
                    score += 2
                
                # Match by type (bridge, nat, etc.)
                if source_net.get("type") == target_net.get("type"):
                    score += 3
                
                # Match by VLAN if available
                if source_net.get("vlan") == target_net.get("vlan"):
                    score += 2
                
                if score > best_score:
                    best_score = score
                    best_match = target_net
            
            if best_match:
                # Create Proxmox network config
                net_config = {
                    "model": source_net.get("model", "virtio"),
                    "bridge": best_match.get("name", "vmbr0"),
                    "firewall": source_net.get("firewall", 0)
                }
                
                # Add VLAN tag if present
                if best_match.get("vlan"):
                    net_config["tag"] = best_match.get("vlan")
                
                mapped_networks.append(net_config)
            else:
                # Default to vmbr0 if no match found
                mapped_networks.append({
                    "model": source_net.get("model", "virtio"),
                    "bridge": "vmbr0",
                    "firewall": source_net.get("firewall", 0)
                })
        
        return mapped_networks
    
    def map_cpu_configuration(self, source_cpu: Dict) -> Dict:
        """
        Map CPU configuration from source to Proxmox
        
        Args:
            source_cpu: Source CPU configuration
            
        Returns:
            Proxmox CPU configuration
        """
        # Default CPU configuration
        cpu_config = {
            "sockets": 1,
            "cores": 2,
            "type": "host"
        }
        
        # Map CPU cores and sockets
        if "cores" in source_cpu:
            cpu_config["cores"] = source_cpu["cores"]
        
        if "sockets" in source_cpu:
            cpu_config["sockets"] = source_cpu["sockets"]
        
        # Map CPU type
        if "type" in source_cpu:
            # Map common CPU types to Proxmox equivalents
            cpu_type_map = {
                "host": "host",
                "qemu64": "qemu64",
                "kvm64": "kvm64",
                "host-passthrough": "host",
                "host-model": "host"
            }
            
            cpu_config["type"] = cpu_type_map.get(source_cpu["type"], "host")
        
        # Map CPU flags
        if "flags" in source_cpu and source_cpu["flags"]:
            cpu_config["flags"] = source_cpu["flags"]
        
        return cpu_config
    
    def map_memory_configuration(self, source_memory: Dict) -> Dict:
        """
        Map memory configuration from source to Proxmox
        
        Args:
            source_memory: Source memory configuration
            
        Returns:
            Proxmox memory configuration
        """
        memory_config = {
            "memory": 1024,  # Default 1GB
            "balloon": 0
        }
        
        # Map memory size (convert to MB if needed)
        if "size_mb" in source_memory:
            memory_config["memory"] = source_memory["size_mb"]
        elif "size_gb" in source_memory:
            memory_config["memory"] = source_memory["size_gb"] * 1024
        
        # Map memory ballooning
        if "ballooning" in source_memory:
            memory_config["balloon"] = 1 if source_memory["ballooning"] else 0
        
        # Map hugepages
        if "hugepages" in source_memory:
            memory_config["hugepages"] = source_memory["hugepages"]
        
        return memory_config
    
    def translate_vm_config(self, source_config: Dict, source_platform: str) -> Dict:
        """
        Translate VM configuration from source platform to Proxmox
        
        Args:
            source_config: Source VM configuration
            source_platform: Source platform (unraid, truenas, esxi)
            
        Returns:
            Proxmox VM configuration
        """
        # Base Proxmox VM configuration
        proxmox_config = {
            "name": source_config.get("name", "Migrated VM"),
            "ostype": "other",
            "scsihw": "virtio-scsi-pci",
            "bootdisk": "scsi0",
            "onboot": 1,
            "agent": 1
        }
        
        # Map OS type
        os_type = source_config.get("os_type", "").lower()
        if "windows" in os_type:
            proxmox_config["ostype"] = "win10" if "10" in os_type else "win11"
        elif "linux" in os_type:
            proxmox_config["ostype"] = "l26"
        
        # Map CPU configuration
        cpu_config = self.map_cpu_configuration(source_config.get("cpu", {}))
        proxmox_config.update(cpu_config)
        
        # Map memory configuration
        memory_config = self.map_memory_configuration(source_config.get("memory", {}))
        proxmox_config.update(memory_config)
        
        # Platform-specific translations
        if source_platform == "unraid":
            # Unraid-specific mappings
            if "vfio" in source_config.get("features", []):
                proxmox_config["machine"] = "q35"
            
            # Map XML-based network devices
            if "network_devices" in source_config:
                proxmox_config["net0"] = f"virtio,bridge=vmbr0"
        
        elif source_platform == "esxi":
            # ESXi-specific mappings
            if source_config.get("firmware", "") == "efi":
                proxmox_config["bios"] = "ovmf"
            
            # Handle VMware tools
            if source_config.get("tools_installed", False):
                proxmox_config["agent"] = 1
        
        elif source_platform == "truenas":
            # TrueNAS-specific mappings
            if source_config.get("zvol_based_disks", False):
                proxmox_config["scsihw"] = "virtio-scsi-pci"
        
        return proxmox_config
    
    def extract_ovf_config(self, ovf_path: str) -> Dict:
        """
        Extract VM configuration from OVF file
        
        Args:
            ovf_path: Path to OVF file
            
        Returns:
            Dict with VM configuration
        """
        try:
            import xml.etree.ElementTree as ET
            
            # Parse OVF XML
            tree = ET.parse(ovf_path)
            root = tree.getroot()
            
            # Define XML namespaces
            namespaces = {
                'ovf': 'http://schemas.dmtf.org/ovf/envelope/1',
                'rasd': 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData',
                'vmw': 'http://www.vmware.com/schema/ovf'
            }
            
            # Extract VM name
            vm_name = "Imported VM"
            for vm in root.findall('.//ovf:VirtualSystem', namespaces):
                name = vm.find('./ovf:Name', namespaces)
                if name is not None:
                    vm_name = name.text
            
            # Extract hardware configuration
            config = {
                "name": vm_name,
                "cpu": {},
                "memory": {},
                "disks": [],
                "networks": []
            }
            
            # Process virtual hardware
            for item in root.findall('.//ovf:Item', namespaces):
                resource_type = item.find('./rasd:ResourceType', namespaces)
                
                if resource_type is None:
                    continue
                
                # CPU (3)
                if resource_type.text == '3':
                    cpu_count = item.find('./rasd:VirtualQuantity', namespaces)
                    if cpu_count is not None:
                        config["cpu"]["cores"] = int(cpu_count.text)
                
                # Memory (4)
                elif resource_type.text == '4':
                    memory = item.find('./rasd:VirtualQuantity', namespaces)
                    if memory is not None:
                        # Convert to MB
                        memory_mb = int(int(memory.text) / 1024)
                        config["memory"]["size_mb"] = memory_mb
                
                # Disk (17)
                elif resource_type.text == '17':
                    disk = {}
                    
                    # Get disk properties
                    address = item.find('./rasd:AddressOnParent', namespaces)
                    if address is not None:
                        disk["index"] = int(address.text)
                    
                    element_name = item.find('./rasd:ElementName', namespaces)
                    if element_name is not None:
                        disk["name"] = element_name.text
                    
                    host_resource = item.find('./rasd:HostResource', namespaces)
                    if host_resource is not None:
                        disk["path"] = host_resource.text
                    
                    config["disks"].append(disk)
                
                # Network (10)
                elif resource_type.text == '10':
                    network = {}
                    
                    # Get network properties
                    element_name = item.find('./rasd:ElementName', namespaces)
                    if element_name is not None:
                        network["name"] = element_name.text
                    
                    connection = item.find('./rasd:Connection', namespaces)
                    if connection is not None:
                        network["network"] = connection.text
                    
                    config["networks"].append(network)
            
            return config
            
        except Exception as e:
            logger.error(f"OVF parsing error: {str(e)}")
            return {"name": "Imported VM"}
    
    def create_container_from_docker(self, node: str, docker_config: Dict) -> Dict:
        """
        Create LXC container from Docker container configuration
        
        Args:
            node: Target Proxmox node
            docker_config: Docker container configuration
            
        Returns:
            Dict with creation results
        """
        try:
            # Map Docker configuration to LXC
            lxc_config = {
                "hostname": docker_config.get("name", "docker-container"),
                "ostemplate": "local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz",  # Default template
                "memory": docker_config.get("memory_limit", 512),
                "swap": docker_config.get("swap_limit", 512),
                "cores": docker_config.get("cpu_limit", 1),
                "net0": "name=eth0,bridge=vmbr0,ip=dhcp",
                "storage": "local",
                "rootfs": f"local:8",  # Default 8GB
                "unprivileged": 1
            }
            
            # Map Docker volumes to LXC mounts
            if "volumes" in docker_config:
                for i, volume in enumerate(docker_config["volumes"]):
                    if i >= 4:  # Proxmox supports up to mp0-mp3
                        break
                    
                    host_path = volume.get("host_path", "")
                    container_path = volume.get("container_path", "")
                    
                    if host_path and container_path:
                        lxc_config[f"mp{i}"] = f"local:{host_path},{container_path}"
            
            # Map Docker environment variables
            if "environment" in docker_config:
                lxc_config["startup"] = "#!/bin/bash\n"
                
                for key, value in docker_config["environment"].items():
                    lxc_config["startup"] += f"export {key}={value}\n"
            
            # Create container
            result = self.proxmox_api.create_container(node, lxc_config)
            
            return result
            
        except Exception as e:
            logger.error(f"Container creation error: {str(e)}")
            return {"success": False, "message": str(e)}
