# docker_deployer

Docker deployer implementation for deploying Docker-based services.

**Module Path**: `proxmox_nli.services.deployment.docker_deployer`

## Classes

### DockerDeployer

Deployer for Docker-based services.

#### deploy(service_def: Dict, vm_id: str, custom_params: Optional[Dict])

Deploy a Docker service.

Args:
    service_def: Service definition dictionary
    vm_id: Target VM ID
    custom_params: Custom deployment parameters
    
Returns:
    Deployment result dictionary

**Returns**: `Dict`

#### stop_service(service_def: Dict, vm_id: str)

Stop a Docker service.

Args:
    service_def: Service definition dictionary
    vm_id: Target VM ID
    
Returns:
    Stop result dictionary

**Returns**: `Dict`

#### remove_service(service_def: Dict, vm_id: str)

Remove a Docker service.

Args:
    service_def: Service definition dictionary
    vm_id: Target VM ID
    
Returns:
    Remove result dictionary

**Returns**: `Dict`

