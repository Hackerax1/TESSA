from .vm_command import VMCommand

class DockerCommands:
    def __init__(self, api):
        self.api = api
        self.vm_command = VMCommand(api)

    def list_docker_containers(self, vm_id=None, node=None):
        """List Docker containers on a VM or across the cluster"""
        if vm_id:
            # Get the VM location if not provided
            if not node:
                vm_info = self._get_vm_location(vm_id)
                if not vm_info['success']:
                    return vm_info
                node = vm_info['node']
            
            # Execute docker ps command via the VM's console
            result = self.vm_command.execute_command(vm_id, node, "docker ps --format '{{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}'")
            
            if result['success']:
                containers = []
                lines = result['output'].strip().split('\n')
                for line in lines[1:]:  # Skip header if present
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
        else:
            # List Docker containers across the cluster (via Proxmox API)
            # This would require checking each running VM
            return {"success": False, "message": "Listing Docker containers across the cluster is not implemented yet"}

    def start_docker_container(self, container_name, vm_id=None, node=None):
        """Start a Docker container on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        if not node:
            vm_info = self._get_vm_location(vm_id)
            if not vm_info['success']:
                return vm_info
            node = vm_info['node']
        
        command = f"docker start {container_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            if container_name in result['output'].strip():
                return {"success": True, "message": f"Docker container {container_name} started successfully"}
            else:
                return {"success": False, "message": f"Failed to start Docker container {container_name}: {result['output']}"}
        else:
            return result

    def stop_docker_container(self, container_name, vm_id=None, node=None):
        """Stop a Docker container on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        if not node:
            vm_info = self._get_vm_location(vm_id)
            if not vm_info['success']:
                return vm_info
            node = vm_info['node']
        
        command = f"docker stop {container_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            if container_name in result['output'].strip():
                return {"success": True, "message": f"Docker container {container_name} stopped successfully"}
            else:
                return {"success": False, "message": f"Failed to stop Docker container {container_name}: {result['output']}"}
        else:
            return result

    def docker_container_logs(self, container_name, vm_id=None, node=None, lines=10):
        """Get logs from a Docker container"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        if not node:
            vm_info = self._get_vm_location(vm_id)
            if not vm_info['success']:
                return vm_info
            node = vm_info['node']
        
        command = f"docker logs --tail {lines} {container_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            return {"success": True, "message": f"Logs for Docker container {container_name}", "logs": result['output']}
        else:
            return result

    def docker_container_info(self, container_name, vm_id=None, node=None):
        """Get detailed information about a Docker container"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        if not node:
            vm_info = self._get_vm_location(vm_id)
            if not vm_info['success']:
                return vm_info
            node = vm_info['node']
        
        command = f"docker inspect {container_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            try:
                import json
                info = json.loads(result['output'])
                return {"success": True, "message": f"Info for Docker container {container_name}", "info": info}
            except Exception as e:
                return {"success": False, "message": f"Failed to parse Docker container info: {str(e)}"}
        else:
            return result

    def pull_docker_image(self, image_name, vm_id=None, node=None):
        """Pull a Docker image on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        if not node:
            vm_info = self._get_vm_location(vm_id)
            if not vm_info['success']:
                return vm_info
            node = vm_info['node']
        
        command = f"docker pull {image_name}"
        result = self.vm_command.execute_command(vm_id, node, command)
        
        if result['success']:
            return {"success": True, "message": f"Docker image {image_name} pulled successfully", "output": result['output']}
        else:
            return result

    def run_docker_container(self, image_name, container_name=None, ports=None, volumes=None, environment=None, vm_id=None, node=None):
        """Run a Docker container on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        if not node:
            vm_info = self._get_vm_location(vm_id)
            if not vm_info['success']:
                return vm_info
            node = vm_info['node']
        
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

    def list_docker_images(self, vm_id=None, node=None):
        """List Docker images on a VM"""
        if not vm_id:
            return {"success": False, "message": "Please specify a VM ID"}
            
        if not node:
            vm_info = self._get_vm_location(vm_id)
            if not vm_info['success']:
                return vm_info
            node = vm_info['node']
        
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

    def _get_vm_location(self, vm_id):
        """Get the node where a VM is located"""
        result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not result['success']:
            return result
        
        for vm in result['data']:
            if str(vm['vmid']) == str(vm_id):
                return {"success": True, "node": vm['node']}
        
        return {"success": False, "message": f"VM {vm_id} not found"}