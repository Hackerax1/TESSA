# event_dispatcher

Event dispatcher for Proxmox NLI.
Handles event subscription and publishing using a pub/sub pattern.

**Module Path**: `proxmox_nli.core.events.event_dispatcher`

## Classes

### EventDispatcher

#### __init__()

Initialize the event dispatcher

#### subscribe(event_type: str, callback: Callable)

Subscribe to an event type

Args:
    event_type: The type of event to subscribe to
    callback: Function to be called when event occurs

**Returns**: `None`

#### unsubscribe(event_type: str, callback: Callable)

Unsubscribe from an event type

Args:
    event_type: The type of event to unsubscribe from
    callback: Function to be removed from subscribers

**Returns**: `None`

#### publish(event_type: str, data: Dict[(str, Any)])

Publish an event to all subscribers

Args:
    event_type: The type of event being published
    data: Event data to be passed to subscribers

**Returns**: `None`

#### get_event_history(event_type: str)

Get historical events, optionally filtered by type

Args:
    event_type: Optional event type to filter by
    
Returns:
    List of historical events

**Returns**: `List[Dict[(str, Any)]]`

#### clear_history()

Clear the event history

**Returns**: `None`

