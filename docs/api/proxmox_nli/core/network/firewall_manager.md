# firewall_manager

Firewall management module for Proxmox NLI.
Handles firewall rule configuration and management.

**Module Path**: `proxmox_nli.core.network.firewall_manager`

## Classes

### FirewallManager

#### __init__(api)

#### add_rule(rule: dict)

Add a new firewall rule

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

**Returns**: `dict`

#### delete_rule(rule_id: int)

Delete a firewall rule by ID

**Returns**: `dict`

#### list_rules()

List all firewall rules

**Returns**: `dict`

#### enable_firewall()

Enable the firewall

**Returns**: `dict`

#### disable_firewall()

Disable the firewall

**Returns**: `dict`

#### get_firewall_status()

Get firewall status

**Returns**: `dict`

#### add_service_rules(service_name: str, ports: List[int], sources: List[str])

Add rules for a common service

Args:
    service_name: Name of service (for comment)
    ports: List of ports to open
    sources: List of source IPs/CIDRs (None for any)

**Returns**: `dict`

