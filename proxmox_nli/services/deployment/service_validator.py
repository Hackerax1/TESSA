"""
Service definition validator to ensure service definitions meet requirements.
"""
import logging
from typing import Dict, List, Optional
import jsonschema
from .validators import DockerValidator, ScriptValidator

logger = logging.getLogger(__name__)

class ServiceValidator:
    """Validator for service definitions."""
    
    # Base schema for common service definition fields
    BASE_SCHEMA = {
        "type": "object",
        "required": ["id", "name", "description", "keywords", "deployment", "vm_requirements"],
        "properties": {
            "id": {"type": "string", "pattern": "^[a-z0-9-]+$"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "keywords": {
                "type": "array",
                "items": {"type": "string"}
            },
            "vm_requirements": {
                "type": "object",
                "required": ["memory", "cores", "disk", "os_template"],
                "properties": {
                    "memory": {"type": "integer", "minimum": 512},
                    "cores": {"type": "integer", "minimum": 1},
                    "disk": {"type": "integer", "minimum": 5},
                    "os_template": {"type": "string"}
                }
            },
            "dependencies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "required"],
                    "properties": {
                        "id": {"type": "string"},
                        "required": {"type": "boolean"},
                        "description": {"type": "string"}
                    }
                }
            },
            "user_goals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "relevance"],
                    "properties": {
                        "id": {"type": "string"},
                        "relevance": {"type": "string", "enum": ["low", "medium", "high"]},
                        "reason": {"type": "string"}
                    }
                }
            },
            "replaces_services": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "quality"],
                    "properties": {
                        "id": {"type": "string"},
                        "quality": {"type": "string", "enum": ["poor", "fair", "good", "excellent"]},
                        "reason": {"type": "string"}
                    }
                }
            },
            "personality_recommendation": {"type": "string"},
            "deployment": {
                "type": "object",
                "required": ["method"],
                "properties": {
                    "method": {"type": "string", "enum": ["docker", "script"]}
                }
            },
            "access_info": {"type": "string"},
            "notes": {"type": "string"}
        }
    }
    
    @classmethod
    def validate_service_definition(cls, service_def: Dict) -> Dict:
        """Validate a service definition.
        
        Args:
            service_def: Service definition dictionary to validate
            
        Returns:
            Dictionary with validation result and any error messages
        """
        try:
            # First validate base schema
            jsonschema.validate(instance=service_def, schema=cls.BASE_SCHEMA)
            
            # Then validate deployment-specific configuration
            deployment_method = service_def['deployment']['method']
            deployment_config = service_def['deployment']
            
            if deployment_method == 'docker':
                result = DockerValidator.validate_deployment_config(deployment_config)
            elif deployment_method == 'script':
                result = ScriptValidator.validate_deployment_config(deployment_config)
            else:
                return {
                    "success": False,
                    "message": f"Unsupported deployment method: {deployment_method}"
                }
                
            if not result["success"]:
                return result
                
            return {
                "success": True,
                "message": "Service definition is valid"
            }
            
        except jsonschema.exceptions.ValidationError as e:
            return {
                "success": False,
                "message": f"Invalid service definition: {str(e)}",
                "error": {
                    "path": list(e.absolute_path),
                    "message": e.message
                }
            }
        except Exception as e:
            logger.error(f"Error validating service definition: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating service definition: {str(e)}"
            }
            
    @classmethod
    def validate_custom_params(cls, service_def: Dict, custom_params: Dict) -> Dict:
        """Validate custom deployment parameters.
        
        Args:
            service_def: Service definition dictionary
            custom_params: Custom parameters to validate
            
        Returns:
            Dictionary with validation result and any error messages
        """
        try:
            deployment_method = service_def['deployment']['method']
            
            if deployment_method == 'docker':
                validator = DockerValidator
            elif deployment_method == 'script':
                validator = ScriptValidator
            else:
                return {
                    "success": False,
                    "message": f"Unsupported deployment method: {deployment_method}"
                }
                
            # Always validate VM params if provided
            if 'vm_params' in custom_params:
                vm_params = custom_params['vm_params']
                if not isinstance(vm_params, dict):
                    return {
                        "success": False,
                        "message": "VM parameters must be a dictionary"
                    }
                    
                # Ensure VM params only contain allowed keys
                allowed_vm_params = {'memory', 'cores', 'disk', 'os_template'}
                invalid_params = set(vm_params.keys()) - allowed_vm_params
                if invalid_params:
                    return {
                        "success": False,
                        "message": f"Invalid VM parameters: {', '.join(invalid_params)}",
                        "allowed_params": list(allowed_vm_params)
                    }
                    
                # Validate VM param values
                vm_schema = cls.BASE_SCHEMA['properties']['vm_requirements']
                try:
                    jsonschema.validate(instance=vm_params, schema=vm_schema)
                except jsonschema.exceptions.ValidationError as e:
                    return {
                        "success": False,
                        "message": f"Invalid VM parameter value: {str(e)}"
                    }
                    
            # Delegate remaining validation to deployment-specific validator
            remaining_params = {k: v for k, v in custom_params.items() if k != 'vm_params'}
            if remaining_params:
                return validator.validate_deployment_config(remaining_params)
                
            return {
                "success": True,
                "message": "Custom parameters are valid"
            }
            
        except Exception as e:
            logger.error(f"Error validating custom parameters: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating custom parameters: {str(e)}"
            }