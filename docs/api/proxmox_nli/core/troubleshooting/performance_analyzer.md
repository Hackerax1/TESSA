# performance_analyzer

Performance Analyzer for Proxmox NLI.
Provides tools for analyzing system performance and detecting bottlenecks.

**Module Path**: `proxmox_nli.core.troubleshooting.performance_analyzer`

## Classes

### PerformanceAnalyzer

Analyzes system performance and detects bottlenecks.

#### __init__(api)

Initialize the performance analyzer.

Args:
    api: Proxmox API client

#### analyze_performance(resource_type: str, context: Dict = None)

Analyze system performance.

Args:
    resource_type: Type of resource to analyze (cpu, memory, disk, network, all)
    context: Additional context for performance analysis
    
Returns:
    Dict with performance analysis results

**Returns**: `Dict`

#### analyze_all_performance(node: str)

Analyze performance of all resources.

Args:
    node: Node to analyze performance on
    
Returns:
    Dict with comprehensive performance analysis results

**Returns**: `Dict`

#### analyze_cpu_performance(node: str)

Analyze CPU performance.

Args:
    node: Node to analyze CPU performance on
    
Returns:
    Dict with CPU performance analysis results

**Returns**: `Dict`

#### analyze_memory_performance(node: str)

Analyze memory performance.

Args:
    node: Node to analyze memory performance on
    
Returns:
    Dict with memory performance analysis results

**Returns**: `Dict`

#### analyze_disk_performance(node: str, storage_id: str = 'pve')

Analyze disk performance.

Args:
    node: Node to analyze disk performance on
    storage_id: Specific storage ID to analyze
    
Returns:
    Dict with disk performance analysis results

**Returns**: `Dict`

#### analyze_network_performance(node: str, interface: str = 'pve')

Analyze network performance.

Args:
    node: Node to analyze network performance on
    interface: Specific network interface to analyze
    
Returns:
    Dict with network performance analysis results

**Returns**: `Dict`

#### detect_bottlenecks(node: str)

Detect performance bottlenecks.

Args:
    node: Node to detect bottlenecks on
    
Returns:
    Dict with bottleneck detection results

**Returns**: `Dict`

