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
                        driver_name = kernel_modules.group(1).strip().split()[0]  # Use first available module
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
                        
        except Exception as e:
            logger.warning(f"Error getting Windows driver information: {str(e)}")
            
        return drivers