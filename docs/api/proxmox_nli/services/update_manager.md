# update_manager

Update management for Proxmox NLI services.
Provides functionality to check for updates and manage service updates through NLI commands.

**Module Path**: `proxmox_nli.services.update_manager`

## Classes

### UpdateManager

Manager for service updates.

#### __init__(service_manager, check_interval: int)

Initialize the update manager.

Args:
    service_manager: ServiceManager instance to interact with services
    check_interval: Interval in seconds between update checks (default: 24 hours)

#### start_checking()

Start the update checking thread.

#### stop_checking()

Stop the update checking thread.

#### check_all_services_for_updates()

Check all deployed services for available updates.

#### get_service_update_status(service_id: str)

Get update information for a specific service.

Args:
    service_id: ID of the service to get update info for
    
Returns:
    Service update dictionary or None if not found

**Returns**: `Optional[Dict]`

#### apply_updates(service_id: str)

Apply available updates to a service.

Args:
    service_id: ID of the service to update
    
Returns:
    Update result dictionary

**Returns**: `Dict`

#### generate_update_report()

Generate a natural language report on available updates.

Returns:
    Dictionary with natural language report on updates

**Returns**: `Dict`

#### check_service_for_updates_now(service_id: str)

Check a specific service for updates immediately.

Args:
    service_id: ID of the service to check
    
Returns:
    Update check result dictionary

**Returns**: `Dict`

#### get_update_summary(service_id: str)

Get a summary of available updates in natural language.

Args:
    service_id: Optional service ID to get update summary for.
               If None, generates summary for all services.
                
Returns:
    Dictionary with update summary

**Returns**: `Dict`

#### apply_updates(service_id: str, update_ids: List[str])

Apply updates to a service.

Args:
    service_id: ID of the service to update
    update_ids: Optional list of specific update IDs to apply.
                If None, applies all available updates.
                
Returns:
    Dictionary with update result

**Returns**: `Dict`

#### generate_update_plan(service_id: str)

Generate a natural language update plan.

Args:
    service_id: Optional service ID to generate plan for.
                If None, generates plan for all services with updates.
                
Returns:
    Dictionary with update plan

**Returns**: `Dict`

