"""
SSH device management operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional
import paramiko
import socket

class SSHDeviceManager:
    def __init__(self, api):
        self.api = api
        self.db_path = '/var/lib/proxmox-nli/ssh_devices.db'

    def scan_network(self, subnet: Optional[str] = None) -> Dict[str, Any]:
        """Scan network for SSH-accessible devices
        
        Args:
            subnet: Optional subnet in CIDR notation to scan
            
        Returns:
            Dict with scan results
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Use nmap to scan network
        cmd = 'nmap -p 22 --open'
        if subnet:
            cmd += f' {subnet}'
        else:
            cmd += ' -sn 192.168.0.0/24'  # Default subnet
        
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': cmd
        })
        
        if not result['success']:
            return result
        
        # Parse nmap output
        devices = []
        current_ip = None
        
        for line in result['data'].splitlines():
            if 'Nmap scan report for' in line:
                # Extract IP address
                current_ip = line.split()[-1].strip('()')
            elif 'open  ssh' in line:
                if current_ip:
                    devices.append({
                        'ip': current_ip,
                        'port': 22,
                        'status': 'open'
                    })
                    current_ip = None
        
        return {
            "success": True,
            "message": f"Found {len(devices)} devices with open SSH port",
            "devices": devices
        }

    def discover_devices(self, subnet: Optional[str] = None, username: str = "root", 
                       password: Optional[str] = None) -> Dict[str, Any]:
        """Discover and add SSH devices
        
        Args:
            subnet: Optional subnet to scan
            username: Default username for connections
            password: Default password for connections
            
        Returns:
            Dict with discovery results
        """
        # First scan for devices
        scan_result = self.scan_network(subnet)
        if not scan_result['success']:
            return scan_result
        
        discovered = []
        failed = []
        
        for device in scan_result['devices']:
            # Try to connect and get system info
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(device['ip'], username=username, password=password, timeout=5)
                
                # Get system info
                stdin, stdout, stderr = ssh.exec_command('uname -a')
                system_info = stdout.read().decode().strip()
                
                stdin, stdout, stderr = ssh.exec_command('hostname')
                hostname = stdout.read().decode().strip()
                
                ssh.close()
                
                device_info = {
                    'ip': device['ip'],
                    'hostname': hostname,
                    'system_info': system_info,
                    'username': username
                }
                
                # Add to database
                self._add_device_to_db(device_info)
                discovered.append(device_info)
                
            except Exception as e:
                failed.append({
                    'ip': device['ip'],
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Discovered {len(discovered)} devices, {len(failed)} failed",
            "discovered": discovered,
            "failed": failed
        }

    def add_device(self, hostname: str, name: Optional[str] = None, username: str = "root",
                  password: Optional[str] = None, port: int = 22,
                  description: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Add an SSH device manually
        
        Args:
            hostname: IP or hostname of device
            name: User-friendly name
            username: SSH username
            password: Optional SSH password
            port: SSH port
            description: Device description
            tags: Optional tags for device
            
        Returns:
            Dict with operation result
        """
        # Test connection first
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, port=port, username=username, password=password, timeout=5)
            
            # Get system info
            stdin, stdout, stderr = ssh.exec_command('uname -a')
            system_info = stdout.read().decode().strip()
            
            ssh.close()
            
            device_info = {
                'ip': hostname,
                'hostname': name or hostname,
                'username': username,
                'port': port,
                'description': description,
                'tags': tags or [],
                'system_info': system_info
            }
            
            # Add to database
            self._add_device_to_db(device_info)
            
            return {
                "success": True,
                "message": f"Added device {hostname}",
                "device": device_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add device: {str(e)}"
            }

    def remove_device(self, hostname: str) -> Dict[str, Any]:
        """Remove an SSH device
        
        Args:
            hostname: IP or hostname of device
            
        Returns:
            Dict with operation result
        """
        try:
            self._remove_device_from_db(hostname)
            return {
                "success": True,
                "message": f"Removed device {hostname}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to remove device: {str(e)}"
            }

    def list_devices(self, device_type: Optional[str] = None) -> Dict[str, Any]:
        """List all SSH devices
        
        Args:
            device_type: Optional device type to filter by
            
        Returns:
            Dict with list of devices
        """
        try:
            devices = self._get_devices_from_db()
            
            if device_type:
                devices = [d for d in devices if device_type in d.get('tags', [])]
            
            return {
                "success": True,
                "message": f"Found {len(devices)} devices",
                "devices": devices
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list devices: {str(e)}"
            }

    def get_device_groups(self) -> Dict[str, Any]:
        """Get devices grouped by type
        
        Returns:
            Dict with device groups
        """
        try:
            devices = self._get_devices_from_db()
            groups = {}
            
            for device in devices:
                for tag in device.get('tags', []):
                    if tag not in groups:
                        groups[tag] = []
                    groups[tag].append(device)
            
            return {
                "success": True,
                "message": f"Found {len(groups)} device groups",
                "groups": groups
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get device groups: {str(e)}"
            }

    def execute_command(self, hostname: str, command: str) -> Dict[str, Any]:
        """Execute command on an SSH device
        
        Args:
            hostname: IP or hostname of device
            command: Command to execute
            
        Returns:
            Dict with command result
        """
        try:
            device = self._get_device_from_db(hostname)
            if not device:
                return {
                    "success": False,
                    "message": f"Device {hostname} not found"
                }
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(device['ip'], port=device['port'], 
                       username=device['username'],
                       timeout=5)
            
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            ssh.close()
            
            return {
                "success": True,
                "message": f"Executed command on {hostname}",
                "output": output,
                "error": error
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to execute command: {str(e)}"
            }

    def execute_command_on_multiple(self, hostnames: List[str], command: str) -> Dict[str, Any]:
        """Execute command on multiple devices
        
        Args:
            hostnames: List of device hostnames
            command: Command to execute
            
        Returns:
            Dict with command results
        """
        results = []
        failed = []
        
        for hostname in hostnames:
            result = self.execute_command(hostname, command)
            if result['success']:
                results.append({
                    'hostname': hostname,
                    'output': result['output'],
                    'error': result['error']
                })
            else:
                failed.append({
                    'hostname': hostname,
                    'error': result['message']
                })
        
        return {
            "success": True,
            "message": f"Executed command on {len(results)} devices, {len(failed)} failed",
            "results": results,
            "failed": failed
        }

    def execute_command_on_group(self, group_name: str, command: str) -> Dict[str, Any]:
        """Execute command on a device group
        
        Args:
            group_name: Device group/type
            command: Command to execute
            
        Returns:
            Dict with command results
        """
        try:
            devices = self._get_devices_from_db()
            group_devices = [d['hostname'] for d in devices if group_name in d.get('tags', [])]
            
            return self.execute_command_on_multiple(group_devices, command)
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to execute command on group: {str(e)}"
            }

    def setup_ssh_keys(self, hostnames: List[str], key_path: Optional[str] = None) -> Dict[str, Any]:
        """Set up SSH key authentication
        
        Args:
            hostnames: List of device hostnames
            key_path: Optional path to existing SSH key
            
        Returns:
            Dict with setup results
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Generate key if not provided
        if not key_path:
            key_result = self.api.api_request('POST', f'nodes/{node}/execute', {
                'command': 'ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa'
            })
            if not key_result['success']:
                return key_result
            key_path = '/root/.ssh/id_rsa.pub'
        
        # Get public key
        key_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'cat {key_path}'
        })
        if not key_result['success']:
            return key_result
        
        public_key = key_result['data'].strip()
        
        results = []
        failed = []
        
        for hostname in hostnames:
            try:
                device = self._get_device_from_db(hostname)
                if not device:
                    failed.append({
                        'hostname': hostname,
                        'error': 'Device not found'
                    })
                    continue
                
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(device['ip'], port=device['port'], 
                          username=device['username'],
                          timeout=5)
                
                # Create .ssh directory and set permissions
                commands = [
                    'mkdir -p ~/.ssh',
                    'chmod 700 ~/.ssh',
                    f'echo "{public_key}" >> ~/.ssh/authorized_keys',
                    'chmod 600 ~/.ssh/authorized_keys'
                ]
                
                for cmd in commands:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    error = stderr.read().decode()
                    if error:
                        raise Exception(error)
                
                ssh.close()
                
                results.append({
                    'hostname': hostname,
                    'status': 'success'
                })
                
            except Exception as e:
                failed.append({
                    'hostname': hostname,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Set up SSH keys on {len(results)} devices, {len(failed)} failed",
            "results": results,
            "failed": failed
        }

    def setup_ssh_keys_for_group(self, group_name: str, key_path: Optional[str] = None) -> Dict[str, Any]:
        """Set up SSH key authentication for a device group
        
        Args:
            group_name: Device group/type
            key_path: Optional path to existing SSH key
            
        Returns:
            Dict with setup results
        """
        try:
            devices = self._get_devices_from_db()
            group_devices = [d['hostname'] for d in devices if group_name in d.get('tags', [])]
            
            return self.setup_ssh_keys(group_devices, key_path)
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to set up SSH keys for group: {str(e)}"
            }

    def _add_device_to_db(self, device_info: Dict[str, Any]) -> None:
        """Add device to database"""
        # Implementation would use SQLite or similar to store device info
        pass

    def _remove_device_from_db(self, hostname: str) -> None:
        """Remove device from database"""
        # Implementation would use SQLite or similar to remove device
        pass

    def _get_device_from_db(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Get device info from database"""
        # Implementation would use SQLite or similar to get device info
        pass

    def _get_devices_from_db(self) -> List[Dict[str, Any]]:
        """Get all devices from database"""
        # Implementation would use SQLite or similar to get all devices
        pass