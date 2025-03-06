"""
Script deployer implementation for deploying script-based services.
"""
import logging
from typing import Dict, Optional, List
from .base_deployer import BaseDeployer

logger = logging.getLogger(__name__)

class ScriptDeployer(BaseDeployer):
    """Deployer for script-based services."""
    
    def deploy(self, service_def: Dict, vm_id: str, custom_params: Optional[Dict] = None) -> Dict:
        """Deploy a script-based service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            custom_params: Custom deployment parameters
            
        Returns:
            Deployment result dictionary
        """
        try:
            # Verify VM is running
            vm_status = self.verify_vm(vm_id)
            if not vm_status["success"]:
                return vm_status
                
            # Get deployment script
            script = service_def['deployment'].get('script', '')
            if not script:
                return {
                    "success": False,
                    "message": "Script deployment specified but no script provided"
                }
                
            # Apply custom script if provided
            if custom_params and 'script' in custom_params:
                script = custom_params['script']
                
            # Execute pre-install steps
            if 'pre_install_steps' in service_def['deployment']:
                pre_result = self._execute_steps(service_def['deployment']['pre_install_steps'], vm_id)
                if not pre_result["success"]:
                    return pre_result
                
            # Execute main deployment script
            script_result = self.run_command(vm_id, script)
            if not script_result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to execute deployment script: {script_result.get('error', '')}"
                }
                
            # Execute post-install steps
            if 'post_install_steps' in service_def['deployment']:
                post_result = self._execute_steps(service_def['deployment']['post_install_steps'], vm_id)
                if not post_result["success"]:
                    logger.warning(f"Post-install steps failed: {post_result.get('message')}")
                
            return {
                "success": True,
                "message": f"Successfully deployed {service_def['name']}",
                "service_id": service_def['id'],
                "vm_id": vm_id,
                "access_info": service_def.get('access_info', "Service is now available")
            }
            
        except Exception as e:
            logger.error(f"Error deploying script service: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying script service: {str(e)}"
            }
            
    def _execute_steps(self, steps: List[str], vm_id: str) -> Dict:
        """Execute a list of script steps.
        
        Args:
            steps: List of commands to execute
            vm_id: Target VM ID
            
        Returns:
            Execution result dictionary
        """
        try:
            for step in steps:
                result = self.run_command(vm_id, step)
                if not result["success"]:
                    return {
                        "success": False,
                        "message": f"Step failed: {result.get('error', '')}",
                        "failed_step": step
                    }
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error executing steps: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing steps: {str(e)}"
            }
            
    def stop_service(self, service_def: Dict, vm_id: str) -> Dict:
        """Stop a script-based service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            
        Returns:
            Stop result dictionary
        """
        try:
            if 'stop_command' in service_def['deployment']:
                result = self.run_command(vm_id, service_def['deployment']['stop_command'])
                if not result["success"]:
                    return {
                        "success": False,
                        "message": f"Failed to stop service: {result.get('error', '')}"
                    }
            else:
                logger.warning(f"No stop command defined for service {service_def['name']}")
                
            return {
                "success": True,
                "message": f"Successfully stopped {service_def['name']}",
                "service_id": service_def['id'],
                "vm_id": vm_id
            }
            
        except Exception as e:
            logger.error(f"Error stopping script service: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping script service: {str(e)}"
            }
            
    def remove_service(self, service_def: Dict, vm_id: str) -> Dict:
        """Remove a script-based service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            
        Returns:
            Remove result dictionary
        """
        try:
            if 'uninstall_command' in service_def['deployment']:
                result = self.run_command(vm_id, service_def['deployment']['uninstall_command'])
                if not result["success"]:
                    return {
                        "success": False,
                        "message": f"Failed to remove service: {result.get('error', '')}"
                    }
            else:
                logger.warning(f"No uninstall command defined for service {service_def['name']}")
                
            return {
                "success": True,
                "message": f"Successfully removed {service_def['name']}",
                "service_id": service_def['id'],
                "vm_id": vm_id
            }
            
        except Exception as e:
            logger.error(f"Error removing script service: {str(e)}")
            return {
                "success": False,
                "message": f"Error removing script service: {str(e)}"
            }