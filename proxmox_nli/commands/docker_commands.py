"""
Docker and container management commands.
Handles interaction with Docker and other container engines on VMs.
"""
from .vm_command import VMCommand
from .container_engines.factory import ContainerEngineFactory

class DockerCommands:
    """
    Commands for managing containers across different container engines.
    Despite the name, this class can work with Docker alternatives like Podman.
    """
    
    def __init__(self, api):
        self.api = api
        self.vm_command = VMCommand(api)
        self.engine_factory = ContainerEngineFactory(api)
        
    def get_container_engine(self, vm_id=None, node=None, engine_name=None):
        """
        Get the appropriate container engine for a VM.
        
        If engine_name is specified, use that engine.
        Otherwise, detect available engines on the VM and use the preferred one.
        
        Args:
            vm_id: Target VM ID
            node: Optional node where VM is located
            engine_name: Optional engine name to use
            
        Returns:
            The container engine to use or None if none available
        """
        if engine_name:
            try:
                return self.engine_factory.get_engine(engine_name)
            except ValueError as e:
                return None
                
        if vm_id:
            # Detect available engines
            result = self.engine_factory.detect_available_engines(vm_id, node)
            if result["success"] and result["preferred_engine"]:
                return self.engine_factory.get_engine(result["preferred_engine"])
                
        # Fall back to default engine
        return self.engine_factory.get_engine()

    def list_docker_containers(self, vm_id=None, node=None, engine_name=None):
        """List containers on a VM or across the cluster"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        engine = self.get_container_engine(vm_id, node, engine_name)
        if not engine:
            return {"success": False, "message": f"No supported container engine found on VM {vm_id}"}
            
        return engine.list_containers(vm_id, node)

    def start_docker_container(self, container_name, vm_id=None, node=None, engine_name=None):
        """Start a container on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        engine = self.get_container_engine(vm_id, node, engine_name)
        if not engine:
            return {"success": False, "message": f"No supported container engine found on VM {vm_id}"}
            
        return engine.start_container(container_name, vm_id, node)

    def stop_docker_container(self, container_name, vm_id=None, node=None, engine_name=None):
        """Stop a container on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        engine = self.get_container_engine(vm_id, node, engine_name)
        if not engine:
            return {"success": False, "message": f"No supported container engine found on VM {vm_id}"}
            
        return engine.stop_container(container_name, vm_id, node)

    def docker_container_logs(self, container_name, vm_id=None, node=None, lines=10, engine_name=None):
        """Get logs from a container"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        engine = self.get_container_engine(vm_id, node, engine_name)
        if not engine:
            return {"success": False, "message": f"No supported container engine found on VM {vm_id}"}
            
        return engine.get_container_logs(container_name, vm_id, node, lines)

    def docker_container_info(self, container_name, vm_id=None, node=None, engine_name=None):
        """Get detailed information about a container"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        engine = self.get_container_engine(vm_id, node, engine_name)
        if not engine:
            return {"success": False, "message": f"No supported container engine found on VM {vm_id}"}
            
        return engine.get_container_info(container_name, vm_id, node)

    def pull_docker_image(self, image_name, vm_id=None, node=None, engine_name=None):
        """Pull a container image on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        engine = self.get_container_engine(vm_id, node, engine_name)
        if not engine:
            return {"success": False, "message": f"No supported container engine found on VM {vm_id}"}
            
        return engine.pull_image(image_name, vm_id, node)

    def run_docker_container(self, image_name, container_name=None, ports=None, volumes=None, environment=None, vm_id=None, node=None, engine_name=None):
        """Run a container on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        engine = self.get_container_engine(vm_id, node, engine_name)
        if not engine:
            return {"success": False, "message": f"No supported container engine found on VM {vm_id}"}
            
        return engine.run_container(image_name, vm_id, node, container_name, ports, volumes, environment)

    def list_docker_images(self, vm_id=None, node=None, engine_name=None):
        """List container images on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        engine = self.get_container_engine(vm_id, node, engine_name)
        if not engine:
            return {"success": False, "message": f"No supported container engine found on VM {vm_id}"}
            
        return engine.list_images(vm_id, node)
    
    def list_available_engines(self, vm_id, node=None):
        """
        List available container engines on a VM.
        
        Args:
            vm_id: Target VM ID
            node: Optional node where VM is located
            
        Returns:
            Dict with available container engines and their versions
        """
        return self.engine_factory.detect_available_engines(vm_id, node)
    
    def _get_vm_location(self, vm_id):
        """Get the node where a VM is located"""
        result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not result['success']:
            return result
        
        for vm in result['data']:
            if str(vm['vmid']) == str(vm_id):
                return {"success": True, "node": vm['node']}
        
        return {"success": False, "message": f"VM {vm_id} not found"}