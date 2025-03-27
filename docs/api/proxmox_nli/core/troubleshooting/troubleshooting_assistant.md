# troubleshooting_assistant

Troubleshooting Assistant for Proxmox NLI.
Provides guided diagnostics and automated issue resolution for Proxmox environments.

**Module Path**: `proxmox_nli.core.troubleshooting.troubleshooting_assistant`

## Classes

### TroubleshootingAssistant

Main troubleshooting assistant class that coordinates diagnostics and issue resolution.

#### __init__(api, service_manager, security_auditor = None, health_monitor = None)

Initialize the troubleshooting assistant.

Args:
    api: Proxmox API client
    service_manager: ServiceManager instance for service-related diagnostics
    security_auditor: SecurityAuditor instance for security-related diagnostics
    health_monitor: ServiceHealthMonitor instance for health-related diagnostics

#### guided_diagnostics(issue_type: str, context: Dict)

Run guided diagnostics for a specific issue type.

Args:
    issue_type: Type of issue to diagnose (vm, container, network, storage, service, security)
    context: Additional context for the diagnostics (e.g., VM ID, service name)
    
Returns:
    Dict with diagnostic results and recommendations

**Returns**: `Dict`

#### analyze_logs(log_type: str, context: Dict)

Analyze logs using natural language processing.

Args:
    log_type: Type of logs to analyze (system, vm, container, service)
    context: Additional context for log analysis (e.g., VM ID, service name)
    
Returns:
    Dict with log analysis results

**Returns**: `Dict`

#### detect_bottlenecks(resource_type: str, context: Dict = None)

Detect performance bottlenecks in the system.

Args:
    resource_type: Type of resource to analyze (cpu, memory, disk, network, all)
    context: Additional context for bottleneck detection
    
Returns:
    Dict with bottleneck detection results

**Returns**: `Dict`

#### visualize_network(scope: str, context: Dict = 'cluster')

Generate network diagnostics visualization.

Args:
    scope: Scope of the visualization (cluster, node, vm, container)
    context: Additional context for network visualization
    
Returns:
    Dict with network visualization data

**Returns**: `Dict`

#### get_self_healing_recommendations(issue_type: str, context: Dict)

Get self-healing recommendations for common problems.

Args:
    issue_type: Type of issue to get recommendations for
    context: Additional context for recommendations
    
Returns:
    Dict with self-healing recommendations

**Returns**: `Dict`

#### execute_healing_action(action_id: str, context: Dict)

Execute a self-healing action.

Args:
    action_id: ID of the healing action to execute
    context: Additional context for the healing action
    
Returns:
    Dict with execution results

**Returns**: `Dict`

#### auto_resolve_issues(issue_type: str, issues: List[Dict], context: Dict)

Attempt to automatically resolve identified issues.

Args:
    issue_type: Type of issue to resolve (vm, container, network, storage, service, security)
    issues: List of issues to resolve, each with an issue_id and description
    context: Additional context for issue resolution
    
Returns:
    Dict with resolution results

**Returns**: `Dict`

#### generate_report(session: Dict, report_format: str)

Generate a report from a troubleshooting session.

Args:
    session: Troubleshooting session data
    report_format: Format of the report (text, html, json)
    
Returns:
    Dict with report data

**Returns**: `Dict`

#### get_troubleshooting_history(issue_type: str, limit: int = None)

Get troubleshooting history, optionally filtered by issue type.

Args:
    issue_type: Type of issue to filter by
    limit: Maximum number of history entries to return
    
Returns:
    List of troubleshooting history entries

**Returns**: `List[Dict]`

