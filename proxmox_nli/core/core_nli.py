"""
Core NLI module providing the main interface for Proxmox natural language processing.
"""
import urllib3
import os
import logging
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from prometheus_client import Summary
from .base_nli import BaseNLI
from .command_executor import CommandExecutor
from .response_generator import ResponseGenerator
from .service_handler import ServiceHandler
from .security.user_manager import UserManager
from ..nlu.nlu_engine import NLU_Engine
from ..nlu.ollama_client import OllamaClient
from ..nlu.huggingface_client import HuggingFaceClient
from ..commands.update_command import UpdateCommand
from ..services.update_manager import UpdateManager
from ..utils.discovery import discover_network_services, DEFAULT_SERVICE_DEFINITIONS
from ..utils.dns_config import update_hosts_file

# Configure logging
logger = logging.getLogger(__name__)

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

class ProxmoxNLI(BaseNLI):
    def __init__(self, host, user, password, realm='pam', verify_ssl=False):
        """Initialize the Proxmox NLI with all components"""
        super().__init__(host, user, password, realm, verify_ssl)
        
        # Initialize NLU engine with Ollama and Hugging Face options
        use_ollama = os.getenv("DISABLE_OLLAMA", "").lower() != "true"
        use_huggingface = os.getenv("DISABLE_HUGGINGFACE", "").lower() != "true"
        
        self.nlu_engine = NLU_Engine(
            use_ollama=use_ollama,
            use_huggingface=use_huggingface,
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3"),
            ollama_url=os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
            huggingface_model=os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"),
            huggingface_api_key=os.getenv("HUGGINGFACE_API_KEY", "")
        )
        
        # Initialize response generator and set LLM clients
        self.response_generator = ResponseGenerator()
        if self.nlu_engine.use_ollama and self.nlu_engine.ollama_client:
            self.response_generator.set_ollama_client(self.nlu_engine.ollama_client)
        if self.nlu_engine.use_huggingface and self.nlu_engine.huggingface_client:
            self.response_generator.set_huggingface_client(self.nlu_engine.huggingface_client)
        
        # Initialize components with self as base_nli
        self.command_executor = CommandExecutor(self)
        self.service_handler = ServiceHandler(self)
        self.user_manager = UserManager(self)
        
        # Initialize update management components
        self.update_manager = UpdateManager(self.service_manager)
        self.update_command = UpdateCommand(self.update_manager)
        
        # Start automatic update checking (once per day by default)
        self.update_manager.start_checking()

    def execute_intent(self, intent, args, entities):
        """Execute the identified intent"""
        # Skip confirmation for safe read-only operations
        safe_intents = ['list_vms', 'list_containers', 'cluster_status', 'node_status', 
                       'storage_info', 'list_docker_containers', 'list_docker_images', 
                       'docker_container_logs', 'vm_status', 'help', 'list_available_services',
                       'list_deployed_services', 'find_service', 'service_status',
                       'check_updates', 'list_updates', 'get_update_status',
                       'get_scheduler_status', 'list_backups', 'verify_backup',
                       'discover_proxmox', 'discover_service', 'discover_all_services']
        
        if self.require_confirmation and intent not in safe_intents:
            # Store command for later execution
            self.pending_command = intent
            self.pending_args = args
            self.pending_entities = entities
            
            # Generate confirmation message
            confirmation_msg = self._get_confirmation_message(intent, args, entities)
            return {"success": True, "requires_confirmation": True, "message": confirmation_msg}
        
        # Handle service-related intents through service handler
        if intent in ['list_available_services', 'list_deployed_services', 'find_service', 
                     'deploy_service', 'service_status', 'stop_service', 'remove_service']:
            return self.service_handler.handle_service_intent(intent, args, entities)
        
        # Handle update-related intents through update command
        elif intent in ['check_updates', 'list_updates', 'apply_updates', 'update_settings', 'get_update_status']:
            return self._handle_update_intent(intent, args, entities)
            
        # --- Handle Discovery Intents ---
        elif intent in ['discover_proxmox', 'discover_service', 'discover_all_services']:
            return self._handle_discovery_intent(intent, args, entities)
            
        # Handle other commands through command executor
        return self.command_executor._execute_command(intent, args, entities)

    def _handle_update_intent(self, intent, args, entities):
        """Handle update-related intents"""
        if not self.update_command:
            return {"success": False, "message": "Update command handler not available"}
        
        # Convert entities to arguments expected by UpdateCommand methods
        command_args = {}
        
        # Extract service ID if specified
        if 'SERVICE_ID' in entities:
            command_args['service_id'] = entities['SERVICE_ID']
        
        # Handle specific update intents
        if intent == 'check_updates':
            return self.update_command.check_updates(command_args)
        elif intent == 'list_updates':
            return self.update_command.list_updates(command_args)
        elif intent == 'apply_updates':
            # Check if "all" flag is set
            if 'ALL' in entities and entities['ALL']:
                command_args['all'] = True
            return self.update_command.apply_updates(command_args)
        elif intent == 'update_settings':
            # Extract settings from entities
            if 'AUTO_CHECK' in entities:
                command_args['auto_check'] = entities['AUTO_CHECK'].lower() == 'true'
            if 'CHECK_INTERVAL' in entities:
                try:
                    command_args['check_interval'] = float(entities['CHECK_INTERVAL'])
                except ValueError:
                    pass
            return self.update_command.update_settings(command_args)
        elif intent == 'get_update_status':
            return self.update_command.get_update_status()
        
        return {"success": False, "message": f"Unknown update intent: {intent}"}

    def _handle_discovery_intent(self, intent, args, entities):
        """Handles all service discovery related intents."""
        logger.info(f"Executing discovery intent: {intent}")
        service_names_to_discover = None # Default: discover all
        target_service_description = "all defined services"
        
        if intent == 'discover_proxmox':
            service_names_to_discover = ["proxmox"]
            target_service_description = "Proxmox instances"
        elif intent == 'discover_service':
            # Extract service name from entities (NLU needs to provide SERVICE_NAME)
            target_name = entities.get('SERVICE_NAME', '').lower()
            if not target_name:
                 return {"success": False, "message": "Please specify which service to discover (e.g., 'discover jellyfin')."}
            
            # Map common names to internal definition keys if needed
            # Example simple mapping:
            service_mapping = { "jellyfin": "jellyfin_http" } 
            internal_name = service_mapping.get(target_name, target_name) # Use target_name if no mapping
            
            if internal_name not in DEFAULT_SERVICE_DEFINITIONS:
                 known_services = ", ".join(DEFAULT_SERVICE_DEFINITIONS.keys())
                 return {"success": False, "message": f"Sorry, I don't know how to discover '{target_name}'. Known types: {known_services}"}
            
            service_names_to_discover = [internal_name]
            target_service_description = f"{target_name} instances"
            
        # For 'discover_all_services', service_names_to_discover remains None
        
        dns_update_message = ""
        message = f"Attempting to discover {target_service_description} on the network...\n"

        try:
            # Perform discovery
            # Can add timeout argument extraction from args/entities if needed later
            discovered_services = discover_network_services(service_names=service_names_to_discover, timeout=10)
            
            all_discovered_hosts = [] # Flatten list for DNS update
            found_any = False
            
            if discovered_services:
                result_message_parts = ["Discovery Results:"]
                for service_name, hosts in discovered_services.items():
                    if hosts:
                        found_any = True
                        result_message_parts.append(f"  {service_name.replace('_', ' ').title()}:")
                        for host in hosts:
                             result_message_parts.append(f"    - Server: {host['server']} ({host['address']}:{host['port']})")
                             all_discovered_hosts.append(host) # Add to flat list for DNS
                    # Optionally report services that were searched for but not found
                    # else:
                    #    result_message_parts.append(f"  {service_name.replace('_',' ').title()}: None found")
                message += "\n".join(result_message_parts)
                logger.info(f"Discovery successful, found {len(all_discovered_hosts)} total instances across requested types.")
            
            if not found_any:
                 message += f"\nNo {target_service_description} found on the local network via mDNS discovery."
                 logger.info("Discovery completed, no matching instances found.")

            # --- Attempt to update hosts file with *all* discovered hosts ---
            if all_discovered_hosts:
                 logger.info(f"Attempting to update local hosts file with {len(all_discovered_hosts)} discovered entries...")
                 # Pass the flat list of all found hosts regardless of type
                 dns_result = update_hosts_file(all_discovered_hosts)
                 dns_update_message = f"\n\nHosts file update status:\n{dns_result.get('message', 'Unknown error during DNS update.')}"
                 logger.info(f"Hosts file update result: {dns_result}")
            # --- End hosts file update ---

            # Combine discovery message and DNS update message
            final_message = message + dns_update_message
            return {"success": True, "message": final_message}
                
        except Exception as e:
            logger.error(f"Error during service discovery execution: {e}", exc_info=True)
            return {"success": False, "message": f"An error occurred during discovery: {e}"}

    def confirm_command(self, confirmed=True):
        """Handle command confirmation"""
        if not self.pending_command:
            return {"success": False, "message": "No pending command to confirm"}
        
        if confirmed:
            # Execute the pending command
            result = self.execute_intent(self.pending_command, self.pending_args, self.pending_entities)
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

    def _get_confirmation_message(self, intent, args, entities):
        """Generate a confirmation message for the pending command"""
        messages = {
            'start_vm': f"Are you sure you want to start VM {entities.get('VM_ID')}?",
            'stop_vm': f"Are you sure you want to stop VM {entities.get('VM_ID')}?",
            'restart_vm': f"Are you sure you want to restart VM {entities.get('VM_ID')}?",
            'delete_vm': f"Are you sure you want to delete VM {entities.get('VM_ID')}? This cannot be undone!",
            'create_vm': "Are you sure you want to create a new VM with these parameters?",
            'deploy_service': f"Are you sure you want to deploy service {entities.get('SERVICE_ID')} to VM {entities.get('VM_ID')}?",
            'stop_service': f"Are you sure you want to stop service {entities.get('SERVICE_ID')} on VM {entities.get('VM_ID')}?",
            'remove_service': f"Are you sure you want to remove service {entities.get('SERVICE_ID')} from VM {entities.get('VM_ID')}?",
            'apply_updates': f"Are you sure you want to apply updates to {entities.get('SERVICE_ID', 'all services')}?",
            'start_backup_scheduler': "Are you sure you want to start the backup scheduler service?",
            'stop_backup_scheduler': "Are you sure you want to stop the backup scheduler service?",
            'schedule_backup': f"Are you sure you want to schedule backups for VM {entities.get('VM_ID')}?",
            'configure_recovery_testing': "Are you sure you want to configure automated recovery testing?",
            'configure_retention_policy': f"Are you sure you want to configure retention policy for VM {entities.get('VM_ID')}?",
            'run_backup_now': f"Are you sure you want to run a backup for VM {entities.get('VM_ID')} immediately?",
            'run_recovery_test_now': "Are you sure you want to run recovery testing immediately?",
        }
        return messages.get(intent, "Are you sure you want to execute this command?") + "\nReply with 'yes' to confirm or 'no' to cancel."

    @REQUEST_TIME.time()
    def process_query(self, query, user=None, source="cli", ip_address=None):
        """
        Process a natural language query and execute the corresponding action.
        
        Args:
            query: The natural language query
            user: The user who made the query
            source: The source of the query (e.g., cli, web, voice)
            ip_address: The IP address of the user (for web queries)
            
        Returns:
            str: The response to the query
        """
        # Check if a confirmation is pending
        if self.pending_command:
            self.audit_logger.log_query(
                query, 
                "confirmation", 
                {"confirmation": query},
                "Confirmation needed for previous command",
                False,
                user, 
                source, 
                ip_address
            )
            return "Please confirm the previous command first."
        
        # Process the query with the NLU engine
        intent, args, entities = self.nlu_engine.process_query(query)
        
        # Execute the intent
        result = self.execute_intent(intent, args, entities)
        
        # Generate a response based on the result
        response = self.response_generator.generate_response(query, intent, result)
        
        # Log the query to the audit log
        success = result.get("success", False) if isinstance(result, dict) else False
        result_msg = result.get("message", str(result)) if isinstance(result, dict) else str(result)
        
        self.audit_logger.log_query(
            query, 
            intent, 
            entities, 
            result_msg, 
            success,
            user, 
            source, 
            ip_address
        )
        
        # Track command in user history if it was successful
        if user and success and not query.lower().strip() in ["yes", "no", "y", "n"]:
            try:
                self.user_manager.add_to_command_history(user, query, intent, entities, success)
            except Exception as e:
                logger.error(f"Error adding command to history: {str(e)}")
        
        return response

    def get_recent_activity(self, limit=100):
        """Get recent audit logs with the specified limit"""
        return self.audit_logger.get_recent_logs(limit)