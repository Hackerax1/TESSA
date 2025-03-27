# log_analyzer

Log Analyzer for Proxmox NLI.
Provides natural language analysis of system and service logs.

**Module Path**: `proxmox_nli.core.troubleshooting.log_analyzer`

## Classes

### LogAnalyzer

Analyzes logs using natural language processing to identify issues and patterns.

#### __init__(api)

Initialize the log analyzer.

Args:
    api: Proxmox API client

#### analyze_logs(log_type: str, context: Dict)

Analyze logs using natural language processing.

Args:
    log_type: Type of logs to analyze (system, vm, container, service)
    context: Additional context for log analysis (e.g., VM ID, service name)
    
Returns:
    Dict with log analysis results

**Returns**: `Dict`

#### analyze_system_logs(context: Dict)

Analyze system logs for issues.

Args:
    context: Additional context for log analysis
    
Returns:
    Dict with log analysis results

**Returns**: `Dict`

#### analyze_vm_logs(vm_id: str, node: str)

Analyze VM logs for issues.

Args:
    vm_id: ID of the VM to analyze logs for
    node: Node where the VM is running
    
Returns:
    Dict with log analysis results

**Returns**: `Dict`

#### analyze_container_logs(container_id: str, node: str)

Analyze container logs for issues.

Args:
    container_id: ID of the container to analyze logs for
    node: Node where the container is running
    
Returns:
    Dict with log analysis results

**Returns**: `Dict`

#### analyze_service_logs(service_id: str, vm_id: str)

Analyze service logs for issues.

Args:
    service_id: ID of the service to analyze logs for
    vm_id: ID of the VM where the service is running
    
Returns:
    Dict with log analysis results

**Returns**: `Dict`

