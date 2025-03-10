"""
VLAN management module for Proxmox NLI.
Handles VLAN creation and management.
"""
import logging
import ipaddress
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class VLANHandler:
    def __init__(self, api):
        self.api = api

    def create_vlan(self, vlan_id: int, name: str, subnet: str, bridge: str = "vmbr0") -> dict:
        """Create a new VLAN
        
        Args:
            vlan_id: VLAN ID (1-4094)
            name: VLAN name
            subnet: Subnet CIDR (e.g. 192.168.1.0/24)
            bridge: Bridge interface to attach VLAN to
            
        Returns:
            dict: Result of operation
        """
        try:
            # Validate VLAN ID
            if not 1 <= vlan_id <= 4094:
                return {
                    'success': False,
                    'message': f'Invalid VLAN ID: {vlan_id}. Must be between 1 and 4094'
                }
            
            # Validate subnet
            try:
                ipaddress.ip_network(subnet)
            except ValueError:
                return {
                    'success': False,
                    'message': f'Invalid subnet: {subnet}'
                }
                
            vlan_config = {
                'vlan_id': vlan_id,
                'name': name,
                'subnet': subnet,
                'bridge': bridge,
                'autostart': 1
            }
            
            # Create VLAN interface
            iface_name = f"{bridge}.{vlan_id}"
            iface_result = self.api.api_request('POST', 'nodes/localhost/network', {
                'type': 'vlan',
                'iface': iface_name,
                'vlan_id': vlan_id,
                'vlan_raw_device': bridge
            })
            
            if not iface_result.get('success', False):
                return iface_result
                
            # Apply network config
            apply_result = self.api.api_request('PUT', 'nodes/localhost/network', {
                'apply': 1
            })
            
            return {
                'success': True,
                'message': f'Successfully created VLAN {vlan_id} ({name}) on {bridge}',
                'vlan': {
                    'id': vlan_id,
                    'name': name,
                    'subnet': subnet,
                    'interface': iface_name
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating VLAN {vlan_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating VLAN: {str(e)}'
            }

    def delete_vlan(self, vlan_id: int, bridge: str = "vmbr0") -> dict:
        """Delete a VLAN by ID
        
        Args:
            vlan_id: VLAN ID to delete
            bridge: Bridge interface the VLAN is attached to
            
        Returns:
            dict: Result of operation
        """
        try:
            iface_name = f"{bridge}.{vlan_id}"
            
            # Delete VLAN interface
            result = self.api.api_request('DELETE', f'nodes/localhost/network/{iface_name}')
            
            if not result.get('success', False):
                return result
                
            # Apply network config
            apply_result = self.api.api_request('PUT', 'nodes/localhost/network', {
                'apply': 1
            })
            
            return {
                'success': True,
                'message': f'Successfully deleted VLAN {vlan_id} from {bridge}',
            }
            
        except Exception as e:
            logger.error(f"Error deleting VLAN {vlan_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error deleting VLAN: {str(e)}'
            }

    def list_vlans(self) -> dict:
        """List all VLANs
        
        Returns:
            dict: List of VLANs
        """
        try:
            result = self.api.api_request('GET', 'nodes/localhost/network')
            
            if not result.get('success', False):
                return result
                
            vlans = []
            for iface in result.get('data', []):
                if iface.get('type') == 'vlan':
                    vlans.append({
                        'id': iface.get('vlan_id'),
                        'name': iface.get('iface'),
                        'bridge': iface.get('vlan_raw_device')
                    })
            
            return {
                'success': True,
                'message': f'Found {len(vlans)} VLANs',
                'vlans': vlans
            }
            
        except Exception as e:
            logger.error(f"Error listing VLANs: {str(e)}")
            return {
                'success': False,
                'message': f'Error listing VLANs: {str(e)}',
                'vlans': []
            }
    
    def assign_vm_to_vlan(self, vm_id: int, vlan_id: int, bridge: str = "vmbr0") -> dict:
        """Assign a VM to a VLAN
        
        Args:
            vm_id: VM ID to assign
            vlan_id: VLAN ID to assign VM to
            bridge: Bridge interface
            
        Returns:
            dict: Result of operation
        """
        try:
            # Get VM location first
            vm_info = self.api.api_request('GET', 'cluster/resources?type=vm')
            if not vm_info.get('success', False):
                return vm_info
            
            node = None
            for vm in vm_info.get('data', []):
                if str(vm.get('vmid')) == str(vm_id):
                    node = vm.get('node')
                    break
            
            if not node:
                return {
                    'success': False,
                    'message': f'VM {vm_id} not found'
                }
            
            # Update VM network configuration
            net_config = {
                'net0': f'virtio,bridge={bridge},tag={vlan_id}'
            }
            
            result = self.api.api_request('PUT', f'nodes/{node}/qemu/{vm_id}/config', net_config)
            
            if not result.get('success', False):
                return result
            
            return {
                'success': True,
                'message': f'Successfully assigned VM {vm_id} to VLAN {vlan_id}',
            }
            
        except Exception as e:
            logger.error(f"Error assigning VM {vm_id} to VLAN {vlan_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error assigning VM to VLAN: {str(e)}'
            }
