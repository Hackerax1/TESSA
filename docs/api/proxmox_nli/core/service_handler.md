# service_handler

Service handler module for managing services in Proxmox NLI.

**Module Path**: `proxmox_nli.core.service_handler`

## Classes

### ServiceHandler

Handles service-related operations for the Proxmox NLI.
This includes deploying, managing, and monitoring services.

#### __init__(base_nli)

Initialize the service handler with a reference to the base NLI instance.

Args:
    base_nli: The base NLI instance

#### handle_service_intent(intent, args, entities)

Handle service-related intents.

Args:
    intent: The identified intent
    args: Arguments for the intent
    entities: Entities extracted from the query
    
Returns:
    dict: Result of the operation

**Returns**: `dict: Result of the operation`

#### list_available_services()

List all available services that can be deployed.

Returns:
    dict: List of available services

**Returns**: `dict: List of available services`

#### list_deployed_services(vm_id)

List all deployed services, optionally filtered by VM.

Args:
    vm_id: Optional VM ID to filter services by
    
Returns:
    dict: List of deployed services

**Returns**: `dict: List of deployed services`

#### find_service(service_id)

Find information about a specific service.

Args:
    service_id: The ID of the service to find
    
Returns:
    dict: Service information

**Returns**: `dict: Service information`

#### deploy_service(service_id, vm_id)

Deploy a service to a VM.

Args:
    service_id: The ID of the service to deploy
    vm_id: The ID of the VM to deploy to
    
Returns:
    dict: Result of the deployment operation

**Returns**: `dict: Result of the deployment operation`

#### get_service_status(service_id, vm_id)

Get the status of a deployed service.

Args:
    service_id: The ID of the service
    vm_id: The ID of the VM the service is deployed on
    
Returns:
    dict: Status information for the service

**Returns**: `dict: Status information for the service`

#### stop_service(service_id, vm_id)

Stop a running service.

Args:
    service_id: The ID of the service to stop
    vm_id: The ID of the VM the service is running on
    
Returns:
    dict: Result of the stop operation

**Returns**: `dict: Result of the stop operation`

#### remove_service(service_id, vm_id)

Remove a deployed service.

Args:
    service_id: The ID of the service to remove
    vm_id: The ID of the VM the service is deployed on
    
Returns:
    dict: Result of the remove operation

**Returns**: `dict: Result of the remove operation`

