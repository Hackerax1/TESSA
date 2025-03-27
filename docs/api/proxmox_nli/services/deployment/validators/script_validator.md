# script_validator

Script-specific validator for script-based service configurations.

**Module Path**: `proxmox_nli.services.deployment.validators.script_validator`

## Classes

### ScriptValidator

Validator for script-based service configurations.

#### validate_script_content(script: str)

Validate script content for basic shell script requirements.

Args:
    script: Script content to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_command_list(commands: List[str])

Validate a list of shell commands.

Args:
    commands: List of commands to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_process_name(process_name: str)

Validate process name for service monitoring.

Args:
    process_name: Process name to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_backup_config(backup_config: Dict)

Validate script service backup configuration.

Args:
    backup_config: Backup configuration to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_deployment_config(cls, deployment_config: Dict)

Validate complete script deployment configuration.

Args:
    deployment_config: Deployment configuration dictionary
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

