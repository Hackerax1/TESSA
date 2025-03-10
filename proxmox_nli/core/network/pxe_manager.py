"""
PXE Manager module for Proxmox NLI.
Handles PXE boot service configuration and management.
"""
import os
import logging
import ipaddress
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PXEManager:
    def __init__(self, api):
        self.api = api
        self.tftp_root = "/srv/tftp"
        self.pxe_config_dir = "/srv/pxe/pxelinux.cfg"
        self.default_services = ["tftpd-hpa", "dnsmasq"]
    
    def enable_pxe_service(self, network_interface: str = "vmbr0", subnet: str = None) -> dict:
        """Enable PXE boot service
        
        Args:
            network_interface: Network interface to serve PXE on
            subnet: Subnet to serve DHCP on (optional)
            
        Returns:
            dict: Result of operation
        """
        try:
            # Check if required packages are installed
            for service in self.default_services:
                check_cmd = f"dpkg -l | grep {service}"
                result = self.api.api_request('POST', 'nodes/localhost/execute', {
                    'command': check_cmd
                })
                
                if not result.get('success', False) or not result.get('data', ''):
                    # Install the package
                    install_cmd = f"apt-get update && apt-get install -y {service}"
                    install_result = self.api.api_request('POST', 'nodes/localhost/execute', {
                        'command': install_cmd
                    })
                    
                    if not install_result.get('success', False):
                        return {
                            'success': False,
                            'message': f"Failed to install {service}"
                        }
            
            # Create necessary directories
            mkdir_cmd = f"mkdir -p {self.tftp_root} {self.pxe_config_dir}"
            self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': mkdir_cmd
            })
            
            # Configure TFTP service
            tftp_config = f"""
# /etc/default/tftpd-hpa
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="{self.tftp_root}"
TFTP_ADDRESS="0.0.0.0:69"
TFTP_OPTIONS="--secure"
"""
            
            # Write TFTP config
            write_cmd = f"cat > /etc/default/tftpd-hpa << 'EOL'\n{tftp_config}\nEOL"
            self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': write_cmd
            })
            
            # Configure dnsmasq for DHCP+PXE if subnet provided
            if subnet:
                try:
                    # Validate subnet
                    network = ipaddress.IPv4Network(subnet)
                    
                    # Get first usable IP for range start
                    start_ip = network.network_address + 100
                    # Get last usable IP for range end
                    end_ip = network.broadcast_address - 1
                    
                    dnsmasq_config = f"""
# PXE boot server configuration
interface={network_interface}
dhcp-range={start_ip},{end_ip},12h
dhcp-boot=pxelinux.0
enable-tftp
tftp-root={self.tftp_root}
"""
                    
                    # Write dnsmasq config
                    write_cmd = f"cat > /etc/dnsmasq.d/pxeboot.conf << 'EOL'\n{dnsmasq_config}\nEOL"
                    self.api.api_request('POST', 'nodes/localhost/execute', {
                        'command': write_cmd
                    })
                    
                except ValueError:
                    return {
                        'success': False,
                        'message': f'Invalid subnet: {subnet}'
                    }
            
            # Restart services
            for service in self.default_services:
                restart_cmd = f"systemctl restart {service}"
                self.api.api_request('POST', 'nodes/localhost/execute', {
                    'command': restart_cmd
                })
                
                # Enable service to start at boot
                enable_cmd = f"systemctl enable {service}"
                self.api.api_request('POST', 'nodes/localhost/execute', {
                    'command': enable_cmd
                })
            
            return {
                'success': True,
                'message': 'PXE boot service enabled successfully',
                'tftp_root': self.tftp_root,
                'pxe_config_dir': self.pxe_config_dir
            }
            
        except Exception as e:
            logger.error(f"Error enabling PXE service: {str(e)}")
            return {
                'success': False,
                'message': f'Error enabling PXE service: {str(e)}'
            }
    
    def disable_pxe_service(self) -> dict:
        """Disable PXE boot service
        
        Returns:
            dict: Result of operation
        """
        try:
            # Stop services
            for service in self.default_services:
                stop_cmd = f"systemctl stop {service}"
                self.api.api_request('POST', 'nodes/localhost/execute', {
                    'command': stop_cmd
                })
                
                # Disable service at boot
                disable_cmd = f"systemctl disable {service}"
                self.api.api_request('POST', 'nodes/localhost/execute', {
                    'command': disable_cmd
                })
            
            # Remove dnsmasq config
            rm_config_cmd = "rm -f /etc/dnsmasq.d/pxeboot.conf"
            self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': rm_config_cmd
            })
            
            return {
                'success': True,
                'message': 'PXE boot service disabled successfully'
            }
            
        except Exception as e:
            logger.error(f"Error disabling PXE service: {str(e)}")
            return {
                'success': False,
                'message': f'Error disabling PXE service: {str(e)}'
            }
    
    def upload_boot_image(self, image_type: str, image_path: str) -> dict:
        """Upload a boot image for PXE
        
        Args:
            image_type: Type of image (e.g., 'ubuntu', 'centos')
            image_path: Local path to boot image
            
        Returns:
            dict: Result of operation
        """
        try:
            # Create directory for the image
            img_dir = f"{self.tftp_root}/{image_type}"
            mkdir_cmd = f"mkdir -p {img_dir}"
            self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': mkdir_cmd
            })
            
            # Check if image exists locally
            check_file_cmd = f"ls -la {image_path}"
            check_result = self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': check_file_cmd
            })
            
            if not check_result.get('success', False) or "No such file" in check_result.get('data', ''):
                return {
                    'success': False,
                    'message': f"Image not found: {image_path}"
                }
            
            # Copy image to TFTP root
            copy_cmd = f"cp -rf {image_path} {img_dir}/"
            copy_result = self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': copy_cmd
            })
            
            if not copy_result.get('success', False):
                return copy_result
            
            # Update PXE configuration
            self._update_pxe_config(image_type, os.path.basename(image_path))
            
            return {
                'success': True,
                'message': f'Boot image for {image_type} uploaded successfully',
                'location': f"{img_dir}/{os.path.basename(image_path)}"
            }
            
        except Exception as e:
            logger.error(f"Error uploading boot image: {str(e)}")
            return {
                'success': False,
                'message': f'Error uploading boot image: {str(e)}'
            }
    
    def list_boot_images(self) -> dict:
        """List available boot images
        
        Returns:
            dict: List of available boot images
        """
        try:
            ls_cmd = f"find {self.tftp_root} -type f -name '*.iso' -o -name '*.img' -o -name 'vmlinuz*' | sort"
            result = self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': ls_cmd
            })
            
            if not result.get('success', False):
                return result
            
            images = []
            for line in result.get('data', '').splitlines():
                if line.strip():
                    images.append(line.strip())
            
            return {
                'success': True,
                'message': f'Found {len(images)} boot images',
                'images': images
            }
            
        except Exception as e:
            logger.error(f"Error listing boot images: {str(e)}")
            return {
                'success': False,
                'message': f'Error listing boot images: {str(e)}',
                'images': []
            }
    
    def get_pxe_status(self) -> dict:
        """Get PXE service status
        
        Returns:
            dict: Status of PXE services
        """
        try:
            status = {}
            
            # Check status of all services
            for service in self.default_services:
                status_cmd = f"systemctl is-active {service}"
                result = self.api.api_request('POST', 'nodes/localhost/execute', {
                    'command': status_cmd
                })
                
                if result.get('success', False):
                    is_active = result.get('data', '').strip() == 'active'
                    status[service] = 'running' if is_active else 'stopped'
                else:
                    status[service] = 'unknown'
            
            # Check if config files exist
            config_status = {}
            config_files = [
                '/etc/default/tftpd-hpa',
                '/etc/dnsmasq.d/pxeboot.conf'
            ]
            
            for cfg in config_files:
                check_cmd = f"test -f {cfg} && echo 'exists' || echo 'missing'"
                result = self.api.api_request('POST', 'nodes/localhost/execute', {
                    'command': check_cmd
                })
                
                if result.get('success', False):
                    config_status[cfg] = result.get('data', '').strip()
                else:
                    config_status[cfg] = 'unknown'
            
            return {
                'success': True,
                'message': 'PXE service status',
                'services': status,
                'configs': config_status
            }
            
        except Exception as e:
            logger.error(f"Error getting PXE status: {str(e)}")
            return {
                'success': False,
                'message': f'Error getting PXE status: {str(e)}'
            }
    
    def _update_pxe_config(self, image_type: str, image_name: str) -> bool:
        """Update PXE boot configuration
        
        Args:
            image_type: Type of image (e.g., 'ubuntu', 'centos')
            image_name: Name of the image file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create default PXE config
            default_config = f"""DEFAULT menu.c32
PROMPT 0
TIMEOUT 300
ONTIMEOUT local
MENU TITLE PXE Boot Menu

LABEL local
    MENU LABEL Boot from local disk
    LOCALBOOT 0

LABEL {image_type}
    MENU LABEL Boot {image_type.capitalize()}
    KERNEL {image_type}/vmlinuz
    APPEND initrd={image_type}/initrd root=/dev/ram0 ramdisk_size=1500000
"""
            
            # Write default PXE config
            write_cmd = f"cat > {self.pxe_config_dir}/default << 'EOL'\n{default_config}\nEOL"
            result = self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': write_cmd
            })
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error updating PXE config: {str(e)}")
            return False