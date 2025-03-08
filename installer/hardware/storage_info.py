import platform
import psutil
import subprocess
import re
import logging
import os
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class StorageInfoManager:
    @staticmethod
    def get_disk_info() -> List[Dict[str, Any]]:
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

    @staticmethod
    def get_gpu_info() -> List[Dict[str, Any]]:
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