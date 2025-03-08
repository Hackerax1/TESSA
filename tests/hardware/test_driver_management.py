import unittest
from unittest.mock import patch, MagicMock
import platform
import shutil
from installer.hardware.driver_manager import DriverManager
from installer.hardware.types import DriverInfo

class TestDriverManager(unittest.TestCase):
    def setUp(self):
        self.driver_manager = DriverManager()

    @patch('platform.system')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_linux_pci_drivers(self, mock_run, mock_which, mock_system):
        mock_system.return_value = "Linux"
        mock_which.return_value = "/usr/sbin/lspci"  # Simulate lspci availability
        
        # Simulate lspci -vvv output format
        mock_run.return_value = MagicMock(
            stdout="""00:02.0 VGA compatible controller: Intel Corporation UHD Graphics 630 (rev 02)
    Subsystem: Intel Corporation UHD Graphics 630
    Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
    Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
    Kernel driver in use: i915
    Kernel modules: i915

02:00.0 Network controller: Intel Corporation Wi-Fi 6 AX200 (rev 1a)
    Subsystem: Intel Corporation Wi-Fi 6 AX200
    Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
    Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
    Kernel driver in use: iwlwifi
    Kernel modules: iwlwifi""",
            stderr="",
            returncode=0
        )

        drivers = self.driver_manager._get_linux_pci_drivers()
        
        self.assertEqual(len(drivers), 2)
        gpu_driver = next(d for d in drivers if "UHD Graphics" in d.device_name)
        wifi_driver = next(d for d in drivers if "Wi-Fi" in d.device_name)
        
        self.assertEqual(gpu_driver.driver_name, "i915")
        self.assertTrue(gpu_driver.is_installed)
        self.assertEqual(gpu_driver.status, "working")
        
        self.assertEqual(wifi_driver.driver_name, "iwlwifi")
        self.assertTrue(wifi_driver.is_installed)
        self.assertEqual(wifi_driver.status, "working")

    @patch('platform.system')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_linux_usb_drivers(self, mock_run, mock_which, mock_system):
        mock_system.return_value = "Linux"
        mock_which.return_value = "/usr/sbin/lsusb"  # Simulate lsusb availability
        
        # Simulate lsusb -v output format
        mock_run.return_value = MagicMock(
            stdout="""Bus 001 Device 002: ID 8087:0029 Intel Corp. Wireless-AC 9560
  bLength                18
  bDescriptorType         1
  bcdUSB               2.00
  bDeviceClass          255 Vendor Specific Class
  iManufacturer           1 Intel Corp.
  iProduct                2 Wireless-AC 9560
  bMaxPacketSize0        64
  idVendor           0x8087
  idProduct          0x0029
  Interface Descriptor:
    bInterfaceClass    255 Vendor Specific Class
    iInterface          0
    Driver=(none)

Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
  bLength                18
  bDescriptorType         1
  bcdUSB               3.00
  bDeviceClass            9 Hub
  iManufacturer           1 Linux Foundation
  iProduct                2 3.0 root hub
  Interface Descriptor:
    bInterfaceClass     9 Hub
    iInterface          0
    Driver=hub""",
            stderr="",
            returncode=0
        )

        drivers = self.driver_manager._get_linux_usb_drivers()
        missing_drivers = [d for d in drivers if not d.is_installed]
        
        self.assertEqual(len(missing_drivers), 1)
        self.assertEqual(missing_drivers[0].device_name, "Intel Corp. Wireless-AC 9560")
        self.assertEqual(missing_drivers[0].status, "missing")

    @patch('platform.system')
    @patch('subprocess.run')
    def test_install_driver(self, mock_run, mock_system):
        mock_system.return_value = "Linux"
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        test_driver = DriverInfo(
            device_id="0000:00:02.0",
            device_name="Test Graphics Card",
            driver_name="test_driver",
            is_installed=False,
            status="missing",
            install_method="package",
            package_name="test-package",
            install_commands=["apt-get install -y test-package"]
        )
        
        # Mock get_driver_info to simulate successful installation
        with patch.object(self.driver_manager, 'get_driver_info') as mock_get_info:
            mock_get_info.return_value = [DriverInfo(
                device_id="0000:00:02.0",
                device_name="Test Graphics Card",
                driver_name="test_driver",
                is_installed=True,
                status="working",
                install_method="package",
                package_name="test-package",
                install_commands=None
            )]
            
            result = self.driver_manager.install_driver(test_driver)
            
            self.assertTrue(result["success"])
            self.assertTrue("installed successfully" in result["message"].lower())
            mock_run.assert_called_with(
                ["apt-get", "install", "-y", "test-package"],
                capture_output=True,
                text=True
            )

    @patch('platform.system')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_windows_drivers(self, mock_run, mock_which, mock_system):
        mock_system.return_value = "Windows"
        mock_which.return_value = "powershell.exe"
        
        # Simulate PowerShell output format
        mock_run.return_value = MagicMock(
            stdout="""
Status     DeviceID                                      Class             FriendlyName
------     --------                                      -----             ------------
Error      PCI\\VEN_10DE&DEV_1F95                       Display           NVIDIA GeForce RTX 3070
Unknown    USB\\VID_046D&PID_C52B                       USB               Logitech USB Device
""",
            stderr="",
            returncode=0
        )

        drivers = self.driver_manager._get_windows_drivers()
        
        self.assertEqual(len(drivers), 2)
        nvidia_driver = next(d for d in drivers if "NVIDIA GeForce RTX 3070" in d.device_name)
        logitech_driver = next(d for d in drivers if "Logitech USB Device" in d.device_name)
        
        self.assertEqual(nvidia_driver.status, "error")
        self.assertEqual(logitech_driver.status, "missing")
        self.assertEqual(nvidia_driver.install_method, "windows_update")
        self.assertEqual(logitech_driver.install_method, "windows_update")

if __name__ == '__main__':
    unittest.main()