# docker_validator

Docker-specific validator for Docker service configurations.

**Module Path**: `proxmox_nli.services.deployment.validators.docker_validator`

## Classes

### DockerValidator

Validator for Docker service configurations.

#### validate_image_name(image_name: str)

Validate Docker image name format.

Args:
    image_name: Docker image name to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_port_mappings(port_mappings: str)

Validate Docker port mapping format.

Args:
    port_mappings: Port mappings string to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_volume_mappings(volume_mappings: str)

Validate Docker volume mapping format.

Args:
    volume_mappings: Volume mappings string to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_environment_vars(env_vars: str)

Validate Docker environment variables format.

Args:
    env_vars: Environment variables string to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_compose_config(compose_content: str)

Validate Docker Compose configuration.

Args:
    compose_content: Docker Compose YAML content to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_backup_config(backup_config: Dict)

Validate Docker service backup configuration.

Args:
    backup_config: Backup configuration to validate
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

#### validate_deployment_config(cls, deployment_config: Dict)

Validate complete Docker deployment configuration.

Args:
    deployment_config: Deployment configuration dictionary
    
Returns:
    Validation result dictionary

**Returns**: `Dict`

