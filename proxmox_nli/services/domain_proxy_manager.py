"""
Domain and reverse proxy management for Proxmox NLI.
Provides functionality to manage domains and configure reverse proxies.
"""
import logging
import json
import os
import re
import time
import subprocess
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DomainProxyManager:
    """Manager for domain and reverse proxy configuration."""
    
    def __init__(self, service_manager):
        """Initialize the domain and proxy manager.
        
        Args:
            service_manager: ServiceManager instance for service operations
        """
        self.service_manager = service_manager
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data', 'domains')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Store domain and proxy configurations
        self.domains = {}
        self.proxies = {}
        self._load_configurations()
        
        # Supported proxy types
        self.proxy_types = ['nginx', 'traefik', 'caddy']
        
    def _load_configurations(self):
        """Load domain and proxy configurations from disk."""
        try:
            domains_file = os.path.join(self.data_dir, 'domains.json')
            if os.path.exists(domains_file):
                with open(domains_file, 'r') as f:
                    self.domains = json.load(f)
                logger.info(f"Loaded {len(self.domains)} domain configurations")
                
            proxies_file = os.path.join(self.data_dir, 'proxies.json')
            if os.path.exists(proxies_file):
                with open(proxies_file, 'r') as f:
                    self.proxies = json.load(f)
                logger.info(f"Loaded {len(self.proxies)} proxy configurations")
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")
            
    def _save_configurations(self):
        """Save domain and proxy configurations to disk."""
        try:
            domains_file = os.path.join(self.data_dir, 'domains.json')
            with open(domains_file, 'w') as f:
                json.dump(self.domains, f)
                
            proxies_file = os.path.join(self.data_dir, 'proxies.json')
            with open(proxies_file, 'w') as f:
                json.dump(self.proxies, f)
                
            logger.debug("Domain and proxy configurations saved to disk")
        except Exception as e:
            logger.error(f"Error saving configurations: {str(e)}")
    
    def add_domain(self, domain_name: str, service_id: str, options: Dict = None) -> Dict:
        """Add a new domain for a service.
        
        Args:
            domain_name: Domain name to add
            service_id: ID of the service to associate with the domain
            options: Additional domain options
            
        Returns:
            Dictionary with domain addition result
        """
        # Validate domain name
        if not self._validate_domain_name(domain_name):
            return {
                'success': False,
                'message': f'Invalid domain name: {domain_name}'
            }
            
        # Check if domain already exists
        if domain_name in self.domains:
            return {
                'success': False,
                'message': f'Domain {domain_name} already exists'
            }
            
        # Get service information
        service_info = self.service_manager.get_service_info(service_id)
        if not service_info.get('success', False):
            return {
                'success': False,
                'message': f'Service not found: {service_id}'
            }
            
        # Create domain configuration
        domain_config = {
            'domain': domain_name,
            'service_id': service_id,
            'service_name': service_info.get('service', {}).get('name', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'options': options or {},
            'status': 'active',
            'ssl': options.get('ssl', True),
            'auto_renew': options.get('auto_renew', True)
        }
        
        # Add to domains dictionary
        self.domains[domain_name] = domain_config
        self._save_configurations()
        
        return {
            'success': True,
            'message': f'Domain {domain_name} added for service {service_id}',
            'domain': domain_config
        }
    
    def remove_domain(self, domain_name: str) -> Dict:
        """Remove a domain.
        
        Args:
            domain_name: Domain name to remove
            
        Returns:
            Dictionary with domain removal result
        """
        if domain_name not in self.domains:
            return {
                'success': False,
                'message': f'Domain {domain_name} not found'
            }
            
        # Remove domain configuration
        domain_config = self.domains.pop(domain_name)
        self._save_configurations()
        
        # Remove associated proxy configurations
        for proxy_id, proxy_config in list(self.proxies.items()):
            if proxy_config.get('domain') == domain_name:
                self.proxies.pop(proxy_id)
                
        self._save_configurations()
        
        return {
            'success': True,
            'message': f'Domain {domain_name} removed',
            'domain': domain_config
        }
    
    def get_domain(self, domain_name: str) -> Dict:
        """Get domain configuration.
        
        Args:
            domain_name: Domain name to get
            
        Returns:
            Dictionary with domain configuration
        """
        if domain_name not in self.domains:
            return {
                'success': False,
                'message': f'Domain {domain_name} not found'
            }
            
        return {
            'success': True,
            'message': f'Domain {domain_name} found',
            'domain': self.domains[domain_name]
        }
    
    def list_domains(self, service_id: str = None) -> Dict:
        """List all domains or domains for a specific service.
        
        Args:
            service_id: Optional service ID to filter by
            
        Returns:
            Dictionary with domain list
        """
        if service_id:
            # Filter domains by service ID
            domains = {
                name: config for name, config in self.domains.items()
                if config.get('service_id') == service_id
            }
        else:
            domains = self.domains
            
        return {
            'success': True,
            'message': f'Found {len(domains)} domains',
            'domains': domains
        }
    
    def configure_proxy(self, domain_name: str, proxy_type: str, options: Dict = None) -> Dict:
        """Configure a reverse proxy for a domain.
        
        Args:
            domain_name: Domain name to configure proxy for
            proxy_type: Type of proxy to configure (nginx, traefik, caddy)
            options: Additional proxy options
            
        Returns:
            Dictionary with proxy configuration result
        """
        if domain_name not in self.domains:
            return {
                'success': False,
                'message': f'Domain {domain_name} not found'
            }
            
        if proxy_type not in self.proxy_types:
            return {
                'success': False,
                'message': f'Unsupported proxy type: {proxy_type}'
            }
            
        domain_config = self.domains[domain_name]
        service_id = domain_config['service_id']
        
        # Get service information
        service_info = self.service_manager.get_service_info(service_id)
        if not service_info.get('success', False):
            return {
                'success': False,
                'message': f'Service not found: {service_id}'
            }
            
        # Create proxy configuration
        proxy_id = f"{domain_name}_{proxy_type}"
        proxy_config = {
            'id': proxy_id,
            'domain': domain_name,
            'service_id': service_id,
            'proxy_type': proxy_type,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'options': options or {},
            'status': 'pending'
        }
        
        # Add to proxies dictionary
        self.proxies[proxy_id] = proxy_config
        self._save_configurations()
        
        # Generate and apply proxy configuration
        apply_result = self._apply_proxy_configuration(proxy_id)
        
        if not apply_result.get('success', False):
            proxy_config['status'] = 'failed'
            proxy_config['error'] = apply_result.get('message')
            self._save_configurations()
            
            return {
                'success': False,
                'message': f'Failed to apply proxy configuration: {apply_result.get("message")}',
                'proxy': proxy_config
            }
            
        proxy_config['status'] = 'active'
        self._save_configurations()
        
        return {
            'success': True,
            'message': f'Proxy configured for {domain_name} using {proxy_type}',
            'proxy': proxy_config
        }
    
    def remove_proxy(self, proxy_id: str) -> Dict:
        """Remove a proxy configuration.
        
        Args:
            proxy_id: ID of the proxy configuration to remove
            
        Returns:
            Dictionary with proxy removal result
        """
        if proxy_id not in self.proxies:
            return {
                'success': False,
                'message': f'Proxy configuration {proxy_id} not found'
            }
            
        proxy_config = self.proxies[proxy_id]
        
        # Remove proxy configuration
        remove_result = self._remove_proxy_configuration(proxy_id)
        
        if not remove_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to remove proxy configuration: {remove_result.get("message")}',
                'proxy': proxy_config
            }
            
        # Remove from proxies dictionary
        self.proxies.pop(proxy_id)
        self._save_configurations()
        
        return {
            'success': True,
            'message': f'Proxy configuration {proxy_id} removed',
            'proxy': proxy_config
        }
    
    def get_proxy(self, proxy_id: str) -> Dict:
        """Get proxy configuration.
        
        Args:
            proxy_id: ID of the proxy configuration to get
            
        Returns:
            Dictionary with proxy configuration
        """
        if proxy_id not in self.proxies:
            return {
                'success': False,
                'message': f'Proxy configuration {proxy_id} not found'
            }
            
        return {
            'success': True,
            'message': f'Proxy configuration {proxy_id} found',
            'proxy': self.proxies[proxy_id]
        }
    
    def list_proxies(self, domain_name: str = None, proxy_type: str = None) -> Dict:
        """List all proxy configurations or filter by domain or type.
        
        Args:
            domain_name: Optional domain name to filter by
            proxy_type: Optional proxy type to filter by
            
        Returns:
            Dictionary with proxy list
        """
        proxies = self.proxies
        
        if domain_name:
            # Filter proxies by domain name
            proxies = {
                id: config for id, config in proxies.items()
                if config.get('domain') == domain_name
            }
            
        if proxy_type:
            # Filter proxies by proxy type
            proxies = {
                id: config for id, config in proxies.items()
                if config.get('proxy_type') == proxy_type
            }
            
        return {
            'success': True,
            'message': f'Found {len(proxies)} proxy configurations',
            'proxies': proxies
        }
    
    def _validate_domain_name(self, domain_name: str) -> bool:
        """Validate a domain name.
        
        Args:
            domain_name: Domain name to validate
            
        Returns:
            True if domain name is valid, False otherwise
        """
        # Basic domain name validation
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain_name))
    
    def _apply_proxy_configuration(self, proxy_id: str) -> Dict:
        """Apply a proxy configuration.
        
        Args:
            proxy_id: ID of the proxy configuration to apply
            
        Returns:
            Dictionary with application result
        """
        if proxy_id not in self.proxies:
            return {
                'success': False,
                'message': f'Proxy configuration {proxy_id} not found'
            }
            
        proxy_config = self.proxies[proxy_id]
        domain_name = proxy_config['domain']
        proxy_type = proxy_config['proxy_type']
        
        if domain_name not in self.domains:
            return {
                'success': False,
                'message': f'Domain {domain_name} not found'
            }
            
        domain_config = self.domains[domain_name]
        service_id = domain_config['service_id']
        
        # Get service information
        service_info = self.service_manager.get_service_info(service_id)
        if not service_info.get('success', False):
            return {
                'success': False,
                'message': f'Service not found: {service_id}'
            }
            
        service = service_info.get('service', {})
        vm_id = service.get('vm_id')
        
        if not vm_id:
            return {
                'success': False,
                'message': f'Service {service_id} does not have a VM ID'
            }
            
        # Generate proxy configuration based on type
        if proxy_type == 'nginx':
            return self._apply_nginx_configuration(proxy_id, domain_name, service, vm_id)
        elif proxy_type == 'traefik':
            return self._apply_traefik_configuration(proxy_id, domain_name, service, vm_id)
        elif proxy_type == 'caddy':
            return self._apply_caddy_configuration(proxy_id, domain_name, service, vm_id)
        else:
            return {
                'success': False,
                'message': f'Unsupported proxy type: {proxy_type}'
            }
    
    def _apply_nginx_configuration(self, proxy_id: str, domain_name: str, service: Dict, vm_id: str) -> Dict:
        """Apply Nginx proxy configuration.
        
        Args:
            proxy_id: Proxy configuration ID
            domain_name: Domain name
            service: Service information
            vm_id: VM ID
            
        Returns:
            Dictionary with application result
        """
        proxy_config = self.proxies[proxy_id]
        options = proxy_config.get('options', {})
        
        # Get service port
        port = service.get('port', 80)
        
        # Generate Nginx configuration
        nginx_config = f"""
server {{
    listen 80;
    server_name {domain_name};
    
    location / {{
        proxy_pass http://localhost:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        
        # If SSL is enabled, add SSL configuration
        if options.get('ssl', True):
            nginx_config += f"""
server {{
    listen 443 ssl;
    server_name {domain_name};
    
    ssl_certificate /etc/letsencrypt/live/{domain_name}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain_name}/privkey.pem;
    
    location / {{
        proxy_pass http://localhost:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
            
        # Write configuration to file on VM
        config_path = f"/etc/nginx/sites-available/{domain_name}"
        enabled_path = f"/etc/nginx/sites-enabled/{domain_name}"
        
        # Create configuration file
        create_result = self.service_manager.docker_deployer.run_command(vm_id, 
            f"echo '{nginx_config}' > {config_path}")
        
        if not create_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to create Nginx configuration: {create_result.get("message")}'
            }
            
        # Create symbolic link if it doesn't exist
        link_result = self.service_manager.docker_deployer.run_command(vm_id, 
            f"ln -sf {config_path} {enabled_path}")
        
        if not link_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to enable Nginx configuration: {link_result.get("message")}'
            }
            
        # If SSL is enabled, obtain certificate
        if options.get('ssl', True):
            ssl_result = self.service_manager.docker_deployer.run_command(vm_id, 
                f"certbot --nginx -d {domain_name} --non-interactive --agree-tos --email {options.get('email', 'admin@example.com')}")
            
            if not ssl_result.get('success', False):
                return {
                    'success': False,
                    'message': f'Failed to obtain SSL certificate: {ssl_result.get("message")}'
                }
                
        # Reload Nginx
        reload_result = self.service_manager.docker_deployer.run_command(vm_id, 
            "systemctl reload nginx")
        
        if not reload_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to reload Nginx: {reload_result.get("message")}'
            }
            
        return {
            'success': True,
            'message': f'Nginx configuration applied for {domain_name}'
        }
    
    def _apply_traefik_configuration(self, proxy_id: str, domain_name: str, service: Dict, vm_id: str) -> Dict:
        """Apply Traefik proxy configuration.
        
        Args:
            proxy_id: Proxy configuration ID
            domain_name: Domain name
            service: Service information
            vm_id: VM ID
            
        Returns:
            Dictionary with application result
        """
        proxy_config = self.proxies[proxy_id]
        options = proxy_config.get('options', {})
        
        # Get service port
        port = service.get('port', 80)
        service_name = service.get('name', 'service').lower().replace(' ', '-')
        
        # Generate Traefik configuration
        traefik_config = {
            "http": {
                "routers": {
                    f"{service_name}-router": {
                        "rule": f"Host(`{domain_name}`)",
                        "service": f"{service_name}-service",
                        "entrypoints": ["web"]
                    }
                },
                "services": {
                    f"{service_name}-service": {
                        "loadBalancer": {
                            "servers": [
                                {
                                    "url": f"http://localhost:{port}"
                                }
                            ]
                        }
                    }
                }
            }
        }
        
        # If SSL is enabled, add HTTPS configuration
        if options.get('ssl', True):
            traefik_config["http"]["routers"][f"{service_name}-router"]["entrypoints"].append("websecure")
            traefik_config["http"]["routers"][f"{service_name}-router"]["tls"] = {
                "certResolver": "letsencrypt"
            }
            
        # Convert to JSON
        traefik_json = json.dumps(traefik_config, indent=2)
        
        # Write configuration to file on VM
        config_path = f"/etc/traefik/conf.d/{domain_name}.json"
        
        # Create configuration file
        create_result = self.service_manager.docker_deployer.run_command(vm_id, 
            f"echo '{traefik_json}' > {config_path}")
        
        if not create_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to create Traefik configuration: {create_result.get("message")}'
            }
            
        # Reload Traefik
        reload_result = self.service_manager.docker_deployer.run_command(vm_id, 
            "systemctl reload traefik")
        
        if not reload_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to reload Traefik: {reload_result.get("message")}'
            }
            
        return {
            'success': True,
            'message': f'Traefik configuration applied for {domain_name}'
        }
    
    def _apply_caddy_configuration(self, proxy_id: str, domain_name: str, service: Dict, vm_id: str) -> Dict:
        """Apply Caddy proxy configuration.
        
        Args:
            proxy_id: Proxy configuration ID
            domain_name: Domain name
            service: Service information
            vm_id: VM ID
            
        Returns:
            Dictionary with application result
        """
        # Get service port
        port = service.get('port', 80)
        
        # Generate Caddy configuration
        caddy_config = f"""
{domain_name} {{
    reverse_proxy localhost:{port}
}}
"""
        
        # Write configuration to file on VM
        config_path = f"/etc/caddy/conf.d/{domain_name}.caddy"
        
        # Create configuration file
        create_result = self.service_manager.docker_deployer.run_command(vm_id, 
            f"echo '{caddy_config}' > {config_path}")
        
        if not create_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to create Caddy configuration: {create_result.get("message")}'
            }
            
        # Reload Caddy
        reload_result = self.service_manager.docker_deployer.run_command(vm_id, 
            "systemctl reload caddy")
        
        if not reload_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to reload Caddy: {reload_result.get("message")}'
            }
            
        return {
            'success': True,
            'message': f'Caddy configuration applied for {domain_name}'
        }
    
    def _remove_proxy_configuration(self, proxy_id: str) -> Dict:
        """Remove a proxy configuration.
        
        Args:
            proxy_id: ID of the proxy configuration to remove
            
        Returns:
            Dictionary with removal result
        """
        if proxy_id not in self.proxies:
            return {
                'success': False,
                'message': f'Proxy configuration {proxy_id} not found'
            }
            
        proxy_config = self.proxies[proxy_id]
        domain_name = proxy_config['domain']
        proxy_type = proxy_config['proxy_type']
        service_id = proxy_config['service_id']
        
        # Get service information
        service_info = self.service_manager.get_service_info(service_id)
        if not service_info.get('success', False):
            return {
                'success': False,
                'message': f'Service not found: {service_id}'
            }
            
        service = service_info.get('service', {})
        vm_id = service.get('vm_id')
        
        if not vm_id:
            return {
                'success': False,
                'message': f'Service {service_id} does not have a VM ID'
            }
            
        # Remove configuration based on proxy type
        if proxy_type == 'nginx':
            return self._remove_nginx_configuration(domain_name, vm_id)
        elif proxy_type == 'traefik':
            return self._remove_traefik_configuration(domain_name, vm_id)
        elif proxy_type == 'caddy':
            return self._remove_caddy_configuration(domain_name, vm_id)
        else:
            return {
                'success': False,
                'message': f'Unsupported proxy type: {proxy_type}'
            }
    
    def _remove_nginx_configuration(self, domain_name: str, vm_id: str) -> Dict:
        """Remove Nginx proxy configuration.
        
        Args:
            domain_name: Domain name
            vm_id: VM ID
            
        Returns:
            Dictionary with removal result
        """
        # Remove configuration files
        config_path = f"/etc/nginx/sites-available/{domain_name}"
        enabled_path = f"/etc/nginx/sites-enabled/{domain_name}"
        
        # Remove symbolic link
        unlink_result = self.service_manager.docker_deployer.run_command(vm_id, 
            f"rm -f {enabled_path}")
        
        if not unlink_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to remove Nginx symbolic link: {unlink_result.get("message")}'
            }
            
        # Remove configuration file
        remove_result = self.service_manager.docker_deployer.run_command(vm_id, 
            f"rm -f {config_path}")
        
        if not remove_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to remove Nginx configuration: {remove_result.get("message")}'
            }
            
        # Reload Nginx
        reload_result = self.service_manager.docker_deployer.run_command(vm_id, 
            "systemctl reload nginx")
        
        if not reload_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to reload Nginx: {reload_result.get("message")}'
            }
            
        return {
            'success': True,
            'message': f'Nginx configuration removed for {domain_name}'
        }
    
    def _remove_traefik_configuration(self, domain_name: str, vm_id: str) -> Dict:
        """Remove Traefik proxy configuration.
        
        Args:
            domain_name: Domain name
            vm_id: VM ID
            
        Returns:
            Dictionary with removal result
        """
        # Remove configuration file
        config_path = f"/etc/traefik/conf.d/{domain_name}.json"
        
        remove_result = self.service_manager.docker_deployer.run_command(vm_id, 
            f"rm -f {config_path}")
        
        if not remove_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to remove Traefik configuration: {remove_result.get("message")}'
            }
            
        # Reload Traefik
        reload_result = self.service_manager.docker_deployer.run_command(vm_id, 
            "systemctl reload traefik")
        
        if not reload_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to reload Traefik: {reload_result.get("message")}'
            }
            
        return {
            'success': True,
            'message': f'Traefik configuration removed for {domain_name}'
        }
    
    def _remove_caddy_configuration(self, domain_name: str, vm_id: str) -> Dict:
        """Remove Caddy proxy configuration.
        
        Args:
            domain_name: Domain name
            vm_id: VM ID
            
        Returns:
            Dictionary with removal result
        """
        # Remove configuration file
        config_path = f"/etc/caddy/conf.d/{domain_name}.caddy"
        
        remove_result = self.service_manager.docker_deployer.run_command(vm_id, 
            f"rm -f {config_path}")
        
        if not remove_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to remove Caddy configuration: {remove_result.get("message")}'
            }
            
        # Reload Caddy
        reload_result = self.service_manager.docker_deployer.run_command(vm_id, 
            "systemctl reload caddy")
        
        if not reload_result.get('success', False):
            return {
                'success': False,
                'message': f'Failed to reload Caddy: {reload_result.get("message")}'
            }
            
        return {
            'success': True,
            'message': f'Caddy configuration removed for {domain_name}'
        }
