# service_deployer

Service deployer module for Proxmox NLI core.

Handles high-level deployment logic and orchestration between different service 
deployment mechanisms. Acts as a facade for the more detailed deployment 
implementations in the services.deployment package.

**Module Path**: `proxmox_nli.core.services.service_deployer`

## Classes

### ServiceDeployer

High-level service deployment orchestration for the NLI core.

This class provides a simpler interface for the NLI system to deploy services
and handles coordination with the main ServiceManager.

#### __init__(base_nli)

Initialize the service deployer with the base NLI context

#### deploy_service(service_id: str, target_vm_id: Optional[str], custom_params: Optional[Dict] = None)

Deploy a service with optional custom parameters

Args:
    service_id: ID of the service to deploy
    target_vm_id: Optional ID of VM to deploy to (None creates a new VM)
    custom_params: Optional custom parameters for the deployment

Returns:
    Deployment result dictionary

**Returns**: `Dict`

#### deploy_services_group(service_ids: List[str], custom_params: Optional[Dict])

Deploy multiple related services as a group with dependency resolution

Args:
    service_ids: List of service IDs to deploy
    custom_params: Optional custom parameters for all deployments
    
Returns:
    Deployment result dictionary

**Returns**: `Dict`

#### stop_service(service_id: str, vm_id: str)

Stop a running service

Args:
    service_id: ID of the service to stop
    vm_id: ID of the VM running the service
    
Returns:
    Stop result dictionary

**Returns**: `Dict`

#### remove_service(service_id: str, vm_id: str, remove_vm: bool)

Remove a deployed service

Args:
    service_id: ID of the service to remove
    vm_id: ID of the VM running the service
    remove_vm: Whether to remove the VM as well
    
Returns:
    Remove result dictionary

**Returns**: `Dict`

