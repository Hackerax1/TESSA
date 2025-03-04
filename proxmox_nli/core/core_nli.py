"""
Core NLI module providing the main interface for Proxmox natural language processing.
"""
import os
from ..api.proxmox_api import ProxmoxAPI
from ..nlu.nlu_engine import NLU_Engine
from ..commands.proxmox_commands import ProxmoxCommands
from ..commands.docker_commands import DockerCommands
from ..commands.vm_command import VMCommand
from ..services.service_catalog import ServiceCatalog
from ..services.service_manager import ServiceManager
from .response_generator import ResponseGenerator
from .audit_logger import AuditLogger
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
        
        # Initialize services
        self.service_catalog = ServiceCatalog()
        self.service_manager = ServiceManager(self.api, self.service_catalog)
        
        # Initialize audit logger
        self.audit_logger = AuditLogger()
        
        # Connect response generator to Ollama client if available
        if use_ollama and self.nlu.ollama_client:
            self.response_generator.set_ollama_client(self.nlu.ollama_client)
        
        start_http_server(8000)
        self.load_custom_commands()
        
        # Add confirmation required flag and pending command storage
        self.require_confirmation = True
        self.pending_command = None
        self.pending_args = None
        self.pending_entities = None
    
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
        # Skip confirmation for safe read-only operations
        safe_intents = ['list_vms', 'list_containers', 'cluster_status', 'node_status', 
                       'storage_info', 'list_docker_containers', 'list_docker_images', 
                       'docker_container_logs', 'vm_status', 'help', 'list_available_services',
                       'list_deployed_services', 'find_service', 'service_status']
        
        if self.require_confirmation and intent not in safe_intents:
            # Store command for later execution
            self.pending_command = intent
            self.pending_args = args
            self.pending_entities = entities
            
            # Generate confirmation message
            confirmation_msg = self._get_confirmation_message(intent, args, entities)
            return {"success": True, "requires_confirmation": True, "message": confirmation_msg}
        
        return self._execute_command(intent, args, entities)
    
    def confirm_command(self, confirmed=True):
        """Handle command confirmation"""
        if not self.pending_command:
            return {"success": False, "message": "No pending command to confirm"}
        
        if confirmed:
            # Execute the pending command
            result = self._execute_command(self.pending_command, self.pending_args, self.pending_entities)
            # Clear pending command
            self.pending_command = None
            self.pending_args = None
            self.pending_entities = None
            return result
        else:
            # Command was rejected
            self.pending_command = None
            self.pending_args = None
            self.pending_entities = None
            return {"success": True, "message": "Command cancelled"}
    
    def _execute_command(self, intent, args, entities):
        """Internal method to actually execute the command"""
        # Move original execute_intent logic here
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
        
        # Service management intents
        elif intent == 'list_available_services':
            services = self.service_catalog.get_all_services()
            service_list = "\n".join([f"- {s['name']}: {s['description']}" for s in services])
            return {
                "success": True,
                "message": f"Available services:\n\n{service_list if service_list else 'No services available'}"
            }
        
        elif intent == 'list_deployed_services':
            result = self.service_manager.list_deployed_services()
            if result["success"] and result["services"]:
                service_list = "\n".join([f"- {s['name']} (ID: {s['service_id']}) on VM {s['vm_id']}" for s in result["services"]])
                return {
                    "success": True,
                    "message": f"Deployed services:\n\n{service_list}"
                }
            else:
                return {
                    "success": True,
                    "message": "No services are currently deployed"
                }
        
        elif intent == 'find_service':
            query = args[0] if args and args[0] else entities.get('QUERY')
            if not query:
                return {"success": False, "message": "Please specify what kind of service you're looking for"}
                
            matching_services = self.service_manager.find_service(query)
            
            if matching_services:
                service_list = "\n".join([f"- {s['name']} (ID: {s['id']}): {s['description']}" for s in matching_services])
                return {
                    "success": True,
                    "message": f"Found these services matching '{query}':\n\n{service_list}\n\nTo deploy one, use 'deploy SERVICE_ID'"
                }
            else:
                return {
                    "success": True,
                    "message": f"No services found matching '{query}'. Please check our available services with 'list services'."
                }
        
        elif intent == 'deploy_service':
            service_id = args[0] if args and args[0] else entities.get('SERVICE_ID')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            custom_params = entities.get('SERVICE_PARAMS', {})
            
            if not service_id:
                return {"success": False, "message": "Please specify which service you want to deploy"}
                
            result = self.service_manager.deploy_service(service_id, vm_id, custom_params)
            
            if result["success"]:
                # Save context for follow-up commands
                self.nlu.context_manager.set_context({
                    'current_service': service_id,
                    'current_service_vm': result.get('vm_id')
                })
                
            return result
        
        elif intent == 'service_status':
            service_id = args[0] if args and args[0] else entities.get('SERVICE_ID')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            
            if not service_id or not vm_id:
                return {"success": False, "message": "Please specify the service ID and VM ID"}
                
            return self.service_manager.get_service_status(service_id, vm_id)
        
        elif intent == 'stop_service':
            service_id = args[0] if args and args[0] else entities.get('SERVICE_ID')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            
            if not service_id or not vm_id:
                return {"success": False, "message": "Please specify the service ID and VM ID"}
                
            return self.service_manager.stop_service(service_id, vm_id)
        
        elif intent == 'remove_service':
            service_id = args[0] if args and args[0] else entities.get('SERVICE_ID')
            vm_id = args[1] if args and len(args) > 1 and args[1] else entities.get('VM_ID')
            remove_vm = entities.get('REMOVE_VM', False)
            
            if not service_id or not vm_id:
                return {"success": False, "message": "Please specify the service ID and VM ID"}
                
            return self.service_manager.remove_service(service_id, vm_id, remove_vm)
                
        # Help intent
        elif intent == 'help':
            return self.get_help()
        else:
            return {"success": False, "message": "I don't understand what you want me to do. Try asking for 'help' to see available commands."}
    
    def _get_confirmation_message(self, intent, args, entities):
        """Generate a confirmation message for the pending command"""
        messages = {
            'start_vm': f"Are you sure you want to start VM {args[0] if args else entities.get('VM_ID')}?",
            'stop_vm': f"Are you sure you want to stop VM {args[0] if args else entities.get('VM_ID')}?",
            'restart_vm': f"Are you sure you want to restart VM {args[0] if args else entities.get('VM_ID')}?",
            'delete_vm': f"Are you sure you want to DELETE VM {args[0] if args else entities.get('VM_ID')}? This cannot be undone!",
            'create_vm': "Are you sure you want to create a new VM with these parameters?",
            'start_docker_container': f"Are you sure you want to start Docker container {entities.get('CONTAINER_NAME')} on VM {entities.get('VM_ID')}?",
            'stop_docker_container': f"Are you sure you want to stop Docker container {entities.get('CONTAINER_NAME')} on VM {entities.get('VM_ID')}?",
            'run_docker_container': f"Are you sure you want to run a new Docker container from image {entities.get('IMAGE_NAME')} on VM {entities.get('VM_ID')}?",
            'run_cli_command': f"Are you sure you want to execute command '{entities.get('COMMAND')}' on VM {entities.get('VM_ID')}?",
            'deploy_service': f"Are you sure you want to deploy {args[0] if args else entities.get('SERVICE_ID')} service{' on VM ' + args[1] if args and len(args) > 1 else ''}?",
            'stop_service': f"Are you sure you want to stop {args[0] if args else entities.get('SERVICE_ID')} service on VM {args[1] if args and len(args) > 1 else entities.get('VM_ID')}?",
            'remove_service': f"Are you sure you want to remove {args[0] if args else entities.get('SERVICE_ID')} service from VM {args[1] if args and len(args) > 1 else entities.get('VM_ID')}?",
        }
        
        return messages.get(intent, "Are you sure you want to execute this command?") + "\nReply with 'yes' to confirm or 'no' to cancel."
    
    def get_help(self):
        """Get help information"""
        help_text = self.get_help_text()
        return {"success": True, "message": help_text}
    
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
            "Service Management:",
            "- list services - List all available services",
            "- list deployed services - List all deployed services",
            "- find service for <description> - Find services matching description",
            "- I want a home network adblocker - Find services matching description",
            "- deploy <service_id> on vm <id> - Deploy a service",
            "- status of service <id> on vm <id> - Check service status",
            "- stop service <id> on vm <id> - Stop a service",
            "- remove service <id> on vm <id> - Remove a service",
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
    def process_query(self, query, user=None, source='cli', ip_address=None):
        """Process a natural language query"""
        # Process the query using NLU engine
        intent, args, entities = self.nlu.process_query(query)
        
        # Execute intent
        result = self.execute_intent(intent, args, entities)
        
        # Log the command execution
        self.audit_logger.log_command(
            query=query,
            intent=intent,
            entities=entities,
            result=result,
            user=user,
            source=source,
            ip_address=ip_address
        )
        
        # Generate response
        return self.response_generator.generate_response(query, intent, result)

    def get_recent_activity(self, limit=100):
        """Get recent command executions"""
        return self.audit_logger.get_recent_logs(limit)

    def get_user_activity(self, user, limit=100):
        """Get recent activity for a specific user"""
        return self.audit_logger.get_user_activity(user, limit)

    def get_failed_commands(self, limit=100):
        """Get recent failed command executions"""
        return self.audit_logger.get_failed_commands(limit)

    def backup_vm(self, vm_id, backup_dir):
        """Backup a VM to the specified directory"""
        return self.commands.backup_vm(vm_id, backup_dir)

    def restore_vm(self, backup_file, vm_id):
        """Restore a VM from the specified backup file"""
        self.commands.restore_vm(backup_file, vm_id)