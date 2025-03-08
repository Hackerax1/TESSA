import psutil
import platform
import json
import subprocess
import re
import logging
import os
import sys
import socket
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class HardwareDetector:
    def __init__(self):
        self.system_info = self.get_system_info()
        self.cpu_info = self.get_cpu_info()
        self.memory_info = self.get_memory_info()
        self.disk_info = self.get_disk_info()
        self.gpu_info = self.get_gpu_info()
        self.network_info = self.get_network_info()
        self.virtualization_info = self.get_virtualization_info()

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

    def get_hardware_summary(self) -> Dict[str, Any]:
        """Get a complete summary of all hardware information."""
        return {
            "system_info": self.system_info,
            "cpu_info": self.cpu_info,
            "memory_info": self.memory_info,
            "disk_info": self.disk_info,
            "gpu_info": self.gpu_info,
            "network_info": self.network_info,
            "virtualization_info": self.virtualization_info
        }

    def save_summary_to_file(self, file_path="hardware_summary.json"):
        """Save the hardware summary to a JSON file."""
        summary = self.get_hardware_summary()
        with open(file_path, "w") as file:
            json.dump(summary, file, indent=4)
        logger.info(f"Hardware summary saved to {file_path}")
        return file_path

if __name__ == "__main__":
    detector = HardwareDetector()
    detector.save_summary_to_file()