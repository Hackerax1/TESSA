"""
Core NLI module providing the main interface for Proxmox natural language processing.
"""
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from prometheus_client import Summary
from .base_nli import BaseNLI
from .command_executor import CommandExecutor
from .service_handler import ServiceHandler
from .user_manager import UserManager

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

class ProxmoxNLI(BaseNLI):
    def __init__(self, host, user, password, realm='pam', verify_ssl=False):
        """Initialize the Proxmox NLI with all components"""
        super().__init__(host, user, password, realm, verify_ssl)
        
        # Initialize components with self as base_nli
        self.command_executor = CommandExecutor(self)
        self.service_handler = ServiceHandler(self)
        self.user_manager = UserManager(self)

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
        
        # Handle service-related intents through service handler
        if intent in ['list_available_services', 'list_deployed_services', 'find_service', 
                     'deploy_service', 'service_status', 'stop_service', 'remove_service']:
            return self.service_handler.handle_service_intent(intent, args, entities)
            
        # Handle other commands through command executor
        return self.command_executor._execute_command(intent, args, entities)

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
        }
        return messages.get(intent, "Are you sure you want to execute this command?") + "\nReply with 'yes' to confirm or 'no' to cancel."

    @REQUEST_TIME.time()
    def process_query(self, query, user=None, source='cli', ip_address=None):
        """Process a natural language query"""
        # Process the query using NLU engine
        intent, args, entities = self.nlu.process_query(query)
        
        # Update user preferences with context through user manager
        if user:
            # Track command usage for this user
            self.user_preferences.track_command_usage(user, query, intent)
            
            # Auto-add favorites for frequently accessed resources
            if intent in ['vm_status', 'start_vm', 'stop_vm', 'restart_vm'] and 'VM_ID' in entities:
                vm_id = entities['VM_ID']
                self.user_preferences.add_favorite_vm(user, vm_id)
            
            if intent in ['node_status'] and 'NODE' in entities:
                node_name = entities['NODE']
                self.user_preferences.add_favorite_node(user, node_name)
                
            if intent in ['deploy_service'] and 'SERVICE_ID' in entities:
                service_id = entities['SERVICE_ID']
                vm_id = entities.get('VM_ID')
                self.user_preferences.add_quick_access_service(user, service_id, vm_id)
                
            # Load user preferences into context for smarter responses
            self.user_manager._load_user_context(user)
        
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
        """Get recent audit logs with the specified limit"""
        return self.audit_logger.get_recent_logs(limit)