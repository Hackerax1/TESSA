"""
Container deployer implementation for deploying services using Docker, Podman, or other container engines.
"""
import logging
from typing import Dict, Optional, Any
from .base_deployer import BaseDeployer
from ...commands.container_engines.factory import ContainerEngineFactory

logger = logging.getLogger(__name__)

class DockerDeployer(BaseDeployer):
    """Deployer for container-based services using Docker, Podman, or others."""
    
    def __init__(self, proxmox_api):
        """Initialize with Proxmox API client"""
        super().__init__(proxmox_api)
        self.engine_factory = ContainerEngineFactory(proxmox_api)
    
    def deploy(self, service_def: Dict, vm_id: str, custom_params: Optional[Dict] = None) -> Dict:
        """Deploy a container service.
        
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
            
            # Get container engine preference from service_def or custom_params
            container_engine = self._get_container_engine_name(service_def, custom_params)
            
            # Check deployment type
            if 'docker_compose' in service_def['deployment']:
                return self._deploy_compose(service_def, vm_id, custom_params, container_engine)
            elif 'docker_image' in service_def['deployment']:
                return self._deploy_container(service_def, vm_id, custom_params, container_engine)
            else:
                return {
                    "success": False,
                    "message": "Container deployment specified but no docker_compose or docker_image provided"
                }
                
        except Exception as e:
            logger.error(f"Error deploying container service: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying container service: {str(e)}"
            }
    
    def _get_container_engine_name(self, service_def: Dict, custom_params: Optional[Dict] = None) -> str:
        """Get the container engine name from service definition or custom params"""
        # Check in custom params first
        if custom_params and 'container_engine' in custom_params:
            return custom_params['container_engine']
        
        # Then check in service definition
        if 'container_engine' in service_def.get('deployment', {}):
            return service_def['deployment']['container_engine']
            
        # Default to Docker
        return 'docker'
    
    def _get_engine_for_vm(self, vm_id: str, preferred_engine: Optional[str] = None) -> Dict[str, Any]:
        """Get the appropriate container engine for a VM"""
        # First check if the preferred engine is installed
        if preferred_engine:
            try:
                engine = self.engine_factory.get_engine(preferred_engine)
                is_installed = engine.is_installed(vm_id)
                if is_installed.get('installed', False):
                    return {
                        "success": True, 
                        "engine": engine,
                        "engine_name": preferred_engine
                    }
                logger.info(f"Preferred engine {preferred_engine} not installed on VM {vm_id}, will auto-detect")
            except ValueError:
                logger.warning(f"Unsupported container engine: {preferred_engine}")
        
        # Auto-detect available engines
        detection_result = self.engine_factory.detect_available_engines(vm_id)
        if detection_result["success"] and detection_result["preferred_engine"]:
            preferred = detection_result["preferred_engine"]
            return {
                "success": True,
                "engine": self.engine_factory.get_engine(preferred),
                "engine_name": preferred
            }
        
        # No engine available
        return {
            "success": False,
            "message": f"No supported container engine found on VM {vm_id}"
        }
            
    def _deploy_compose(self, service_def: Dict, vm_id: str, custom_params: Optional[Dict] = None, 
                        preferred_engine: Optional[str] = None) -> Dict:
        """Deploy using container compose."""
        try:
            # Get the appropriate container engine
            engine_result = self._get_engine_for_vm(vm_id, preferred_engine)
            if not engine_result["success"]:
                return engine_result
            
            engine = engine_result["engine"]
            engine_name = engine_result["engine_name"]
            compose_command = engine.get_compose_command()
            
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
                
            # Run compose up
            result = self.run_command(vm_id, f'{compose_command} up -d')
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to start services: {result.get('error', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully deployed {service_def['name']} using {engine_name}",
                "service_id": service_def['id'],
                "vm_id": vm_id,
                "container_engine": engine_name,
                "access_info": service_def.get('access_info', "Service is now available")
            }
            
        except Exception as e:
            logger.error(f"Error deploying compose service: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying compose service: {str(e)}"
            }
            
    def _deploy_container(self, service_def: Dict, vm_id: str, custom_params: Optional[Dict] = None,
                          preferred_engine: Optional[str] = None) -> Dict:
        """Deploy using container run."""
        try:
            # Get the appropriate container engine
            engine_result = self._get_engine_for_vm(vm_id, preferred_engine)
            if not engine_result["success"]:
                return engine_result
            
            engine = engine_result["engine"]
            engine_name = engine_result["engine_name"]
            
            # Extract configuration
            docker_image = service_def['deployment']['docker_image']
            port_mappings = service_def['deployment'].get('port_mappings', '')
            volume_mappings = service_def['deployment'].get('volume_mappings', '')
            environment_vars = service_def['deployment'].get('environment_vars', '')
            docker_run_args = service_def['deployment'].get('docker_run_args', '')
            
            # Apply custom params
            if custom_params:
                if 'docker_image' in custom_params:
                    docker_image = custom_params['docker_image']
                if 'port_mappings' in custom_params:
                    port_mappings = custom_params['port_mappings']
                if 'volume_mappings' in custom_params:
                    volume_mappings = custom_params['volume_mappings']
                if 'environment_vars' in custom_params:
                    environment_vars = custom_params['environment_vars']
                if 'docker_run_args' in custom_params:
                    docker_run_args = custom_params['docker_run_args']
                    
            # Pull the image
            pull_result = engine.pull_image(docker_image, vm_id)
            if not pull_result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to pull image: {pull_result.get('error', '')}"
                }
            
            # Parse arguments for the container engine
            ports = []
            if port_mappings:
                # Convert "-p 8080:80 -p 443:443" format to list of port mappings
                parts = port_mappings.split('-p')
                for part in parts:
                    if part.strip():
                        ports.append(part.strip())
            
            volumes = []
            if volume_mappings:
                # Convert "-v /host:/container -v /host2:/container2" format to list of volume mappings
                parts = volume_mappings.split('-v')
                for part in parts:
                    if part.strip():
                        volumes.append(part.strip())
            
            env_vars = []
            if environment_vars:
                # Convert "-e VAR=value -e VAR2=value2" format to list of environment variables
                parts = environment_vars.split('-e')
                for part in parts:
                    if part.strip():
                        env_vars.append(part.strip())
            
            # Run the container
            run_result = engine.run_container(
                image_name=docker_image,
                vm_id=vm_id,
                container_name=service_def['id'],
                ports=ports,
                volumes=volumes,
                environment=env_vars
            )
            
            if not run_result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to start container: {run_result.get('error', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully deployed {service_def['name']} container using {engine_name}",
                "service_id": service_def['id'],
                "vm_id": vm_id,
                "container_engine": engine_name,
                "access_info": service_def.get('access_info', "Service is now available")
            }
            
        except Exception as e:
            logger.error(f"Error deploying container: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying container: {str(e)}"
            }
            
    def stop_service(self, service_def: Dict, vm_id: str) -> Dict:
        """Stop a container service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            
        Returns:
            Stop result dictionary
        """
        try:
            # Get container engine preference
            preferred_engine = self._get_container_engine_name(service_def, None)
            
            # Get the appropriate container engine
            engine_result = self._get_engine_for_vm(vm_id, preferred_engine)
            if not engine_result["success"]:
                return engine_result
            
            engine = engine_result["engine"]
            engine_name = engine_result["engine_name"]
            
            if 'docker_compose' in service_def['deployment']:
                compose_command = engine.get_compose_command()
                result = self.run_command(vm_id, f'{compose_command} down')
            else:
                result = engine.stop_container(service_def['id'], vm_id)
                
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to stop service: {result.get('error', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully stopped {service_def['name']} using {engine_name}",
                "service_id": service_def['id'],
                "vm_id": vm_id,
                "container_engine": engine_name
            }
            
        except Exception as e:
            logger.error(f"Error stopping container service: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping container service: {str(e)}"
            }
            
    def remove_service(self, service_def: Dict, vm_id: str) -> Dict:
        """Remove a container service.
        
        Args:
            service_def: Service definition dictionary
            vm_id: Target VM ID
            
        Returns:
            Remove result dictionary
        """
        try:
            # Get container engine preference
            preferred_engine = self._get_container_engine_name(service_def, None)
            
            # Get the appropriate container engine
            engine_result = self._get_engine_for_vm(vm_id, preferred_engine)
            if not engine_result["success"]:
                return engine_result
            
            engine = engine_result["engine"]
            engine_name = engine_result["engine_name"]
            
            if 'docker_compose' in service_def['deployment']:
                compose_command = engine.get_compose_command()
                result = self.run_command(vm_id, f'{compose_command} down -v')
            else:
                # First stop the container if running
                stop_result = engine.stop_container(service_def['id'], vm_id)
                # Then remove it (using direct command since some engines might need different params)
                cmd = f"{engine.name} rm -f {service_def['id']}"
                result = self.run_command(vm_id, cmd)
                
            if not result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to remove service: {result.get('error', '')}"
                }
                
            return {
                "success": True,
                "message": f"Successfully removed {service_def['name']} using {engine_name}",
                "service_id": service_def['id'],
                "vm_id": vm_id,
                "container_engine": engine_name
            }
            
        except Exception as e:
            logger.error(f"Error removing container service: {str(e)}")
            return {
                "success": False,
                "message": f"Error removing container service: {str(e)}"
            }