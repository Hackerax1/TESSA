"""
DNS management module for Proxmox NLI.
Handles DNS configuration and management.
"""
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DNSManager:
    def __init__(self, api):
        self.api = api

    def add_dns_record(self, hostname: str, ip_address: str, comment: str = None) -> dict:
        """Add a new DNS record
        
        Args:
            hostname: Hostname to add
            ip_address: IP address for hostname
            comment: Optional comment describing the record
        
        Returns:
            dict: Result of operation
        """
        try:
            # Validate hostname
            if not self._validate_hostname(hostname):
                return {
                    'success': False,
                    'message': f'Invalid hostname: {hostname}'
                }
            
            # Validate IP address
            if not self._validate_ip_address(ip_address):
                return {
                    'success': False,
                    'message': f'Invalid IP address: {ip_address}'
                }
            
            record = {
                'hostname': hostname,
                'ip': ip_address
            }
            
            if comment:
                record['comment'] = comment
            
            return self.api.api_request('POST', 'nodes/localhost/dns', record)
        
        except Exception as e:
            logger.error(f"Error adding DNS record: {str(e)}")
            return {
                'success': False,
                'message': f'Error adding DNS record: {str(e)}'
            }

    def delete_dns_record(self, record_id: str) -> dict:
        """Delete a DNS record by ID
        
        Args:
            record_id: ID of the DNS record to delete
        
        Returns:
            dict: Result of operation
        """
        try:
            return self.api.api_request('DELETE', f'nodes/localhost/dns/{record_id}')
            
        except Exception as e:
            logger.error(f"Error deleting DNS record: {str(e)}")
            return {
                'success': False,
                'message': f'Error deleting DNS record: {str(e)}'
            }

    def list_dns_records(self) -> dict:
        """List all DNS records
        
        Returns:
            dict: List of DNS records
        """
        try:
            result = self.api.api_request('GET', 'nodes/localhost/dns')
            
            if not result.get('success', False):
                return result
            
            return {
                'success': True,
                'message': f'Found {len(result.get("data", []))} DNS records',
                'records': result.get('data', [])
            }
            
        except Exception as e:
            logger.error(f"Error listing DNS records: {str(e)}")
            return {
                'success': False,
                'message': f'Error listing DNS records: {str(e)}',
                'records': []
            }

    def lookup_hostname(self, hostname: str) -> dict:
        """Lookup hostname in DNS
        
        Args:
            hostname: Hostname to lookup
            
        Returns:
            dict: Result with IP address if found
        """
        try:
            result = self.api.api_request('GET', 'nodes/localhost/dns')
            
            if not result.get('success', False):
                return result
                
            for record in result.get('data', []):
                if record.get('hostname') == hostname:
                    return {
                        'success': True,
                        'message': f'Found DNS record for {hostname}',
                        'record': record
                    }
            
            return {
                'success': False,
                'message': f'No DNS record found for {hostname}'
            }
            
        except Exception as e:
            logger.error(f"Error looking up hostname {hostname}: {str(e)}")
            return {
                'success': False,
                'message': f'Error looking up hostname: {str(e)}'
            }

    def lookup_ip(self, ip_address: str) -> dict:
        """Lookup IP address in DNS
        
        Args:
            ip_address: IP address to lookup
            
        Returns:
            dict: Result with hostname if found
        """
        try:
            result = self.api.api_request('GET', 'nodes/localhost/dns')
            
            if not result.get('success', False):
                return result
                
            for record in result.get('data', []):
                if record.get('ip') == ip_address:
                    return {
                        'success': True,
                        'message': f'Found DNS record for {ip_address}',
                        'record': record
                    }
            
            return {
                'success': False,
                'message': f'No DNS record found for {ip_address}'
            }
            
        except Exception as e:
            logger.error(f"Error looking up IP {ip_address}: {str(e)}")
            return {
                'success': False,
                'message': f'Error looking up IP: {str(e)}'
            }

    def update_dns_servers(self, servers: List[str]) -> dict:
        """Update DNS servers for the node
        
        Args:
            servers: List of DNS server IP addresses
            
        Returns:
            dict: Result of operation
        """
        try:
            # Validate all servers first
            for server in servers:
                if not self._validate_ip_address(server):
                    return {
                        'success': False,
                        'message': f'Invalid DNS server IP: {server}'
                    }
                    
            # Format nameserver string
            nameservers = ','.join(servers)
            
            # Update resolv.conf options
            result = self.api.api_request('PUT', 'nodes/localhost/network/config', {
                'nameserver': nameservers
            })
            
            if not result.get('success', False):
                return result
                
            # Apply changes
            apply_result = self.api.api_request('PUT', 'nodes/localhost/network', {
                'apply': 1
            })
            
            return {
                'success': True,
                'message': f'DNS servers updated successfully',
                'servers': servers
            }
            
        except Exception as e:
            logger.error(f"Error updating DNS servers: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating DNS servers: {str(e)}'
            }

    def _validate_hostname(self, hostname: str) -> bool:
        """Validate hostname format
        
        Args:
            hostname: Hostname to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Basic hostname validation pattern
        pattern = r'^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])(\.[a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])*$'
        return bool(re.match(pattern, hostname))

    def _validate_ip_address(self, ip: str) -> bool:
        """Validate IP address format
        
        Args:
            ip: IP address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Simple IPv4 validation pattern
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip)
        
        if not match:
            return False
            
        # Validate each octet
        for i in range(1, 5):
            octet = int(match.group(i))
            if octet < 0 or octet > 255:
                return False
                
        return True
