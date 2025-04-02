"""
GPU Passthrough Optimization Assistant for TESSA.

This module provides functionality to detect, configure, and optimize GPU passthrough
for Proxmox virtual machines.
"""
import logging
import os
import json
import re
import subprocess
from typing import Dict, List, Any, Optional, Tuple

from ..api.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class GPUPassthroughAssistant:
    """Assistant for optimizing GPU passthrough configurations."""
    
    def __init__(self, api: ProxmoxAPI):
        """Initialize with Proxmox API connection."""
        self.api = api
        
    def detect_gpus(self, node_name: str = None) -> Dict:
        """
        Detect available GPUs on the specified node.
        
        Args:
            node_name: Name of the node to check (default: first available node)
            
        Returns:
            Dictionary with detected GPUs and their information
        """
        try:
            # Get node name if not provided
            if not node_name:
                nodes = self.api.get_nodes()
                if not nodes:
                    return {
                        "success": False,
                        "message": "No nodes found"
                    }
                node_name = nodes[0]["node"]
                
            # Execute lspci command on the node
            result = self.api.execute_node_command(
                node=node_name,
                command="lspci -nnk | grep -A 3 VGA"
            )
            
            if not result["success"]:
                return result
                
            # Parse lspci output to find GPUs
            gpus = self._parse_lspci_output(result["data"])
            
            # Get IOMMU groups
            iommu_result = self.api.execute_node_command(
                node=node_name,
                command="find /sys/kernel/iommu_groups/ -type l | sort -V"
            )
            
            if iommu_result["success"]:
                iommu_groups = self._parse_iommu_groups(iommu_result["data"])
                
                # Match GPUs with IOMMU groups
                for gpu in gpus:
                    gpu_id = gpu["pci_id"].split(":")[0]
                    for group in iommu_groups:
                        if any(gpu_id in device for device in group["devices"]):
                            gpu["iommu_group"] = group["group_id"]
                            gpu["iommu_devices"] = group["devices"]
                            break
            
            # Check if VFIO modules are loaded
            vfio_result = self.api.execute_node_command(
                node=node_name,
                command="lsmod | grep vfio"
            )
            
            vfio_loaded = vfio_result["success"] and vfio_result["data"].strip() != ""
            
            # Check if IOMMU is enabled
            iommu_enabled_result = self.api.execute_node_command(
                node=node_name,
                command="dmesg | grep -i 'IOMMU enabled'"
            )
            
            iommu_enabled = iommu_enabled_result["success"] and iommu_enabled_result["data"].strip() != ""
            
            return {
                "success": True,
                "node": node_name,
                "gpus": gpus,
                "vfio_loaded": vfio_loaded,
                "iommu_enabled": iommu_enabled
            }
        except Exception as e:
            logger.error(f"Error detecting GPUs: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to detect GPUs: {str(e)}"
            }
            
    def _parse_lspci_output(self, output: str) -> List[Dict]:
        """Parse lspci output to extract GPU information."""
        gpus = []
        current_gpu = None
        
        for line in output.split('\n'):
            line = line.strip()
            
            # New GPU entry
            if "VGA compatible controller" in line or "3D controller" in line:
                if current_gpu:
                    gpus.append(current_gpu)
                    
                # Extract PCI ID and GPU name
                pci_match = re.search(r'([0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f])', line)
                vendor_match = re.search(r'\[([0-9a-f]{4}):([0-9a-f]{4})\]', line)
                
                current_gpu = {
                    "pci_id": pci_match.group(1) if pci_match else "Unknown",
                    "name": line.split(":")[1].split("[")[0].strip() if ":" in line else "Unknown",
                    "vendor_id": vendor_match.group(1) if vendor_match else "Unknown",
                    "device_id": vendor_match.group(2) if vendor_match else "Unknown",
                    "driver": "Unknown",
                    "iommu_group": None,
                    "iommu_devices": []
                }
            # Driver information
            elif current_gpu and "Kernel driver in use:" in line:
                current_gpu["driver"] = line.split(":")[1].strip()
                
        # Add the last GPU
        if current_gpu:
            gpus.append(current_gpu)
            
        return gpus
        
    def _parse_iommu_groups(self, output: str) -> List[Dict]:
        """Parse IOMMU groups output."""
        groups = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Extract group ID and device
            match = re.search(r'/sys/kernel/iommu_groups/(\d+)/devices/([0-9a-f:\.]+)', line)
            if match:
                group_id = match.group(1)
                device = match.group(2)
                
                if group_id not in groups:
                    groups[group_id] = {
                        "group_id": group_id,
                        "devices": []
                    }
                    
                groups[group_id]["devices"].append(device)
                
        return list(groups.values())
        
    def check_passthrough_compatibility(self, node_name: str = None) -> Dict:
        """
        Check if the system is compatible with GPU passthrough.
        
        Args:
            node_name: Name of the node to check (default: first available node)
            
        Returns:
            Dictionary with compatibility information
        """
        try:
            # Get node name if not provided
            if not node_name:
                nodes = self.api.get_nodes()
                if not nodes:
                    return {
                        "success": False,
                        "message": "No nodes found"
                    }
                node_name = nodes[0]["node"]
                
            # Check CPU virtualization support
            virt_result = self.api.execute_node_command(
                node=node_name,
                command="grep -E 'vmx|svm' /proc/cpuinfo"
            )
            
            virt_supported = virt_result["success"] and virt_result["data"].strip() != ""
            
            # Check if IOMMU is enabled in kernel
            cmdline_result = self.api.execute_node_command(
                node=node_name,
                command="cat /proc/cmdline"
            )
            
            iommu_enabled = False
            if cmdline_result["success"]:
                cmdline = cmdline_result["data"]
                if ("intel_iommu=on" in cmdline or "amd_iommu=on" in cmdline) and "iommu=pt" in cmdline:
                    iommu_enabled = True
                    
            # Check if VFIO modules are available
            vfio_result = self.api.execute_node_command(
                node=node_name,
                command="modinfo vfio-pci"
            )
            
            vfio_available = vfio_result["success"] and vfio_result["data"].strip() != ""
            
            # Detect GPUs
            gpu_result = self.detect_gpus(node_name)
            
            # Check if any GPUs are using VFIO driver
            gpus_using_vfio = False
            if gpu_result["success"]:
                for gpu in gpu_result["gpus"]:
                    if gpu["driver"] == "vfio-pci":
                        gpus_using_vfio = True
                        break
                        
            # Overall compatibility assessment
            compatibility = {
                "compatible": virt_supported and iommu_enabled and vfio_available,
                "virt_supported": virt_supported,
                "iommu_enabled": iommu_enabled,
                "vfio_available": vfio_available,
                "gpus_using_vfio": gpus_using_vfio
            }
            
            return {
                "success": True,
                "node": node_name,
                "compatibility": compatibility,
                "gpus": gpu_result.get("gpus", []) if gpu_result["success"] else []
            }
        except Exception as e:
            logger.error(f"Error checking passthrough compatibility: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to check passthrough compatibility: {str(e)}"
            }
            
    def get_optimization_recommendations(self, node_name: str = None, vm_id: Optional[str] = None) -> Dict:
        """
        Get optimization recommendations for GPU passthrough.
        
        Args:
            node_name: Name of the node to check (default: first available node)
            vm_id: Optional VM ID to get specific recommendations for
            
        Returns:
            Dictionary with optimization recommendations
        """
        try:
            # Check compatibility first
            compat_result = self.check_passthrough_compatibility(node_name)
            
            if not compat_result["success"]:
                return compat_result
                
            node_name = compat_result["node"]
            compatibility = compat_result["compatibility"]
            gpus = compat_result["gpus"]
            
            # Generate general recommendations
            recommendations = []
            
            if not compatibility["virt_supported"]:
                recommendations.append({
                    "type": "error",
                    "component": "cpu",
                    "message": "CPU virtualization not supported or enabled in BIOS",
                    "solution": "Enable virtualization (VT-x/AMD-V) in BIOS settings"
                })
                
            if not compatibility["iommu_enabled"]:
                recommendations.append({
                    "type": "error",
                    "component": "kernel",
                    "message": "IOMMU not enabled in kernel parameters",
                    "solution": "Add 'intel_iommu=on' or 'amd_iommu=on' and 'iommu=pt' to GRUB_CMDLINE_LINUX in /etc/default/grub, then run 'update-grub' and reboot"
                })
                
            if not compatibility["vfio_available"]:
                recommendations.append({
                    "type": "error",
                    "component": "modules",
                    "message": "VFIO modules not available",
                    "solution": "Install VFIO modules: modprobe vfio vfio_iommu_type1 vfio_pci"
                })
                
            # GPU-specific recommendations
            for gpu in gpus:
                if gpu["driver"] != "vfio-pci":
                    recommendations.append({
                        "type": "warning",
                        "component": "gpu",
                        "gpu_name": gpu["name"],
                        "pci_id": gpu["pci_id"],
                        "message": f"GPU {gpu['name']} is not using VFIO driver (currently using {gpu['driver']})",
                        "solution": f"Add GPU PCI ID ({gpu['vendor_id']}:{gpu['device_id']}) to VFIO configuration"
                    })
                    
                if gpu["iommu_group"] and len(gpu["iommu_devices"]) > 1:
                    recommendations.append({
                        "type": "info",
                        "component": "iommu",
                        "gpu_name": gpu["name"],
                        "message": f"GPU is in IOMMU group {gpu['iommu_group']} with {len(gpu['iommu_devices'])} other devices",
                        "solution": "All devices in the same IOMMU group must be passed through together"
                    })
                    
            # VM-specific recommendations
            if vm_id:
                vm_result = self.api.get_vm_config(node_name, vm_id)
                
                if vm_result["success"]:
                    vm_config = vm_result["data"]
                    
                    # Check if machine type is optimal for GPU passthrough
                    if "machine" in vm_config and vm_config["machine"] != "q35":
                        recommendations.append({
                            "type": "warning",
                            "component": "vm",
                            "message": f"VM is using machine type '{vm_config['machine']}', which may not be optimal for GPU passthrough",
                            "solution": "Change machine type to 'q35' for better PCI passthrough support"
                        })
                        
                    # Check if CPU type is optimal
                    if "cpu" in vm_config and vm_config["cpu"] != "host":
                        recommendations.append({
                            "type": "warning",
                            "component": "vm",
                            "message": "VM is not using host CPU model, which may cause issues with GPU passthrough",
                            "solution": "Set CPU type to 'host' for best compatibility"
                        })
                        
                    # Check for other optimal settings
                    if "args" not in vm_config or "-cpu host,kvm=off" not in vm_config["args"]:
                        recommendations.append({
                            "type": "info",
                            "component": "vm",
                            "message": "VM may benefit from additional CPU flags for GPU passthrough",
                            "solution": "Add '-cpu host,kvm=off,hv_vendor_id=proxmox,+kvm_pv_unhalt,+kvm_pv_eoi' to VM args"
                        })
            
            return {
                "success": True,
                "node": node_name,
                "vm_id": vm_id,
                "compatibility": compatibility,
                "gpus": gpus,
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get optimization recommendations: {str(e)}"
            }
            
    def apply_optimizations(self, node_name: str, vm_id: str, optimizations: List[str]) -> Dict:
        """
        Apply selected optimizations to a VM.
        
        Args:
            node_name: Name of the node
            vm_id: VM ID to optimize
            optimizations: List of optimization keys to apply
            
        Returns:
            Dictionary with results of applied optimizations
        """
        try:
            results = []
            
            for opt in optimizations:
                if opt == "machine_type":
                    # Change machine type to q35
                    result = self.api.update_vm_config(
                        node=node_name,
                        vmid=vm_id,
                        config={"machine": "q35"}
                    )
                    results.append({
                        "optimization": "machine_type",
                        "success": result["success"],
                        "message": result.get("message", "Machine type changed to q35")
                    })
                    
                elif opt == "cpu_type":
                    # Set CPU type to host
                    result = self.api.update_vm_config(
                        node=node_name,
                        vmid=vm_id,
                        config={"cpu": "host"}
                    )
                    results.append({
                        "optimization": "cpu_type",
                        "success": result["success"],
                        "message": result.get("message", "CPU type set to host")
                    })
                    
                elif opt == "cpu_flags":
                    # Add CPU flags for better passthrough
                    vm_result = self.api.get_vm_config(node_name, vm_id)
                    
                    if vm_result["success"]:
                        vm_config = vm_result["data"]
                        args = vm_config.get("args", "")
                        
                        if "-cpu" not in args:
                            args += " -cpu host,kvm=off,hv_vendor_id=proxmox,+kvm_pv_unhalt,+kvm_pv_eoi"
                        
                        result = self.api.update_vm_config(
                            node=node_name,
                            vmid=vm_id,
                            config={"args": args}
                        )
                        results.append({
                            "optimization": "cpu_flags",
                            "success": result["success"],
                            "message": result.get("message", "CPU flags added for better passthrough")
                        })
                    else:
                        results.append({
                            "optimization": "cpu_flags",
                            "success": False,
                            "message": "Failed to get VM configuration"
                        })
                        
                elif opt == "iommu_fix":
                    # Add ACS override for IOMMU groups
                    host_result = self.api.execute_node_command(
                        node=node_name,
                        command="echo 'options vfio_iommu_type1 allow_unsafe_interrupts=1' > /etc/modprobe.d/iommu_unsafe_interrupts.conf && update-initramfs -u"
                    )
                    results.append({
                        "optimization": "iommu_fix",
                        "success": host_result["success"],
                        "message": host_result.get("message", "IOMMU interrupt remapping fix applied")
                    })
                    
                elif opt == "hugepages":
                    # Enable hugepages for better performance
                    vm_result = self.api.get_vm_config(node_name, vm_id)
                    
                    if vm_result["success"]:
                        vm_config = vm_result["data"]
                        memory = vm_config.get("memory", 1024)
                        
                        # Calculate hugepages (memory in MB / 2)
                        hugepages = memory // 2
                        
                        host_result = self.api.execute_node_command(
                            node=node_name,
                            command=f"echo {hugepages} > /proc/sys/vm/nr_hugepages"
                        )
                        
                        if host_result["success"]:
                            # Add hugepages to VM config
                            args = vm_config.get("args", "")
                            if "-mem-path" not in args:
                                args += " -mem-path /dev/hugepages"
                                
                            result = self.api.update_vm_config(
                                node=node_name,
                                vmid=vm_id,
                                config={"args": args}
                            )
                            results.append({
                                "optimization": "hugepages",
                                "success": result["success"],
                                "message": result.get("message", f"Hugepages enabled ({hugepages} pages)")
                            })
                        else:
                            results.append({
                                "optimization": "hugepages",
                                "success": False,
                                "message": "Failed to set hugepages on host"
                            })
                    else:
                        results.append({
                            "optimization": "hugepages",
                            "success": False,
                            "message": "Failed to get VM configuration"
                        })
            
            return {
                "success": True,
                "node": node_name,
                "vm_id": vm_id,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error applying optimizations: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to apply optimizations: {str(e)}"
            }
            
    def configure_gpu_passthrough(self, node_name: str, vm_id: str, gpu_pci_id: str) -> Dict:
        """
        Configure GPU passthrough for a VM.
        
        Args:
            node_name: Name of the node
            vm_id: VM ID to configure
            gpu_pci_id: PCI ID of the GPU to pass through
            
        Returns:
            Dictionary with configuration result
        """
        try:
            # Get GPU information
            gpu_result = self.detect_gpus(node_name)
            
            if not gpu_result["success"]:
                return gpu_result
                
            # Find the GPU
            gpu = None
            for g in gpu_result["gpus"]:
                if g["pci_id"] == gpu_pci_id:
                    gpu = g
                    break
                    
            if not gpu:
                return {
                    "success": False,
                    "message": f"GPU with PCI ID {gpu_pci_id} not found"
                }
                
            # Check if GPU is using VFIO driver
            if gpu["driver"] != "vfio-pci":
                # Bind GPU to VFIO driver
                bind_result = self.api.execute_node_command(
                    node=node_name,
                    command=f"echo {gpu['vendor_id']} {gpu['device_id']} > /sys/bus/pci/drivers/vfio-pci/new_id"
                )
                
                if not bind_result["success"]:
                    return {
                        "success": False,
                        "message": f"Failed to bind GPU to VFIO driver: {bind_result.get('message', '')}"
                    }
                    
            # Add GPU to VM configuration
            hostpci = f"0{gpu_pci_id},pcie=1"
            
            # If GPU is in an IOMMU group with other devices, add them too
            if gpu["iommu_group"] and len(gpu["iommu_devices"]) > 1:
                # Find audio device in the same group (common for GPUs)
                for device in gpu["iommu_devices"]:
                    if device != gpu_pci_id and "audio" in device.lower():
                        hostpci += f";0{device},pcie=1"
                        break
                        
            # Update VM configuration
            result = self.api.update_vm_config(
                node=node_name,
                vmid=vm_id,
                config={
                    "hostpci0": hostpci,
                    "machine": "q35",
                    "cpu": "host"
                }
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "node": node_name,
                    "vm_id": vm_id,
                    "gpu": gpu,
                    "message": "GPU passthrough configured successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to configure GPU passthrough: {result.get('message', '')}"
                }
        except Exception as e:
            logger.error(f"Error configuring GPU passthrough: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to configure GPU passthrough: {str(e)}"
            }
            
    def get_passthrough_status(self, node_name: str = None) -> Dict:
        """
        Get the current status of GPU passthrough on the node.
        
        Args:
            node_name: Name of the node to check (default: first available node)
            
        Returns:
            Dictionary with passthrough status
        """
        try:
            # Get node name if not provided
            if not node_name:
                nodes = self.api.get_nodes()
                if not nodes:
                    return {
                        "success": False,
                        "message": "No nodes found"
                    }
                node_name = nodes[0]["node"]
                
            # Get GPUs
            gpu_result = self.detect_gpus(node_name)
            
            if not gpu_result["success"]:
                return gpu_result
                
            # Get VMs with GPU passthrough
            vms_with_gpu = []
            vms = self.api.get_all_vms(node_name)
            
            for vm in vms:
                vm_config = self.api.get_vm_config(node_name, vm["vmid"])
                
                if vm_config["success"]:
                    config = vm_config["data"]
                    
                    # Check for hostpci entries
                    for key, value in config.items():
                        if key.startswith("hostpci"):
                            # Extract PCI IDs
                            pci_ids = []
                            for part in value.split(";"):
                                pci_id = part.split(",")[0]
                                if pci_id.startswith("0"):
                                    pci_id = pci_id[1:]
                                pci_ids.append(pci_id)
                                
                            # Check if any of the GPUs are passed through
                            for gpu in gpu_result["gpus"]:
                                if gpu["pci_id"] in pci_ids:
                                    vms_with_gpu.append({
                                        "vm_id": vm["vmid"],
                                        "name": vm.get("name", f"VM {vm['vmid']}"),
                                        "status": vm.get("status", "unknown"),
                                        "gpu": gpu["name"],
                                        "pci_id": gpu["pci_id"]
                                    })
                                    break
            
            return {
                "success": True,
                "node": node_name,
                "gpus": gpu_result["gpus"],
                "vfio_loaded": gpu_result["vfio_loaded"],
                "iommu_enabled": gpu_result["iommu_enabled"],
                "vms_with_gpu": vms_with_gpu
            }
        except Exception as e:
            logger.error(f"Error getting passthrough status: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get passthrough status: {str(e)}"
            }
