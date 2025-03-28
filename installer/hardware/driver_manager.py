import platform
import subprocess
import re
import logging
import os
import shutil
from typing import Dict, List, Optional, Any, Set

from .types import DriverInfo

logger = logging.getLogger(__name__)

class DriverManager:
    def __init__(self):
        self._driver_info_cache = None

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

    def _get_linux_pci_drivers(self) -> List[DriverInfo]:
        """Get PCI device driver information on Linux."""
        drivers = []
        try:
            if platform.system() != "Linux" or not shutil.which("lspci"):
                return drivers

            result = subprocess.run(["lspci", "-vvv"], capture_output=True, text=True)
            if result.returncode == 0:
                current_device = None
                for line in result.stdout.split('\n'):
                    if line and not line.startswith('\t') and not line.startswith(' '):  # New device
                        if current_device:
                            drivers.append(current_device)
                        device_match = re.match(r'.*?: (.+)', line)
                        if device_match:
                            current_device = DriverInfo(
                                device_id="",
                                device_name=device_match.group(1).strip(),
                                driver_name="",
                                is_installed=False,
                                status="unknown"
                            )
                    elif current_device and "Kernel driver in use:" in line:
                        driver = line.split("Kernel driver in use:")[1].strip()
                        current_device.driver_name = driver
                        current_device.is_installed = True
                        current_device.status = "working"

                if current_device:  # Add the last device
                    drivers.append(current_device)

            return drivers
        except Exception as e:
            logger.error(f"Error getting Linux PCI drivers: {str(e)}")
            return drivers

    def _get_linux_usb_drivers(self) -> List[DriverInfo]:
        """Get USB device driver information on Linux."""
        drivers = []
        try:
            if platform.system() != "Linux" or not shutil.which("lsusb"):
                return drivers

            result = subprocess.run(["lsusb", "-v"], capture_output=True, text=True)
            if result.returncode == 0:
                current_device = None
                for line in result.stdout.split('\n'):
                    if "Bus " in line and "Device " in line:  # New device
                        if current_device:
                            drivers.append(current_device)
                        device_match = re.search(r'ID \w+:\w+\s+(.+)', line)
                        if device_match:
                            current_device = DriverInfo(
                                device_id="",
                                device_name=device_match.group(1).strip(),
                                driver_name="",
                                is_installed=False,
                                status="missing"
                            )
                    elif current_device and "Driver=" in line:
                        driver = line.split("Driver=")[1].strip()
                        if driver != "(none)":
                            current_device.driver_name = driver
                            current_device.is_installed = True
                            current_device.status = "working"

                if current_device:  # Add the last device
                    drivers.append(current_device)

            return drivers
        except Exception as e:
            logger.error(f"Error getting Linux USB drivers: {str(e)}")
            return drivers

    def _get_linux_firmware_status(self) -> List[DriverInfo]:
        """Get Linux firmware package status."""
        drivers = []
        try:
            if platform.system() != "Linux":
                return drivers
                
            # Check for common firmware package management tools
            if shutil.which("dmesg"):
                # Look for firmware loading errors in dmesg
                result = subprocess.run(["dmesg"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "firmware" in line.lower() and "failed" in line.lower():
                            # Extract device information from the error message
                            match = re.search(r'firmware: failed to load ([^\s]+)', line, re.IGNORECASE)
                            if match:
                                firmware_name = match.group(1)
                                drivers.append(DriverInfo(
                                    device_id="",
                                    device_name=f"Unknown device ({firmware_name})",
                                    driver_name=firmware_name,
                                    is_installed=False,
                                    status="missing",
                                    install_method="package_manager",
                                    package_name=f"firmware-{firmware_name}",
                                    install_commands=["apt-get update", f"apt-get install -y firmware-{firmware_name}"]
                                ))
            
            return drivers
        except Exception as e:
            logger.error(f"Error checking Linux firmware status: {str(e)}")
            return drivers

    def _get_windows_drivers(self) -> List[DriverInfo]:
        """Get device driver information on Windows."""
        drivers = []
        try:
            if platform.system() != "Windows" or not shutil.which("powershell.exe"):
                return drivers

            cmd = ["powershell.exe", "Get-PnpDevice | Format-Table Status,DeviceID,Class,FriendlyName -AutoSize"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                # Skip header lines
                data_lines = []
                for i, line in enumerate(lines):
                    if "------" in line:  # Found separator line
                        data_lines = lines[i+1:]
                        break
                
                if not data_lines and len(lines) >= 3:  # If we didn't find separator, try using lines after header
                    data_lines = lines[3:]
                
                for line in data_lines:
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        status, device_id, device_class, friendly_name = parts
                        drivers.append(DriverInfo(
                            device_id=device_id,
                            device_name=friendly_name,
                            driver_name="",
                            is_installed=status.lower() not in ["error", "unknown"],
                            status=status.lower(),
                            install_method="windows_update"
                        ))

            return drivers
        except Exception as e:
            logger.error(f"Error getting Windows drivers: {str(e)}")
            return drivers