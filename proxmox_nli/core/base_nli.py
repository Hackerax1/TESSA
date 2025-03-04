"""
Base NLI module providing core initialization and common functionality.
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
from .user_preferences import UserPreferencesManager
from prometheus_client import start_http_server
import importlib.util
import sys

class BaseNLI:
    def __init__(self, host, user, password, realm='pam', verify_ssl=False):
        """Initialize the Base Natural Language Interface"""
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
        
        # Initialize user preferences manager
        self.user_preferences = UserPreferencesManager()
        
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

    def get_help(self):
        """Get help information"""
        help_text = self.get_help_text()
        return {"success": True, "message": help_text}