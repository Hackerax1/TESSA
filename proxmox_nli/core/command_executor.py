"""
Command executor module handling execution of various Proxmox commands.
Provides centralized command routing, validation, and execution.
"""
from typing import Dict, Any, Optional, List

class CommandExecutor:
    def __init__(self, base_nli):
        self.base_nli = base_nli
        self.commands = base_nli.commands
        self.docker_commands = base_nli.docker_commands
        self.vm_command = base_nli.vm_command
        self.get_help = base_nli.get_help

    def execute_command(self, command: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a command with validation and proper routing
        
        Args:
            command: Command to execute
            args: Optional command arguments
            
        Returns:
            Dict containing command execution results
        """
        # Validate command and arguments
        validation_result = self._validate_command(command, args)
        if not validation_result['success']:
            return validation_result
            
        # Route command to appropriate handler
        try:
            if command.startswith('vm'):
                return self.vm_command.execute_command(**args)
            elif command.startswith('docker'):
                return self.docker_commands.handle_command(command, args)
            elif command.startswith('backup'):
                return self.commands.backup_commands.handle_command(command, args)
            elif command.startswith('network'):
                return self.commands.network_commands.handle_command(command, args)
            elif command.startswith('storage'):
                return self.commands.storage_commands.handle_command(command, args)
            elif command.startswith('security'):
                return self.commands.security_commands.handle_command(command, args)
            else:
                # Default to main command handler
                return self.commands.handle_command(command, args)
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing command: {str(e)}"
            }

    def _execute_command(self, command: str, positional_args: List[str] = None, entities: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a command with positional arguments and entities
        
        This is an internal method used for command routing with more specific parameter handling.
        
        Args:
            command: Command to execute
            positional_args: List of positional arguments
            entities: Dictionary of named entities/parameters
            
        Returns:
            Dict containing command execution results
        """
        if positional_args is None:
            positional_args = []
        if entities is None:
            entities = {}
            
        # Help command handling
        if command == "help":
            return self.get_help()
            
        # VM Commands
        if command == "list_vms":
            return self.commands.list_vms()
        elif command == "start_vm":
            if len(positional_args) > 0:
                vm_id = positional_args[0]
            elif "VM_ID" in entities:
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a VM ID"}
            return self.commands.start_vm(vm_id)
        elif command == "stop_vm":
            if len(positional_args) > 0:
                vm_id = positional_args[0]
            elif "VM_ID" in entities:
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a VM ID"}
            return self.commands.stop_vm(vm_id)
        elif command == "restart_vm":
            if len(positional_args) > 0:
                vm_id = positional_args[0]
            elif "VM_ID" in entities:
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a VM ID"}
            return self.commands.restart_vm(vm_id)
        elif command == "delete_vm":
            if len(positional_args) > 0:
                vm_id = positional_args[0]
            elif "VM_ID" in entities:
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a VM ID"}
            return self.commands.delete_vm(vm_id)
        elif command == "vm_status":
            if len(positional_args) > 0:
                vm_id = positional_args[0]
            elif "VM_ID" in entities:
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a VM ID"}
            return self.commands.get_vm_status(vm_id)
        elif command == "create_vm":
            if "PARAMS" in entities:
                vm_params = entities["PARAMS"]
            else:
                return {"success": False, "message": "Please specify VM parameters"}
            return self.commands.create_vm(vm_params)
            
        # Docker Commands
        elif command == "list_docker_containers":
            if len(positional_args) > 0:
                vm_id = positional_args[0]
            elif "VM_ID" in entities:
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a VM ID"}
            return self.docker_commands.list_docker_containers(vm_id)
        elif command == "start_docker_container":
            if len(positional_args) > 1:
                container_name = positional_args[0]
                vm_id = positional_args[1]
            elif "CONTAINER_NAME" in entities and "VM_ID" in entities:
                container_name = entities["CONTAINER_NAME"]
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a container name and VM ID"}
            return self.docker_commands.start_docker_container(container_name, vm_id)
        elif command == "stop_docker_container":
            if len(positional_args) > 1:
                container_name = positional_args[0]
                vm_id = positional_args[1]
            elif "CONTAINER_NAME" in entities and "VM_ID" in entities:
                container_name = entities["CONTAINER_NAME"]
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a container name and VM ID"}
            return self.docker_commands.stop_docker_container(container_name, vm_id)
            
        # CLI Commands
        elif command == "run_cli_command":
            if len(positional_args) > 1:
                cmd = positional_args[0]
                vm_id = positional_args[1]
            elif "COMMAND" in entities and "VM_ID" in entities:
                cmd = entities["COMMAND"]
                vm_id = entities["VM_ID"]
            else:
                return {"success": False, "message": "Please specify a command and VM ID"}
            return self.vm_command.run_cli_command(vm_id, cmd)
            
        # Invalid Command
        return {
            "success": False,
            "message": f"I don't understand the command '{command}'. Try using 'help' for available commands."
        }
        
    def _validate_command(self, command: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate command and arguments before execution
        
        Args:
            command: Command to validate
            args: Optional command arguments
            
        Returns:
            Dict indicating validation success/failure
        """
        if not command:
            return {
                "success": False,
                "message": "No command provided"
            }
            
        # Add more validation logic as needed
        return {"success": True}