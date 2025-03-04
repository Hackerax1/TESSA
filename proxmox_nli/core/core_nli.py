"""
Core NLI module providing the main interface for Proxmox natural language processing.
"""
from prometheus_client import Summary
from .base_nli import BaseNLI
from .command_executor import CommandExecutor
from .service_handler import ServiceHandler
from .user_manager import UserManager

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

class ProxmoxNLI(BaseNLI, CommandExecutor, ServiceHandler, UserManager):
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
        
        # Handle service-related intents
        if intent in ['list_available_services', 'list_deployed_services', 'find_service', 
                     'deploy_service', 'service_status', 'stop_service', 'remove_service']:
            return self.handle_service_intent(intent, args, entities)
            
        # Handle other commands
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
    
    @REQUEST_TIME.time()
    def process_query(self, query, user=None, source='cli', ip_address=None):
        """Process a natural language query"""
        # Process the query using NLU engine
        intent, args, entities = self.nlu.process_query(query)
        
        # Update user preferences with context
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
            self._load_user_context(user)
        
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

    def backup_vm(self, vm_id, backup_dir):
        """Backup a VM to the specified directory"""
        return self.commands.backup_vm(vm_id, backup_dir)

    def restore_vm(self, backup_file, vm_id):
        """Restore a VM from the specified backup file"""
        return self.commands.restore_vm(backup_file, vm_id)