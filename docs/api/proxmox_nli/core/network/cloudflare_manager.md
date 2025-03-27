# cloudflare_manager

Cloudflare integration module for Proxmox NLI.
Handles Cloudflare-specific domain and tunnel configuration.

**Module Path**: `proxmox_nli.core.network.cloudflare_manager`

## Classes

### CloudflareManager

#### __init__(base_dir)

#### configure_domain(domain_name, email, global_api_key)

Configure a domain with Cloudflare

#### create_tunnel(domain_name, tunnel_name)

Create a new Cloudflare tunnel for the domain

#### get_domains()

Get all configured Cloudflare domains

#### get_tunnels()

Get all configured Cloudflare tunnels

#### remove_domain(domain_name)

Remove a domain configuration

