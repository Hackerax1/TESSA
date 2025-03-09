"""
SSH Device Manager module for Proxmox NLI.
Handles discovery, connection, and management of SSH-enabled devices on the network.
"""
import os
import re
import json
import socket
import logging
import ipaddress
import subprocess
import threading
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

@dataclass
class SSHDevice:
    """Represents an SSH-accessible device on the network"""
    hostname: str  # Can be IP or hostname
    name: str = ""  # User-friendly name
    username: str = "root"
    port: int = 22
    key_path: str = ""  # Path to private key
    password: str = ""  # Optional password for fallback authentication
    device_type: str = "unknown"  # server, pi, nas, etc.
    description: str = ""
    tags: List[str] = field(default_factory=list)
    last_seen: str = ""  # ISO format timestamp
    connection_successful: bool = False
    system_info: Dict[str, Any] = field(default_factory=dict)
    favorite: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding sensitive fields"""
        device_dict = asdict(self)
        device_dict.pop('password', None)  # Remove password for security
        return device_dict


class SSHDeviceManager:
    """Manages SSH connections to network devices"""
    
    def __init__(self, config_dir: str = None, api = None):
        self.api = api  # Optional API reference for integration
        
        # Set config directory with fallback to ~/.proxmox_nli/ssh_devices
        if config_dir is None:
            self.config_dir = os.path.expanduser(os.path.join('~', '.proxmox_nli', 'ssh_devices'))
        else:
            self.config_dir = config_dir
            
        self.devices_file = os.path.join(self.config_dir, 'devices.json')
        self.scan_results = {}
        self.devices: Dict[str, SSHDevice] = {}
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load existing devices if available
        self.load_devices()
    
    def load_devices(self) -> None:
        """Load devices from the JSON file"""
        try:
            if os.path.exists(self.devices_file):
                with open(self.devices_file, 'r') as f:
                    devices_data = json.load(f)
                
                for hostname, device_data in devices_data.items():
                    self.devices[hostname] = SSHDevice(**device_data)
                    
                logger.info(f"Loaded {len(self.devices)} SSH devices from {self.devices_file}")
            else:
                logger.info(f"No SSH devices file found at {self.devices_file}")
        except Exception as e:
            logger.error(f"Error loading SSH devices: {str(e)}")
    
    def save_devices(self) -> bool:
        """Save devices to the JSON file"""
        try:
            # Convert to dictionaries, excluding sensitive data
            devices_data = {hostname: device.to_dict() for hostname, device in self.devices.items()}
            
            with open(self.devices_file, 'w') as f:
                json.dump(devices_data, f, indent=2)
                
            logger.info(f"Saved {len(self.devices)} SSH devices to {self.devices_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving SSH devices: {str(e)}")
            return False
    
    def add_device(self, device: SSHDevice) -> Dict[str, Any]:
        """Add or update a device in the manager"""
        try:
            # Store device in collection
            self.devices[device.hostname] = device
            
            # Save to disk
            success = self.save_devices()
            
            return {
                "success": success,
                "message": f"Device {device.hostname} {'added' if success else 'failed to add'}",
                "device": device.to_dict() if success else None
            }
        except Exception as e:
            logger.error(f"Error adding device: {str(e)}")
            return {
                "success": False,
                "message": f"Error adding device: {str(e)}"
            }
    
    def remove_device(self, hostname: str) -> Dict[str, Any]:
        """Remove a device from the manager"""
        try:
            if hostname in self.devices:
                device = self.devices.pop(hostname)
                success = self.save_devices()
                
                return {
                    "success": success,
                    "message": f"Device {hostname} {'removed' if success else 'failed to remove'}",
                    "device": device.to_dict() if success else None
                }
            else:
                return {
                    "success": False,
                    "message": f"Device {hostname} not found"
                }
        except Exception as e:
            logger.error(f"Error removing device: {str(e)}")
            return {
                "success": False,
                "message": f"Error removing device: {str(e)}"
            }
    
    def get_device(self, hostname: str) -> Optional[SSHDevice]:
        """Get a device by hostname or IP"""
        return self.devices.get(hostname)
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all devices as dictionaries"""
        return [device.to_dict() for device in self.devices.values()]
    
    def scan_network(self, subnet: str = "192.168.1.0/24", timeout: int = 2) -> Dict[str, Any]:
        """Scan the network for SSH-accessible devices"""
        try:
            # Parse subnet
            network = ipaddress.ip_network(subnet)
            total_hosts = network.num_addresses - 2  # Exclude network and broadcast addresses
            
            # Track results for responsive hosts
            results = {}
            scan_start_time = time.time()
            
            logger.info(f"Starting network scan of {subnet} for SSH devices")
            
            # Use multiple threads to speed up scanning
            with ThreadPoolExecutor(max_workers=32) as executor:
                # Submit tasks
                futures = {}
                for ip in network.hosts():
                    ip_str = str(ip)
                    futures[executor.submit(self._check_ssh_port, ip_str, timeout)] = ip_str
                
                # Process results as they complete
                active_hosts = 0
                ssh_hosts = 0
                
                for future in as_completed(futures):
                    ip_str = futures[future]
                    try:
                        is_ssh_open = future.result()
                        if is_ssh_open:
                            results[ip_str] = {"ssh": True}
                            ssh_hosts += 1
                            
                            # Try to get hostname
                            try:
                                hostname = socket.getfqdn(ip_str)
                                if hostname and hostname != ip_str:
                                    results[ip_str]["hostname"] = hostname
                            except:
                                pass
                            
                        active_hosts += 1
                    except Exception as e:
                        logger.debug(f"Error checking {ip_str}: {str(e)}")
            
            scan_duration = time.time() - scan_start_time
            
            # Store results
            self.scan_results = results
            
            return {
                "success": True,
                "message": f"Found {ssh_hosts} SSH devices out of {active_hosts} active hosts. Scan took {scan_duration:.1f} seconds.",
                "results": results,
                "total_hosts": total_hosts,
                "active_hosts": active_hosts,
                "ssh_hosts": ssh_hosts,
                "scan_duration_seconds": scan_duration
            }
        except Exception as e:
            logger.error(f"Error scanning network: {str(e)}")
            return {
                "success": False,
                "message": f"Error scanning network: {str(e)}"
            }
    
    def _check_ssh_port(self, ip: str, timeout: float) -> bool:
        """Check if SSH port is open on specified IP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, 22))
            sock.close()
            return result == 0
        except:
            return False
    
    def discover_and_add_devices(self, subnet: str = "192.168.1.0/24", username: str = "root", 
                                 password: str = None, key_path: str = None) -> Dict[str, Any]:
        """Scan network and add discovered SSH devices"""
        # First scan the network
        scan_result = self.scan_network(subnet)
        if not scan_result["success"]:
            return scan_result
        
        # Process results
        devices_found = 0
        devices_added = 0
        
        for ip, info in scan_result["results"].items():
            if info.get("ssh", False):
                devices_found += 1
                
                # Skip if device already exists
                if ip in self.devices:
                    continue
                
                # Try to get hostname or use IP
                device_name = info.get("hostname", ip)
                
                # Add device
                device = SSHDevice(
                    hostname=ip,
                    name=device_name,
                    username=username,
                    password=password if password else "",
                    key_path=key_path if key_path else "",
                )
                
                # Test connection and get system info
                try:
                    connection_result = self.test_connection(device)
                    if connection_result["success"]:
                        device.connection_successful = True
                        device.system_info = connection_result.get("system_info", {})
                        device.device_type = self._determine_device_type(device.system_info)
                        devices_added += 1
                except Exception as e:
                    logger.debug(f"Failed to connect to {ip}: {str(e)}")
                
                # Add device to manager
                self.add_device(device)
        
        return {
            "success": True,
            "message": f"Found {devices_found} SSH devices, added {devices_added} new devices",
            "devices_found": devices_found,
            "devices_added": devices_added,
            "devices": self.get_all_devices()
        }
    
    def _determine_device_type(self, system_info: Dict) -> str:
        """Determine device type based on system info"""
        os_info = system_info.get("os", "").lower()
        host_info = system_info.get("hostname", "").lower()
        
        if "raspberry" in os_info or "raspbian" in os_info or "pi" in host_info:
            return "raspberry_pi"
        elif "nas" in host_info or "synology" in os_info or "freenas" in os_info:
            return "nas"
        elif "proxmox" in os_info:
            return "proxmox"
        elif "ubuntu" in os_info or "debian" in os_info:
            return "linux_server"
        elif "centos" in os_info or "rhel" in os_info or "fedora" in os_info:
            return "linux_server"
        elif "esxi" in os_info or "vmware" in os_info:
            return "vmware"
        else:
            return "unknown"

    def test_connection(self, device: SSHDevice) -> Dict[str, Any]:
        """Test connection to a device and gather basic system info"""
        try:
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try to connect
            try:
                if device.key_path and os.path.isfile(device.key_path):
                    private_key = paramiko.RSAKey.from_private_key_file(device.key_path)
                    client.connect(
                        device.hostname, 
                        port=device.port,
                        username=device.username,
                        pkey=private_key,
                        timeout=5
                    )
                elif device.password:
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        password=device.password,
                        timeout=5
                    )
                else:
                    # Try to use default keys
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        timeout=5
                    )
            except paramiko.AuthenticationException:
                return {
                    "success": False,
                    "message": "Authentication failed",
                    "error_type": "authentication"
                }
            except paramiko.SSHException as e:
                return {
                    "success": False,
                    "message": f"SSH error: {str(e)}",
                    "error_type": "ssh"
                }
            except socket.timeout:
                return {
                    "success": False,
                    "message": "Connection timed out",
                    "error_type": "timeout"
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Connection error: {str(e)}",
                    "error_type": "general"
                }
            
            # Get system info
            system_info = {}
            
            try:
                # Get hostname
                stdin, stdout, stderr = client.exec_command("hostname")
                hostname = stdout.read().decode().strip()
                system_info["hostname"] = hostname
                
                # Get operating system info
                stdin, stdout, stderr = client.exec_command("cat /etc/os-release 2>/dev/null || uname -a")
                os_info = stdout.read().decode().strip()
                system_info["os"] = os_info
                
                # Get CPU info
                stdin, stdout, stderr = client.exec_command("cat /proc/cpuinfo | grep 'model name' | head -1")
                cpu_info = stdout.read().decode().strip()
                if cpu_info:
                    cpu_info = cpu_info.split(':')[-1].strip()
                    system_info["cpu"] = cpu_info
                
                # Get memory info
                stdin, stdout, stderr = client.exec_command("free -h | grep Mem")
                mem_info = stdout.read().decode().strip()
                if mem_info:
                    mem_info = re.sub(r'\s+', ' ', mem_info).strip()
                    system_info["memory"] = mem_info
                
                # Get disk info
                stdin, stdout, stderr = client.exec_command("df -h / | tail -1")
                disk_info = stdout.read().decode().strip()
                if disk_info:
                    disk_info = re.sub(r'\s+', ' ', disk_info).strip()
                    system_info["disk"] = disk_info
            except Exception as e:
                logger.error(f"Error getting system info: {str(e)}")
            
            # Close connection
            client.close()
            
            return {
                "success": True,
                "message": "Connection successful",
                "system_info": system_info
            }
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            return {
                "success": False,
                "message": f"Error testing connection: {str(e)}"
            }
    
    def execute_command(self, hostname: str, command: str) -> Dict[str, Any]:
        """Execute a command on a device"""
        try:
            device = self.get_device(hostname)
            if not device:
                return {
                    "success": False,
                    "message": f"Device {hostname} not found"
                }
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            try:
                if device.key_path and os.path.isfile(device.key_path):
                    private_key = paramiko.RSAKey.from_private_key_file(device.key_path)
                    client.connect(
                        device.hostname, 
                        port=device.port,
                        username=device.username,
                        pkey=private_key,
                        timeout=5
                    )
                elif device.password:
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        password=device.password,
                        timeout=5
                    )
                else:
                    # Try to use default keys
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        timeout=5
                    )
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Connection error: {str(e)}"
                }
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            exit_code = stdout.channel.recv_exit_status()
            
            # Close connection
            client.close()
            
            return {
                "success": exit_code == 0,
                "message": "Command executed",
                "output": output,
                "error": error,
                "exit_code": exit_code
            }
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing command: {str(e)}"
            }
    
    def execute_command_on_multiple(self, hostnames: List[str], command: str) -> Dict[str, Any]:
        """Execute a command on multiple devices in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_host = {
                executor.submit(self.execute_command, hostname, command): hostname 
                for hostname in hostnames if hostname in self.devices
            }
            
            for future in as_completed(future_to_host):
                hostname = future_to_host[future]
                try:
                    result = future.result()
                    results[hostname] = result
                except Exception as e:
                    results[hostname] = {
                        "success": False,
                        "message": f"Error: {str(e)}"
                    }
        
        return {
            "success": True,
            "message": f"Command executed on {len(results)} devices",
            "results": results
        }
    
    def get_device_groups(self) -> Dict[str, List[str]]:
        """Get devices grouped by type"""
        groups = {}
        
        for hostname, device in self.devices.items():
            device_type = device.device_type
            if device_type not in groups:
                groups[device_type] = []
            
            groups[device_type].append(hostname)
        
        return groups
    
    def setup_ssh_keys(self, hostnames: List[str], key_path: str = None) -> Dict[str, Any]:
        """Set up SSH key authentication for multiple devices"""
        if key_path is None:
            # Generate a key if not provided
            key_path = os.path.join(self.config_dir, 'ssh_key')
            
            if not os.path.exists(key_path):
                try:
                    # Generate SSH key pair
                    subprocess.run(
                        ['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', key_path, '-N', ''],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    logger.info(f"Generated SSH key at {key_path}")
                except Exception as e:
                    logger.error(f"Failed to generate SSH key: {str(e)}")
                    return {
                        "success": False,
                        "message": f"Failed to generate SSH key: {str(e)}"
                    }
        
        # Read the public key
        try:
            with open(f"{key_path}.pub", 'r') as f:
                public_key = f.read().strip()
        except Exception as e:
            logger.error(f"Failed to read public key: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to read public key: {str(e)}"
            }
        
        # Deploy key to devices
        results = {}
        success_count = 0
        
        for hostname in hostnames:
            device = self.get_device(hostname)
            if not device:
                results[hostname] = {
                    "success": False,
                    "message": "Device not found"
                }
                continue
            
            # Connect to device
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect with existing credentials
                if device.password:
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        password=device.password,
                        timeout=5
                    )
                elif device.key_path and os.path.isfile(device.key_path):
                    private_key = paramiko.RSAKey.from_private_key_file(device.key_path)
                    client.connect(
                        device.hostname, 
                        port=device.port,
                        username=device.username,
                        pkey=private_key,
                        timeout=5
                    )
                else:
                    # Skip this device
                    results[hostname] = {
                        "success": False,
                        "message": "No authentication method available"
                    }
                    continue
                
                # Create .ssh directory if it doesn't exist
                stdin, stdout, stderr = client.exec_command("mkdir -p ~/.ssh")
                exit_code = stdout.channel.recv_exit_status()
                
                if exit_code != 0:
                    error = stderr.read().decode()
                    results[hostname] = {
                        "success": False,
                        "message": f"Failed to create .ssh directory: {error}"
                    }
                    client.close()
                    continue
                
                # Append public key to authorized_keys
                stdin, stdout, stderr = client.exec_command(
                    f"echo '{public_key}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
                )
                exit_code = stdout.channel.recv_exit_status()
                
                if exit_code != 0:
                    error = stderr.read().decode()
                    results[hostname] = {
                        "success": False,
                        "message": f"Failed to add public key: {error}"
                    }
                    client.close()
                    continue
                
                # Success - update device
                device.key_path = key_path
                self.add_device(device)
                
                results[hostname] = {
                    "success": True,
                    "message": "SSH key added successfully"
                }
                success_count += 1
                
                # Close connection
                client.close()
            
            except Exception as e:
                results[hostname] = {
                    "success": False,
                    "message": f"Error: {str(e)}"
                }
        
        return {
            "success": True,
            "message": f"SSH key setup completed for {success_count}/{len(hostnames)} devices",
            "results": results,
            "key_path": key_path
        }
    
    def upload_file(self, hostname: str, local_path: str, remote_path: str) -> Dict[str, Any]:
        """Upload a file to a device"""
        try:
            device = self.get_device(hostname)
            if not device:
                return {
                    "success": False,
                    "message": f"Device {hostname} not found"
                }
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            try:
                if device.key_path and os.path.isfile(device.key_path):
                    private_key = paramiko.RSAKey.from_private_key_file(device.key_path)
                    client.connect(
                        device.hostname, 
                        port=device.port,
                        username=device.username,
                        pkey=private_key,
                        timeout=5
                    )
                elif device.password:
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        password=device.password,
                        timeout=5
                    )
                else:
                    # Try to use default keys
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        timeout=5
                    )
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Connection error: {str(e)}"
                }
            
            # Upload file
            sftp = client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            
            # Close connection
            client.close()
            
            return {
                "success": True,
                "message": f"File uploaded to {remote_path}"
            }
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return {
                "success": False,
                "message": f"Error uploading file: {str(e)}"
            }
    
    def download_file(self, hostname: str, remote_path: str, local_path: str) -> Dict[str, Any]:
        """Download a file from a device"""
        try:
            device = self.get_device(hostname)
            if not device:
                return {
                    "success": False,
                    "message": f"Device {hostname} not found"
                }
            
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            try:
                if device.key_path and os.path.isfile(device.key_path):
                    private_key = paramiko.RSAKey.from_private_key_file(device.key_path)
                    client.connect(
                        device.hostname, 
                        port=device.port,
                        username=device.username,
                        pkey=private_key,
                        timeout=5
                    )
                elif device.password:
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        password=device.password,
                        timeout=5
                    )
                else:
                    # Try to use default keys
                    client.connect(
                        device.hostname,
                        port=device.port,
                        username=device.username,
                        timeout=5
                    )
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Connection error: {str(e)}"
                }
            
            # Download file
            sftp = client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            
            # Close connection
            client.close()
            
            return {
                "success": True,
                "message": f"File downloaded to {local_path}"
            }
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return {
                "success": False,
                "message": f"Error downloading file: {str(e)}"
            }