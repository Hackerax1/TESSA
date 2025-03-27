# resource_analyzer

Resource analysis and optimization module for Proxmox NLI.
Provides insights and recommendations for resource usage optimization.

**Module Path**: `proxmox_nli.core.monitoring.resource_analyzer`

## Classes

### ResourceAnalyzer

#### __init__(api, prometheus_url: Optional[str])

#### analyze_vm_resources(vm_id: str, days: int)

Analyze VM resource usage and provide optimization recommendations

**Returns**: `Dict`

#### get_cluster_efficiency()

Get overall cluster efficiency metrics

**Returns**: `Dict`

