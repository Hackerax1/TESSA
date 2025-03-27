# firewall_manager

Firewall management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.network.firewall_manager`

## Classes

### FirewallManager

#### __init__(api)

#### add_rule(rule: Dict[(str, Any)])

Add a firewall rule

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

**Returns**: `Dict[(str, Any)]`

#### list_rules()

List all firewall rules

Returns:
    Dict with list of firewall rules

**Returns**: `Dict[(str, Any)]`

#### delete_rule(rule_id: int)

Delete a firewall rule

Args:
    rule_id: ID of the rule to delete
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### add_service_rules(service_name: str, ports: List[int], sources: Optional[List[str]])

Add firewall rules for a service

Args:
    service_name: Name of the service (for comments)
    ports: List of ports to allow
    sources: Optional list of source IPs/networks
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### get_firewall_status()

Get firewall status

Returns:
    Dict with firewall status information

**Returns**: `Dict[(str, Any)]`

#### toggle_firewall(enable: bool)

Enable or disable the firewall

Args:
    enable: Whether to enable (True) or disable (False) the firewall
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

