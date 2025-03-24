"""
Firewall management operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional

class FirewallManager:
    def __init__(self, api):
        self.api = api

    def add_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Add a firewall rule
        
        Args:
            rule: Rule definition including:
                - action: ACCEPT, DROP, REJECT
                - type: in, out
                - proto: Protocol (tcp, udp, etc.)
                - dport: Destination port(s)
                - source: Source address (optional)
                - dest: Destination address (optional)
                - comment: Rule description
            
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
        
        # Add rule
        result = self.api.api_request('POST', f'nodes/{node}/firewall/rules', rule)
        if result['success']:
            return {"success": True, "message": "Firewall rule added successfully"}
        return result

    def list_rules(self) -> Dict[str, Any]:
        """List all firewall rules
        
        Returns:
            Dict with list of firewall rules
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        result = self.api.api_request('GET', f'nodes/{node}/firewall/rules')
        if not result['success']:
            return result
        
        rules = []
        for rule in result['data']:
            rules.append({
                'pos': rule.get('pos', 0),
                'action': rule.get('action', ''),
                'type': rule.get('type', ''),
                'proto': rule.get('proto', ''),
                'dport': rule.get('dport', ''),
                'source': rule.get('source', ''),
                'dest': rule.get('dest', ''),
                'comment': rule.get('comment', '')
            })
        
        return {"success": True, "message": "Firewall rules", "rules": rules}

    def delete_rule(self, rule_id: int) -> Dict[str, Any]:
        """Delete a firewall rule
        
        Args:
            rule_id: ID of the rule to delete
            
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
        
        result = self.api.api_request('DELETE', f'nodes/{node}/firewall/rules/{rule_id}')
        if result['success']:
            return {"success": True, "message": f"Deleted firewall rule {rule_id}"}
        return result

    def add_service_rules(self, service_name: str, ports: List[int], sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Add firewall rules for a service
        
        Args:
            service_name: Name of the service (for comments)
            ports: List of ports to allow
            sources: Optional list of source IPs/networks
            
        Returns:
            Dict with operation result
        """
        success = True
        messages = []
        
        for port in ports:
            rule = {
                'action': 'ACCEPT',
                'type': 'in',
                'proto': 'tcp',
                'dport': str(port),
                'comment': f"Allow {service_name} on port {port}"
            }
            
            if sources:
                for source in sources:
                    rule['source'] = source
                    result = self.add_rule(rule)
                    if not result['success']:
                        success = False
                        messages.append(f"Failed to add rule for {service_name} port {port} from {source}")
            else:
                result = self.add_rule(rule)
                if not result['success']:
                    success = False
                    messages.append(f"Failed to add rule for {service_name} port {port}")
                
        if success:
            return {"success": True, "message": f"Added firewall rules for {service_name}"}
        else:
            return {"success": False, "message": "Failed to add some rules", "details": messages}

    def get_firewall_status(self) -> Dict[str, Any]:
        """Get firewall status
        
        Returns:
            Dict with firewall status information
        """
        # Get first cluster node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Get firewall status
        result = self.api.api_request('GET', f'nodes/{node}/firewall')
        if not result['success']:
            return result
        
        # Get active rules count
        rules_result = self.list_rules()
        rules_count = len(rules_result.get('rules', [])) if rules_result['success'] else 0
        
        return {
            "success": True,
            "message": "Firewall status",
            "status": {
                "enabled": result['data'].get('enable', False),
                "logging": result['data'].get('log', 'nolog'),
                "rules_count": rules_count
            }
        }

    def toggle_firewall(self, enable: bool) -> Dict[str, Any]:
        """Enable or disable the firewall
        
        Args:
            enable: Whether to enable (True) or disable (False) the firewall
            
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
        
        result = self.api.api_request('PUT', f'nodes/{node}/firewall', {
            'enable': enable
        })
        
        if result['success']:
            status = "enabled" if enable else "disabled"
            return {"success": True, "message": f"Firewall {status} successfully"}
        return result