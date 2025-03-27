# network_diagnostics

Network Diagnostics for Proxmox NLI.
Provides tools for diagnosing network issues and visualizing network topology.

**Module Path**: `proxmox_nli.core.troubleshooting.network_diagnostics`

## Classes

### NetworkDiagnostics

Provides network diagnostics and visualization tools.

#### __init__(api)

Initialize the network diagnostics.

Args:
    api: Proxmox API client

#### run_diagnostics(context: Dict)

Run network diagnostics.

Args:
    context: Additional context for network diagnostics
    
Returns:
    Dict with network diagnostic results

**Returns**: `Dict`

#### comprehensive_diagnostics(context: Dict)

Run comprehensive network diagnostics.

Args:
    context: Additional context for network diagnostics
    
Returns:
    Dict with comprehensive network diagnostic results

**Returns**: `Dict`

#### check_connectivity(target: str)

Check network connectivity to a target.

Args:
    target: Target to ping
    
Returns:
    Dict with connectivity check results

**Returns**: `Dict`

#### check_dns(domain: str)

Check DNS resolution for a domain.

Args:
    domain: Domain to resolve
    
Returns:
    Dict with DNS check results

**Returns**: `Dict`

#### check_port(host: str, port: int = 'localhost')

Check if a port is open on a host.

Args:
    host: Host to check
    port: Port to check
    
Returns:
    Dict with port check results

**Returns**: `Dict`

#### check_route(target: str)

Check routing to a target.

Args:
    target: Target to check routing for
    
Returns:
    Dict with route check results

**Returns**: `Dict`

#### get_network_interfaces()

Get network interfaces information.

Returns:
    Dict with network interfaces information

**Returns**: `Dict`

#### get_listening_ports()

Get listening ports information.

Returns:
    Dict with listening ports information

**Returns**: `Dict`

#### get_active_connections()

Get active network connections.

Returns:
    Dict with active connections information

**Returns**: `Dict`

#### get_firewall_rules()

Get firewall rules.

Returns:
    Dict with firewall rules information

**Returns**: `Dict`

#### visualize_network(scope: str, context: Dict = 'cluster')

Generate network visualization data.

Args:
    scope: Scope of the visualization (cluster, node, vm, container)
    context: Additional context for network visualization
    
Returns:
    Dict with network visualization data

**Returns**: `Dict`

