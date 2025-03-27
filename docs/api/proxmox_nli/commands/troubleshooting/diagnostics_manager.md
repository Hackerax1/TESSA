# diagnostics_manager

System diagnostics and troubleshooting operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.troubleshooting.diagnostics_manager`

## Classes

### DiagnosticsManager

#### __init__(api)

#### run_system_diagnostics(node: str)

Run comprehensive system diagnostics

Args:
    node: Node name
    
Returns:
    Dict with diagnostic results

**Returns**: `Dict[(str, Any)]`

#### analyze_performance_issues(node: str, timeframe: str)

Analyze system performance issues

Args:
    node: Node name
    timeframe: Time period to analyze (e.g., 1h, 24h)
    
Returns:
    Dict with performance analysis

**Returns**: `Dict[(str, Any)]`

#### get_error_report(node: str, timeframe: str)

Generate error report from logs

Args:
    node: Node name
    timeframe: Time period to analyze
    
Returns:
    Dict with error report

**Returns**: `Dict[(str, Any)]`

#### run_health_check(node: str)

Run comprehensive health check

Args:
    node: Node name
    
Returns:
    Dict with health check results

**Returns**: `Dict[(str, Any)]`

