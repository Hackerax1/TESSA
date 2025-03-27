# diagnostic_tools

Diagnostic Tools for Proxmox NLI.
Provides tools for diagnosing common issues in Proxmox environments.

**Module Path**: `proxmox_nli.core.troubleshooting.diagnostic_tools`

## Classes

### DiagnosticTools

Collection of diagnostic tools for troubleshooting Proxmox environments.

#### __init__(api)

Initialize the diagnostic tools.

Args:
    api: Proxmox API client

#### run_diagnostics(diagnostic_type: str, context: Dict)

Run diagnostics for a specific type.

Args:
    diagnostic_type: Type of diagnostics to run (network, storage, system, proxmox)
    context: Additional context for the diagnostics
    
Returns:
    Dict with diagnostic results

**Returns**: `Dict`

#### check_network(context: Dict)

Check network connectivity and configuration.

Args:
    context: Additional context for network diagnostics
    
Returns:
    Dict with network diagnostic results

**Returns**: `Dict`

#### check_storage(node: str, storage_id: str = 'pve')

Check storage health and configuration.

Args:
    node: Node to check storage on
    storage_id: Specific storage ID to check
    
Returns:
    Dict with storage diagnostic results

**Returns**: `Dict`

#### check_system(node: str)

Check system health and configuration.

Args:
    node: Node to check system on
    
Returns:
    Dict with system diagnostic results

**Returns**: `Dict`

#### check_proxmox(node: str)

Check Proxmox-specific configuration and status.

Args:
    node: Node to check Proxmox on
    
Returns:
    Dict with Proxmox diagnostic results

**Returns**: `Dict`

