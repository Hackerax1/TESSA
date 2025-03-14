"""
Core NLI module providing the main interface for Proxmox natural language processing.
"""
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from prometheus_client import Summary
from .base_nli import BaseNLI
from .command_executor import CommandExecutor
from .services.service_handler import ServiceHandler
from .security.user_manager import UserManager

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
        
        # Process the query with the NLU
        intent, entities = self.nlu.process_query(query)
        
        # Find the appropriate command
        cmd_name, cmd_func = self._find_command(intent)
        
        if not cmd_name:
            self.audit_logger.log_query(
                query, 
                "unknown", 
                {}, 
                "Intent not recognized", 
                False,
                user, 
                source, 
                ip_address
            )
            return "I'm not sure how to help with that. Could you try rephrasing?"
            
        # Check if command needs confirmation
        if cmd_name in self.commands_needing_confirmation:
            dangerous_actions = ["delete", "destroy", "remove", "reset", "shutdown"]
            needs_confirmation = any(action in cmd_name.lower() for action in dangerous_actions)
            
            # Further analyze entities to detect deletion/destruction operations
            if entities and isinstance(entities, dict):
                for value in entities.values():
                    if isinstance(value, str) and any(action in value.lower() for action in dangerous_actions):
                        needs_confirmation = True
                        break
            
            if needs_confirmation:
                self.pending_command = {
                    "func": cmd_func,
                    "entities": entities,
                    "query": query,
                    "intent": intent,
                    "user": user,
                    "source": source,
                    "ip_address": ip_address
                }
                
                self.audit_logger.log_query(
                    query, 
                    intent, 
                    entities, 
                    "Confirmation requested", 
                    False,
                    user, 
                    source, 
                    ip_address
                )
                
                # Show details of what will be done
                details = ", ".join([f"{k}: {v}" for k, v in entities.items() if v])
                if details:
                    details = f" with {details}"
                    
                return f"This operation ({cmd_name}{details}) can be destructive. Are you sure you want to proceed? (yes/no)"
                
        # Execute the command with any extracted entities
        try:
            if entities:
                result = cmd_func(**entities)
            else:
                result = cmd_func()
                
            # Generate a response based on the result
            response = self._generate_response(intent, entities, result)
            
            success = result.get("success", False) if isinstance(result, dict) else False
            result_msg = result.get("message", str(result)) if isinstance(result, dict) else str(result)
            
            # Log the query to the audit log
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
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            self.audit_logger.log_query(
                query, 
                intent, 
                entities, 
                f"Error: {str(e)}", 
                False,
                user, 
                source, 
                ip_address
            )
            return f"I encountered an error while processing your request: {str(e)}"

    def get_recent_activity(self, limit=100):
        """Get recent audit logs with the specified limit"""
        return self.audit_logger.get_recent_logs(limit)