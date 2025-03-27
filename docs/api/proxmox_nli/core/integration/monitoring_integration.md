# monitoring_integration

Monitoring Integration module for connecting TESSA with monitoring platforms.

**Module Path**: `proxmox_nli.core.integration.monitoring_integration`

## Classes

### MonitoringBackendBase

Abstract base class for monitoring backend implementations

#### configure(settings: Dict[(str, Any)])

Configure the monitoring backend

**Returns**: `Dict[(str, Any)]`

#### test_connection()

Test connection to the monitoring backend

**Returns**: `Dict[(str, Any)]`

#### register_metrics(metrics: List[Dict[(str, Any)]])

Register new metrics with the backend

**Returns**: `Dict[(str, Any)]`

#### send_metrics(metrics: List[Dict[(str, Any)]])

Send metrics to the backend

**Returns**: `Dict[(str, Any)]`

#### query_metrics(query: str, start_time: int, end_time: int = None)

Query metrics from the backend

**Returns**: `Dict[(str, Any)]`

### MonitoringIntegration

Main class for managing monitoring platform integrations

#### __init__(config_dir: str)

Initialize with optional config directory path

#### configure_backend(backend: str, settings: Dict[(str, Any)])

Configure a monitoring backend with settings

**Returns**: `Dict[(str, Any)]`

#### register_custom_metric(name: str, metric_type: str, help_text: str, labels: List[str])

Register a custom metric

**Returns**: `Dict[(str, Any)]`

#### send_metrics(metrics: List[Dict[(str, Any)]])

Send metrics to all enabled backends

**Returns**: `Dict[(str, Any)]`

#### query_metrics(query: str, backend: str, start_time: int = None, end_time: int = None)

Query metrics from a specific backend or try all enabled backends

**Returns**: `Dict[(str, Any)]`

#### configure_dashboard(name: str, backend: str, config: Dict[(str, Any)])

Configure a monitoring dashboard

**Returns**: `Dict[(str, Any)]`

#### test_backend(backend: str)

Test connection to a monitoring backend

**Returns**: `Dict[(str, Any)]`

