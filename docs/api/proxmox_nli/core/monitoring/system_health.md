# system_health

System health monitoring module for overall system status and health checks.

**Module Path**: `proxmox_nli.core.monitoring.system_health`

## Classes

### SystemHealth

Manages overall system health monitoring and status

#### __init__(api, monitoring_integration)

Initialize with API connection and optional monitoring integration

#### start_health_checks(interval: int)

Start system health monitoring

**Returns**: `Dict[(str, Any)]`

#### stop_health_checks()

Stop system health monitoring

**Returns**: `Dict[(str, Any)]`

#### get_system_health()

Get current system health status

**Returns**: `Dict[(str, Any)]`

