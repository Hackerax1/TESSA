# resource_monitor

Resource monitoring module for active tracking of system resources.

**Module Path**: `proxmox_nli.core.monitoring.resource_monitor`

## Classes

### ResourceMonitor

Actively monitors system resources and provides alerts

#### __init__(api, monitoring_integration)

Initialize with API connection and optional monitoring integration

#### start_monitoring(interval: int)

Start resource monitoring

**Returns**: `Dict[(str, Any)]`

#### stop_monitoring()

Stop resource monitoring

**Returns**: `Dict[(str, Any)]`

#### register_alert_callback(callback: callable)

Register a callback for resource alerts

**Returns**: `None`

#### update_thresholds(thresholds: Dict[(str, Dict[(str, int)])])

Update monitoring thresholds

**Returns**: `Dict[(str, Any)]`

#### get_resource_summary()

Get a summary of current resource usage

**Returns**: `Dict[(str, Any)]`

