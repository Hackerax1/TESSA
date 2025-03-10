"""
Firewall management module for Proxmox NLI.
Handles firewall rule configuration and management.
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FirewallManager:
    def __init__(self, api):
        self.api = api

    def add_rule(self, rule: dict) -> dict:
        """Add a new firewall rule
        
        Args:
            rule: Dictionary containing firewall rule parameters
                - action: ACCEPT, DROP, REJECT
                - type: in, out
                - source: Source IP/CIDR (optional)
                - dest: Destination IP/CIDR (optional)
                - proto: Protocol (tcp, udp, icmp, etc.)
                - dport: Destination port(s)
                - sport: Source port(s) (optional)
                - comment: Rule description
        """
        try:
            # Validate rule
            required = ['action', 'type']
            for field in required:
                if field not in rule:
                    return {
                        'success': False,
                        'message': f'Missing required field: {field}'
                    }
            
            return self.api.api_request('POST', 'nodes/localhost/firewall/rules', rule)
        except Exception as e:
            logger.error(f"Error adding firewall rule: {str(e)}")
            return {
                'success': False,
                'message': f'Error adding firewall rule: {str(e)}'
            }

    def delete_rule(self, rule_id: int) -> dict:
        """Delete a firewall rule by ID"""
        try:
            return self.api.api_request('DELETE', f'nodes/localhost/firewall/rules/{rule_id}')
        except Exception as e:
            logger.error(f"Error deleting firewall rule {rule_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error deleting firewall rule: {str(e)}'
            }

    def list_rules(self) -> dict:
        """List all firewall rules"""
        try:
            return self.api.api_request('GET', 'nodes/localhost/firewall/rules')
        except Exception as e:
            logger.error(f"Error listing firewall rules: {str(e)}")
            return {
                'success': False,
                'message': f'Error listing firewall rules: {str(e)}',
                'rules': []
            }
    
    def enable_firewall(self) -> dict:
        """Enable the firewall"""
        try:
            return self.api.api_request('PUT', 'nodes/localhost/firewall/options', {
                'enable': 1
            })
        except Exception as e:
            logger.error(f"Error enabling firewall: {str(e)}")
            return {
                'success': False,
                'message': f'Error enabling firewall: {str(e)}'
            }
    
    def disable_firewall(self) -> dict:
        """Disable the firewall"""
        try:
            return self.api.api_request('PUT', 'nodes/localhost/firewall/options', {
                'enable': 0
            })
        except Exception as e:
            logger.error(f"Error disabling firewall: {str(e)}")
            return {
                'success': False,
                'message': f'Error disabling firewall: {str(e)}'
            }
    
    def get_firewall_status(self) -> dict:
        """Get firewall status"""
        try:
            return self.api.api_request('GET', 'nodes/localhost/firewall/options')
        except Exception as e:
            logger.error(f"Error getting firewall status: {str(e)}")
            return {
                'success': False,
                'message': f'Error getting firewall status: {str(e)}'
            }
    
    def add_service_rules(self, service_name: str, ports: List[int], sources: List[str] = None) -> dict:
        """Add rules for a common service
        
        Args:
            service_name: Name of service (for comment)
            ports: List of ports to open
            sources: List of source IPs/CIDRs (None for any)
        """
        try:
            results = []
            for port in ports:
                rule = {
                    'action': 'ACCEPT',
                    'type': 'in',
                    'proto': 'tcp',
                    'dport': str(port),
                    'comment': f'Allow {service_name} ({port}/tcp)'
                }
                
                if sources:
                    for source in sources:
                        rule['source'] = source
                        result = self.add_rule(rule)
                        results.append(result)
                else:
                    result = self.add_rule(rule)
                    results.append(result)
            
            success = all(r.get('success', False) for r in results)
            return {
                'success': success,
                'message': f'{"Successfully" if success else "Failed to"} add rules for {service_name}',
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error adding service rules for {service_name}: {str(e)}")
            return {
                'success': False,
                'message': f'Error adding service rules: {str(e)}'
            }
