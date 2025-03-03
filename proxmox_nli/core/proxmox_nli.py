from ..api.proxmox_api import ProxmoxAPI
from ..nlu.nlu_engine import NLU_Engine
from ..commands.proxmox_commands import ProxmoxCommands
from ..commands.docker_commands import DockerCommands
from ..commands.vm_command import VMCommand

class ProxmoxNLI:
    def __init__(self, host, user, password, realm='pam', verify_ssl=False):
        """Initialize the Proxmox Natural Language Interface"""
        self.api = ProxmoxAPI(host, user, password, realm, verify_ssl)
        self.nlu = NLU_Engine()
        self.commands = ProxmoxCommands(self.api)
        self.docker_commands = DockerCommands(self.api)
        self.vm_command = VMCommand(self.api)
    
    def execute_intent(self, intent, args, entities):
        """Execute the identified intent"""
        # VM management intents
        if intent == 'list_vms':
            return self.commands.list_vms()
        elif intent == 'start_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.start_vm(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'stop_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.stop_vm(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'restart_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.restart_vm(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'vm_status':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.get_vm_status(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'create_vm':
            params = entities.get('PARAMS', {})
            return self.commands.create_vm(params)
        elif intent == 'delete_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.delete_vm(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
                
        # Container management intents
        elif intent == 'list_containers':
            return self.commands.list_containers()
            
        # Cluster management intents
        elif intent == 'cluster_status':
            return self.commands.get_cluster_status()
        elif intent == 'node_status':
            node = args[0] if args else entities.get('NODE')
            if node:
                return self.commands.get_node_status(node)
            else:
                return {"success": False, "message": "Please specify a node name"}
        elif intent == 'storage_info':
            return self.commands.get_storage_info()
            
        # Docker management intents
        elif intent == 'list_docker_containers':
            vm_id = args[0] if args and args[0] else entities.get('VM_ID')
            if vm_id:
                return self.docker_commands.list_docker_containers(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'start_docker_container':
            container_name = args[0] if args and args[0] else entities.get('CONTAINER_NAME')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            if container_name and vm_id:
                return self.docker_commands.start_docker_container(container_name, vm_id)
            else:
                return {"success": False, "message": "Please specify a container name and VM ID"}
        elif intent == 'stop_docker_container':
            container_name = args[0] if args and args[0] else entities.get('CONTAINER_NAME')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            if container_name and vm_id:
                return self.docker_commands.stop_docker_container(container_name, vm_id)
            else:
                return {"success": False, "message": "Please specify a container name and VM ID"}
        elif intent == 'docker_container_logs':
            container_name = args[0] if args and args[0] else entities.get('CONTAINER_NAME')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            if container_name and vm_id:
                return self.docker_commands.docker_container_logs(container_name, vm_id)
            else:
                return {"success": False, "message": "Please specify a container name and VM ID"}
        elif intent == 'list_docker_images':
            vm_id = args[0] if args and args[0] else entities.get('VM_ID')
            if vm_id:
                return self.docker_commands.list_docker_images(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'pull_docker_image':
            image_name = args[0] if args and args[0] else entities.get('IMAGE_NAME')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            if image_name and vm_id:
                return self.docker_commands.pull_docker_image(image_name, vm_id)
            else:
                return {"success": False, "message": "Please specify an image name and VM ID"}
        elif intent == 'run_docker_container':
            image_name = args[0] if args and args[0] else entities.get('IMAGE_NAME')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
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
            else:
                return {"success": False, "message": "Please specify an image name and VM ID"}
                
        # VM CLI command execution
        elif intent == 'run_cli_command':
            command = args[0] if args and args[0] else entities.get('COMMAND')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            if command and vm_id:
                return self.vm_command.run_cli_command(vm_id, command)
            else:
                return {"success": False, "message": "Please specify a command and VM ID"}
                
        # Help intent
        elif intent == 'help':
            return self.get_help()
        else:
            return {"success": False, "message": "I don't understand what you want me to do. Try asking for 'help' to see available commands."}
    
    def generate_response(self, query, intent, result):
        """Generate a natural language response"""
        if not result['success']:
            return f"Sorry, there was an error: {result['message']}"
        
        # VM management responses
        if intent == 'list_vms':
            if not result.get('vms'):
                return "I couldn't find any virtual machines."
            
            vm_list = result['vms']
            if len(vm_list) == 0:
                return "There are no virtual machines running on your Proxmox cluster."
            
            response = f"I found {len(vm_list)} virtual machines:\n\n"
            for vm in vm_list:
                response += f"• VM {vm['id']} - {vm['name']} ({vm['status']}) on node {vm['node']}\n"
                response += f"  CPU: {vm['cpu']} cores, Memory: {vm['memory']:.1f} MB, Disk: {vm['disk']:.1f} GB\n\n"
            
            return response.strip()
        
        elif intent in ['start_vm', 'stop_vm', 'restart_vm', 'delete_vm']:
            return result['message']
        
        elif intent == 'vm_status':
            status = result['status']
            response = f"Status of VM {result['message'].split()[-1]}:\n"
            response += f"• State: {status['status']}\n"
            response += f"• CPU usage: {status['cpu']:.2f}\n"
            response += f"• Memory: {status['memory']:.1f} MB\n"
            response += f"• Disk: {status['disk']:.1f} GB"
            return response
        
        elif intent == 'create_vm':
            return result['message']
        
        # Container management responses
        elif intent == 'list_containers':
            if not result.get('containers'):
                return "I couldn't find any containers."
            
            container_list = result['containers']
            if len(container_list) == 0:
                return "There are no containers running on your Proxmox cluster."
            
            response = f"I found {len(container_list)} containers:\n\n"
            for ct in container_list:
                response += f"• Container {ct['id']} - {ct['name']} ({ct['status']}) on node {ct['node']}\n"
            
            return response.strip()
        
        # Cluster management responses
        elif intent == 'cluster_status':
            status = result['status']
            response = "Cluster status:\n"
            for node in status:
                response += f"• {node['name']} ({node['type']}): {node['status']}\n"
            return response.strip()
        
        elif intent == 'node_status':
            status = result['status']
            node_name = result['message'].split()[1]
            response = f"Status of node {node_name}:\n"
            response += f"• CPU: {status['cpuinfo']['cpus']} CPUs, {status['loadavg'][0]:.2f} load\n"
            response += f"• Memory: {status['memory']['used'] / (1024*1024):.1f} MB used of {status['memory']['total'] / (1024*1024):.1f} MB\n"
            response += f"• Uptime: {status['uptime'] // 86400} days {(status['uptime'] % 86400) // 3600} hours"
            return response
        
        elif intent == 'storage_info':
            storages = result['storages']
            response = f"I found {len(storages)} storage locations:\n\n"
            for storage in storages:
                used_percent = (storage['used'] / storage['total'] * 100) if storage['total'] > 0 else 0
                response += f"• {storage['name']} ({storage['type']}) on node {storage['node']}:\n"
                response += f"  {storage['used']:.1f} GB used of {storage['total']:.1f} GB ({used_percent:.1f}%)\n"
                response += f"  {storage['available']:.1f} GB available\n\n"
            return response.strip()
        
        # Docker management responses
        elif intent == 'list_docker_containers':
            if not result.get('containers'):
                return "I couldn't find any Docker containers on this VM."
            
            containers = result['containers']
            if len(containers) == 0:
                return "There are no Docker containers on this VM."
            
            response = f"I found {len(containers)} Docker containers:\n\n"
            for container in containers:
                response += f"• {container['name']} ({container['id']})\n"
                response += f"  Image: {container['image']}\n"
                response += f"  Status: {container['status']}\n\n"
            return response.strip()
        
        elif intent in ['start_docker_container', 'stop_docker_container']:
            return result['message']
        
        elif intent == 'docker_container_logs':
            response = f"Logs for container {result['message'].split()[-2]}:\n\n"
            response += result['logs']
            return response
        
        elif intent == 'list_docker_images':
            if not result.get('images'):
                return "I couldn't find any Docker images on this VM."
            
            images = result['images']
            if len(images) == 0:
                return "There are no Docker images on this VM."
            
            response = f"I found {len(images)} Docker images:\n\n"
            for image in images:
                response += f"• {image['name']} ({image['id']})\n"
                response += f"  Size: {image['size']}\n\n"
            return response.strip()
        
        elif intent == 'pull_docker_image':
            return f"Docker image pulled successfully. Output:\n\n{result['output']}"
        
        elif intent == 'run_docker_container':
            return f"Docker container started with ID: {result['container_id']}"
        
        # VM CLI command execution response
        elif intent == 'run_cli_command':
            response = "Command executed successfully. Output:\n\n"
            response += result['output']
            return response
        
        elif intent == 'help':
            return self.get_help_text()
        
        else:
            return "I'm not sure how to respond to that. Try asking for 'help' to see available commands."
    
    def get_help(self):
        """Get help information"""
        return {"success": True, "message": "Available commands"}
    
    def get_help_text(self):
        """Get the help text with all available commands"""
        commands = [
            "VM Management:",
            "- list vms - Show all virtual machines",
            "- start vm <id> - Start a virtual machine",
            "- stop vm <id> - Stop a virtual machine",
            "- restart vm <id> - Restart a virtual machine",
            "- status of vm <id> - Get status of a virtual machine",
            "- create a new vm with 2GB RAM, 2 CPUs and 20GB disk using ubuntu - Create a new VM",
            "- delete vm <id> - Delete a virtual machine",
            "",
            "Container Management:",
            "- list containers - Show all LXC containers",
            "",
            "Cluster Management:",
            "- get cluster status - Show cluster status",
            "- get status of node <n> - Show node status",
            "- get storage info - Show storage information",
            "",
            "Docker Management:",
            "- list docker containers on vm <id> - List Docker containers on a VM",
            "- start docker container <n> on vm <id> - Start a Docker container",
            "- stop docker container <n> on vm <id> - Stop a Docker container",
            "- show logs for docker container <n> on vm <id> - Show Docker container logs",
            "- list docker images on vm <id> - List Docker images on a VM",
            "- pull docker image <n> on vm <id> - Pull a Docker image on a VM",
            "- run docker container using image <n> on vm <id> - Run a new Docker container",
            "",
            "CLI Command Execution:",
            "- run command \"<command>\" on vm <id> - Execute a command on a VM",
            "- execute \"<command>\" on vm <id> - Execute a command on a VM",
            "",
            "General:",
            "- help - Show this help message"
        ]
        return "\n".join(commands)
    
    def process_query(self, query):
        """Process a natural language query"""
        # Preprocess the query
        preprocessed_query = self.nlu.preprocess_query(query)
        
        # Extract entities
        entities = self.nlu.extract_entities(query)
        
        # Identify intent
        intent, args = self.nlu.identify_intent(preprocessed_query)
        
        # Update conversation context
        self.nlu.update_context(intent, entities)
        
        # Execute intent
        result = self.execute_intent(intent, args, entities)
        
        return self.generate_response(query, intent, result)


def cli_mode(args):
    """Run the Proxmox NLI in command line interface mode"""
    proxmox_nli = ProxmoxNLI(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl
    )
    
    print("Proxmox Natural Language Interface")
    print("Type 'exit' or 'quit' to exit")
    print("Type 'help' to see available commands")
    
    while True:
        query = input("\n> ")
        if query.lower() in ['exit', 'quit']:
            break
        
        response = proxmox_nli.process_query(query)
        print(response)


def web_mode(args):
    """Run the Proxmox NLI as a web server with voice recognition"""
    from app import start_app
    
    print("Starting web interface on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop the server")
    
    start_app(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl,
        debug=args.debug
    )