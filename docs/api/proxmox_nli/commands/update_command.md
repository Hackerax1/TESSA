# update_command

Update management commands for Proxmox NLI.

This module provides a command interface for the update management system,
allowing users to check for and apply updates through natural language commands.

**Module Path**: `proxmox_nli.commands.update_command`

## Classes

### UpdateCommand

Handles natural language commands for update management.

#### __init__(update_manager: UpdateManager)

Initialize the UpdateCommand with an UpdateManager.

Args:
    update_manager: The UpdateManager instance to use

#### check_updates(service_id: Optional[str])

Check for updates for a specific service or all services.

Args:
    service_id: Optional ID of the service to check for updates.
               If None, checks all services.
               
Returns:
    Dictionary with update check results

**Returns**: `Dict[(str, Any)]`

#### list_updates(service_id: Optional[str])

List available updates for services.

Args:
    service_id: Optional ID of the service to list updates for.
               If None, lists updates for all services.
               
Returns:
    Dictionary with update information

**Returns**: `Dict[(str, Any)]`

#### apply_updates(service_id: Optional[str], update_ids: Optional[List[str]] = None)

Apply updates to a service or all services.

Args:
    service_id: ID of the service to update. If None and update_ids is None,
               applies all available updates to all services with pending updates.
    update_ids: Optional list of specific update IDs to apply.
               
Returns:
    Dictionary with results of the update operation

**Returns**: `Dict[(str, Any)]`

#### generate_update_plan(service_id: Optional[str])

Generate an update plan for services.

Args:
    service_id: Optional ID of the service to generate a plan for.
               If None, generates a plan for all services with updates.
               
Returns:
    Dictionary with update plan

**Returns**: `Dict[(str, Any)]`

#### schedule_updates(service_id: Optional[str], schedule_time: Optional[str] = None)

Schedule updates to be applied at a specified time.

Args:
    service_id: Optional ID of the service to schedule updates for.
               If None, schedules updates for all services with pending updates.
    schedule_time: When to apply the updates (e.g., "tonight", "tomorrow 3am")
                 
Returns:
    Dictionary with scheduling results

**Returns**: `Dict[(str, Any)]`

#### get_update_status()

Get the current status of the update system.

Returns:
    Dictionary with update status information including:
    - Last check time
    - Auto-check status
    - Number of services with updates available
    - Next scheduled check

**Returns**: `Dict[(str, Any)]`

