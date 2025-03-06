"""
Docker deployer implementation for deploying Docker-based services.
"""
import logging
from typing import Dict, Optional
from .base_deployer import BaseDeployer

logger = logging.getLogger(__name__)

class DockerDeployer(BaseDeployer):
    """Deployer for Docker-based services."""
    
    def deploy(self, service_def: Dict, vm_id: str, custom_params: Optional[Dict] = None) -> Dict:
        """Deploy a Docker service.
        
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
                
            # Check deployment type
            if 'docker_compose' in service_def['deployment']:
                return self._deploy_compose(service_def, vm_id, custom_params)
            elif 'docker_image' in service_def['deployment']:
                return self._deploy_container(service_def, vm_id, custom_params)
            else:
                return {
                    "success": False,
                    "message": "Docker deployment specified but no docker_compose or docker_image provided"
                }
                
        except Exception as e:
            logger.error(f"Error deploying Docker service: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying Docker service: {str(e)}"
            }
            
    def _deploy_compose(self, service_def: Dict, vm_id: str, custom_params: Optional[Dict] = None) -> Dict:
        """Deploy using docker-compose."""
        try:
            # Get compose content
            compose_content = service_def['deployment']['docker_compose']
            if custom_params and 'docker_compose' in custom_params:
                compose_content = custom_params['docker_compose']
                
            # Write docker-compose.yml
            result = self.run_command(vm_id, f'cat > docker-compose.yml << EOL\n{compose_content}\nEOL')
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to create docker-compose.yml: {result.get('error', '')}"
                }
                
            # Run docker-compose up
            result = self.run_command(vm_id, 'docker-compose up -d')
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to start services: {result.get('error', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully deployed {service_def['name']} using docker-compose",
                "service_id": service_def['id'],
                "vm_id": vm_id,
                "access_info": service_def.get('access_info', "Service is now available")
            }
            
        except Exception as e:
            logger.error(f"Error deploying docker-compose service: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying docker-compose service: {str(e)}"
            }
            
    def _deploy_container(self, service_def: Dict, vm_id: str, custom_params: Optional[Dict] = None) -> Dict:
        """Deploy using docker run."""
        try:
            docker_image = service_def['deployment']['docker_image']
            
            # Pull the image
            result = self.run_command(vm_id, f'docker pull {docker_image}')
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to pull image: {result.get('error', '')}"
                }
                
            # Build docker run command
            port_mappings = service_def['deployment'].get('port_mappings', '')
            volume_mappings = service_def['deployment'].get('volume_mappings', '')
            environment_vars = service_def['deployment'].get('environment_vars', '')
            docker_run_args = service_def['deployment'].get('docker_run_args', '')
            
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
                    
            # Run the container
            docker_cmd = f"docker run -d --name {service_def['id']} {port_mappings} {volume_mappings} {environment_vars} {docker_run_args} {docker_image}"
            result = self.run_command(vm_id, docker_cmd)
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to start container: {result.get('error', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully deployed {service_def['name']} container",
                "service_id": service_def['id'],
                "vm_id": vm_id,
                "access_info": service_def.get('access_info', "Service is now available")
            }
            
        except Exception as e:
            logger.error(f"Error deploying Docker container: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying Docker container: {str(e)}"
            }
            
    def stop_service(self, service_def: Dict, vm_id: str) -> Dict:
        """Stop a Docker service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            
        Returns:
            Stop result dictionary
        """
        try:
            if 'docker_compose' in service_def['deployment']:
                result = self.run_command(vm_id, 'docker-compose down')
            else:
                result = self.run_command(vm_id, f"docker stop {service_def['id']}")
                
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to stop service: {result.get('error', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully stopped {service_def['name']}",
                "service_id": service_def['id'],
                "vm_id": vm_id
            }
            
        except Exception as e:
            logger.error(f"Error stopping Docker service: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping Docker service: {str(e)}"
            }
            
    def remove_service(self, service_def: Dict, vm_id: str) -> Dict:
        """Remove a Docker service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            
        Returns:
            Remove result dictionary
        """
        try:
            if 'docker_compose' in service_def['deployment']:
                result = self.run_command(vm_id, 'docker-compose down -v')
            else:
                result = self.run_command(vm_id, f"docker rm -f {service_def['id']}")
                
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to remove service: {result.get('error', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully removed {service_def['name']}",
                "service_id": service_def['id'],
                "vm_id": vm_id
            }
            
        except Exception as e:
            logger.error(f"Error removing Docker service: {str(e)}")
            return {
                "success": False,
                "message": f"Error removing Docker service: {str(e)}"
            }