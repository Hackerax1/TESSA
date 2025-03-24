"""
DNS management operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional

class DNSManager:
    def __init__(self, api):
        self.api = api

    def add_dns_record(self, hostname: str, ip_address: str, comment: Optional[str] = None) -> Dict[str, Any]:
        """Add a DNS record
        
        Args:
            hostname: Hostname to add
            ip_address: IP address for hostname
            comment: Optional comment
            
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
        
        # Add hosts entry
        config = {
            'hostname': hostname,
            'ip': ip_address,
            'comment': comment or ''
        }
        
        result = self.api.api_request('POST', f'nodes/{node}/dns', config)
        if result['success']:
            return {"success": True, "message": f"Added DNS record for {hostname}"}
        return result

    def list_dns_records(self) -> Dict[str, Any]:
        """List all DNS records
        
        Returns:
            Dict with list of DNS records
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        result = self.api.api_request('GET', f'nodes/{node}/dns')
        if not result['success']:
            return result
        
        records = []
        for record in result['data']:
            records.append({
                'hostname': record.get('hostname', ''),
                'ip': record.get('ip', ''),
                'comment': record.get('comment', '')
            })
        
        return {"success": True, "message": "DNS records", "records": records}

    def delete_dns_record(self, hostname: str) -> Dict[str, Any]:
        """Delete a DNS record
        
        Args:
            hostname: Hostname to delete
            
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
        
        result = self.api.api_request('DELETE', f'nodes/{node}/dns/{hostname}')
        if result['success']:
            return {"success": True, "message": f"Deleted DNS record for {hostname}"}
        return result

    def update_dns_servers(self, servers: List[str]) -> Dict[str, Any]:
        """Update DNS servers
        
        Args:
            servers: List of DNS server IP addresses
            
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
        
        # Update resolv.conf through API
        config = {
            'dns1': servers[0] if len(servers) > 0 else None,
            'dns2': servers[1] if len(servers) > 1 else None,
            'dns3': servers[2] if len(servers) > 2 else None
        }
        
        result = self.api.api_request('PUT', f'nodes/{node}/dns', config)
        if result['success']:
            return {"success": True, "message": "Updated DNS servers"}
        return result

    def get_dns_servers(self) -> Dict[str, Any]:
        """Get configured DNS servers
        
        Returns:
            Dict with list of DNS servers
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        result = self.api.api_request('GET', f'nodes/{node}/dns')
        if not result['success']:
            return result
        
        servers = []
        if result['data'].get('dns1'):
            servers.append(result['data']['dns1'])
        if result['data'].get('dns2'):
            servers.append(result['data']['dns2'])
        if result['data'].get('dns3'):
            servers.append(result['data']['dns3'])
        
        return {
            "success": True,
            "message": "DNS servers",
            "servers": servers
        }

    def check_dns_resolution(self, hostname: str) -> Dict[str, Any]:
        """Test DNS resolution for a hostname
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            Dict with resolution result
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Use dig command to test resolution
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'dig +short {hostname}'
        })
        
        if not result['success']:
            return result
        
        ip_address = result['data'].strip()
        if ip_address:
            return {
                "success": True,
                "message": f"Successfully resolved {hostname}",
                "ip": ip_address
            }
        else:
            return {
                "success": False,
                "message": f"Failed to resolve {hostname}"
            }