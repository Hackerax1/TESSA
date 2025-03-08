import unittest
from unittest.mock import patch, MagicMock
import platform
import psutil
from installer.hardware.system_info import SystemInfoManager
from installer.hardware.storage_info import StorageInfoManager
from installer.hardware.network_info import NetworkInfoManager

class TestSystemInfoManager(unittest.TestCase):
    def setUp(self):
        self.system_info = SystemInfoManager()

    @patch('platform.system')
    @patch('platform.node')
    @patch('platform.release')
    @patch('platform.version')
    @patch('platform.machine')
    @patch('platform.processor')
    @patch('socket.gethostname')
    def test_get_system_info(self, mock_hostname, mock_processor, mock_machine, 
                            mock_version, mock_release, mock_node, mock_system):
        # Setup mocks
        mock_system.return_value = "Linux"
        mock_node.return_value = "test-node"
        mock_release.return_value = "5.15.0"
        mock_version.return_value = "Test Version"
        mock_machine.return_value = "x86_64"
        mock_processor.return_value = "Intel(R) Core(TM) i7"
        mock_hostname.return_value = "test-host"

        info = self.system_info.get_system_info()
        
        self.assertEqual(info["system"], "Linux")
        self.assertEqual(info["node"], "test-node")
        self.assertEqual(info["release"], "5.15.0")
        self.assertEqual(info["version"], "Test Version")
        self.assertEqual(info["machine"], "x86_64")
        self.assertEqual(info["processor"], "Intel(R) Core(TM) i7")
        self.assertEqual(info["hostname"], "test-host")

    @patch('psutil.virtual_memory')
    def test_get_memory_info(self, mock_vmem):
        # Setup mock for virtual memory
        mock_vmem.return_value = MagicMock(
            total=16000000000,  # 16GB
            available=8000000000,
            used=8000000000,
            percent=50.0
        )

        memory_info = self.system_info.get_memory_info()
        
        self.assertEqual(memory_info["total"], 16000000000)
        self.assertEqual(memory_info["available"], 8000000000)
        self.assertEqual(memory_info["used"], 8000000000)
        self.assertEqual(memory_info["percentage"], 50.0)

    @patch('platform.system')
    @patch('subprocess.run')
    def test_get_cpu_info_linux(self, mock_run, mock_system):
        mock_system.return_value = "Linux"
        mock_run.return_value = MagicMock(
            stdout="""processor       : 0
model name      : Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 vmx
""",
            stderr="",
            returncode=0
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = mock_run.return_value.stdout
            cpu_info = self.system_info.get_cpu_info()
            
            self.assertEqual(cpu_info.get("model"), "Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz")
            self.assertTrue(cpu_info["virtualization_support"]["vmx"])
            self.assertTrue(cpu_info["virtualization_support"]["available"])

class TestStorageInfoManager(unittest.TestCase):
    def setUp(self):
        self.storage_info = StorageInfoManager()

    @patch('psutil.disk_partitions')
    @patch('psutil.disk_usage')
    def test_get_disk_info(self, mock_usage, mock_partitions):
        # Setup mocks
        mock_partitions.return_value = [
            MagicMock(device="/dev/sda1", mountpoint="/", fstype="ext4"),
            MagicMock(device="/dev/sda2", mountpoint="/home", fstype="ext4")
        ]
        
        mock_usage.return_value = MagicMock(
            total=500000000000,  # 500GB
            used=200000000000,
            free=300000000000,
            percent=40.0
        )

        disk_info = self.storage_info.get_disk_info()
        
        self.assertEqual(len(disk_info), 2)
        self.assertEqual(disk_info[0]["device"], "/dev/sda1")
        self.assertEqual(disk_info[0]["mountpoint"], "/")
        self.assertEqual(disk_info[0]["fstype"], "ext4")
        self.assertEqual(disk_info[0]["total"], 500000000000)
        self.assertEqual(disk_info[0]["used"], 200000000000)
        self.assertEqual(disk_info[0]["free"], 300000000000)

class TestNetworkInfoManager(unittest.TestCase):
    def setUp(self):
        self.network_info = NetworkInfoManager()

    @patch('psutil.net_if_addrs')
    @patch('psutil.net_if_stats')
    def test_get_network_info(self, mock_stats, mock_addrs):
        # Setup mocks
        mock_addrs.return_value = {
            "eth0": [
                MagicMock(
                    family=2,  # AF_INET
                    address="192.168.1.100",
                    netmask="255.255.255.0",
                    broadcast="192.168.1.255"
                )
            ]
        }
        
        mock_stats.return_value = {
            "eth0": MagicMock(
                isup=True,
                speed=1000,  # 1Gbps
                mtu=1500,
                duplex="full"
            )
        }

        network_info = self.network_info.get_network_info()
        
        self.assertTrue("interfaces" in network_info)
        self.assertEqual(len(network_info["interfaces"]), 1)
        eth0 = next(i for i in network_info["interfaces"] if i["name"] == "eth0")
        self.assertTrue(eth0["is_up"])
        self.assertEqual(eth0["speed"], 1000)
        self.assertEqual(eth0["mtu"], 1500)
        self.assertEqual(eth0["duplex"], "full")
        self.assertEqual(eth0["addresses"][0]["address"], "192.168.1.100")
        self.assertEqual(eth0["addresses"][0]["netmask"], "255.255.255.0")

if __name__ == '__main__':
    unittest.main()