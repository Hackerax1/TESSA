"""
Script-specific validator for script-based service configurations.
"""
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

class ScriptValidator:
    """Validator for script-based service configurations."""
    
    # Adding backup schema to existing class
    BACKUP_SCHEMA = {
        "paths": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "destination"],
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                    "exclude": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "pre_backup_script": {"type": "string"},
        "post_backup_script": {"type": "string"},
        "pre_restore_script": {"type": "string"},
        "post_restore_script": {"type": "string"}
    }
    
    @staticmethod
    def validate_script_content(script: str) -> Dict:
        """Validate script content for basic shell script requirements.
        
        Args:
            script: Script content to validate
            
        Returns:
            Validation result dictionary
        """
        if not script.strip():
            return {
                "success": False,
                "message": "Script content cannot be empty"
            }
            
        # Check for interpreter line
        first_line = script.strip().split('\n')[0]
        if not first_line.startswith('#!'):
            logger.warning("Script does not specify interpreter (shebang line)")
            
        # Check for common script errors
        errors = []
        
        # Check for unmatched quotes
        single_quotes = len(re.findall(r"(?<!\\)'", script)) % 2
        double_quotes = len(re.findall(r'(?<!\\)"', script)) % 2
        if single_quotes:
            errors.append("Unmatched single quotes")
        if double_quotes:
            errors.append("Unmatched double quotes")
            
        # Check for syntax that might indicate errors
        if re.search(r'[^\\]&&[^&]', script):
            errors.append("Possible syntax error: single & in command chaining (use && for AND)")
        if re.search(r'[^\\]\|\|[^|]', script):
            errors.append("Possible syntax error: single | in command chaining (use || for OR)")
            
        if errors:
            return {
                "success": False,
                "message": "Script validation failed",
                "errors": errors
            }
            
        return {
            "success": True,
            "message": "Valid script content"
        }
        
    @staticmethod
    def validate_command_list(commands: List[str]) -> Dict:
        """Validate a list of shell commands.
        
        Args:
            commands: List of commands to validate
            
        Returns:
            Validation result dictionary
        """
        if not commands:
            return {
                "success": False,
                "message": "Command list cannot be empty"
            }
            
        errors = []
        for i, cmd in enumerate(commands):
            if not cmd.strip():
                errors.append(f"Command {i+1} is empty")
                continue
                
            # Check for common command errors
            if ';' in cmd and not cmd.endswith(';'):
                errors.append(f"Command {i+1} has semicolon in middle (might indicate multiple commands)")
                
            if re.search(r'[^\\]>|[^\\]<', cmd):
                errors.append(f"Command {i+1} contains redirection (should be handled by script)")
                
            if '`' in cmd:
                errors.append(f"Command {i+1} uses backticks (prefer $() for command substitution)")
                
        if errors:
            return {
                "success": False,
                "message": "Command validation failed",
                "errors": errors
            }
            
        return {
            "success": True,
            "message": "Valid command list"
        }
        
    @staticmethod
    def validate_process_name(process_name: str) -> Dict:
        """Validate process name for service monitoring.
        
        Args:
            process_name: Process name to validate
            
        Returns:
            Validation result dictionary
        """
        if not process_name.strip():
            return {
                "success": False,
                "message": "Process name cannot be empty"
            }
            
        # Check for valid process name format
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$'
        if not re.match(pattern, process_name):
            return {
                "success": False,
                "message": f"Invalid process name format: {process_name}"
            }
            
        return {
            "success": True,
            "message": "Valid process name"
        }
        
    @staticmethod
    def validate_backup_config(backup_config: Dict) -> Dict:
        """Validate script service backup configuration.
        
        Args:
            backup_config: Backup configuration to validate
            
        Returns:
            Validation result dictionary
        """
        if not backup_config:
            return {
                "success": True,
                "message": "No backup configuration provided"
            }
            
        try:
            # Basic structure validation
            if not isinstance(backup_config, dict):
                return {
                    "success": False,
                    "message": "Backup configuration must be a dictionary"
                }
                
            # Validate backup paths if specified
            if 'paths' in backup_config:
                if not isinstance(backup_config['paths'], list):
                    return {
                        "success": False,
                        "message": "Paths must be a list"
                    }
                    
                for path_config in backup_config['paths']:
                    if not isinstance(path_config, dict):
                        return {
                            "success": False,
                            "message": "Each path configuration must be a dictionary"
                        }
                        
                    if 'source' not in path_config or 'destination' not in path_config:
                        return {
                            "success": False,
                            "message": "Path configuration must include source and destination"
                        }
                        
                    if 'exclude' in path_config and not isinstance(path_config['exclude'], list):
                        return {
                            "success": False,
                            "message": "Path exclude patterns must be a list"
                        }
                        
            # Validate backup scripts if specified
            for field in ['pre_backup_script', 'post_backup_script', 'pre_restore_script', 'post_restore_script']:
                if field in backup_config:
                    script = backup_config[field]
                    if not isinstance(script, str):
                        return {
                            "success": False,
                            "message": f"{field} must be a string"
                        }
                        
                    # Validate script content
                    script_result = ScriptValidator.validate_script_content(script)
                    if not script_result["success"]:
                        return {
                            "success": False,
                            "message": f"Invalid {field}: {script_result['message']}",
                            "errors": script_result.get('errors', [])
                        }
                        
            return {
                "success": True,
                "message": "Valid backup configuration"
            }
            
        except Exception as e:
            logger.error(f"Error validating backup configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating backup configuration: {str(e)}"
            }
    
    @classmethod
    def validate_deployment_config(cls, deployment_config: Dict) -> Dict:
        """Validate complete script deployment configuration.
        
        Args:
            deployment_config: Deployment configuration dictionary
            
        Returns:
            Validation result dictionary
        """
        try:
            # Validate main deployment script
            if 'script' in deployment_config:
                script_result = cls.validate_script_content(deployment_config['script'])
                if not script_result["success"]:
                    return script_result
                    
            # Validate pre-install steps
            if 'pre_install_steps' in deployment_config:
                pre_result = cls.validate_command_list(deployment_config['pre_install_steps'])
                if not pre_result["success"]:
                    return {
                        "success": False,
                        "message": "Invalid pre-install steps",
                        "errors": pre_result["errors"]
                    }
                    
            # Validate post-install steps
            if 'post_install_steps' in deployment_config:
                post_result = cls.validate_command_list(deployment_config['post_install_steps'])
                if not post_result["success"]:
                    return {
                        "success": False,
                        "message": "Invalid post-install steps",
                        "errors": post_result["errors"]
                    }
                    
            # Validate process name if provided
            if 'process_name' in deployment_config:
                process_result = cls.validate_process_name(deployment_config['process_name'])
                if not process_result["success"]:
                    return process_result
                    
            # Validate stop command if provided
            if 'stop_command' in deployment_config:
                stop_result = cls.validate_command_list([deployment_config['stop_command']])
                if not stop_result["success"]:
                    return {
                        "success": False,
                        "message": "Invalid stop command",
                        "errors": stop_result["errors"]
                    }
                    
            # Validate uninstall command if provided
            if 'uninstall_command' in deployment_config:
                uninstall_result = cls.validate_command_list([deployment_config['uninstall_command']])
                if not uninstall_result["success"]:
                    return {
                        "success": False,
                        "message": "Invalid uninstall command",
                        "errors": uninstall_result["errors"]
                    }
                    
            # Add backup configuration validation
            if 'backup' in deployment_config:
                backup_result = cls.validate_backup_config(deployment_config['backup'])
                if not backup_result["success"]:
                    return backup_result
                    
            return {
                "success": True,
                "message": "Valid script deployment configuration"
            }
            
        except Exception as e:
            logger.error(f"Error validating script deployment configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating script deployment configuration: {str(e)}"
            }