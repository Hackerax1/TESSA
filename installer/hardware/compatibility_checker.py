import platform
import logging
from typing import Dict, List, Any

from .types import HardwareCompatibility

logger = logging.getLogger(__name__)

class CompatibilityChecker:
    def __init__(self, system_info: Dict[str, str], cpu_info: Dict[str, Any], 
                 memory_info: Dict[str, Any], disk_info: List[Dict[str, Any]], 
                 gpu_info: List[Dict[str, Any]], network_info: Dict[str, Any]):
        self.system_info = system_info
        self.cpu_info = cpu_info
        self.memory_info = memory_info
        self.disk_info = disk_info
        self.gpu_info = gpu_info
        self.network_info = network_info

    def check_hardware_compatibility(self) -> List[HardwareCompatibility]:
        """Check if the hardware is compatible with Proxmox and provide fallback options."""
        compatibility_results = []
        
        self._check_cpu_virtualization(compatibility_results)
        self._check_cpu_cores(compatibility_results)
        self._check_ram(compatibility_results)
        self._check_disk_space(compatibility_results)
        self._check_network(compatibility_results)
        self._check_gpu_passthrough(compatibility_results)

        return compatibility_results

    def _check_cpu_virtualization(self, results: List[HardwareCompatibility]):
        """Check CPU virtualization support."""
        cpu_virt_available = False
        if "virtualization_support" in self.cpu_info and isinstance(self.cpu_info["virtualization_support"], dict):
            cpu_virt_available = self.cpu_info["virtualization_support"].get("available", False)
        
        if not cpu_virt_available:
            results.append(
                HardwareCompatibility(
                    component="CPU Virtualization",
                    is_compatible=False,
                    message="CPU doesn't support hardware virtualization (VT-x/AMD-V)",
                    severity="critical",
                    fallback_available=True,
                    fallback_option="software_emulation",
                    fallback_description="Use software-based emulation (QEMU without KVM). Warning: Performance will be significantly reduced."
                )
            )
        else:
            results.append(
                HardwareCompatibility(
                    component="CPU Virtualization",
                    is_compatible=True,
                    message="CPU supports hardware virtualization",
                    severity="info",
                    fallback_available=False
                )
            )

    def _check_cpu_cores(self, results: List[HardwareCompatibility]):
        """Check CPU core count."""
        min_cores = 2
        cpu_cores = self.cpu_info.get("physical_cores", 1) or 1
        
        if cpu_cores < min_cores:
            results.append(
                HardwareCompatibility(
                    component="CPU Cores",
                    is_compatible=False,
                    message=f"CPU has only {cpu_cores} core(s), minimum recommended is {min_cores}",
                    severity="warning",
                    fallback_available=True,
                    fallback_option="limited_vm_count",
                    fallback_description=f"Limit the number of VMs and containers running simultaneously. Consider using lightweight containers instead of full VMs."
                )
            )
        else:
            results.append(
                HardwareCompatibility(
                    component="CPU Cores",
                    is_compatible=True,
                    message=f"CPU has {cpu_cores} core(s), which meets the minimum requirement of {min_cores}",
                    severity="info",
                    fallback_available=False
                )
            )

    def _check_ram(self, results: List[HardwareCompatibility]):
        """Check RAM capacity."""
        min_ram_gb = 4
        total_ram_bytes = self.memory_info.get("total", 0)
        total_ram_gb = total_ram_bytes / (1024**3)
        
        if total_ram_gb < min_ram_gb:
            results.append(
                HardwareCompatibility(
                    component="RAM",
                    is_compatible=False,
                    message=f"System has only {total_ram_gb:.1f} GB RAM, minimum recommended is {min_ram_gb} GB",
                    severity="warning",
                    fallback_available=True,
                    fallback_option="increase_swap",
                    fallback_description=f"Configure additional swap space (at least {min_ram_gb - total_ram_gb:.1f} GB more). Performance will be reduced when swap is used. Consider limiting VM memory usage and using lightweight containers."
                )
            )
        else:
            results.append(
                HardwareCompatibility(
                    component="RAM",
                    is_compatible=True,
                    message=f"System has {total_ram_gb:.1f} GB RAM, which meets the minimum requirement of {min_ram_gb} GB",
                    severity="info",
                    fallback_available=False
                )
            )

    def _check_disk_space(self, results: List[HardwareCompatibility]):
        """Check available disk space."""
        min_disk_gb = 32
        largest_free_space = 0
        
        for disk in self.disk_info:
            free_space_gb = disk.get("free", 0) / (1024**3)
            largest_free_space = max(largest_free_space, free_space_gb)
        
        if largest_free_space < min_disk_gb:
            results.append(
                HardwareCompatibility(
                    component="Disk Space",
                    is_compatible=False,
                    message=f"Maximum free disk space is only {largest_free_space:.1f} GB, minimum recommended is {min_disk_gb} GB",
                    severity="warning",
                    fallback_available=True,
                    fallback_option="external_storage",
                    fallback_description="Use external storage for VM disks or attach additional storage via iSCSI, NFS, or USB drives."
                )
            )
        else:
            results.append(
                HardwareCompatibility(
                    component="Disk Space",
                    is_compatible=True,
                    message=f"System has {largest_free_space:.1f} GB free space, which meets the minimum requirement of {min_disk_gb} GB",
                    severity="info",
                    fallback_available=False
                )
            )

    def _check_network(self, results: List[HardwareCompatibility]):
        """Check network interface availability and speed."""
        has_network = False
        
        for interface in self.network_info.get("interfaces", []):
            if interface.get("is_up", False) and interface.get("name", "") != "lo" and interface.get("name", "").lower() != "loopback":
                has_network = True
                break
        
        if not has_network:
            results.append(
                HardwareCompatibility(
                    component="Network Interfaces",
                    is_compatible=False,
                    message="No active network interfaces detected",
                    severity="critical",
                    fallback_available=True,
                    fallback_option="usb_network",
                    fallback_description="Add a USB network adapter. Alternatively, configure Wi-Fi if available (though wired connections are recommended for server use)."
                )
            )
        else:
            # Check if any interfaces have decent speed
            has_fast_network = False
            for interface in self.network_info.get("interfaces", []):
                if interface.get("is_up", False) and interface.get("speed", 0) >= 100:  # 100 Mbps or higher
                    has_fast_network = True
                    break
            
            if not has_fast_network:
                results.append(
                    HardwareCompatibility(
                        component="Network Speed",
                        is_compatible=False,
                        message="No high-speed network interfaces detected",
                        severity="warning",
                        fallback_available=True,
                        fallback_option="limit_network_services",
                        fallback_description="Network performance might be limited. Consider avoiding network-intensive services or adding a faster network card."
                    )
                )
            else:
                results.append(
                    HardwareCompatibility(
                        component="Network Interfaces",
                        is_compatible=True,
                        message="Active network interfaces detected",
                        severity="info",
                        fallback_available=False
                    )
                )

    def _check_gpu_passthrough(self, results: List[HardwareCompatibility]):
        """Check GPU passthrough capabilities."""
        has_gpu = len(self.gpu_info) > 0
        if has_gpu:
            # IOMMU check is more complex and depends on the motherboard and BIOS settings
            # For now, we'll just suggest a fallback based on the presence of a GPU
            results.append(
                HardwareCompatibility(
                    component="GPU Passthrough",
                    is_compatible=False,
                    message="GPU detected, but passthrough capability can't be automatically verified",
                    severity="info",
                    fallback_available=True,
                    fallback_option="gpu_limited_support",
                    fallback_description="GPU passthrough requires IOMMU support in CPU/motherboard and proper BIOS settings. If unsupported, you can still use GPU for host graphics and consider software rendering for VMs."
                )
            )

    def apply_fallback_configuration(self, component: str, fallback_option: str) -> Dict[str, Any]:
        """Apply a specific fallback configuration for a hardware component."""
        result = {
            "success": False,
            "message": "",
            "applied_changes": {}
        }
        
        try:
            if component == "RAM" and fallback_option == "increase_swap":
                # Create or expand swap file
                if platform.system() == "Linux":
                    # Check current swap
                    swap_info = self.memory_info.get("swap", {})
                    current_swap_gb = swap_info.get("total", 0) / (1024**3)
                    
                    # Determine how much swap to add
                    total_ram_gb = self.memory_info.get("total", 0) / (1024**3)
                    target_total_gb = max(4, total_ram_gb * 2)  # Double RAM or at least 4GB
                    additional_swap_needed = max(0, target_total_gb - current_swap_gb)
                    
                    if additional_swap_needed > 0:
                        # Just calculate the necessary swap, don't actually create it in this method
                        result["success"] = True
                        result["message"] = f"Calculated additional swap needed: {additional_swap_needed:.1f} GB"
                        result["applied_changes"] = {
                            "additional_swap_gb": additional_swap_needed,
                            "target_total_swap_gb": target_total_gb
                        }
                
            elif component == "CPU Virtualization" and fallback_option == "software_emulation":
                # Configure for software emulation
                result["success"] = True
                result["message"] = "Configured software emulation settings"
                result["applied_changes"] = {
                    "use_kvm": False,
                    "cpu_type": "qemu64",
                    "performance_warning": True
                }
                
            elif component == "Disk Space" and fallback_option == "external_storage":
                # Just indicate external storage will be used
                result["success"] = True
                result["message"] = "Configured for external storage use"
                result["applied_changes"] = {
                    "use_external_storage": True,
                    "setup_mount_points": True
                }
                
            elif component == "Network Interfaces" and fallback_option == "usb_network":
                # Cannot actually apply this automatically, just note the requirement
                result["success"] = True
                result["message"] = "USB network adapter required"
                result["applied_changes"] = {
                    "requires_usb_network": True
                }
                
            elif component == "CPU Cores" and fallback_option == "limited_vm_count":
                # Calculate recommended VM limits based on cores
                cpu_cores = self.cpu_info.get("physical_cores", 1) or 1
                recommended_vm_limit = max(1, cpu_cores - 1)
                
                result["success"] = True
                result["message"] = f"Limited VM count to {recommended_vm_limit}"
                result["applied_changes"] = {
                    "max_recommended_vms": recommended_vm_limit,
                    "use_containers": True
                }
                
            else:
                result["message"] = f"Unknown fallback option '{fallback_option}' for component '{component}'"
                
        except Exception as e:
            result["message"] = f"Error applying fallback: {str(e)}"
            logger.error(f"Fallback application error: {str(e)}", exc_info=True)
            
        return result