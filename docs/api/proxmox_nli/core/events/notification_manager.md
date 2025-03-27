# notification_manager

Notification manager for Proxmox NLI.
Handles sending notifications through various channels (email, websocket, desktop notifications).

**Module Path**: `proxmox_nli.core.events.notification_manager`

## Classes

### NotificationManager

#### __init__(event_dispatcher)

Initialize the notification manager

#### send_notification(message: str, level: str, title: str = 'info', channels: List[str] = None, metadata: Dict[(str, Any)] = None)

Send a notification through configured channels

Args:
    message: The notification message
    level: Notification level (critical, warning, info)
    title: Optional notification title
    channels: List of channels to use (email, websocket, desktop)
    metadata: Additional notification metadata
    
Returns:
    Dict with notification status

**Returns**: `Dict[(str, Any)]`

#### get_notification_history(level: str, limit: int = None)

Get notification history, optionally filtered by level

Args:
    level: Optional notification level to filter by
    limit: Maximum number of notifications to return
    
Returns:
    List of historical notifications

**Returns**: `List[Dict[(str, Any)]]`

#### update_config(new_config: Dict[(str, Any)])

Update notification configuration

Args:
    new_config: New configuration to merge with existing

**Returns**: `None`

