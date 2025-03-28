"""Tests for hardware compatibility and detection functionality."""
import unittest
from unittest.mock import Mock, patch
from installer.hardware.compatibility_checker import CompatibilityChecker
from installer.hardware.types import HardwareCompatibility

class TestCompatibilityChecker(unittest.TestCase):
    """Test cases for hardware compatibility checking."""
    
    def setUp(self):
        """Set up test environment."""
        self.system_info = {
            "system": "Test System",
            "manufacturer": "Test Manufacturer",
            "product": "Test Product",
            "version": "1.0"
        }
        
        self.cpu_info = {
            "model": "AMD Ryzen 9 5950X",
            "physical_cores": 16,
            "total_cores": 32,
            "virtualization_support": {
                "svm": True,  # AMD virtualization
                "vmx": False  # Intel virtualization
            }
        }
        
        self.memory_info = {
            "total": 32 * 1024 * 1024 * 1024,  # 32GB
            "available": 28 * 1024 * 1024 * 1024,  # 28GB
            "used": 4 * 1024 * 1024 * 1024,  # 4GB
            "percent": 12.5
        }
        
        self.disk_info = [{
            "device": "/dev/nvme0n1",
            "size": 1000 * 1024 * 1024 * 1024,  # 1TB
            "model": "Samsung 970 EVO Plus",
            "type": "nvme",
            "used": 200 * 1024 * 1024 * 1024,  # 200GB
            "free": 800 * 1024 * 1024 * 1024   # 800GB
        }]
        
        self.gpu_info = [{
            "name": "NVIDIA GeForce RTX 3080",
            "memory": 10 * 1024 * 1024 * 1024,  # 10GB
            "driver": "nvidia",
            "supports_passthrough": True
        }]
        
        self.network_info = {
            "interfaces": [{
                "name": "eth0",
                "speed": 1000,  # 1Gbps
                "is_up": True,
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

    def test_check_cpu_compatibility(self):
        """Test CPU compatibility checking."""
        results = []
        self.checker._check_cpu_virtualization(results)
        
        # Find CPU-related results
        cpu_results = [r for r in results if r.component == "CPU Virtualization"]
        self.assertTrue(len(cpu_results) > 0)
        self.assertTrue(cpu_results[0].is_compatible)
        
        # Test without virtualization support
        self.checker.cpu_info["virtualization_support"]["svm"] = False
        self.checker.cpu_info["virtualization_support"]["vmx"] = False
        
        results = []
        self.checker._check_cpu_virtualization(results)
        cpu_results = [r for r in results if r.component == "CPU Virtualization"]
        self.assertTrue(len(cpu_results) > 0)
        self.assertFalse(cpu_results[0].is_compatible)
        self.assertEqual(cpu_results[0].severity, "critical")

    def test_check_memory_compatibility(self):
        """Test memory compatibility checking."""
        results = []
        self.checker._check_ram(results)
        
        ram_result = next(r for r in results if r.component == "RAM")
        self.assertTrue(ram_result.is_compatible)
        
        # Test with insufficient RAM
        self.checker.memory_info["total"] = 2 * 1024 * 1024 * 1024  # 2GB
        
        results = []
        self.checker._check_ram(results)
        
        ram_result = next(r for r in results if r.component == "RAM")
        self.assertFalse(ram_result.is_compatible)
        self.assertEqual(ram_result.severity, "warning")
        self.assertTrue(ram_result.fallback_available)
        self.assertEqual(ram_result.fallback_option, "increase_swap")

    def test_check_disk_space(self):
        """Test disk space compatibility checking."""
        results = []
        self.checker._check_disk_space(results)
        
        disk_result = next(r for r in results if r.component == "Disk Space")
        self.assertTrue(disk_result.is_compatible)
        
        # Test with insufficient disk space
        self.checker.disk_info[0]["free"] = 16 * 1024 * 1024 * 1024  # 16GB
        
        results = []
        self.checker._check_disk_space(results)
        
        disk_result = next(r for r in results if r.component == "Disk Space")
        self.assertFalse(disk_result.is_compatible)
        self.assertEqual(disk_result.severity, "warning")
        self.assertTrue(disk_result.fallback_available)

    def test_check_network_compatibility(self):
        """Test network compatibility checking."""
        results = []
        self.checker._check_network(results)
        
        network_results = [r for r in results if r.component.startswith("Network")]
        self.assertTrue(any(r.is_compatible for r in network_results))
        
        # Test with slow network
        self.checker.network_info["interfaces"][0]["speed"] = 10  # 10Mbps
        
        results = []
        self.checker._check_network(results)
        
        network_results = [r for r in results if r.component.startswith("Network")]
        self.assertTrue(any(r.is_compatible for r in network_results))
        self.assertTrue(any(r.severity == "warning" for r in network_results))

    def test_check_gpu_passthrough(self):
        """Test GPU passthrough compatibility checking."""
        results = []
        self.checker._check_gpu_passthrough(results)
        
        gpu_results = [r for r in results if r.component == "GPU Passthrough"]
        self.assertTrue(len(gpu_results) > 0)
        
        # GPU is detected but passthrough capability needs verification
        self.assertFalse(gpu_results[0].is_compatible)
        self.assertEqual(gpu_results[0].severity, "info")
        self.assertTrue(gpu_results[0].fallback_available)

if __name__ == '__main__':
    unittest.main()