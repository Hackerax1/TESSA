"""
Cloudflare integration module for Proxmox NLI.
Handles Cloudflare-specific domain and tunnel configuration.
"""
import os
import json
import subprocess
from pathlib import Path

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
        if not domain_name or not email:
            return {
                "success": False,
                "message": "Domain name and email are required"
            }
            
        # Store domain configuration
        self.config["domains"][domain_name] = {
            "email": email,
            "configured": True,
            "api_configured": bool(global_api_key)
        }
        
        if global_api_key:
            # Store API key securely (in practice, use proper secrets management)
            self.config["domains"][domain_name]["api_key"] = global_api_key
            
        self.config["configured"] = True
        self._save_config()
        
        return {
            "success": True,
            "message": f"Domain {domain_name} configured for Cloudflare",
            "next_steps": self._get_setup_instructions(domain_name)
        }
    
    def create_tunnel(self, domain_name, tunnel_name="homelab"):
        """Create a new Cloudflare tunnel for the domain"""
        if domain_name not in self.config["domains"]:
            return {
                "success": False,
                "message": f"Domain {domain_name} not configured in Cloudflare manager"
            }
            
        try:
            # Check if cloudflared is installed
            subprocess.run(["cloudflared", "--version"], 
                         check=True, 
                         capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                "success": False,
                "message": "cloudflared not installed. Please install it first."
            }
            
        # Store tunnel configuration
        tunnel_config = {
            "name": tunnel_name,
            "domain": domain_name,
            "status": "created"
        }
        
        self.config["tunnels"][tunnel_name] = tunnel_config
        self._save_config()
        
        return {
            "success": True,
            "message": f"Tunnel {tunnel_name} created for {domain_name}",
            "next_steps": self._get_tunnel_instructions(tunnel_name, domain_name)
        }
    
    def _get_setup_instructions(self, domain_name):
        """Generate setup instructions for Cloudflare domain configuration"""
        return {
            "steps": [
                "1. Log into Cloudflare Dashboard (https://dash.cloudflare.com)",
                f"2. Add site {domain_name} to your Cloudflare account",
                "3. Update your domain's nameservers to the ones provided by Cloudflare",
                "4. Wait for DNS propagation (can take 24-48 hours)",
                "5. Enable Full or Full (Strict) SSL/TLS encryption mode",
                "6. Consider enabling additional security features:",
                "   - Always Use HTTPS",
                "   - Automatic HTTPS Rewrites",
                "   - Opportunistic Encryption",
                "   - TLS 1.3",
                "   - Minimum TLS Version: 1.2"
            ],
            "security_recommendations": [
                "- Enable Web Application Firewall (WAF)",
                "- Configure rate limiting rules",
                "- Enable bot protection",
                "- Use Cloudflare Access for sensitive services",
                "- Regular security scanning"
            ]
        }
    
    def _get_tunnel_instructions(self, tunnel_name, domain_name):
        """Generate instructions for tunnel setup"""
        return {
            "steps": [
                "1. Install cloudflared CLI if not already installed",
                "2. Authenticate with Cloudflare:",
                "   $ cloudflared tunnel login",
                f"3. Create your tunnel:",
                f"   $ cloudflared tunnel create {tunnel_name}",
                "4. Configure your tunnel:",
                "   Create ~/.cloudflared/config.yml with:",
                "   ```",
                "   tunnel: <your-tunnel-id>",
                "   credentials-file: /etc/cloudflared/<tunnel-id>.json",
                "   ingress:",
                f"     - hostname: {domain_name}",
                "       service: http://localhost:8006",
                f"     - hostname: *.{domain_name}",
                "       service: http://localhost:8006",
                "     - service: http_status:404",
                "   ```",
                "5. Start the tunnel:",
                "   $ cloudflared tunnel run",
                "6. Configure DNS:",
                f"   $ cloudflared tunnel route dns <tunnel-id> {domain_name}"
            ]
        }
    
    def get_domains(self):
        """Get all configured Cloudflare domains"""
        return self.config["domains"]
    
    def get_tunnels(self):
        """Get all configured Cloudflare tunnels"""
        return self.config["tunnels"]
    
    def remove_domain(self, domain_name):
        """Remove a domain configuration"""
        if domain_name in self.config["domains"]:
            del self.config["domains"][domain_name]
            # Remove associated tunnels
            self.config["tunnels"] = {
                name: tunnel for name, tunnel in self.config["tunnels"].items()
                if tunnel["domain"] != domain_name
            }
            self._save_config()
            return {"success": True, "message": f"Domain {domain_name} removed"}
        return {"success": False, "message": f"Domain {domain_name} not found"}