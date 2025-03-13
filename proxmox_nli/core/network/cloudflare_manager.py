"""
Cloudflare integration module for Proxmox NLI.
Handles Cloudflare-specific domain and tunnel configuration.
"""
import os
import json
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CloudflareManager:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(self.base_dir, 'config', 'cloudflare_config.json')
        self.config = self._load_config()
        
    def _load_config(self):
        """Load Cloudflare configuration from file"""
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            return {
                "configured": False,
                "tunnels": {},
                "domains": {}
            }
            
        with open(self.config_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"configured": False, "tunnels": {}, "domains": {}}
    
    def _save_config(self):
        """Save Cloudflare configuration to file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def configure_domain(self, domain_name, email, global_api_key=None):
        """Configure a domain with Cloudflare"""
        try:
            # Add domain to config
            self.config["domains"][domain_name] = {
                "email": email,
                "configured": True,
                "last_updated": str(Path.ctime(Path.today()))
            }
            
            # If API key provided, store it (in practice, should be encrypted)
            if global_api_key:
                self.config["domains"][domain_name]["api_key"] = global_api_key
                
            self._save_config()
            
            # Generate setup instructions
            instructions = self._get_setup_instructions(domain_name)
            
            return {
                "success": True,
                "message": f"Domain {domain_name} configured with Cloudflare",
                "instructions": instructions
            }
            
        except Exception as e:
            logger.error(f"Error configuring Cloudflare domain: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring Cloudflare domain: {str(e)}"
            }
    
    def create_tunnel(self, domain_name, tunnel_name="homelab"):
        """Create a new Cloudflare tunnel for the domain"""
        try:
            # Check if domain is configured
            if domain_name not in self.config["domains"]:
                return {
                    "success": False,
                    "message": f"Domain {domain_name} not configured with Cloudflare"
                }
                
            # Add tunnel to config
            tunnel_id = f"{tunnel_name}-{domain_name}"
            self.config["tunnels"][tunnel_id] = {
                "name": tunnel_name,
                "domain": domain_name,
                "configured": True,
                "last_updated": str(Path.ctime(Path.today()))
            }
            
            self._save_config()
            
            # Generate tunnel instructions
            instructions = self._get_tunnel_instructions(tunnel_name, domain_name)
            
            return {
                "success": True,
                "message": f"Tunnel {tunnel_name} created for domain {domain_name}",
                "instructions": instructions,
                "tunnel_id": tunnel_id
            }
            
        except Exception as e:
            logger.error(f"Error creating Cloudflare tunnel: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating Cloudflare tunnel: {str(e)}"
            }
    
    def _get_setup_instructions(self, domain_name):
        """Generate setup instructions for Cloudflare domain configuration"""
        return {
            "steps": [
                "1. Log in to Cloudflare dashboard at https://dash.cloudflare.com",
                f"2. Add domain {domain_name} and verify ownership",
                "3. Update your domain nameservers to the ones provided by Cloudflare",
                "4. Wait for DNS to propagate (may take up to 24 hours)"
            ],
            "recommendations": [
                "- Enable Always Use HTTPS",
                "- Set SSL/TLS encryption mode to Full (strict)",
                "- Enable Brotli compression",
                "- Set minimum TLS version to 1.2",
                "- Enable HTTP/2",
                "- Configure Page Rules for caching",
                "- Set up Firewall Rules for security",
                "- Regular security scanning"
            ]
        }
    
    def _get_tunnel_instructions(self, tunnel_name, domain_name):
        """Generate instructions for tunnel setup"""
        return {
            "steps": [
                "1. Install cloudflared on your Proxmox host",
                f"2. Authenticate cloudflared: cloudflared tunnel login",
                f"3. Create tunnel: cloudflared tunnel create {tunnel_name}",
                f"4. Create config file in ~/.cloudflared/config.yml",
                "5. Start the tunnel: cloudflared tunnel run",
                f"6. Configure DNS for {domain_name} to point to your tunnel"
            ],
            "config_example": f"""tunnel: {tunnel_name}
credentials-file: /path/to/credentials.json
ingress:
  - hostname: app.{domain_name}
    service: http://localhost:8080
  - hostname: www.{domain_name}
    service: http://localhost:80
  - service: http_status:404
"""
        }
    
    def get_domains(self):
        """Get all configured Cloudflare domains"""
        return {
            "success": True,
            "domains": self.config["domains"]
        }
    
    def get_tunnels(self):
        """Get all configured Cloudflare tunnels"""
        return {
            "success": True,
            "tunnels": self.config["tunnels"]
        }
    
    def remove_domain(self, domain_name):
        """Remove a domain configuration"""
        try:
            # Check if domain exists
            if domain_name not in self.config["domains"]:
                return {
                    "success": False,
                    "message": f"Domain {domain_name} not found in configuration"
                }
            
            # Remove domain and any associated tunnels
            del self.config["domains"][domain_name]
            
            # Remove any tunnels for this domain
            tunnels_to_remove = []
            for tunnel_id, tunnel in self.config["tunnels"].items():
                if tunnel["domain"] == domain_name:
                    tunnels_to_remove.append(tunnel_id)
                    
            for tunnel_id in tunnels_to_remove:
                del self.config["tunnels"][tunnel_id]
                
            self._save_config()
            
            return {
                "success": True,
                "message": f"Domain {domain_name} and associated tunnels removed",
                "cleanup_steps": [
                    "1. Remove the domain from Cloudflare dashboard",
                    "2. Update your domain nameservers if needed",
                    f"3. Run 'cloudflared tunnel delete <tunnel-id>' for any tunnels"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error removing Cloudflare domain: {str(e)}")
            return {
                "success": False,
                "message": f"Error removing Cloudflare domain: {str(e)}"
            }