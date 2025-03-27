# service_validator

Service definition validator to ensure service definitions meet requirements.

**Module Path**: `proxmox_nli.services.deployment.service_validator`

## Classes

### ServiceValidator

Validator for service definitions.

#### validate_service_definition(cls, service_def: Dict)

Validate a service definition.

Args:
    service_def: Service definition dictionary to validate
    
Returns:
    Dictionary with validation result and any error messages

**Returns**: `Dict`

#### validate_custom_params(cls, service_def: Dict, custom_params: Dict)

Validate custom deployment parameters.

Args:
    service_def: Service definition dictionary
    custom_params: Custom parameters to validate
    
Returns:
    Dictionary with validation result and any error messages

**Returns**: `Dict`

