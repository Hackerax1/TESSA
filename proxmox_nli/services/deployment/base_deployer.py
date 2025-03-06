"""
Base deployer class implementing common deployment functionality.
"""
import logging
from typing import Dict, Optional
from ...api.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class BaseDeployer:
    """Base class for service deployers."""
    
    def __init__(self, proxmox_api: ProxmoxAPI):
        """Initialize the deployer.
        
        Args:
            proxmox_api: ProxmoxAPI instance for interacting with Proxmox
        """
        self.api = proxmox_api
        
    def deploy(self, service_def: Dict, vm_id: str, custom_params: Optional[Dict] = None) -> Dict:
        """Deploy a service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            custom_params: Optional custom deployment parameters
            
        Returns:
            Deployment result dictionary
        """
        raise NotImplementedError("Subclasses must implement deploy()")
        
    def verify_vm(self, vm_id: str) -> Dict:
        """Verify VM exists and is running.
        
        Args:
            vm_id: VM ID to verify
            
        Returns:
            Status dictionary
        """
        try:
            # Check if VM exists and get status
            vm_info = self.api.api_request('GET', f'nodes/localhost/qemu/{vm_id}/status/current')
            if not vm_info['success']:
                return {
                    "success": False,
                    "message": f"Failed to get VM {vm_id} status"
                }
                
            status = vm_info['data']['status']
            if status != 'running':
                # Try to start the VM
                start_result = self.api.api_request('POST', f'nodes/localhost/qemu/{vm_id}/status/start')
                if not start_result['success']:
                    return {
                        "success": False,
                        "message": f"Failed to start VM {vm_id}"
                    }
                    
            return {
                "success": True,
                "status": "running"
            }
            
        except Exception as e:
            logger.error(f"Error verifying VM: {str(e)}")
            return {
                "success": False,
                "message": f"Error verifying VM: {str(e)}"
            }
            
    def run_command(self, vm_id: str, command: str) -> Dict:
        """Run a command on the target VM.
        
        Args:
            vm_id: Target VM ID
            command: Command to run
            
        Returns:
            Command result dictionary
        """
        try:
            result = self.api.api_request('POST', f'nodes/localhost/qemu/{vm_id}/agent/exec', {
                'command': command
            })
            
            return {
                "success": result['success'],
                "output": result.get('data', {}).get('out', ''),
                "error": result.get('data', {}).get('err', '')
            }
            
        except Exception as e:
            logger.error(f"Error running command: {str(e)}")
            return {
                "success": False,
                "message": f"Error running command: {str(e)}"
            }