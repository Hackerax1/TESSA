# metrics_dashboard

Service metrics dashboard for Proxmox NLI.
Provides plain language explanations of service performance metrics.

**Module Path**: `proxmox_nli.services.metrics_dashboard`

## Classes

### ServiceMetricsDashboard

Provides a dashboard with plain language explanations of service metrics.

#### __init__(service_manager, health_monitor)

Initialize the metrics dashboard.

Args:
    service_manager: ServiceManager instance to interact with services
    health_monitor: Optional ServiceHealthMonitor instance for health data

#### load_metrics_history()

Load metrics history from disk.

#### save_metrics_history()

Save metrics history to disk.

#### update_metrics(service_id: str, metrics: Dict)

Update metrics for a specific service.

Args:
    service_id: ID of the service to update metrics for
    metrics: Dictionary of metrics to update

#### update_service_metrics_from_health()

Update metrics for all services using health monitor data.

#### get_service_dashboard(service_id: str)

Get a dashboard with plain language explanations for a specific service.

Args:
    service_id: ID of the service to get dashboard for
    
Returns:
    Dashboard dictionary with metrics and explanations

**Returns**: `Dict`

#### generate_dashboard_report(service_id: str)

Generate a consolidated natural language dashboard report.

Args:
    service_id: ID of the service to generate report for
    
Returns:
    Report dictionary with natural language dashboard report

**Returns**: `Dict`

#### get_system_dashboard()

Get a system-wide dashboard with metrics for all services.

Returns:
    Dashboard dictionary with metrics for all services

**Returns**: `Dict`

#### generate_system_dashboard_report()

Generate a natural language system-wide dashboard report.

Returns:
    Report dictionary with natural language system dashboard

**Returns**: `Dict`

