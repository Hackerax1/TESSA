# base_deployer

Base deployer class implementing common deployment functionality.

**Module Path**: `proxmox_nli.services.deployment.base_deployer`

## Classes

### BaseDeployer

Base class for service deployers.

#### __init__(proxmox_api: ProxmoxAPI)

Initialize the deployer.

Args:
    proxmox_api: ProxmoxAPI instance for interacting with Proxmox

#### deploy(service_def: Dict, vm_id: str, custom_params: Optional[Dict])

Deploy a service.

Args:
    service_def: Service definition dictionary
    vm_id: Target VM ID
    custom_params: Optional custom deployment parameters
    
Returns:
    Deployment result dictionary

**Returns**: `Dict`

#### verify_vm(vm_id: str)

Verify VM exists and is running.

Args:
    vm_id: VM ID to verify
    
Returns:
    Status dictionary

**Returns**: `Dict`

#### run_command(vm_id: str, command: str)

Run a command on the target VM.

Args:
    vm_id: Target VM ID
    command: Command to run
    
Returns:
    Command result dictionary

**Returns**: `Dict`

