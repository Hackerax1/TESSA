"""Tests for hardware compatibility and detection functionality."""
import unittest
from unittest.mock import Mock, patch
import os
import sys
from installer.hardware.compatibility_checker import CompatibilityChecker
from installer.hardware.hardware_compatibility_db import HardwareCompatibilityDB

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
            "used": 4 * 1024 * 1024 * 1024  # 4GB
        }
        
        self.disk_info = [{
            "device": "/dev/nvme0n1",
            "size": 1000 * 1024 * 1024 * 1024,  # 1TB
            "model": "Samsung 970 EVO Plus",
            "type": "nvme",
            "used": 200 * 1024 * 1024 * 1024,  # 200GB
            "free": 800 * 1024 * 1024 * 1024  # 800GB
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
        self.checker._check_cpu(results)
        
        # Find CPU-related results
        cpu_results = [r for r in results if r.component.startswith("CPU")]
        
        # Should be compatible (AMD-V support)
        self.assertTrue(any(r.is_compatible for r in cpu_results))
        
        # Modify CPU info to remove virtualization support
        self.checker.cpu_info["virtualization_support"]["svm"] = False
        
        results = []
        self.checker._check_cpu(results)
        cpu_results = [r for r in results if r.component.startswith("CPU")]
        
        # Should not be compatible (no virtualization support)
        self.assertTrue(any(not r.is_compatible for r in cpu_results))
        
    def test_check_memory_compatibility(self):
        """Test memory compatibility checking."""
        results = []
        self.checker._check_ram(results)
        
        ram_result = next(r for r in results if r.component == "RAM")
        self.assertTrue(ram_result.is_compatible)
        
        # Test with insufficient RAM
        self.checker.memory_info["total"] = 4 * 1024 * 1024 * 1024  # 4GB
        
        results = []
        self.checker._check_ram(results)
        
        ram_result = next(r for r in results if r.component == "RAM")
        self.assertFalse(ram_result.is_compatible)
        self.assertEqual(ram_result.severity, "warning")
        self.assertTrue(ram_result.fallback_available)
        self.assertEqual(ram_result.fallback_option, "increase_swap")
        
    def test_check_storage_compatibility(self):
        """Test storage compatibility checking."""
        results = []
        self.checker._check_storage(results)
        
        storage_result = next(r for r in results if r.component == "Storage")
        self.assertTrue(storage_result.is_compatible)
        
        # Test with insufficient storage
        self.checker.disk_info[0]["size"] = 50 * 1024 * 1024 * 1024  # 50GB
        
        results = []
        self.checker._check_storage(results)
        
        storage_result = next(r for r in results if r.component == "Storage")
        self.assertFalse(storage_result.is_compatible)
        self.assertEqual(storage_result.severity, "critical")
        
    def test_check_network_compatibility(self):
        """Test network compatibility checking."""
        results = []
        self.checker._check_network(results)
        
        network_result = next(r for r in results if r.component == "Network")
        self.assertTrue(network_result.is_compatible)
        
        # Test with slow network
        self.checker.network_info["interfaces"][0]["speed"] = 100  # 100Mbps
        
        results = []
        self.checker._check_network(results)
        
        network_result = next(r for r in results if r.component == "Network")
        self.assertTrue(network_result.is_compatible)  # Should still be compatible
        self.assertEqual(network_result.severity, "warning")  # But with warning
        
    def test_check_gpu_compatibility(self):
        """Test GPU compatibility checking."""
        results = []
        self.checker._check_gpu(results)
        
        gpu_result = next(r for r in results if r.component == "GPU")
        self.assertTrue(gpu_result.is_compatible)
        
        # Test without passthrough support
        self.checker.gpu_info[0]["supports_passthrough"] = False
        
        results = []
        self.checker._check_gpu(results)
        
        gpu_result = next(r for r in results if r.component == "GPU")
        self.assertTrue(gpu_result.is_compatible)  # Should still be compatible
        self.assertEqual(gpu_result.severity, "info")  # But with info about limited passthrough
        
    @patch('proxmox_nli.installer.hardware.hardware_compatibility_db.HardwareCompatibilityDB')
    def test_community_database_integration(self, mock_db):
        """Test integration with community hardware database."""
        # Mock database responses
        mock_db.return_value.get_hardware_compatibility.return_value = {
            "is_compatible": True,
            "notes": "Tested by community",
            "reported_issues": []
        }
        
        checker = CompatibilityChecker(
            self.system_info,
            self.cpu_info,
            self.memory_info,
            self.disk_info,
            self.gpu_info,
            self.network_info,
            compatibility_db=mock_db.return_value
        )
        
        results = checker.check_compatibility()
        
        # Verify database was queried for CPU and GPU
        mock_db.return_value.get_hardware_compatibility.assert_any_call(
            "cpu",
            mock_db.return_value._generate_hardware_id({"model": self.cpu_info["model"]})
        )
        
        mock_db.return_value.get_hardware_compatibility.assert_any_call(
            "gpu",
            mock_db.return_value._generate_hardware_id({"name": self.gpu_info[0]["name"]})
        )
        
    def test_generate_report(self):
        """Test compatibility report generation."""
        results = self.checker.check_compatibility()
        report = self.checker.generate_report()
        
        self.assertIn('system_info', report)
        self.assertIn('compatibility_results', report)
        self.assertIn('recommendations', report)
        
        # Verify report content
        self.assertEqual(report['system_info']['system'], self.system_info['system'])
        self.assertGreater(len(report['compatibility_results']), 0)
        
if __name__ == '__main__':
    unittest.main()