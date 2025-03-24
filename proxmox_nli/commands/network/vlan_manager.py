"""
VLAN management operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional

class VLANManager:
    def __init__(self, api):
        self.api = api

    def create_vlan(self, vlan_id: int, name: str, subnet: str, bridge: str = "vmbr0") -> Dict[str, Any]:
        """Create a new VLAN
        
        Args:
            vlan_id: VLAN ID (1-4094)
            name: Name of the VLAN
            subnet: Subnet in CIDR notation
            bridge: Bridge interface to attach VLAN to
            
        Returns:
            Dict with operation result
        """
        # Get first node in cluster for initial config
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Create VLAN interface config
        iface_name = f"{bridge}.{vlan_id}"
        config = {
            'type': 'vlan',
            'name': iface_name,
            'vlan-id': vlan_id,
            'vlan-raw-device': bridge,
            'cidr': subnet,
            'comments': name
        }
        
        result = self.api.api_request('POST', f'nodes/{node}/network', config)
        if not result['success']:
            return result
        
        # Apply network changes
        apply_result = self.api.api_request('POST', f'nodes/{node}/network/reload')
        if apply_result['success']:
            return {"success": True, "message": f"Created VLAN {name} (ID: {vlan_id}) on {bridge}"}
        return apply_result

    def list_vlans(self, node: Optional[str] = None) -> Dict[str, Any]:
        """List all configured VLANs
        
        Args:
            node: Optional node name to filter VLANs
            
        Returns:
            Dict with list of VLANs
        """
        if not node:
            # Get first available node
            nodes_result = self.api.api_request('GET', 'nodes')
            if not nodes_result['success']:
                return nodes_result
            if not nodes_result['data']:
                return {"success": False, "message": "No nodes available"}
            node = nodes_result['data'][0]['node']
        
        result = self.api.api_request('GET', f'nodes/{node}/network')
        if not result['success']:
            return result
        
        vlans = []
        for iface in result['data']:
            if iface.get('type') == 'vlan':
                vlans.append({
                    'name': iface.get('name', ''),
                    'vlan_id': iface.get('vlan-id'),
                    'bridge': iface.get('vlan-raw-device'),
                    'cidr': iface.get('cidr'),
                    'comments': iface.get('comments', '')
                })
        
        return {"success": True, "message": "VLANs", "vlans": vlans}

    def delete_vlan(self, vlan_id: int, bridge: str = "vmbr0") -> Dict[str, Any]:
        """Delete a VLAN
        
        Args:
            vlan_id: VLAN ID to delete
            bridge: Bridge interface
            
        Returns:
            Dict with operation result
        """
        # Get first node in cluster
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        iface_name = f"{bridge}.{vlan_id}"
        
        result = self.api.api_request('DELETE', f'nodes/{node}/network/{iface_name}')
        if not result['success']:
            return result
        
        # Apply network changes
        apply_result = self.api.api_request('POST', f'nodes/{node}/network/reload')
        if apply_result['success']:
            return {"success": True, "message": f"Deleted VLAN {vlan_id} from {bridge}"}
        return apply_result

    def assign_vm_to_vlan(self, vm_id: str, vlan_id: int, bridge: str = "vmbr0") -> Dict[str, Any]:
        """Assign a VM to a VLAN
        
        Args:
            vm_id: ID of the VM
            vlan_id: ID of the VLAN
            bridge: Bridge interface
            
        Returns:
            Dict with operation result
        """
        # Find VM node
        vm_result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not vm_result['success']:
            return vm_result
        
        node = None
        for vm in vm_result['data']:
            if str(vm['vmid']) == str(vm_id):
                node = vm['node']
                break
        
        if not node:
            return {"success": False, "message": f"VM {vm_id} not found"}
        
        # Get VM config
        config_result = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/config')
        if not config_result['success']:
            return config_result
        
        # Update network interface config
        net_config = f"model=virtio,bridge={bridge},tag={vlan_id}"
        update_result = self.api.api_request('PUT', f'nodes/{node}/qemu/{vm_id}/config', {
            'net0': net_config
        })
        
        if update_result['success']:
            return {"success": True, "message": f"Assigned VM {vm_id} to VLAN {vlan_id}"}
        return update_result