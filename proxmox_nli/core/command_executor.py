"""
Command executor module handling execution of various Proxmox commands.
"""

class CommandExecutor:
    def __init__(self, base_nli):
        self.commands = base_nli.commands
        self.docker_commands = base_nli.docker_commands
        self.vm_command = base_nli.vm_command
        self.get_help = base_nli.get_help

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

        # ZFS Management Commands
        elif intent == 'create_zfs_pool':
            node = args[0] if args else entities.get('NODE')
            name = args[1] if len(args) > 1 else entities.get('POOL_NAME')
            devices = args[2:] if len(args) > 2 else entities.get('DEVICES', [])
            raid_level = entities.get('RAID_LEVEL', 'mirror')
            
            if not all([node, name, devices]):
                return {"success": False, "message": "Please specify node, pool name, and devices"}
                
            return self.commands.create_zfs_pool(node, name, devices, raid_level)
            
        elif intent == 'list_zfs_pools':
            node = args[0] if args else entities.get('NODE')
            if not node:
                return {"success": False, "message": "Please specify a node"}
            return self.commands.get_zfs_pools(node)
            
        elif intent == 'create_zfs_dataset':
            node = args[0] if args else entities.get('NODE')
            name = args[1] if len(args) > 1 else entities.get('DATASET_NAME')
            options = entities.get('OPTIONS', {})
            
            if not all([node, name]):
                return {"success": False, "message": "Please specify node and dataset name"}
                
            return self.commands.create_zfs_dataset(node, name, options)
            
        elif intent == 'list_zfs_datasets':
            node = args[0] if args else entities.get('NODE')
            pool = args[1] if len(args) > 1 else entities.get('POOL_NAME')
            
            if not node:
                return {"success": False, "message": "Please specify a node"}
                
            return self.commands.get_zfs_datasets(node, pool)
            
        elif intent == 'set_zfs_properties':
            node = args[0] if args else entities.get('NODE')
            dataset = args[1] if len(args) > 1 else entities.get('DATASET_NAME')
            properties = entities.get('PROPERTIES', {})
            
            if not all([node, dataset, properties]):
                return {"success": False, "message": "Please specify node, dataset, and properties"}
                
            return self.commands.set_zfs_properties(node, dataset, properties)
            
        elif intent == 'create_zfs_snapshot':
            node = args[0] if args else entities.get('NODE')
            dataset = args[1] if len(args) > 1 else entities.get('DATASET_NAME')
            snapshot_name = args[2] if len(args) > 2 else entities.get('SNAPSHOT_NAME')
            recursive = entities.get('RECURSIVE', False)
            
            if not all([node, dataset, snapshot_name]):
                return {"success": False, "message": "Please specify node, dataset, and snapshot name"}
                
            return self.commands.create_zfs_snapshot(node, dataset, snapshot_name, recursive)
            
        elif intent == 'setup_zfs_auto_snapshots':
            node = args[0] if args else entities.get('NODE')
            dataset = args[1] if len(args) > 1 else entities.get('DATASET_NAME')
            schedule = args[2] if len(args) > 2 else entities.get('SCHEDULE', 'hourly')
            
            if not all([node, dataset]):
                return {"success": False, "message": "Please specify node and dataset"}
                
            return self.commands.setup_auto_snapshots(node, dataset, schedule)

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