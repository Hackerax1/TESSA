# health_checker

Service health checking module for Proxmox NLI.

Provides service health monitoring and status reporting functionality.

**Module Path**: `proxmox_nli.core.services.health_checker`

## Classes

### HealthChecker

Health monitoring for deployed services.

Provides functionality to:
- Check the health/status of deployed services
- Monitor service metrics
- Track uptime and reliability
- Generate health reports

#### __init__(base_nli)

Initialize the health checker with base NLI context

#### check_service_health(service_id: str, vm_id: str)

Check the health of a specific deployed service

Args:
    service_id: ID of the service to check
    vm_id: ID of the VM running the service
    
Returns:
    Health check result dictionary

**Returns**: `Dict[(str, Any)]`

#### check_all_services_health()

Check the health of all deployed services

Returns:
    Dictionary with health status of all services

**Returns**: `Dict[(str, Any)]`

#### get_service_metrics(service_id: str, vm_id: str)

Get detailed metrics for a specific service

Args:
    service_id: ID of the service
    vm_id: ID of the VM running the service
    
Returns:
    Dictionary with service metrics

**Returns**: `Dict[(str, Any)]`

#### generate_health_report()

Generate a comprehensive health report for all services

Returns:
    Health report dictionary

**Returns**: `Dict[(str, Any)]`

