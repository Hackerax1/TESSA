# troubleshooting_commands

Troubleshooting Commands for Proxmox NLI.
Provides natural language interface for troubleshooting and diagnostic features.

**Module Path**: `proxmox_nli.commands.troubleshooting_commands`

## Classes

### TroubleshootingCommands

Commands for troubleshooting and diagnostics.

#### __init__(api, proxmox_commands, service_manager = None, security_auditor = None, health_monitor = None)

Initialize troubleshooting commands.

Args:
    api: Proxmox API client
    proxmox_commands: ProxmoxCommands instance for command delegation
    service_manager: ServiceManager instance for service-related operations
    security_auditor: SecurityAuditor instance for security-related operations
    health_monitor: ServiceHealthMonitor instance for health monitoring

#### process_command(command: str)

Process a natural language troubleshooting command.

Args:
    command: Natural language command
    
Returns:
    Dict with command results

**Returns**: `Dict`

#### diagnose_issue(issue_type: str, context_str: str)

Diagnose an issue using the troubleshooting assistant.

Args:
    issue_type: Type of issue to diagnose
    context_str: String with additional context
    
Returns:
    Dict with diagnostic results

**Returns**: `Dict`

#### analyze_logs(log_type: str, context_str: str = None)

Analyze logs using the log analyzer.

Args:
    log_type: Type of logs to analyze
    context_str: String with additional context
    
Returns:
    Dict with log analysis results

**Returns**: `Dict`

#### run_network_diagnostics(diagnostic_type: str, context_str: str)

Run network diagnostics.

Args:
    diagnostic_type: Type of network diagnostic to run
    context_str: String with additional context
    
Returns:
    Dict with network diagnostic results

**Returns**: `Dict`

#### analyze_performance(resource_type: str, context_str: str)

Analyze system performance.

Args:
    resource_type: Type of resource to analyze
    context_str: String with additional context
    
Returns:
    Dict with performance analysis results

**Returns**: `Dict`

#### auto_resolve_issues(issue_type: str, context_str: str)

Automatically resolve issues.

Args:
    issue_type: Type of issue to resolve
    context_str: String with additional context
    
Returns:
    Dict with resolution results

**Returns**: `Dict`

#### generate_report(report_format: str, issue_type: str = None, context_str: str = None)

Generate a troubleshooting report.

Args:
    report_format: Format of the report (text, html, json)
    issue_type: Type of issue to include in the report
    context_str: String with additional context
    
Returns:
    Dict with report generation results

**Returns**: `Dict`

#### view_troubleshooting_history(issue_type: str, limit: int = None)

View troubleshooting history.

Args:
    issue_type: Type of issue to filter by
    limit: Maximum number of history entries to return
    
Returns:
    Dict with troubleshooting history

**Returns**: `Dict`

#### get_help()

Get help information for troubleshooting commands.

Returns:
    Dict with help information

**Returns**: `Dict`

