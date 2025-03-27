# script_deployer

Script deployer implementation for deploying script-based services.

**Module Path**: `proxmox_nli.services.deployment.script_deployer`

## Classes

### ScriptDeployer

Deployer for script-based services.

#### deploy(service_def: Dict, vm_id: str, custom_params: Optional[Dict])

Deploy a script-based service.

Args:
    service_def: Service definition dictionary
    vm_id: Target VM ID
    custom_params: Custom deployment parameters
    
Returns:
    Deployment result dictionary

**Returns**: `Dict`

#### stop_service(service_def: Dict, vm_id: str)

Stop a script-based service.

Args:
    service_def: Service definition dictionary
    vm_id: Target VM ID
    
Returns:
    Stop result dictionary

**Returns**: `Dict`

#### remove_service(service_def: Dict, vm_id: str)

Remove a script-based service.

Args:
    service_def: Service definition dictionary
    vm_id: Target VM ID
    
Returns:
    Remove result dictionary

**Returns**: `Dict`

