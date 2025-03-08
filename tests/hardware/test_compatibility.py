import unittest
from unittest.mock import patch, MagicMock
import platform
from installer.hardware.compatibility_checker import CompatibilityChecker
from installer.hardware.types import HardwareCompatibility

class TestCompatibilityChecker(unittest.TestCase):
    def setUp(self):
        # Setup sample hardware info for testing
        self.system_info = {
            "system": "Linux",
            "machine": "x86_64",
            "processor": "Intel(R) Core(TM) i7"
        }
        
        self.cpu_info = {
            "physical_cores": 4,
            "total_cores": 8,
            "model": "Intel(R) Core(TM) i7",
            "virtualization_support": {
                "vmx": True,
                "svm": False,
                "available": True
            }
        }
        
        self.memory_info = {
            "total": 16000000000,  # 16GB
            "available": 8000000000,
            "used": 8000000000,
            "percentage": 50.0
        }
        
        self.disk_info = [{
            "device": "/dev/sda1",
            "mountpoint": "/",
            "filesystem": "ext4",
            "total": 500000000000,  # 500GB
            "used": 200000000000,
            "free": 300000000000
        }]
        
        self.gpu_info = [{
            "name": "NVIDIA GeForce RTX 3080",
            "memory": 10737418240  # 10GB
        }]
        
        self.network_info = {
            "interfaces": [{
                "name": "eth0",
                "is_up": True,
                "speed": 1000,  # 1Gbps
                "addresses": [{
                    "address": "192.168.1.100",
                    "netmask": "255.255.255.0"
                }]
            }]
        }
        
        self.checker = CompatibilityChecker(
            self.system_info,
            self.cpu_info,
            self.memory_info,
            self.disk_info,
            self.gpu_info,
            self.network_info
        )

    def test_check_cpu_virtualization_supported(self):
        results = []
        self.checker._check_cpu_virtualization(results)
        
        virt_result = next(r for r in results if r.component == "CPU Virtualization")
        self.assertTrue(virt_result.is_compatible)
        self.assertEqual(virt_result.severity, "info")
        self.assertFalse(virt_result.fallback_available)

    def test_check_cpu_virtualization_unsupported(self):
        # Modify CPU info to simulate no virtualization support
        self.cpu_info["virtualization_support"]["available"] = False
        self.cpu_info["virtualization_support"]["vmx"] = False
        
        results = []
        self.checker._check_cpu_virtualization(results)
        
        virt_result = next(r for r in results if r.component == "CPU Virtualization")
        self.assertFalse(virt_result.is_compatible)
        self.assertEqual(virt_result.severity, "critical")
        self.assertTrue(virt_result.fallback_available)
        self.assertEqual(virt_result.fallback_option, "software_emulation")

    def test_check_ram_sufficient(self):
        results = []
        self.checker._check_ram(results)
        
        ram_result = next(r for r in results if r.component == "RAM")
        self.assertTrue(ram_result.is_compatible)
        self.assertEqual(ram_result.severity, "info")
        self.assertFalse(ram_result.fallback_available)

    def test_check_ram_insufficient(self):
        # Modify memory info to simulate low RAM
        self.memory_info["total"] = 2000000000  # 2GB
        
        results = []
        self.checker._check_ram(results)
        
        ram_result = next(r for r in results if r.component == "RAM")
        self.assertFalse(ram_result.is_compatible)
        self.assertEqual(ram_result.severity, "warning")
        self.assertTrue(ram_result.fallback_available)
        self.assertEqual(ram_result.fallback_option, "increase_swap")

    def test_check_disk_space_sufficient(self):
        results = []
        self.checker._check_disk_space(results)
        
        disk_result = next(r for r in results if r.component == "Disk Space")
        self.assertTrue(disk_result.is_compatible)
        self.assertEqual(disk_result.severity, "info")
        self.assertFalse(disk_result.fallback_available)

    def test_check_disk_space_insufficient(self):
        # Modify disk info to simulate low space
        self.disk_info[0]["free"] = 20000000000  # 20GB
        
        results = []
        self.checker._check_disk_space(results)
        
        disk_result = next(r for r in results if r.component == "Disk Space")
        self.assertFalse(disk_result.is_compatible)
        self.assertEqual(disk_result.severity, "warning")
        self.assertTrue(disk_result.fallback_available)
        self.assertEqual(disk_result.fallback_option, "external_storage")

    def test_check_network_sufficient(self):
        results = []
        self.checker._check_network(results)
        
        net_result = next(r for r in results if r.component == "Network Interfaces")
        self.assertTrue(net_result.is_compatible)
        self.assertEqual(net_result.severity, "info")
        self.assertFalse(net_result.fallback_available)

    def test_check_network_no_interfaces(self):
        # Modify network info to simulate no interfaces
        self.network_info["interfaces"] = []
        
        results = []
        self.checker._check_network(results)
        
        net_result = next(r for r in results if r.component == "Network Interfaces")
        self.assertFalse(net_result.is_compatible)
        self.assertEqual(net_result.severity, "critical")
        self.assertTrue(net_result.fallback_available)
        self.assertEqual(net_result.fallback_option, "usb_network")

    def test_check_network_slow_speed(self):
        # Modify network info to simulate slow network
        self.network_info["interfaces"][0]["speed"] = 10  # 10 Mbps
        
        results = []
        self.checker._check_network(results)
        
        net_result = next(r for r in results if r.component == "Network Speed")
        self.assertFalse(net_result.is_compatible)
        self.assertEqual(net_result.severity, "warning")
        self.assertTrue(net_result.fallback_available)
        self.assertEqual(net_result.fallback_option, "limit_network_services")

    @patch('platform.system')
    def test_apply_fallback_ram_swap(self, mock_system):
        # Setup Linux environment and low memory condition
        mock_system.return_value = "Linux"
        self.system_info["system"] = "Linux"
        self.memory_info["total"] = 2000000000  # 2GB
        self.memory_info["swap"] = {"total": 1000000000}  # 1GB existing swap
        
        result = self.checker.apply_fallback_configuration("RAM", "increase_swap")
        
        self.assertTrue(result["success"])
        self.assertTrue("swap" in result["message"].lower())
        self.assertTrue("additional_swap_gb" in result["applied_changes"])
        self.assertGreater(result["applied_changes"]["additional_swap_gb"], 0)
        self.assertGreaterEqual(result["applied_changes"].get("target_total_swap_gb", 0), 4)

    def test_apply_fallback_cpu_emulation(self):
        result = self.checker.apply_fallback_configuration("CPU Virtualization", "software_emulation")
        
        self.assertTrue(result["success"])
        self.assertTrue("emulation" in result["message"].lower())
        self.assertFalse(result["applied_changes"]["use_kvm"])
        self.assertEqual(result["applied_changes"]["cpu_type"], "qemu64")

    def test_full_compatibility_check(self):
        results = self.checker.check_hardware_compatibility()
        
        self.assertTrue(isinstance(results, list))
        self.assertTrue(all(isinstance(r, HardwareCompatibility) for r in results))
        
        # Check that all major components are covered
        components = {r.component for r in results}
        required_components = {
            "CPU Virtualization", 
            "CPU Cores",
            "RAM",
            "Disk Space",
            "Network Interfaces"
        }
        self.assertTrue(required_components.issubset(components))

if __name__ == '__main__':
    unittest.main()