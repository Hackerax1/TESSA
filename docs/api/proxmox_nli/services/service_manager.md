# service_manager

Service manager for deploying and managing services via Proxmox VE.
This module handles the actual deployment of services defined in the service catalog.

**Module Path**: `proxmox_nli.services.service_manager`

## Classes

### ServiceManager

Manager for deploying and managing services on Proxmox VE.

#### __init__(proxmox_api: ProxmoxAPI, service_catalog: ServiceCatalog)

Initialize the service manager.

Args:
    proxmox_api: ProxmoxAPI instance for interacting with Proxmox VE
    service_catalog: ServiceCatalog instance, or None to create a new one

#### find_service(query: str)

Find services matching the user's query.

Args:
    query: Natural language query describing desired service
    
Returns:
    List of matching service definitions

**Returns**: `List[Dict]`

#### deploy_service(service_id: str, target_vm_id: str, custom_params: Dict = None)

Deploy a service on a target VM.

Args:
    service_id: ID of the service to deploy
    target_vm_id: ID of the VM to deploy the service on. If None, creates a new VM.
    custom_params: Custom parameters for service deployment
    
Returns:
    Dictionary with deployment result

**Returns**: `Dict`

#### get_service_status(service_id: str, vm_id: str)

Get status of a deployed service.

Args:
    service_id: ID of the service to check
    vm_id: ID of the VM running the service
    
Returns:
    Status information dictionary

**Returns**: `Dict`

#### list_deployed_services()

List all deployed services.

Returns:
    Dictionary with deployed services information

**Returns**: `Dict`

#### stop_service(service_id: str, vm_id: str)

Stop a running service.

Args:
    service_id: ID of the service to stop
    vm_id: ID of the VM running the service
    
Returns:
    Stop result dictionary

**Returns**: `Dict`

#### remove_service(service_id: str, vm_id: str, remove_vm: bool)

Remove a deployed service.

Args:
    service_id: ID of the service to remove
    vm_id: ID of the VM running the service
    remove_vm: Whether to remove the VM as well
    
Returns:
    Remove result dictionary

**Returns**: `Dict`

#### setup_cloudflare_service(domain_name, email, tunnel_name)

Set up Cloudflare service with domain and tunnel configuration

#### remove_cloudflare_service(domain_name)

Remove Cloudflare service configuration

