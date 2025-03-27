# webhook_handler

Webhook handler for Proxmox NLI.
Manages webhook registrations and dispatches events to external services.

**Module Path**: `proxmox_nli.core.events.webhook_handler`

## Classes

### WebhookHandler

#### __init__(event_dispatcher)

Initialize the webhook handler

#### register_webhook(webhook: Dict[(str, Any)])

Register a new webhook

Args:
    webhook: Dictionary containing webhook configuration
            Required keys: url, events
            Optional: secret, headers, enabled
            
Returns:
    Dict with registration status

**Returns**: `Dict[(str, Any)]`

#### unregister_webhook(webhook_id: int)

Unregister a webhook

Args:
    webhook_id: ID of the webhook to unregister
    
Returns:
    Dict with unregistration status

**Returns**: `Dict[(str, bool)]`

#### handle_event(event_data: Dict[(str, Any)])

Handle an event by dispatching to relevant webhooks

Args:
    event_data: Event data to be sent to webhooks

**Returns**: `None`

#### get_webhook_history(webhook_id: Optional[int], limit: int = None)

Get webhook delivery history

Args:
    webhook_id: Optional webhook ID to filter by
    limit: Maximum number of records to return
    
Returns:
    List of webhook delivery attempts

**Returns**: `List[Dict[(str, Any)]]`

