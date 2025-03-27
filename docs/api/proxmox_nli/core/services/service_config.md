# service_config

Service configuration management module for Proxmox NLI.

Handles saving, loading and merging of service configurations.

**Module Path**: `proxmox_nli.core.services.service_config`

## Classes

### ServiceConfig

Service configuration management for the Proxmox NLI system.

Handles:
- Loading and saving service configurations
- Merging default configs with user preferences
- Validating configurations against service requirements

#### __init__(base_nli)

Initialize the service configuration manager

#### get_service_config(service_id: str, user_id: Optional[str])

Get configuration for a service, combining defaults with user preferences

Args:
    service_id: ID of the service to get configuration for
    user_id: Optional user ID to get user-specific preferences
    
Returns:
    Combined service configuration

**Returns**: `Dict[(str, Any)]`

#### save_service_config(service_id: str, config: Dict[(str, Any)])

Save configuration for a service

Args:
    service_id: ID of the service
    config: Configuration to save
    
Returns:
    True if successful, False otherwise

**Returns**: `bool`

#### validate_config(service_id: str, config: Dict[(str, Any)])

Validate service configuration against service requirements

Args:
    service_id: ID of the service
    config: Configuration to validate
    
Returns:
    Validation result with any validation errors

**Returns**: `Dict[(str, Any)]`

