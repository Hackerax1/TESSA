# metrics_collector

Metrics collection module for gathering system and application metrics.

**Module Path**: `proxmox_nli.core.monitoring.metrics_collector`

## Classes

### MetricsCollector

Collects and aggregates metrics from various sources

#### __init__(api, monitoring_integration)

Initialize with API connection and optional monitoring integration

#### start_collection(interval: int)

Start metrics collection in background thread

**Returns**: `Dict[(str, Any)]`

#### stop_collection()

Stop metrics collection

**Returns**: `Dict[(str, Any)]`

#### get_buffered_metrics(count: int)

Get metrics from buffer

**Returns**: `List[Dict]`

#### collect_all_metrics()

Collect all configured metrics

**Returns**: `Dict[(str, Any)]`

