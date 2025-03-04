"""
Core NLI module providing the main interface for Proxmox natural language processing.
"""
import os
from ..api.proxmox_api import ProxmoxAPI
from ..nlu.nlu_engine import NLU_Engine
from ..commands.proxmox_commands import ProxmoxCommands
from ..commands.docker_commands import DockerCommands
from ..commands.vm_command import VMCommand
from .response_generator import ResponseGenerator
from prometheus_client import start_http_server, Summary
import importlib.util
import sys

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

class ProxmoxNLI:
    def __init__(self, host, user, password, realm='pam', verify_ssl=False):
        """Initialize the Proxmox Natural Language Interface"""
        self.api = ProxmoxAPI(host, user, password, realm, verify_ssl)
        
        # Initialize NLU with Ollama integration
        use_ollama = os.getenv("DISABLE_OLLAMA", "").lower() != "true"
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        
        self.nlu = NLU_Engine(
            use_ollama=use_ollama, 
            ollama_model=ollama_model,
            ollama_url=ollama_url
        )
        
        self.commands = ProxmoxCommands(self.api)
        self.docker_commands = DockerCommands(self.api)
        self.vm_command = VMCommand(self.api)
        self.response_generator = ResponseGenerator()
        
        # Connect response generator to Ollama client if available
        if use_ollama and self.nlu.ollama_client:
            self.response_generator.set_ollama_client(self.nlu.ollama_client)
        
        start_http_server(8000)
        self.load_custom_commands()
    
    def load_custom_commands(self):
        """Load custom commands from the custom_commands directory"""
        custom_commands_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'custom_commands')
        if not os.path.exists(custom_commands_dir):
            return
        for filename in os.listdir(custom_commands_dir):
            if filename.endswith('.py'):
                module_name = filename[:-3]
                file_path = os.path.join(custom_commands_dir, filename)
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                if hasattr(module, 'register_commands'):
                    module.register_commands(self)
    
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
    
    def get_help(self):
        """Get help information"""
        return {"success": True, "message": "Available commands"}
    
    @staticmethod
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
    
    @REQUEST_TIME.time()
    def process_query(self, query):
        """Process a natural language query"""
        # Process the query using NLU engine
        intent, args, entities = self.nlu.process_query(query)
        
        # Execute intent
        result = self.execute_intent(intent, args, entities)
        
        # Generate response
        return self.response_generator.generate_response(query, intent, result)

    def backup_vm(self, vm_id, backup_dir):
        """Backup a VM to the specified directory"""
        return self.commands.backup_vm(vm_id, backup_dir)

    def restore_vm(self, backup_file, vm_id):
        """Restore a VM from the specified backup file"""
        self.commands.restore_vm(backup_file, vm_id)