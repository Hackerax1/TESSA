# predictive_analyzer

Predictive resource allocation and power management module.

**Module Path**: `proxmox_nli.core.monitoring.predictive_analyzer`

## Classes

### PredictiveAnalyzer

Analyzes resource usage patterns and predicts future requirements.

#### __init__(resource_analyzer: ResourceAnalyzer)

Initialize the predictive analyzer.

Args:
    resource_analyzer: ResourceAnalyzer instance for historical data

#### predict_resource_needs(vm_id: str, hours_ahead: int)

Predict future resource requirements for a VM.

Args:
    vm_id: VM identifier
    hours_ahead: Number of hours to predict ahead
    
Returns:
    Dict with predicted resource requirements

**Returns**: `Dict`

#### analyze_power_efficiency(node_id: str)

Analyze power efficiency and generate recommendations.

Args:
    node_id: Optional node identifier. If None, analyzes all nodes.
    
Returns:
    Dict with power efficiency analysis and recommendations

**Returns**: `Dict`

