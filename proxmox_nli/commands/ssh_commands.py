"""
SSH Device Commands module for Proxmox NLI.
Provides commands for managing SSH connections to devices on the network.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from ..core.ssh_device_manager import SSHDeviceManager, SSHDevice

logger = logging.getLogger(__name__)

class SSHCommands:
    """Commands for managing SSH devices on the network"""
    
    def __init__(self, api=None):
        self.api = api
        config_dir = os.path.join(os.path.expanduser("~"), ".proxmox_nli", "ssh_devices")
        self.ssh_manager = SSHDeviceManager(config_dir=config_dir, api=api)
    
    def scan_network(self, subnet: str = None) -> dict:
        """Scan network for SSH-accessible devices
        
        Args:
            subnet (str, optional): Subnet to scan in CIDR notation. Defaults to local subnet.
        
        Returns:
            dict: Scan results
        """
        # If no subnet provided, try to auto-detect
        if subnet is None:
            # Use default home network subnets if we can't detect
            subnet = "192.168.1.0/24"  # Default home network
        
        return self.ssh_manager.scan_network(subnet=subnet)
    
    def discover_devices(self, subnet: str = None, username: str = "root", password: str = None) -> dict:
        """Discover and add SSH devices on the network
        
        Args:
            subnet (str, optional): Subnet to scan in CIDR notation. Defaults to local subnet.
            username (str, optional): Default username for connections. Defaults to "root".
            password (str, optional): Default password for connections. Defaults to None.
        
        Returns:
            dict: Discovery results
        """
        # If no subnet provided, try to auto-detect
        if subnet is None:
            # Use default home network subnets if we can't detect
            subnet = "192.168.1.0/24"  # Default home network
        
        return self.ssh_manager.discover_and_add_devices(
            subnet=subnet,
            username=username,
            password=password
        )
    
    def list_devices(self, device_type: str = None) -> dict:
        """List all SSH devices or devices of a specific type
        
        Args:
            device_type (str, optional): Filter by device type. Defaults to None.
        
        Returns:
            dict: List of devices
        """
        devices = self.ssh_manager.get_all_devices()
        
        if device_type:
            devices = [device for device in devices if device.get("device_type") == device_type]
        
        return {
            "success": True,
            "message": f"Found {len(devices)} devices",
            "devices": devices
        }
    
    def get_device_groups(self) -> dict:
        """Get devices grouped by their type
        
        Returns:
            dict: Device groups
        """
        groups = self.ssh_manager.get_device_groups()
        
        return {
            "success": True,
            "message": f"Found {len(groups)} device groups",
            "groups": groups
        }
    
    def add_device(self, hostname: str, name: str = None, username: str = "root", 
                  password: str = None, port: int = 22, 
                  description: str = "", tags: List[str] = None) -> dict:
        """Add an SSH device manually
        
        Args:
            hostname (str): IP or hostname of the device
            name (str, optional): User-friendly name. Defaults to hostname.
            username (str, optional): Username for SSH. Defaults to "root".
            password (str, optional): Password for SSH. Defaults to None.
            port (int, optional): SSH port. Defaults to 22.
            description (str, optional): Description of the device. Defaults to "".
            tags (List[str], optional): Tags for the device. Defaults to None.
        
        Returns:
            dict: Result of operation
        """
        if name is None:
            name = hostname
        
        if tags is None:
            tags = []
        
        device = SSHDevice(
            hostname=hostname,
            name=name,
            username=username,
            password=password if password else "",
            port=port,
            description=description,
            tags=tags
        )
        
        # Test connection if credentials provided
        if password or (username == "root"):
            test_result = self.ssh_manager.test_connection(device)
            if test_result["success"]:
                device.connection_successful = True
                device.system_info = test_result.get("system_info", {})
                device.device_type = self.ssh_manager._determine_device_type(device.system_info)
        
        return self.ssh_manager.add_device(device)
    
    def update_device(self, hostname: str, name: str = None, username: str = None, 
                     password: str = None, port: int = None, 
                     description: str = None, tags: List[str] = None) -> dict:
        """Update an existing SSH device
        
        Args:
            hostname (str): IP or hostname of the device
            name (str, optional): User-friendly name. Defaults to None.
            username (str, optional): Username for SSH. Defaults to None.
            password (str, optional): Password for SSH. Defaults to None.
            port (int, optional): SSH port. Defaults to None.
            description (str, optional): Description of the device. Defaults to None.
            tags (List[str], optional): Tags for the device. Defaults to None.
        
        Returns:
            dict: Result of operation
        """
        device = self.ssh_manager.get_device(hostname)
        if not device:
            return {
                "success": False,
                "message": f"Device {hostname} not found"
            }
        
        # Update fields if provided
        if name is not None:
            device.name = name
        if username is not None:
            device.username = username
        if password is not None:
            device.password = password
        if port is not None:
            device.port = port
        if description is not None:
            device.description = description
        if tags is not None:
            device.tags = tags
        
        return self.ssh_manager.add_device(device)
    
    def remove_device(self, hostname: str) -> dict:
        """Remove an SSH device
        
        Args:
            hostname (str): IP or hostname of the device
        
        Returns:
            dict: Result of operation
        """
        return self.ssh_manager.remove_device(hostname)
    
    def execute_command(self, hostname: str, command: str) -> dict:
        """Execute a command on a device
        
        Args:
            hostname (str): IP or hostname of the device
            command (str): Command to execute
        
        Returns:
            dict: Command execution results
        """
        return self.ssh_manager.execute_command(hostname, command)
    
    def execute_command_on_multiple(self, hostnames: List[str], command: str) -> dict:
        """Execute a command on multiple devices
        
        Args:
            hostnames (List[str]): List of hostnames to execute on
            command (str): Command to execute
        
        Returns:
            dict: Command execution results for each device
        """
        return self.ssh_manager.execute_command_on_multiple(hostnames, command)
    
    def execute_command_on_group(self, group_name: str, command: str) -> dict:
        """Execute a command on a group of devices
        
        Args:
            group_name (str): Group name (device type)
            command (str): Command to execute
        
        Returns:
            dict: Command execution results for each device
        """
        groups = self.ssh_manager.get_device_groups()
        
        if group_name not in groups:
            return {
                "success": False,
                "message": f"Group {group_name} not found",
                "available_groups": list(groups.keys())
            }
        
        hostnames = groups[group_name]
        return self.ssh_manager.execute_command_on_multiple(hostnames, command)
    
    def setup_ssh_keys(self, hostnames: List[str], key_path: str = None) -> dict:
        """Set up SSH key authentication for multiple devices
        
        Args:
            hostnames (List[str]): List of hostnames to set up
            key_path (str, optional): Path to existing SSH key. Defaults to None.
        
        Returns:
            dict: Results of key setup
        """
        return self.ssh_manager.setup_ssh_keys(hostnames, key_path)
    
    def setup_ssh_keys_for_group(self, group_name: str, key_path: str = None) -> dict:
        """Set up SSH key authentication for a group of devices
        
        Args:
            group_name (str): Group name (device type)
            key_path (str, optional): Path to existing SSH key. Defaults to None.
        
        Returns:
            dict: Results of key setup
        """
        groups = self.ssh_manager.get_device_groups()
        
        if group_name not in groups:
            return {
                "success": False,
                "message": f"Group {group_name} not found",
                "available_groups": list(groups.keys())
            }
        
        hostnames = groups[group_name]
        return self.ssh_manager.setup_ssh_keys(hostnames, key_path)
    
    def upload_file(self, hostname: str, local_path: str, remote_path: str) -> dict:
        """Upload a file to a device
        
        Args:
            hostname (str): IP or hostname of the device
            local_path (str): Local file path
            remote_path (str): Remote file path
        
        Returns:
            dict: Upload result
        """
        return self.ssh_manager.upload_file(hostname, local_path, remote_path)
    
    def download_file(self, hostname: str, remote_path: str, local_path: str) -> dict:
        """Download a file from a device
        
        Args:
            hostname (str): IP or hostname of the device
            remote_path (str): Remote file path
            local_path (str): Local file path
        
        Returns:
            dict: Download result
        """
        return self.ssh_manager.download_file(hostname, remote_path, local_path)