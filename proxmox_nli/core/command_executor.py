"""
Command executor module handling execution of various Proxmox commands.
"""
from .base_nli import BaseNLI

class CommandExecutor(BaseNLI):
    def _execute_command(self, intent, args, entities):
        """Internal method to execute the command"""
        # VM Management
        if intent == 'list_vms':
            return self.commands.list_vms()
        elif intent == 'start_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.start_vm(vm_id)
            return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'stop_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.stop_vm(vm_id)
            return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'restart_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.restart_vm(vm_id)
            return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'vm_status':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.get_vm_status(vm_id)
            return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'create_vm':
            params = entities.get('PARAMS', {})
            return self.commands.create_vm(params)
        elif intent == 'delete_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.delete_vm(vm_id)
            return {"success": False, "message": "Please specify a VM ID"}

        # Container Management
        elif intent == 'list_containers':
            return self.commands.list_containers()

        # Cluster Management
        elif intent == 'cluster_status':
            return self.commands.get_cluster_status()
        elif intent == 'node_status':
            node = args[0] if args else entities.get('NODE')
            if node:
                return self.commands.get_node_status(node)
            return {"success": False, "message": "Please specify a node name"}
        elif intent == 'storage_info':
            return self.commands.get_storage_info()

        # Docker Management
        elif intent == 'list_docker_containers':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.docker_commands.list_docker_containers(vm_id)
            return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'start_docker_container':
            container_name = args[0] if args else entities.get('CONTAINER_NAME')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            if container_name and vm_id:
                return self.docker_commands.start_docker_container(container_name, vm_id)
            return {"success": False, "message": "Please specify a container name and VM ID"}
        elif intent == 'stop_docker_container':
            container_name = args[0] if args else entities.get('CONTAINER_NAME')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            if container_name and vm_id:
                return self.docker_commands.stop_docker_container(container_name, vm_id)
            return {"success": False, "message": "Please specify a container name and VM ID"}
        elif intent == 'docker_container_logs':
            container_name = args[0] if args else entities.get('CONTAINER_NAME')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            if container_name and vm_id:
                return self.docker_commands.docker_container_logs(container_name, vm_id)
            return {"success": False, "message": "Please specify a container name and VM ID"}
        elif intent == 'list_docker_images':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.docker_commands.list_docker_images(vm_id)
            return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'pull_docker_image':
            image_name = args[0] if args else entities.get('IMAGE_NAME')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            if image_name and vm_id:
                return self.docker_commands.pull_docker_image(image_name, vm_id)
            return {"success": False, "message": "Please specify an image name and VM ID"}
        elif intent == 'run_docker_container':
            image_name = args[0] if args else entities.get('IMAGE_NAME')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            if image_name and vm_id:
                docker_params = entities.get('DOCKER_PARAMS', {})
                return self.docker_commands.run_docker_container(
                    image_name, 
                    docker_params.get('container_name'), 
                    docker_params.get('ports'), 
                    docker_params.get('volumes'),
                    docker_params.get('environment'),
                    vm_id
                )
            return {"success": False, "message": "Please specify an image name and VM ID"}

        # CLI Command Execution
        elif intent == 'run_cli_command':
            command = args[0] if args else entities.get('COMMAND')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            if command and vm_id:
                return self.vm_command.run_cli_command(vm_id, command)
            return {"success": False, "message": "Please specify a command and VM ID"}

        # Help Intent
        elif intent == 'help':
            return self.get_help()
        else:
            return {"success": False, "message": "I don't understand what you want me to do. Try asking for 'help' to see available commands."}