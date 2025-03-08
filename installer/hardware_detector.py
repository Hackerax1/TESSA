import json
import logging
from typing import Dict, List, Any

from .hardware.types import HardwareCompatibility, DriverInfo
from .hardware.driver_manager import DriverManager
from .hardware.system_info import SystemInfoManager
from .hardware.storage_info import StorageInfoManager
from .hardware.network_info import NetworkInfoManager
from .hardware.compatibility_checker import CompatibilityChecker

logger = logging.getLogger(__name__)

class HardwareDetector:
    def __init__(self):
        # Initialize managers
        self.system_manager = SystemInfoManager()
        self.storage_manager = StorageInfoManager()
        self.network_manager = NetworkInfoManager()
        self.driver_manager = DriverManager()
        
        # Cache hardware info on init
        self.system_info = self.system_manager.get_system_info()
        self.cpu_info = self.system_manager.get_cpu_info()
        self.memory_info = self.system_manager.get_memory_info()
        self.disk_info = self.storage_manager.get_disk_info()
        self.gpu_info = self.storage_manager.get_gpu_info()
        self.network_info = self.network_manager.get_network_info()
        self.virtualization_info = self.system_manager.get_virtualization_info()

        # Initialize compatibility checker
        self.compatibility_checker = CompatibilityChecker(
            system_info=self.system_info,
            cpu_info=self.cpu_info,
            memory_info=self.memory_info,
            disk_info=self.disk_info,
            gpu_info=self.gpu_info,
            network_info=self.network_info
        )

    def get_system_info(self) -> Dict[str, str]:
        """Get basic system information."""
        return self.system_info

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information."""
        return self.cpu_info

    def get_memory_info(self) -> Dict[str, int]:
        """Get detailed memory information."""
        return self.memory_info

    def get_disk_info(self) -> List[Dict[str, Any]]:
        """Get detailed disk information for all partitions."""
        return self.disk_info

    def get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get information about installed GPUs."""
        return self.gpu_info

    def get_network_info(self) -> Dict[str, Any]:
        """Get information about network interfaces."""
        return self.network_info

    def get_virtualization_info(self) -> Dict[str, Any]:
        """Detect virtualization capabilities and status."""
        return self.virtualization_info

    def get_driver_info(self) -> List[DriverInfo]:
        """Get information about installed and missing drivers."""
        return self.driver_manager.get_driver_info()

    def install_driver(self, driver_info: DriverInfo) -> Dict[str, Any]:
        """Attempt to install a driver."""
        return self.driver_manager.install_driver(driver_info)

    def check_hardware_compatibility(self) -> List[HardwareCompatibility]:
        """Check if the hardware is compatible with Proxmox and provide fallback options."""
        return self.compatibility_checker.check_hardware_compatibility()

    def apply_fallback_configuration(self, component: str, fallback_option: str) -> Dict[str, Any]:
        """Apply a specific fallback configuration for a hardware component."""
        return self.compatibility_checker.apply_fallback_configuration(component, fallback_option)

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