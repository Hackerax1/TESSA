"""
Container management operations for Proxmox NLI.
"""
from typing import Dict, Any, List

class ContainerManager:
    def __init__(self, api):
        self.api = api

    def list_containers(self) -> Dict[str, Any]:
        """List all LXC containers"""
        result = self.api.api_request('GET', 'cluster/resources?type=lxc')
        if result['success']:
            containers = []
            for ct in result['data']:
                containers.append({
                    'id': ct['vmid'],
                    'name': ct.get('name', f"CT {ct['vmid']}"),
                    'status': ct['status'],
                    'node': ct['node']
                })
            return {"success": True, "message": "Found containers", "containers": containers}
        return result

    def create_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new LXC container"""
        # Get first available node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Get next available ID
        nextid_result = self.api.api_request('GET', 'cluster/nextid')
        if not nextid_result['success']:
            return nextid_result
        
        ct_id = nextid_result['data']
        
        # Default parameters
        create_params = {
            'vmid': ct_id,
            'hostname': params.get('hostname', f'ct-{ct_id}'),
            'cores': params.get('cores', 1),
            'memory': params.get('memory', 512),
            'swap': params.get('swap', 512),
            'storage': params.get('storage', 'local-lvm'),
            'password': params.get('password', 'changeme'),
            'ostemplate': params.get('ostemplate', 'local:vztmpl/ubuntu-20.04-standard_20.04-1_amd64.tar.gz')
        }
        
        # Create container
        result = self.api.api_request('POST', f'nodes/{node}/lxc', create_params)
        if result['success']:
            return {"success": True, "message": f"Container {ct_id} created successfully"}
        return result

    def start_container(self, ct_id: str) -> Dict[str, Any]:
        """Start a container"""
        # Find container node
        result = self.api.api_request('GET', 'cluster/resources?type=lxc')
        if not result['success']:
            return result
        
        node = None
        for ct in result['data']:
            if str(ct['vmid']) == str(ct_id):
                node = ct['node']
                break
        
        if not node:
            return {"success": False, "message": f"Container {ct_id} not found"}
        
        result = self.api.api_request('POST', f'nodes/{node}/lxc/{ct_id}/status/start')
        if result['success']:
            return {"success": True, "message": f"Container {ct_id} started successfully"}
        return result

    def stop_container(self, ct_id: str) -> Dict[str, Any]:
        """Stop a container"""
        # Find container node
        result = self.api.api_request('GET', 'cluster/resources?type=lxc')
        if not result['success']:
            return result
        
        node = None
        for ct in result['data']:
            if str(ct['vmid']) == str(ct_id):
                node = ct['node']
                break
        
        if not node:
            return {"success": False, "message": f"Container {ct_id} not found"}
        
        result = self.api.api_request('POST', f'nodes/{node}/lxc/{ct_id}/status/stop')
        if result['success']:
            return {"success": True, "message": f"Container {ct_id} stopped successfully"}
        return result

    def delete_container(self, ct_id: str) -> Dict[str, Any]:
        """Delete a container"""
        # Find container node
        result = self.api.api_request('GET', 'cluster/resources?type=lxc')
        if not result['success']:
            return result
        
        node = None
        for ct in result['data']:
            if str(ct['vmid']) == str(ct_id):
                node = ct['node']
                break
        
        if not node:
            return {"success": False, "message": f"Container {ct_id} not found"}
        
        result = self.api.api_request('DELETE', f'nodes/{node}/lxc/{ct_id}')
        if result['success']:
            return {"success": True, "message": f"Container {ct_id} deleted successfully"}
        return result

    def get_container_status(self, ct_id: str) -> Dict[str, Any]:
        """Get status of a container"""
        # Find container node
        result = self.api.api_request('GET', 'cluster/resources?type=lxc')
        if not result['success']:
            return result
        
        node = None
        container_info = None
        for ct in result['data']:
            if str(ct['vmid']) == str(ct_id):
                node = ct['node']
                container_info = ct
                break
        
        if not node:
            return {"success": False, "message": f"Container {ct_id} not found"}
        
        result = self.api.api_request('GET', f'nodes/{node}/lxc/{ct_id}/status/current')
        if result['success']:
            status = result['data']
            return {
                "success": True,
                "message": f"Container {ct_id} status",
                "status": {
                    "name": container_info.get('name', f'ct-{ct_id}'),
                    "status": status['status'],
                    "cpu": status.get('cpu', 0),
                    "memory": status.get('mem', 0) / (1024*1024),  # Convert to MB
                    "swap": status.get('swap', 0) / (1024*1024),  # Convert to MB
                    "uptime": status.get('uptime', 0)
                }
            }
        return result