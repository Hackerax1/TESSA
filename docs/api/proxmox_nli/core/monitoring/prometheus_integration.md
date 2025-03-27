# prometheus_integration

Prometheus integration for metrics collection and monitoring.

**Module Path**: `proxmox_nli.core.monitoring.prometheus_integration`

## Classes

### PrometheusClient

Client for interacting with Prometheus API

#### __init__(base_url: str)

#### query(query: str, time: Optional[datetime])

Execute a PromQL query.

**Returns**: `Dict`

#### query_range(query: str, start: datetime, end: datetime, step: str)

Execute a PromQL query over a time range.

**Returns**: `Dict`

### PrometheusMetricsCollector

Collector for Prometheus metrics specific to Proxmox monitoring.

#### __init__(client: PrometheusClient)

#### get_node_metrics(node: str, duration: timedelta)

Get metrics for a specific node.

**Returns**: `Dict`

