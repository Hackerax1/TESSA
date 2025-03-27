# health_monitoring

Service health monitoring for Proxmox NLI.
Provides natural language status reports on service health.

**Module Path**: `proxmox_nli.services.health_monitoring`

## Classes

### ServiceHealthMonitor

Monitors health of deployed services and provides natural language status reports.

#### __init__(service_manager, check_interval: int)

Initialize the service health monitor.

Args:
    service_manager: ServiceManager instance to interact with services
    check_interval: Interval in seconds between health checks (default: 5 minutes)

#### start_monitoring()

Start the monitoring thread.

#### stop_monitoring()

Stop the monitoring thread.

#### check_services_health()

Check health of all deployed services.

#### get_service_health(service_id: str)

Get health information for a specific service.

Args:
    service_id: ID of the service to get health for
    
Returns:
    Service health dictionary or None if not found

**Returns**: `Optional[Dict]`

#### get_health_report(service_id: str)

Generate a natural language health report for a service.

Args:
    service_id: ID of the service to generate report for
    
Returns:
    Report dictionary with natural language status

**Returns**: `Dict`

#### get_all_services_health_summary()

Get a summary of health for all services.

Returns:
    Dictionary with health summary for all monitored services

**Returns**: `Dict`

#### generate_system_health_report()

Generate a natural language report on overall system health.

Returns:
    Dictionary with natural language report on system health

**Returns**: `Dict`

#### generate_natural_language_report(service_id: str)

Generate a natural language report of service health.

Args:
    service_id: Optional service ID to generate report for.
                If None, generates report for all services.
                
Returns:
    Dictionary with natural language report

**Returns**: `Dict`

#### get_service_health_summary(service_id: str)

Get a summary of service health in natural language.

Args:
    service_id: ID of the service to get health summary for
    
Returns:
    Dictionary with health summary

**Returns**: `Dict`

