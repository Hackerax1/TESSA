"""
PXE boot service management operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional
import os

class PXEManager:
    def __init__(self, api):
        self.api = api
        self.pxe_path = '/var/lib/tftpboot'

    def enable_pxe_service(self, network_interface: str = "vmbr0", subnet: Optional[str] = None) -> Dict[str, Any]:
        """Set up PXE service for network booting
        
        Args:
            network_interface: Network interface to serve PXE on
            subnet: Optional subnet for DHCP
            
        Returns:
            Dict with operation result
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Install required packages
        install_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': 'apt-get install -y tftpd-hpa syslinux pxelinux'
        })
        
        if not install_result['success']:
            return install_result
        
        # Create required directories
        setup_commands = [
            f'mkdir -p {self.pxe_path}/pxelinux.cfg',
            f'cp /usr/lib/PXELINUX/pxelinux.0 {self.pxe_path}/',
            f'cp /usr/lib/syslinux/modules/bios/*.c32 {self.pxe_path}/'
        ]
        
        for cmd in setup_commands:
            result = self.api.api_request('POST', f'nodes/{node}/execute', {
                'command': cmd
            })
            if not result['success']:
                return result
        
        # Configure TFTP
        tftp_config = (
            'TFTP_USERNAME="tftp"\n'
            'TFTP_DIRECTORY="/var/lib/tftpboot"\n'
            'TFTP_ADDRESS=":69"\n'
            'TFTP_OPTIONS="--secure"'
        )
        
        config_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'echo "{tftp_config}" > /etc/default/tftpd-hpa'
        })
        
        if not config_result['success']:
            return config_result
        
        # Start services
        services_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': 'systemctl restart tftpd-hpa'
        })
        
        if services_result['success']:
            return {"success": True, "message": "PXE service enabled successfully"}
        return services_result

    def disable_pxe_service(self) -> Dict[str, Any]:
        """Disable PXE boot service
        
        Returns:
            Dict with operation result
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Stop and disable services
        services_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': 'systemctl stop tftpd-hpa && systemctl disable tftpd-hpa'
        })
        
        if services_result['success']:
            return {"success": True, "message": "PXE service disabled successfully"}
        return services_result

    def get_pxe_status(self) -> Dict[str, Any]:
        """Get PXE service status
        
        Returns:
            Dict with service status
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Check service status
        service_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': 'systemctl status tftpd-hpa'
        })
        
        if not service_result['success']:
            return service_result
        
        # Parse status output
        output = service_result['data']
        active = 'Active: active (running)' in output
        enabled = 'enabled;' in output
        
        return {
            "success": True,
            "message": "PXE service status",
            "status": {
                "active": active,
                "enabled": enabled,
                "tftp_path": self.pxe_path
            }
        }

    def upload_boot_image(self, image_type: str, image_path: str) -> Dict[str, Any]:
        """Upload a boot image for PXE
        
        Args:
            image_type: Type of image (e.g., 'ubuntu', 'centos')
            image_path: Local path to boot image
            
        Returns:
            Dict with operation result
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Create directory for image type
        image_dir = f"{self.pxe_path}/images/{image_type}"
        mkdir_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'mkdir -p {image_dir}'
        })
        
        if not mkdir_result['success']:
            return mkdir_result
        
        # Copy image file
        copy_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'cp {image_path} {image_dir}/'
        })
        
        if not copy_result['success']:
            return copy_result
        
        # Update PXE configuration
        config_path = f"{self.pxe_path}/pxelinux.cfg/default"
        menu_entry = (
            f'LABEL {image_type}\n'
            f'  MENU LABEL Boot {image_type}\n'
            f'  KERNEL images/{image_type}/vmlinuz\n'
            f'  APPEND initrd=images/{image_type}/initrd.img'
        )
        
        config_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'echo "{menu_entry}" >> {config_path}'
        })
        
        if config_result['success']:
            return {"success": True, "message": f"Added boot image for {image_type}"}
        return config_result

    def list_boot_images(self) -> Dict[str, Any]:
        """List available PXE boot images
        
        Returns:
            Dict with list of boot images
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # List images directory
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'ls -l {self.pxe_path}/images/'
        })
        
        if not result['success']:
            return result
        
        images = []
        for line in result['data'].splitlines():
            if line.startswith('d'):  # Directory
                parts = line.split()
                if len(parts) >= 9:
                    image_type = parts[8]
                    images.append({
                        'type': image_type,
                        'path': f"{self.pxe_path}/images/{image_type}"
                    })
        
        return {
            "success": True,
            "message": "PXE boot images",
            "images": images
        }