"""
Command executor module handling execution of various Proxmox commands.
Provides centralized command routing, validation, and execution.
"""
from typing import Dict, Any, Optional

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