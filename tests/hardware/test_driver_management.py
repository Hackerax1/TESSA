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
        
        # Simulate lspci -vvv output format with correct device name
        mock_run.return_value = MagicMock(
            stdout="""00:02.0 VGA compatible controller: Intel Corporation UHD Graphics 630 (rev 02)
    Subsystem: Intel Corporation UHD Graphics 630
    Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
    Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
    Kernel driver in use: i915
    Kernel modules: i915""",
            stderr="",
            returncode=0
        )

        drivers = self.driver_manager._get_linux_pci_drivers()
        self.assertTrue(any("UHD Graphics" in d.device_name for d in drivers))
        gpu_driver = next(d for d in drivers if "UHD Graphics" in d.device_name)
        self.assertEqual(gpu_driver.driver_name, "i915")
        self.assertTrue(gpu_driver.is_installed)

    @patch('platform.system')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_linux_usb_drivers(self, mock_run, mock_which, mock_system):
        mock_system.return_value = "Linux"
        mock_which.return_value = "/usr/sbin/lsusb"
        
        # Update USB device data to include a device with missing driver
        mock_run.return_value = MagicMock(
            stdout="""Bus 001 Device 002: ID 8087:0029 Intel Corp. Wireless-AC 9560
  bLength                18
  bDescriptorType         1
  bcdUSB               2.00
  bDeviceClass          255 Vendor Specific Class
  iManufacturer           1 Intel Corp.
  iProduct                2 Wireless-AC 9560
  Interface Descriptor:
    bInterfaceClass    255 Vendor Specific Class
    iInterface          0 
    Driver=(none)""",
            stderr="",
            returncode=0
        )

        drivers = self.driver_manager._get_linux_usb_drivers()
        missing_drivers = [d for d in drivers if not d.is_installed]
        self.assertEqual(len(missing_drivers), 1)
        self.assertEqual(missing_drivers[0].device_name, "Intel Corp. Wireless-AC 9560")

    @patch('platform.system')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_windows_drivers(self, mock_run, mock_which, mock_system):
        mock_system.return_value = "Windows"
        mock_which.return_value = "powershell.exe"
        
        # Update Windows driver data to match expected GPU
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
        self.assertEqual(nvidia_driver.status, "error")
        self.assertEqual(nvidia_driver.install_method, "windows_update")

if __name__ == '__main__':
    unittest.main()