# dns_manager

DNS management module for Proxmox NLI.
Handles DNS configuration and management.

**Module Path**: `proxmox_nli.core.network.dns_manager`

## Classes

### DNSManager

#### __init__(api)

#### add_dns_record(hostname: str, ip_address: str, comment: str)

Add a new DNS record

Args:
    hostname: Hostname to add
    ip_address: IP address for hostname
    comment: Optional comment describing the record

Returns:
    dict: Result of operation

**Returns**: `dict`

#### delete_dns_record(record_id: str)

Delete a DNS record by ID

Args:
    record_id: ID of the DNS record to delete

Returns:
    dict: Result of operation

**Returns**: `dict`

#### list_dns_records()

List all DNS records

Returns:
    dict: List of DNS records

**Returns**: `dict`

#### lookup_hostname(hostname: str)

Lookup hostname in DNS

Args:
    hostname: Hostname to lookup
    
Returns:
    dict: Result with IP address if found

**Returns**: `dict`

#### lookup_ip(ip_address: str)

Lookup IP address in DNS

Args:
    ip_address: IP address to lookup
    
Returns:
    dict: Result with hostname if found

**Returns**: `dict`

#### update_dns_servers(servers: List[str])

Update DNS servers for the node

Args:
    servers: List of DNS server IP addresses
    
Returns:
    dict: Result of operation

**Returns**: `dict`

