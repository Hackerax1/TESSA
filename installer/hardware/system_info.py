import platform
import psutil
import subprocess
import re
import logging
import os
import socket
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SystemInfoManager:
    @staticmethod
    def get_system_info() -> Dict[str, str]:
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

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
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

    @staticmethod
    def get_memory_info() -> Dict[str, int]:
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

    @staticmethod
    def get_virtualization_info() -> Dict[str, Any]:
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