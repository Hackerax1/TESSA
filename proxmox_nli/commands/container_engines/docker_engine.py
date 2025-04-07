"""
Docker container engine implementation.
"""
import json
from typing import Dict, List, Optional, Any
from .base_engine import ContainerEngine
from ..vm_command import VMCommand

class DockerEngine(ContainerEngine):
    """Docker container engine implementation."""
    
    def __init__(self, api):
        """Initialize Docker engine with api client"""
        self.api = api
        self.vm_command = VMCommand(api)
    
    def list_containers(self, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """List containers on a VM using Docker"""
        # Get the VM location if not provided
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        # Execute docker ps command via the VM's console
        result = self.vm_command.execute_command(vm_id, node, "docker ps --format '{{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}'")
        
        if result['success']:
            containers = []
            lines = result['output'].strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        containers.append({
                            'id': parts[0],
                            'image': parts[1],
                            'status': parts[2],
                            'name': parts[3]
                        })
            
            return {"success": True, "message": f"Docker containers on VM {vm_id}", "containers": containers}
        else:
            return result
    
    def start_container(self, container_name: str, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Start a Docker container on a VM"""
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        command = f"docker start {container_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            if container_name in result['output'].strip():
                return {"success": True, "message": f"Docker container {container_name} started successfully"}
            else:
                return {"success": False, "message": f"Failed to start Docker container {container_name}: {result['output']}"}
        else:
            return result
    
    def stop_container(self, container_name: str, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Stop a Docker container on a VM"""
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        command = f"docker stop {container_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            if container_name in result['output'].strip():
                return {"success": True, "message": f"Docker container {container_name} stopped successfully"}
            else:
                return {"success": False, "message": f"Failed to stop Docker container {container_name}: {result['output']}"}
        else:
            return result
    
    def get_container_logs(self, container_name: str, vm_id: str, node: Optional[str] = None, lines: int = 10) -> Dict[str, Any]:
        """Get logs from a Docker container"""
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        command = f"docker logs --tail {lines} {container_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            return {"success": True, "message": f"Logs for Docker container {container_name}", "logs": result['output']}
        else:
            return result
    
    def get_container_info(self, container_name: str, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a Docker container"""
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        command = f"docker inspect {container_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            try:
                info = json.loads(result['output'])
                return {"success": True, "message": f"Info for Docker container {container_name}", "info": info}
            except Exception as e:
                return {"success": False, "message": f"Failed to parse Docker container info: {str(e)}"}
        else:
            return result
    
    def pull_image(self, image_name: str, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Pull a Docker image on a VM"""
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        command = f"docker pull {image_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            return {"success": True, "message": f"Docker image {image_name} pulled successfully", "output": result['output']}
        else:
            return result
    
    def run_container(self, 
                     image_name: str, 
                     vm_id: str, 
                     node: Optional[str] = None,
                     container_name: Optional[str] = None, 
                     ports: Optional[List[str]] = None,
                     volumes: Optional[List[str]] = None,
                     environment: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run a Docker container on a VM"""
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        # Build docker run command
        command = "docker run -d"
        
        if container_name:
            command += f" --name {container_name}"
        
        if ports:
            for port in ports:
                command += f" -p {port}"
        
        if volumes:
            for volume in volumes:
                command += f" -v {volume}"
        
        if environment:
            for env in environment:
                command += f" -e {env}"
        
        command += f" {image_name}"
        
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            return {"success": True, "message": f"Docker container started successfully", "container_id": result['output'].strip()}
        else:
            return result
    
    def list_images(self, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """List Docker images on a VM"""
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        command = "docker images --format '{{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.Size}}'"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            images = []
            lines = result['output'].strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 3:
                        images.append({
                            'name': parts[0],
                            'id': parts[1],
                            'size': parts[2]
                        })
            
            return {"success": True, "message": "Docker images", "images": images}
        else:
            return result
    
    def get_compose_command(self) -> str:
        """Get the Docker Compose command"""
        return "docker-compose"
    
    def is_installed(self, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Check if Docker is installed on the VM"""
        if not node:
            node_info = self._get_vm_location(vm_id)
            if not node_info['success']:
                return node_info
            node = node_info['node']
        
        # Try to run a simple Docker command to check if it's installed
        command = "docker --version"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        is_installed = result['success'] and "Docker version" in result['output']
        
        return {
            "success": True,
            "installed": is_installed,
            "version": result['output'].strip() if is_installed else None,
            "message": f"Docker {'is' if is_installed else 'is not'} installed on VM {vm_id}"
        }
    
    @property
    def name(self) -> str:
        """Get container engine name"""
        return "docker"
    
    def _get_vm_location(self, vm_id: str) -> Dict[str, Any]:
        """Get the node where a VM is located"""
        result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not result['success']:
            return result
        
        for vm in result['data']:
            if str(vm['vmid']) == str(vm_id):
                return {"success": True, "node": vm['node']}
        
        return {"success": False, "message": f"VM {vm_id} not found"}