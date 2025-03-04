"""
Service manager for deploying and managing services via Proxmox VE.
This module handles the actual deployment of services defined in the service catalog.
"""
import logging
import os
from typing import Dict, List, Optional, Tuple

from ..api.proxmox_api import ProxmoxAPI
from .service_catalog import ServiceCatalog

logger = logging.getLogger(__name__)

class ServiceManager:
    """Manager for deploying and managing services on Proxmox VE."""
    
    def __init__(self, proxmox_api: ProxmoxAPI, service_catalog: ServiceCatalog = None):
        """Initialize the service manager.
        
        Args:
            proxmox_api: ProxmoxAPI instance for interacting with Proxmox VE
            service_catalog: ServiceCatalog instance, or None to create a new one
        """
        self.api = proxmox_api
        self.catalog = service_catalog if service_catalog else ServiceCatalog()
        
    def find_service(self, query: str) -> List[Dict]:
        """Find services matching the user's query.
        
        Args:
            query: Natural language query describing desired service
            
        Returns:
            List of matching service definitions
        """
        return self.catalog.find_services_by_keywords(query)
        
    def deploy_service(self, service_id: str, target_vm_id: str = None, 
                     custom_params: Dict = None) -> Dict:
        """Deploy a service on a target VM.
        
        Args:
            service_id: ID of the service to deploy
            target_vm_id: ID of the VM to deploy the service on. If None, creates a new VM.
            custom_params: Custom parameters for service deployment
            
        Returns:
            Dictionary with deployment result
        """
        # Get service definition
        service_def = self.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        # Check if target VM exists and is running, or create a new one
        vm_id = target_vm_id
        if not vm_id:
            # Create a new VM based on service requirements
            vm_params = service_def.get('vm_requirements', {})
            vm_params['name'] = f"{service_def['id']}-vm"
            
            # Apply custom VM params if provided
            if custom_params and 'vm_params' in custom_params:
                vm_params.update(custom_params['vm_params'])
                
            # Call Proxmox API to create VM
            try:
                # Implementation depends on proxmox_commands structure
                # This is a placeholder - actual implementation would use the API
                vm_result = {"success": True, "vm_id": "100", "message": "VM created successfully"}
                vm_id = vm_result["vm_id"]
                
                if not vm_result["success"]:
                    return {
                        "success": False,
                        "message": f"Failed to create VM: {vm_result['message']}"
                    }
            except Exception as e:
                logger.error(f"Error creating VM: {str(e)}")
                return {
                    "success": False, 
                    "message": f"Failed to create VM: {str(e)}"
                }
        
        # Ensure VM is running
        try:
            vm_status = {"success": True, "status": "running"}  # Placeholder
            if vm_status.get("status") != "running":
                # Start the VM
                start_result = {"success": True}  # Placeholder
                if not start_result["success"]:
                    return {
                        "success": False,
                        "message": f"Failed to start VM {vm_id}"
                    }
        except Exception as e:
            logger.error(f"Error checking VM status: {str(e)}")
            return {
                "success": False,
                "message": f"Error checking VM status: {str(e)}"
            }
            
        # Execute deployment steps based on deployment method
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        if deployment_method == 'docker':
            return self._deploy_docker_service(service_def, vm_id, custom_params)
        elif deployment_method == 'script':
            return self._deploy_script_service(service_def, vm_id, custom_params)
        else:
            return {
                "success": False,
                "message": f"Unsupported deployment method: {deployment_method}"
            }
    
    def _deploy_docker_service(self, service_def: Dict, vm_id: str, 
                             custom_params: Dict = None) -> Dict:
        """Deploy a Docker-based service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            custom_params: Custom deployment parameters
            
        Returns:
            Deployment result dictionary
        """
        docker_compose = service_def['deployment'].get('docker_compose')
        docker_image = service_def['deployment'].get('docker_image')
        docker_run_args = service_def['deployment'].get('docker_run_args', '')
        
        try:
            if docker_compose:
                # Deploy using docker-compose
                # 1. Create the docker-compose.yml file on the VM
                compose_content = docker_compose
                if custom_params and 'docker_compose' in custom_params:
                    # Merge or replace compose content based on implementation needs
                    compose_content = custom_params['docker_compose']
                    
                # Write docker-compose.yml to VM
                cmd_result = {"success": True}  # Placeholder
                
                # 2. Run docker-compose up
                cmd_result = {"success": True}  # Placeholder
                
                if not cmd_result.get("success", False):
                    return {
                        "success": False,
                        "message": f"Failed to deploy Docker Compose service: {cmd_result.get('message', '')}"
                    }
            elif docker_image:
                # Deploy using docker run
                # 1. Pull the Docker image
                cmd = f"docker pull {docker_image}"
                cmd_result = {"success": True}  # Placeholder
                
                # 2. Run the Docker container
                port_mappings = service_def['deployment'].get('port_mappings', '')
                volume_mappings = service_def['deployment'].get('volume_mappings', '')
                environment_vars = service_def['deployment'].get('environment_vars', '')
                
                # Apply custom params
                if custom_params:
                    if 'port_mappings' in custom_params:
                        port_mappings = custom_params['port_mappings']
                    if 'volume_mappings' in custom_params:
                        volume_mappings = custom_params['volume_mappings']
                    if 'environment_vars' in custom_params:
                        environment_vars = custom_params['environment_vars']
                    if 'docker_run_args' in custom_params:
                        docker_run_args = custom_params['docker_run_args']
                
                # Build docker run command
                docker_cmd = f"docker run -d --name {service_def['id']} {port_mappings} {volume_mappings} {environment_vars} {docker_run_args} {docker_image}"
                cmd_result = {"success": True}  # Placeholder
                
                if not cmd_result.get("success", False):
                    return {
                        "success": False,
                        "message": f"Failed to deploy Docker container: {cmd_result.get('message', '')}"
                    }
            else:
                return {
                    "success": False,
                    "message": "Docker deployment specified but no docker_compose or docker_image provided"
                }
                
            # Run any post-installation steps
            for step in service_def['deployment'].get('post_install_steps', []):
                cmd_result = {"success": True}  # Placeholder
                if not cmd_result.get("success", False):
                    logger.warning(f"Post-install step failed: {step}")
            
            return {
                "success": True,
                "message": f"Successfully deployed {service_def['name']} on VM {vm_id}",
                "service_id": service_def['id'],
                "vm_id": vm_id,
                "access_info": service_def.get('access_info', "Service is now available")
            }
            
        except Exception as e:
            logger.error(f"Error deploying Docker service: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying Docker service: {str(e)}"
            }
    
    def _deploy_script_service(self, service_def: Dict, vm_id: str, 
                             custom_params: Dict = None) -> Dict:
        """Deploy a service using custom script.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            custom_params: Custom deployment parameters
            
        Returns:
            Deployment result dictionary
        """
        script = service_def['deployment'].get('script', '')
        
        if not script:
            return {
                "success": False,
                "message": "Script deployment specified but no script provided"
            }
            
        # Apply custom script if provided
        if custom_params and 'script' in custom_params:
            script = custom_params['script']
            
        try:
            # Upload and execute script on VM
            cmd_result = {"success": True}  # Placeholder
            
            if not cmd_result.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to deploy script service: {cmd_result.get('message', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully deployed {service_def['name']} on VM {vm_id}",
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
    
    def get_service_status(self, service_id: str, vm_id: str) -> Dict:
        """Get status of a deployed service.
        
        Args:
            service_id: ID of the service to check
            vm_id: ID of the VM running the service
            
        Returns:
            Status information dictionary
        """
        service_def = self.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        try:
            if deployment_method == 'docker':
                # Check Docker container status
                cmd = f"docker ps -a --filter name={service_id} --format '{{{{.Status}}}}'"
                cmd_result = {"success": True, "output": "Up 2 hours"}  # Placeholder
                
                if cmd_result.get("success", False):
                    return {
                        "success": True,
                        "status": cmd_result.get("output", "Unknown"),
                        "service_id": service_id,
                        "vm_id": vm_id
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to get Docker container status: {cmd_result.get('message', '')}"
                    }
            else:
                # For script-based services, check using a status command if available
                if 'status_check' in service_def['deployment']:
                    status_cmd = service_def['deployment']['status_check']
                    cmd_result = {"success": True, "output": "Service is running"}  # Placeholder
                    
                    return {
                        "success": True,
                        "status": cmd_result.get("output", "Unknown"),
                        "service_id": service_id,
                        "vm_id": vm_id
                    }
                else:
                    # Default to checking if the service process is running
                    default_check = f"ps aux | grep -v grep | grep {service_def.get('process_name', service_id)}"
                    cmd_result = {"success": True, "output": "Service is running"}  # Placeholder
                    
                    return {
                        "success": True,
                        "status": "Running" if cmd_result.get("output") else "Not running",
                        "service_id": service_id,
                        "vm_id": vm_id
                    }
                    
        except Exception as e:
            logger.error(f"Error checking service status: {str(e)}")
            return {
                "success": False,
                "message": f"Error checking service status: {str(e)}"
            }
    
    def list_deployed_services(self) -> Dict:
        """List all deployed services.
        
        Returns:
            Dictionary with deployed services information
        """
        # This is a placeholder - actual implementation would query all VMs
        # and identify which ones are running known services
        return {
            "success": True,
            "services": []
        }
    
    def stop_service(self, service_id: str, vm_id: str) -> Dict:
        """Stop a running service.
        
        Args:
            service_id: ID of the service to stop
            vm_id: ID of the VM running the service
            
        Returns:
            Result dictionary
        """
        service_def = self.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        try:
            if deployment_method == 'docker':
                # Stop Docker container
                cmd = f"docker stop {service_id}"
                cmd_result = {"success": True}  # Placeholder
                
                if cmd_result.get("success", False):
                    return {
                        "success": True,
                        "message": f"Successfully stopped service {service_def['name']}",
                        "service_id": service_id,
                        "vm_id": vm_id
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to stop Docker container: {cmd_result.get('message', '')}"
                    }
            else:
                # For script-based services, run a stop command if available
                if 'stop_command' in service_def['deployment']:
                    stop_cmd = service_def['deployment']['stop_command']
                    cmd_result = {"success": True}  # Placeholder
                    
                    return {
                        "success": True,
                        "message": f"Successfully stopped service {service_def['name']}",
                        "service_id": service_id,
                        "vm_id": vm_id
                    }
                else:
                    return {
                        "success": False,
                        "message": f"No stop command defined for service {service_def['name']}"
                    }
                    
        except Exception as e:
            logger.error(f"Error stopping service: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping service: {str(e)}"
            }
    
    def remove_service(self, service_id: str, vm_id: str, remove_vm: bool = False) -> Dict:
        """Remove a deployed service.
        
        Args:
            service_id: ID of the service to remove
            vm_id: ID of the VM running the service
            remove_vm: Whether to remove the VM as well
            
        Returns:
            Result dictionary
        """
        service_def = self.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        try:
            if deployment_method == 'docker':
                # Remove Docker container
                cmd = f"docker rm -f {service_id}"
                cmd_result = {"success": True}  # Placeholder
                
                if not cmd_result.get("success", False):
                    return {
                        "success": False,
                        "message": f"Failed to remove Docker container: {cmd_result.get('message', '')}"
                    }
            else:
                # For script-based services, run an uninstall command if available
                if 'uninstall_command' in service_def['deployment']:
                    uninstall_cmd = service_def['deployment']['uninstall_command']
                    cmd_result = {"success": True}  # Placeholder
                    
                    if not cmd_result.get("success", False):
                        return {
                            "success": False,
                            "message": f"Failed to uninstall service: {cmd_result.get('message', '')}"
                        }
                
            # Remove VM if requested
            if remove_vm:
                # Call Proxmox API to delete VM
                vm_result = {"success": True}  # Placeholder
                
                if not vm_result.get("success", False):
                    return {
                        "success": False,
                        "message": f"Failed to remove VM {vm_id}: {vm_result.get('message', '')}"
                    }
                    
            return {
                "success": True,
                "message": f"Successfully removed service {service_def['name']}" + 
                          (f" and VM {vm_id}" if remove_vm else ""),
                "service_id": service_id,
                "vm_id": vm_id
            }
                    
        except Exception as e:
            logger.error(f"Error removing service: {str(e)}")
            return {
                "success": False,
                "message": f"Error removing service: {str(e)}"
            }