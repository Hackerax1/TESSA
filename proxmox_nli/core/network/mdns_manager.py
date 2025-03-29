"""
mDNS/Avahi integration module for Proxmox NLI.
Enables zero-configuration networking through multicast DNS.
"""
import logging
import subprocess
import socket
import re
import json
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class MDNSManager:
    """Manager for mDNS/Avahi service discovery integration"""
    
    def __init__(self, api):
        """Initialize mDNS manager
        
        Args:
            api: API instance for Proxmox API calls
        """
        self.api = api
        self.service_dir = '/etc/avahi/services'
        self.domain = 'local'
        self._init_avahi()
    
    def _init_avahi(self) -> Dict[str, Any]:
        """Initialize Avahi service if not already installed
        
        Returns:
            Dict with result of initialization
        """
        try:
            # Check if avahi-daemon is installed
            result = self._exec_command('which avahi-daemon')
            
            if not result['success'] or not result['output'].strip():
                # Install avahi if not present
                logger.info("Avahi daemon not found, installing...")
                install_result = self._exec_command('apt-get update && apt-get install -y avahi-daemon avahi-utils')
                
                if not install_result['success']:
                    logger.error(f"Failed to install Avahi: {install_result.get('error')}")
                    return {
                        'success': False,
                        'message': f"Failed to install Avahi: {install_result.get('error')}"
                    }
            
            # Make sure the service is running
            self._exec_command('systemctl enable avahi-daemon')
            service_result = self._exec_command('systemctl start avahi-daemon')
            
            if not service_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to start Avahi daemon: {service_result.get('error')}"
                }
            
            # Create service directory if it doesn't exist
            self._exec_command(f'mkdir -p {self.service_dir}')
            
            return {
                'success': True,
                'message': "Avahi daemon initialized successfully"
            }
            
        except Exception as e:
            logger.error(f"Error initializing Avahi daemon: {str(e)}")
            return {
                'success': False,
                'message': f"Error initializing Avahi daemon: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get Avahi/mDNS service status
        
        Returns:
            Dict with service status information
        """
        try:
            status_result = self._exec_command('systemctl status avahi-daemon')
            active = 'Active: active' in status_result.get('output', '')
            
            services_result = self.list_services()
            
            return {
                'success': True,
                'active': active,
                'service_count': len(services_result.get('services', [])),
                'services': services_result.get('services', []),
                'status_output': status_result.get('output', '')
            }
            
        except Exception as e:
            logger.error(f"Error getting Avahi status: {str(e)}")
            return {
                'success': False, 
                'message': f"Error getting Avahi status: {str(e)}"
            }
    
    def register_service(self, 
                         name: str, 
                         service_type: str, 
                         port: int, 
                         protocol: str = 'tcp', 
                         host: Optional[str] = None,
                         txt_records: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Register a service with mDNS/Avahi
        
        Args:
            name: Service name
            service_type: Type of service (e.g., _http, _ssh)
            port: Port number
            protocol: Protocol (tcp or udp)
            host: Host name (defaults to local hostname)
            txt_records: Optional TXT records for additional info
            
        Returns:
            Dict with registration result
        """
        try:
            # Validate inputs
            if not name or not service_type or not port:
                return {
                    'success': False,
                    'message': "Missing required parameters: name, service_type, port"
                }
            
            if not service_type.startswith('_'):
                service_type = f"_{service_type}"
                
            if protocol not in ('tcp', 'udp'):
                return {
                    'success': False,
                    'message': f"Invalid protocol: {protocol}, must be 'tcp' or 'udp'"
                }
                
            # Use hostname if host not specified
            if not host:
                host = socket.gethostname()
            
            # Create XML service file
            service_file = os.path.join(self.service_dir, f"{name}.service")
            
            # Generate XML content
            xml_content = f"""<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>{name}</name>
  <service>
    <type>{service_type}._{protocol}</type>
    <port>{port}</port>
"""
            
            # Add TXT records if provided
            if txt_records:
                for key, value in txt_records.items():
                    xml_content += f'    <txt-record>{key}={value}</txt-record>\n'
                
            xml_content += """  </service>
</service-group>
"""
            
            # Write service file
            result = self._exec_command(f"cat > {service_file} << 'EOL'\n{xml_content}\nEOL")
            
            if not result['success']:
                return {
                    'success': False,
                    'message': f"Failed to create service file: {result.get('error')}"
                }
            
            # Reload Avahi
            reload_result = self._exec_command('systemctl reload avahi-daemon')
            
            if not reload_result['success']:
                return {
                    'success': False,
                    'message': f"Service file created but failed to reload Avahi: {reload_result.get('error')}"
                }
            
            return {
                'success': True,
                'message': f"Service {name} registered successfully",
                'service_file': service_file,
                'service_type': f"{service_type}._{protocol}"
            }
            
        except Exception as e:
            logger.error(f"Error registering service {name}: {str(e)}")
            return {
                'success': False,
                'message': f"Error registering service: {str(e)}"
            }
    
    def unregister_service(self, name: str) -> Dict[str, Any]:
        """Unregister a service from mDNS/Avahi
        
        Args:
            name: Service name
            
        Returns:
            Dict with unregistration result
        """
        try:
            service_file = os.path.join(self.service_dir, f"{name}.service")
            
            # Check if service exists
            check_result = self._exec_command(f"test -f {service_file} && echo 'exists'")
            
            if not check_result['success'] or 'exists' not in check_result.get('output', ''):
                return {
                    'success': False,
                    'message': f"Service {name} not found"
                }
            
            # Remove service file
            remove_result = self._exec_command(f"rm -f {service_file}")
            
            if not remove_result['success']:
                return {
                    'success': False,
                    'message': f"Failed to remove service file: {remove_result.get('error')}"
                }
            
            # Reload Avahi
            reload_result = self._exec_command('systemctl reload avahi-daemon')
            
            if not reload_result['success']:
                return {
                    'success': False,
                    'message': f"Service file removed but failed to reload Avahi: {reload_result.get('error')}"
                }
            
            return {
                'success': True,
                'message': f"Service {name} unregistered successfully"
            }
            
        except Exception as e:
            logger.error(f"Error unregistering service {name}: {str(e)}")
            return {
                'success': False,
                'message': f"Error unregistering service: {str(e)}"
            }
    
    def list_services(self) -> Dict[str, Any]:
        """List all registered mDNS/Avahi services
        
        Returns:
            Dict with list of services
        """
        try:
            # List service files
            result = self._exec_command(f"ls -1 {self.service_dir}/*.service 2>/dev/null || true")
            
            if not result['success']:
                return {
                    'success': False,
                    'message': f"Failed to list services: {result.get('error')}"
                }
            
            service_files = result.get('output', '').strip().split('\n')
            services = []
            
            # No services found
            if not service_files or (len(service_files) == 1 and not service_files[0]):
                return {
                    'success': True,
                    'message': "No services registered",
                    'services': []
                }
            
            # Parse each service file
            for service_file in service_files:
                if not service_file:
                    continue
                    
                name = os.path.basename(service_file).replace('.service', '')
                
                # Read file content
                content_result = self._exec_command(f"cat {service_file}")
                
                if content_result['success']:
                    content = content_result.get('output', '')
                    
                    # Extract service type and port
                    service_type_match = re.search(r'<type>([^<]+)</type>', content)
                    port_match = re.search(r'<port>([^<]+)</port>', content)
                    
                    service_type = service_type_match.group(1) if service_type_match else 'unknown'
                    port = port_match.group(1) if port_match else 'unknown'
                    
                    services.append({
                        'name': name,
                        'service_type': service_type,
                        'port': port,
                        'file': service_file
                    })
            
            return {
                'success': True,
                'message': f"Found {len(services)} service(s)",
                'services': services
            }
            
        except Exception as e:
            logger.error(f"Error listing services: {str(e)}")
            return {
                'success': False,
                'message': f"Error listing services: {str(e)}"
            }
    
    def discover_services(self, service_type: Optional[str] = None) -> Dict[str, Any]:
        """Discover mDNS/Avahi services on the network
        
        Args:
            service_type: Optional service type filter (e.g., _http._tcp)
            
        Returns:
            Dict with discovered services
        """
        try:
            # Build command based on presence of service type filter
            if service_type:
                if not service_type.startswith('_'):
                    service_type = f"_{service_type}"
                    
                if '.' not in service_type:
                    service_type = f"{service_type}._tcp"
                    
                cmd = f"avahi-browse {service_type} -t -r -p"
            else:
                cmd = "avahi-browse -a -t -r -p"
            
            # Execute discovery command
            result = self._exec_command(cmd)
            
            if not result['success']:
                return {
                    'success': False,
                    'message': f"Failed to discover services: {result.get('error')}"
                }
            
            output = result.get('output', '')
            discovered = []
            
            # Parse avahi-browse output
            current_service = None
            for line in output.split('\n'):
                line = line.strip()
                
                if not line or line.startswith('=') or line.startswith('-'):
                    continue
                    
                if line.startswith('+'):
                    # New service entry
                    parts = line.split(';')
                    if len(parts) >= 4:
                        current_service = {
                            'interface': parts[1],
                            'service_type': parts[2],
                            'name': parts[3],
                            'hostname': '',
                            'address': '',
                            'port': ''
                        }
                        
                elif line.startswith(' ') and current_service:
                    # Service details
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'hostname':
                            current_service['hostname'] = value
                        elif key == 'address':
                            current_service['address'] = value
                        elif key == 'port':
                            current_service['port'] = value
                            # Add completed service to results
                            discovered.append(current_service.copy())
                            current_service = None
            
            return {
                'success': True,
                'message': f"Discovered {len(discovered)} service(s)",
                'services': discovered
            }
            
        except Exception as e:
            logger.error(f"Error discovering services: {str(e)}")
            return {
                'success': False,
                'message': f"Error discovering services: {str(e)}"
            }
    
    def _exec_command(self, command: str) -> Dict[str, Union[bool, str]]:
        """Execute a command on the node
        
        Args:
            command: Command to execute
            
        Returns:
            Dict with command execution result
        """
        try:
            # Use the node's API to execute the command
            result = self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': command
            })
            
            if not result.get('success', False):
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error')
                }
            
            return {
                'success': True,
                'output': result.get('data', '')
            }
            
        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }