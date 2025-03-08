import psutil
import platform
import json
import subprocess
import re
import logging
import os
import sys
import socket
import shutil
import urllib.request
import tempfile
from typing import Dict, List, Optional, Tuple, Any, NamedTuple, Set

logger = logging.getLogger(__name__)

class HardwareCompatibility(NamedTuple):
    """Result of hardware compatibility check with possible fallback options."""
    component: str
    is_compatible: bool
    message: str
    severity: str  # 'critical', 'warning', or 'info'
    fallback_available: bool
    fallback_option: Optional[str] = None
    fallback_description: Optional[str] = None

class DriverInfo(NamedTuple):
    """Information about a hardware driver."""
    device_id: str           # PCI/USB ID or other identifier
    device_name: str         # Human-readable device name
    driver_name: str         # Current driver name if installed, or recommended driver
    is_installed: bool       # Whether the driver is currently installed
    status: str              # 'working', 'missing', 'outdated', etc.
    install_method: str      # How to install: 'package', 'module', 'firmware', etc.
    package_name: Optional[str] = None  # Package name if applicable
    source_url: Optional[str] = None    # Source URL for manual download
    install_commands: Optional[List[str]] = None  # Commands to run for installation

class HardwareDetector:
    def __init__(self):
        self.system_info = self.get_system_info()
        self.cpu_info = self.get_cpu_info()
        self.memory_info = self.get_memory_info()
        self.disk_info = self.get_disk_info()
        self.gpu_info = self.get_gpu_info()
        self.network_info = self.get_network_info()
        self.virtualization_info = self.get_virtualization_info()
        self._driver_info_cache = None

    def get_system_info(self) -> Dict[str, str]:
        """Get basic system information."""
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn()
        }

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information."""
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "cpu_usage": psutil.cpu_percent(interval=1)
        }
        
        # Add CPU frequency if available
        try:
            freq = psutil.cpu_freq()
            if freq:
                cpu_info.update({
                    "max_frequency": freq.max,
                    "min_frequency": freq.min,
                    "current_frequency": freq.current
                })
        except Exception as e:
            logger.warning(f"Could not get CPU frequency: {str(e)}")
        
        # Try to get CPU model and additional details
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "cpu", "get", "Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed"],
                    capture_output=True, text=True, check=True
                )
                output = result.stdout.strip()
                lines = output.split('\n')
                if len(lines) >= 2:
                    cpu_info["model"] = lines[1].split('  ')[0].strip()
            except Exception as e:
                logger.warning(f"Could not get detailed CPU info from wmic: {str(e)}")
        elif platform.system() == "Linux":
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                
                model_name = re.search(r'model name\s+:\s+(.*)', cpuinfo)
                if model_name:
                    cpu_info["model"] = model_name.group(1)
                
                # Get CPU flags for feature detection
                flags = re.search(r'flags\s+:\s+(.*)', cpuinfo)
                if flags:
                    cpu_info["flags"] = flags.group(1).split()
                    
                    # Check for virtualization support
                    cpu_info["virtualization_support"] = {
                        "vmx": "vmx" in cpu_info["flags"],  # Intel VT-x
                        "svm": "svm" in cpu_info["flags"],  # AMD-V
                        "available": any(flag in cpu_info["flags"] for flag in ["vmx", "svm"])
                    }
            except Exception as e:
                logger.warning(f"Could not read /proc/cpuinfo: {str(e)}")
        
        return cpu_info

    def get_memory_info(self) -> Dict[str, int]:
        """Get detailed memory information."""
        svmem = psutil.virtual_memory()
        memory_info = {
            "total": svmem.total,
            "available": svmem.available,
            "used": svmem.used,
            "percentage": svmem.percent
        }
        
        # Add swap information
        try:
            swap = psutil.swap_memory()
            memory_info["swap"] = {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percentage": swap.percent
            }
        except Exception as e:
            logger.warning(f"Could not get swap information: {str(e)}")
            
        return memory_info

    def get_disk_info(self) -> List[Dict[str, Any]]:
        """Get detailed disk information for all partitions."""
        partitions = psutil.disk_partitions()
        disk_info = []
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partition_info = {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percentage": usage.percent
                }
                
                # Add additional disk performance metrics if available
                try:
                    if platform.system() == "Windows":
                        # For Windows, we can get disk IO counters
                        disk_io = psutil.disk_io_counters(perdisk=True)
                        drive_letter = partition.device.rstrip(':\\')
                        if drive_letter in disk_io:
                            io_info = disk_io[drive_letter]
                            partition_info["io_counters"] = {
                                "read_count": io_info.read_count,
                                "write_count": io_info.write_count,
                                "read_bytes": io_info.read_bytes,
                                "write_bytes": io_info.write_bytes
                            }
                except Exception as e:
                    logger.debug(f"Could not get disk IO counters: {str(e)}")
                
                disk_info.append(partition_info)
            except PermissionError:
                # Skip partitions we don't have access to
                logger.debug(f"Permission denied for partition: {partition.mountpoint}")
            except Exception as e:
                logger.warning(f"Error getting disk usage for {partition.mountpoint}: {str(e)}")
                
        return disk_info

    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get information about installed GPUs."""
        gpu_info = []
        
        if platform.system() == "Windows":
            try:
                # Try to get GPU info using Windows Management Instrumentation
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM,DriverVersion"],
                    capture_output=True, text=True, check=True
                )
                output = result.stdout.strip()
                lines = output.split('\n')
                
                # Skip header line
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split('  ')
                        parts = [p for p in parts if p.strip()]
                        if len(parts) >= 1:
                            gpu = {"name": parts[0].strip()}
                            if len(parts) >= 2 and parts[1].strip().isdigit():
                                gpu["memory"] = int(parts[1].strip())
                            if len(parts) >= 3:
                                gpu["driver_version"] = parts[2].strip()
                            gpu_info.append(gpu)
            except Exception as e:
                logger.warning(f"Could not get GPU information: {str(e)}")
        
        elif platform.system() == "Linux":
            try:
                # Check if lspci is available
                if os.system("which lspci > /dev/null 2>&1") == 0:
                    result = subprocess.run(
                        ["lspci", "-v", "-nn"],
                        capture_output=True, text=True, check=True
                    )
                    output = result.stdout
                    
                    # Look for VGA compatible controllers
                    vga_controllers = re.finditer(r'VGA compatible controller.*?(?=^\S)', output, re.MULTILINE | re.DOTALL)
                    for controller in vga_controllers:
                        controller_text = controller.group(0)
                        
                        # Extract name
                        name_match = re.search(r'VGA compatible controller: (.*?) \[', controller_text)
                        if name_match:
                            gpu = {"name": name_match.group(1).strip()}
                            
                            # Try to extract memory information
                            memory_match = re.search(r'Memory at .* \[size=(\d+)([KMG])B\]', controller_text)
                            if memory_match:
                                size = int(memory_match.group(1))
                                unit = memory_match.group(2)
                                if unit == 'G':
                                    size *= 1024 * 1024 * 1024
                                elif unit == 'M':
                                    size *= 1024 * 1024
                                elif unit == 'K':
                                    size *= 1024
                                gpu["memory"] = size
                                
                            gpu_info.append(gpu)
            except Exception as e:
                logger.warning(f"Could not get GPU information: {str(e)}")
                
        return gpu_info

    def get_network_info(self) -> Dict[str, Any]:
        """Get information about network interfaces."""
        network_info = {
            "interfaces": [],
            "hostname": socket.gethostname()
        }
        
        # Try to get external IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            network_info["primary_ip"] = s.getsockname()[0]
            s.close()
        except Exception as e:
            logger.debug(f"Could not determine primary IP: {str(e)}")
        
        # Get interface details
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for interface_name, addresses in interfaces.items():
            interface_info = {
                "name": interface_name,
                "addresses": [],
                "is_up": False
            }
            
            # Add status information if available
            if interface_name in stats:
                stat = stats[interface_name]
                interface_info.update({
                    "is_up": stat.isup,
                    "speed": stat.speed,
                    "mtu": stat.mtu,
                    "duplex": stat.duplex if hasattr(stat, 'duplex') else None
                })
            
            # Add address information
            for address in addresses:
                addr_info = {
                    "family": str(address.family),
                    "address": address.address
                }
                
                if hasattr(address, 'netmask') and address.netmask:
                    addr_info["netmask"] = address.netmask
                    
                if hasattr(address, 'broadcast') and address.broadcast:
                    addr_info["broadcast"] = address.broadcast
                    
                interface_info["addresses"].append(addr_info)
                
            network_info["interfaces"].append(interface_info)
            
        return network_info

    def get_virtualization_info(self) -> Dict[str, Any]:
        """Detect virtualization capabilities and status."""
        virt_info = {
            "is_virtual_machine": False,
            "virtualization_support": False,
            "virtualization_type": None
        }
        
        # Check if running in a VM
        if platform.system() == "Linux":
            try:
                # Check if systemd-detect-virt is available
                result = subprocess.run(
                    ["systemd-detect-virt"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    virt_info["is_virtual_machine"] = True
                    virt_info["virtualization_type"] = result.stdout.strip()
            except Exception:
                # Try alternative method
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                    
                    # Check for hypervisor flag
                    if re.search(r'hypervisor', cpuinfo, re.IGNORECASE):
                        virt_info["is_virtual_machine"] = True
                except Exception as e:
                    logger.debug(f"Could not check virtualization status: {str(e)}")
        
        elif platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["systeminfo"],
                    capture_output=True, text=True, check=True
                )
                output = result.stdout
                
                # Check for Hyper-V or other virtualization platforms
                if re.search(r'hyper-v', output, re.IGNORECASE) or \
                   re.search(r'vmware', output, re.IGNORECASE) or \
                   re.search(r'virtualbox', output, re.IGNORECASE) or \
                   re.search(r'kvm', output, re.IGNORECASE):
                    virt_info["is_virtual_machine"] = True
                
                # Check for virtualization support
                if re.search(r'virtualization.*enabled', output, re.IGNORECASE):
                    virt_info["virtualization_support"] = True
            except Exception as e:
                logger.debug(f"Could not check virtualization status: {str(e)}")
        
        return virt_info

    def check_hardware_compatibility(self) -> List[HardwareCompatibility]:
        """
        Check if the hardware is compatible with Proxmox and provide fallback options
        for partially compatible components.
        
        Returns:
            List of HardwareCompatibility objects, each describing a component's
            compatibility status and fallback options if available.
        """
        compatibility_results = []
        
        # Check CPU virtualization support
        cpu_virt_available = False
        if "virtualization_support" in self.cpu_info and isinstance(self.cpu_info["virtualization_support"], dict):
            cpu_virt_available = self.cpu_info["virtualization_support"].get("available", False)
        
        if not cpu_virt_available:
            compatibility_results.append(
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
            compatibility_results.append(
                HardwareCompatibility(
                    component="CPU Virtualization",
                    is_compatible=True,
                    message="CPU supports hardware virtualization",
                    severity="info",
                    fallback_available=False
                )
            )
        
        # Check CPU cores
        min_cores = 2
        cpu_cores = self.cpu_info.get("physical_cores", 1) or 1
        
        if cpu_cores < min_cores:
            compatibility_results.append(
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
            compatibility_results.append(
                HardwareCompatibility(
                    component="CPU Cores",
                    is_compatible=True,
                    message=f"CPU has {cpu_cores} core(s), which meets the minimum requirement of {min_cores}",
                    severity="info",
                    fallback_available=False
                )
            )
        
        # Check RAM
        min_ram_gb = 4
        total_ram_bytes = self.memory_info.get("total", 0)
        total_ram_gb = total_ram_bytes / (1024**3)
        
        if total_ram_gb < min_ram_gb:
            compatibility_results.append(
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
            compatibility_results.append(
                HardwareCompatibility(
                    component="RAM",
                    is_compatible=True,
                    message=f"System has {total_ram_gb:.1f} GB RAM, which meets the minimum requirement of {min_ram_gb} GB",
                    severity="info",
                    fallback_available=False
                )
            )
        
        # Check Disk Space
        min_disk_gb = 32
        largest_free_space = 0
        
        for disk in self.disk_info:
            free_space_gb = disk.get("free", 0) / (1024**3)
            largest_free_space = max(largest_free_space, free_space_gb)
        
        if largest_free_space < min_disk_gb:
            compatibility_results.append(
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
            compatibility_results.append(
                HardwareCompatibility(
                    component="Disk Space",
                    is_compatible=True,
                    message=f"System has {largest_free_space:.1f} GB free space, which meets the minimum requirement of {min_disk_gb} GB",
                    severity="info",
                    fallback_available=False
                )
            )
        
        # Check Network Interfaces
        has_network = False
        
        for interface in self.network_info.get("interfaces", []):
            if interface.get("is_up", False) and interface.get("name", "") != "lo" and interface.get("name", "").lower() != "loopback":
                has_network = True
                break
        
        if not has_network:
            compatibility_results.append(
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
                compatibility_results.append(
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
                compatibility_results.append(
                    HardwareCompatibility(
                        component="Network Interfaces",
                        is_compatible=True,
                        message="Active network interfaces detected",
                        severity="info",
                        fallback_available=False
                    )
                )

        # Check for GPU passthrough capabilities
        has_gpu = len(self.gpu_info) > 0
        if has_gpu:
            # IOMMU check is more complex and depends on the motherboard and BIOS settings
            # For now, we'll just suggest a fallback based on the presence of a GPU
            compatibility_results.append(
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

        return compatibility_results

    def apply_fallback_configuration(self, component: str, fallback_option: str) -> Dict[str, Any]:
        """
        Apply a specific fallback configuration for a hardware component.
        
        Args:
            component: The hardware component name (e.g., "CPU", "RAM")
            fallback_option: The specific fallback option to apply
            
        Returns:
            Dict containing the result of the fallback application
        """
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
                        # Note: Actual swap creation would happen elsewhere via setup scripts
                
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

    def get_driver_info(self) -> List[DriverInfo]:
        """
        Get information about installed and missing drivers.
        
        Returns:
            A list of DriverInfo objects with driver details.
        """
        if self._driver_info_cache is not None:
            return self._driver_info_cache
            
        driver_info = []
        
        if platform.system() == "Linux":
            # Get PCI device information
            driver_info.extend(self._get_linux_pci_drivers())
            
            # Get USB device information that might need drivers
            driver_info.extend(self._get_linux_usb_drivers())
            
            # Check for missing firmware packages
            driver_info.extend(self._get_linux_firmware_status())
            
        elif platform.system() == "Windows":
            # Get Windows driver information
            driver_info.extend(self._get_windows_drivers())
            
        self._driver_info_cache = driver_info
        return driver_info

    def _get_linux_pci_drivers(self) -> List[DriverInfo]:
        """Get driver information for PCI devices on Linux."""
        drivers = []
        
        try:
            if shutil.which("lspci") is not None:
                # First get the detailed PCI info
                result = subprocess.run(
                    ["lspci", "-vvv"],
                    capture_output=True, text=True, check=True
                )
                
                # Parse the output
                devices = re.split(r'\n(?=\S)', result.stdout)
                
                for device in devices:
                    match = re.match(r'^(\S+)\s+(.*?)(?=:|$)', device)
                    if not match:
                        continue
                        
                    pci_id = match.group(1).strip()
                    device_name = match.group(2).strip()
                    
                    # Extract driver information
                    kernel_driver = re.search(r'Kernel driver in use: (\S+)', device)
                    kernel_modules = re.search(r'Kernel modules: (.*?)(?=\n\S|\n\Z|$)', device)
                    
                    if kernel_driver:
                        driver_name = kernel_driver.group(1)
                        status = "working"
                        is_installed = True
                    elif kernel_modules:
                        # Driver is available but not in use
                        driver_name = kernel_modules.group(1).strip().split()[0]  # Use the first available module
                        status = "available_not_loaded"
                        is_installed = False
                    else:
                        # No driver information
                        driver_name = "unknown"
                        status = "missing"
                        is_installed = False
                    
                    # Determine installation method and package for missing drivers
                    install_method = "package"
                    package_name = None
                    install_commands = None
                    
                    if not is_installed:
                        package_name = self._find_linux_driver_package(driver_name, device_name)
                        
                        if package_name:
                            install_commands = [f"apt-get install -y {package_name}"]
                        else:
                            install_method = "module"
                            install_commands = [f"modprobe {driver_name}"]
                    
                    drivers.append(DriverInfo(
                        device_id=pci_id,
                        device_name=device_name,
                        driver_name=driver_name,
                        is_installed=is_installed,
                        status=status,
                        install_method=install_method,
                        package_name=package_name,
                        install_commands=install_commands
                    ))
        except Exception as e:
            logger.warning(f"Error getting PCI driver information: {str(e)}")
            
        return drivers

    def _get_linux_usb_drivers(self) -> List[DriverInfo]:
        """Get driver information for USB devices on Linux."""
        drivers = []
        
        try:
            if shutil.which("lsusb") is not None:
                # Get USB devices
                result = subprocess.run(
                    ["lsusb", "-v"],
                    capture_output=True, text=True, check=True
                )
                
                # Parse the output
                devices = re.split(r'\n(?=Bus\s+\d+\s+Device\s+\d+:)', result.stdout)
                
                for device in devices:
                    match = re.match(r'Bus\s+\d+\s+Device\s+\d+:\s+ID\s+([0-9a-fA-F:]+)\s+(.*?)$', device, re.MULTILINE)
                    if not match:
                        continue
                        
                    usb_id = match.group(1).strip()
                    device_name = match.group(2).strip()
                    
                    # Check if the device has a driver
                    driver_match = re.search(r'iInterface\s+\d+\s*\n.*?Driver=(.*?)(?:\s|$)', device, re.DOTALL)
                    
                    if driver_match and driver_match.group(1) != "(none)":
                        driver_name = driver_match.group(1)
                        status = "working"
                        is_installed = True
                    else:
                        # No driver or driver is (none)
                        # Try to find a recommended driver
                        driver_name = self._find_recommended_usb_driver(usb_id, device)
                        if driver_name:
                            status = "missing"
                            is_installed = False
                        else:
                            driver_name = "unknown"
                            status = "no_driver_needed"
                            is_installed = True  # No driver needed is effectively "installed"
                    
                    # Only include devices that need drivers and don't have them
                    if status == "missing":
                        package_name = self._find_linux_driver_package(driver_name, device_name)
                        
                        install_method = "package"
                        install_commands = None
                        
                        if package_name:
                            install_commands = [f"apt-get install -y {package_name}"]
                        
                        drivers.append(DriverInfo(
                            device_id=usb_id,
                            device_name=device_name,
                            driver_name=driver_name,
                            is_installed=is_installed,
                            status=status,
                            install_method=install_method,
                            package_name=package_name,
                            install_commands=install_commands
                        ))
        except Exception as e:
            logger.warning(f"Error getting USB driver information: {str(e)}")
            
        return drivers

    def _find_recommended_usb_driver(self, usb_id: str, device_info: str) -> Optional[str]:
        """Find a recommended driver for a USB device based on ID and device info."""
        # This is a simplified implementation. In a real-world scenario,
        # this would query a database or use more sophisticated logic.
        
        # Extract vendor:product ID
        vendor_product = usb_id.lower()
        
        # Common USB device types and their drivers
        # Format: (id_pattern, device_pattern, driver_name)
        usb_driver_map = [
            # USB WiFi adapters
            (r"0bda:.*", r"(wireless|wifi|wlan|802\.11)", "rtl8192cu"),
            (r"148f:.*", r"(wireless|wifi|wlan|802\.11)", "rt2800usb"),
            (r"7392:.*", r"(wireless|wifi|wlan|802\.11)", "rtl8192cu"),
            
            # USB Ethernet adapters
            (r"0b95:.*", r"ethernet|network", "asix"),
            (r"0b95:1780", r"ethernet|network", "asix"),
            (r"0bda:8152", r"ethernet|network", "r8152"),
            
            # USB Bluetooth adapters
            (r".*", r"bluetooth", "btusb"),
            
            # USB storage controllers
            (r".*", r"storage|mass storage", "usb-storage"),
            
            # USB serial adapters
            (r"067b:.*", r"serial|converter", "ftdi_sio"),
            (r"0403:.*", r"serial|converter", "ftdi_sio"),
            (r"10c4:.*", r"serial|converter", "cp210x"),
        ]
        
        device_info_lower = device_info.lower()
        
        for id_pattern, device_pattern, driver in usb_driver_map:
            if (re.match(id_pattern, vendor_product) and 
                re.search(device_pattern, device_info_lower)):
                return driver
                
        return None

    def _get_linux_firmware_status(self) -> List[DriverInfo]:
        """Check for missing firmware packages on Linux."""
        drivers = []
        
        try:
            # Common firmware packages needed for various hardware
            firmware_packages = [
                "firmware-linux",
                "firmware-linux-nonfree",
                "firmware-misc-nonfree",
                "firmware-iwlwifi",
                "firmware-realtek",
                "firmware-atheros",
                "firmware-bnx2",
                "firmware-bnx2x",
                "firmware-brcm80211"
            ]
            
            # Distribution-specific adjustments
            if os.path.exists("/etc/debian_version"):
                pass  # Use default packages for Debian
            elif os.path.exists("/etc/redhat-release"):
                firmware_packages = ["linux-firmware"]  # RHEL/CentOS/Fedora
            elif os.path.exists("/etc/arch-release"):
                firmware_packages = ["linux-firmware"]  # Arch Linux
            
            # Check if the packages are installed
            installed_packages = set()
            
            if shutil.which("dpkg") is not None:
                # Debian/Ubuntu
                result = subprocess.run(
                    ["dpkg", "-l"],
                    capture_output=True, text=True, check=True
                )
                
                for line in result.stdout.splitlines():
                    if line.startswith("ii "):
                        parts = line.split()
                        if len(parts) >= 2:
                            installed_packages.add(parts[1])
            elif shutil.which("rpm") is not None:
                # RHEL/CentOS/Fedora
                result = subprocess.run(
                    ["rpm", "-qa"],
                    capture_output=True, text=True, check=True
                )
                
                installed_packages.update(result.stdout.splitlines())
            elif shutil.which("pacman") is not None:
                # Arch Linux
                result = subprocess.run(
                    ["pacman", "-Q"],
                    capture_output=True, text=True, check=True
                )
                
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if parts:
                        installed_packages.add(parts[0])
            
            # Check for missing firmware packages that might be needed
            for package in firmware_packages:
                is_installed = any(package in pkg for pkg in installed_packages)
                
                if not is_installed:
                    # Determine the installation command
                    install_cmd = ""
                    if shutil.which("apt-get") is not None:
                        install_cmd = f"apt-get install -y {package}"
                    elif shutil.which("yum") is not None:
                        install_cmd = f"yum install -y {package}"
                    elif shutil.which("dnf") is not None:
                        install_cmd = f"dnf install -y {package}"
                    elif shutil.which("pacman") is not None:
                        install_cmd = f"pacman -S --noconfirm {package}"
                    
                    drivers.append(DriverInfo(
                        device_id="firmware",
                        device_name=f"System Firmware ({package})",
                        driver_name=package,
                        is_installed=is_installed,
                        status="missing",
                        install_method="package",
                        package_name=package,
                        install_commands=[install_cmd] if install_cmd else None
                    ))
                    
        except Exception as e:
            logger.warning(f"Error checking firmware packages: {str(e)}")
            
        return drivers

    def _find_linux_driver_package(self, driver_name: str, device_name: str) -> Optional[str]:
        """Find the appropriate package for a driver on Linux."""
        # This is a simplified implementation. In a real-world scenario,
        # this would query the package database or use more sophisticated matching.
        
        # Common driver to package mappings for major distributions
        driver_package_map = {
            # Network drivers
            "r8169": "r8168-dkms" if "Realtek" in device_name else None,
            "e1000e": "linux-modules-extra-$(uname -r)",
            "iwlwifi": "firmware-iwlwifi",
            "ath9k": "firmware-atheros",
            "rtl8192cu": "firmware-realtek",
            "rt2800usb": "firmware-misc-nonfree",
            
            # GPU drivers
            "nouveau": None,  # Built into the kernel
            "radeon": None,   # Built into the kernel
            "amdgpu": "firmware-amd-graphics",
            "i915": "firmware-misc-nonfree",
            "nvidia": "nvidia-driver",
            
            # Storage drivers
            "ahci": None,     # Built into the kernel
            "nvme": None,     # Built into the kernel
            
            # USB controllers
            "xhci_hcd": None, # Built into the kernel
            "ehci_hcd": None, # Built into the kernel
            "ohci_hcd": None, # Built into the kernel
            
            # Other common drivers
            "snd_hda_intel": "firmware-misc-nonfree",
            "btusb": "firmware-misc-nonfree"
        }
        
        return driver_package_map.get(driver_name)

    def _get_windows_drivers(self) -> List[DriverInfo]:
        """Get driver information for devices on Windows."""
        drivers = []
        
        try:
            if shutil.which("powershell.exe") is not None:
                # Use PowerShell to query devices with problems
                result = subprocess.run(
                    ["powershell.exe", "-Command", "Get-PnpDevice | Where-Object { $_.Status -ne 'OK' }"],
                    capture_output=True, text=True, check=True
                )
                
                # Process the output
                lines = result.stdout.strip().split('\n')
                
                current_device = None
                device_id = None
                device_name = None
                status = None
                
                for line in lines:
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    if "Status" in line and "DeviceID" in line and "Class" in line:
                        # This is a header line, skip it
                        continue
                        
                    if "--" in line and "----" in line:
                        # This is a separator line, skip it
                        continue
                    
                    # This should be a device line
                    parts = line.split()
                    if len(parts) >= 3:
                        status_val = parts[0]
                        device_id = parts[-1]
                        device_name = " ".join(parts[1:-1])
                        
                        # Map Windows status to our status
                        status_map = {
                            "Error": "error",
                            "Unknown": "missing",
                            "Degraded": "outdated"
                        }
                        
                        status = status_map.get(status_val, "issue")
                        
                        # For Windows, we recommend automatic update or manual download
                        drivers.append(DriverInfo(
                            device_id=device_id,
                            device_name=device_name,
                            driver_name="Unknown",
                            is_installed=False,
                            status=status,
                            install_method="windows_update",
                            package_name=None,
                            install_commands=["Start-Process ms-settings:windowsupdate"]
                        ))
                        
                # If no problematic devices were found but we need hardware IDs,
                # we can get a list of all devices for informational purposes
                if not drivers:
                    # This is optional and can be resource-intensive, so we'll skip it for now
                    pass
                        
        except Exception as e:
            logger.warning(f"Error getting Windows driver information: {str(e)}")
            
        return drivers

    def install_driver(self, driver_info: DriverInfo) -> Dict[str, Any]:
        """
        Attempt to install a driver.
        
        Args:
            driver_info: DriverInfo object containing driver details
            
        Returns:
            Dict with installation results
        """
        result = {
            "success": False,
            "message": "",
            "device": driver_info.device_name,
            "commands_run": []
        }
        
        try:
            if not driver_info.install_commands:
                result["message"] = "No installation commands available for this driver."
                return result
                
            # Execute the installation commands
            for cmd in driver_info.install_commands:
                cmd_parts = cmd.split()
                cmd_result = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True
                )
                
                result["commands_run"].append({
                    "command": cmd,
                    "returncode": cmd_result.returncode,
                    "stdout": cmd_result.stdout,
                    "stderr": cmd_result.stderr
                })
                
                if cmd_result.returncode != 0:
                    result["message"] = f"Command failed: {cmd}"
                    return result
            
            # Verify installation by checking driver info again
            self._driver_info_cache = None  # Clear cache to force refresh
            updated_drivers = self.get_driver_info()
            
            # Find the same device in updated list
            for updated_driver in updated_drivers:
                if (updated_driver.device_id == driver_info.device_id and
                    updated_driver.device_name == driver_info.device_name):
                    
                    if updated_driver.is_installed:
                        result["success"] = True
                        result["message"] = f"Driver {driver_info.driver_name} installed successfully."
                    else:
                        result["message"] = f"Driver installation completed but driver still shows as not installed."
                    
                    return result
            
            # If we get here, we couldn't verify
            result["success"] = True  # Assume success since commands executed without error
            result["message"] = "Driver installation commands completed, but couldn't verify installation status."
            
        except Exception as e:
            result["message"] = f"Error installing driver: {str(e)}"
            logger.error(f"Driver installation error: {str(e)}", exc_info=True)
            
        return result

    def get_hardware_summary(self) -> Dict[str, Any]:
        """Get a complete summary of all hardware information."""
        return {
            "system_info": self.system_info,
            "cpu_info": self.cpu_info,
            "memory_info": self.memory_info,
            "disk_info": self.disk_info,
            "gpu_info": self.gpu_info,
            "network_info": self.network_info,
            "virtualization_info": self.virtualization_info,
            "compatibility": self.check_hardware_compatibility(),
            "drivers": self.get_driver_info()
        }

    def save_summary_to_file(self, file_path="hardware_summary.json"):
        """Save the hardware summary to a JSON file."""
        summary = self.get_hardware_summary()
        
        # Convert NamedTuple objects to dictionaries
        if "compatibility" in summary:
            summary["compatibility"] = [comp._asdict() for comp in summary["compatibility"]]
            
        if "drivers" in summary:
            summary["drivers"] = [driver._asdict() for driver in summary["drivers"]]
            
        with open(file_path, "w") as file:
            json.dump(summary, file, indent=4)
        logger.info(f"Hardware summary saved to {file_path}")
        return file_path

if __name__ == "__main__":
    detector = HardwareDetector()
    detector.save_summary_to_file()