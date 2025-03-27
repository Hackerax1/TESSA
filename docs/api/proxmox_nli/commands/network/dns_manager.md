# dns_manager

DNS management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.network.dns_manager`

## Classes

### DNSManager

#### __init__(api)

#### add_dns_record(hostname: str, ip_address: str, comment: Optional[str])

Add a DNS record

Args:
    hostname: Hostname to add
    ip_address: IP address for hostname
    comment: Optional comment
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### list_dns_records()

List all DNS records

Returns:
    Dict with list of DNS records

**Returns**: `Dict[(str, Any)]`

#### delete_dns_record(hostname: str)

Delete a DNS record

Args:
    hostname: Hostname to delete
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### update_dns_servers(servers: List[str])

Update DNS servers

Args:
    servers: List of DNS server IP addresses
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### get_dns_servers()

Get configured DNS servers

Returns:
    Dict with list of DNS servers

**Returns**: `Dict[(str, Any)]`

#### check_dns_resolution(hostname: str)

Test DNS resolution for a hostname

Args:
    hostname: Hostname to resolve
    
Returns:
    Dict with resolution result

**Returns**: `Dict[(str, Any)]`

