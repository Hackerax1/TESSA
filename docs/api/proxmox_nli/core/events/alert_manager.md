# alert_manager

Alert manager for Proxmox NLI.
Handles system alerts, monitoring thresholds, and alert routing.

**Module Path**: `proxmox_nli.core.events.alert_manager`

## Classes

### AlertManager

#### __init__(event_dispatcher, notification_manager = None)

Initialize the alert manager

Args:
    event_dispatcher: Optional EventDispatcher instance
    notification_manager: Optional NotificationManager instance

#### register_alert_handler(metric: str, handler: Callable)

Register a new alert handler for a metric

Args:
    metric: The metric to handle
    handler: Function to handle the metric

**Returns**: `None`

#### create_alert(alert_type: str, message: str, level: str, source: str = 'warning', metadata: Dict[(str, Any)] = None)

Create a new alert

Args:
    alert_type: Type of alert (e.g., cpu_usage, disk_full)
    message: Alert message
    level: Alert level (critical, warning, info)
    source: Source of the alert
    metadata: Additional alert metadata
    
Returns:
    Dict containing alert details

**Returns**: `Dict[(str, Any)]`

#### update_alert(alert_id: str, updates: Dict[(str, Any)])

Update an existing alert

Args:
    alert_id: ID of the alert to update
    updates: Dictionary of fields to update
    
Returns:
    Updated alert dict or None if not found

**Returns**: `Optional[Dict[(str, Any)]]`

#### resolve_alert(alert_id: str, resolution: str)

Resolve an active alert

Args:
    alert_id: ID of the alert to resolve
    resolution: Optional resolution message
    
Returns:
    bool indicating success

**Returns**: `bool`

#### get_active_alerts(level: str, alert_type: str = None)

Get active alerts with optional filtering

Args:
    level: Optional alert level to filter by
    alert_type: Optional alert type to filter by
    
Returns:
    List of active alerts

**Returns**: `List[Dict[(str, Any)]]`

#### get_alert_history(start_time: datetime, end_time: datetime = None, level: str = None, alert_type: str = None, limit: int = None)

Get alert history with optional filtering

Args:
    start_time: Optional start time for filtering
    end_time: Optional end time for filtering
    level: Optional alert level to filter by
    alert_type: Optional alert type to filter by
    limit: Maximum number of alerts to return
    
Returns:
    List of historical alerts

**Returns**: `List[Dict[(str, Any)]]`

#### clean_old_alerts(days: int)

Clean up old alerts from history

Args:
    days: Number of days to keep, defaults to config retention_days
    
Returns:
    Number of alerts removed

**Returns**: `int`

#### update_thresholds(new_thresholds: Dict[(str, Any)])

Update alert thresholds

Args:
    new_thresholds: Dictionary of threshold updates

**Returns**: `None`

