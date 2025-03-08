"""
Docker-specific validator for Docker service configurations.
"""
import logging
from typing import Dict, Optional, List
from docker.errors import DockerException
from docker import DockerClient
import re

logger = logging.getLogger(__name__)

class DockerValidator:
    """Validator for Docker service configurations."""
    
    # Adding backup schema to existing class
    BACKUP_SCHEMA = {
        "volumes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "backup_path"],
                "properties": {
                    "name": {"type": "string"},
                    "backup_path": {"type": "string"},
                    "exclude": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "pre_backup_commands": {
            "type": "array",
            "items": {"type": "string"}
        },
        "post_backup_commands": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
    
    @staticmethod
    def validate_image_name(image_name: str) -> Dict:
        """Validate Docker image name format.
        
        Args:
            image_name: Docker image name to validate
            
        Returns:
            Validation result dictionary
        """
        pattern = r'^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*(?::[0-9]+)?/)?[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*(?::[a-zA-Z0-9_]+)?$'
        if re.match(pattern, image_name):
            return {
                "success": True,
                "message": "Valid Docker image name"
            }
        return {
            "success": False,
            "message": f"Invalid Docker image name format: {image_name}"
        }
        
    @staticmethod
    def validate_port_mappings(port_mappings: str) -> Dict:
        """Validate Docker port mapping format.
        
        Args:
            port_mappings: Port mappings string to validate
            
        Returns:
            Validation result dictionary
        """
        if not port_mappings:
            return {"success": True, "message": "No port mappings specified"}
            
        pattern = r'^(?:-p\s+\d+(?::\d+)?(?:/(?:tcp|udp))?\s*)*$'
        if re.match(pattern, port_mappings.strip()):
            return {
                "success": True,
                "message": "Valid port mappings format"
            }
        return {
            "success": False,
            "message": f"Invalid port mappings format: {port_mappings}"
        }
        
    @staticmethod
    def validate_volume_mappings(volume_mappings: str) -> Dict:
        """Validate Docker volume mapping format.
        
        Args:
            volume_mappings: Volume mappings string to validate
            
        Returns:
            Validation result dictionary
        """
        if not volume_mappings:
            return {"success": True, "message": "No volume mappings specified"}
            
        pattern = r'^(?:-v\s+[a-zA-Z0-9._/-]+(?::[a-zA-Z0-9._/-]+)?(?::[rwm]+)?\s*)*$'
        if re.match(pattern, volume_mappings.strip()):
            return {
                "success": True,
                "message": "Valid volume mappings format"
            }
        return {
            "success": False,
            "message": f"Invalid volume mappings format: {volume_mappings}"
        }
        
    @staticmethod
    def validate_environment_vars(env_vars: str) -> Dict:
        """Validate Docker environment variables format.
        
        Args:
            env_vars: Environment variables string to validate
            
        Returns:
            Validation result dictionary
        """
        if not env_vars:
            return {"success": True, "message": "No environment variables specified"}
            
        pattern = r'^(?:-e\s+[a-zA-Z_][a-zA-Z0-9_]*=?[^\s]*\s*)*$'
        if re.match(pattern, env_vars.strip()):
            return {
                "success": True,
                "message": "Valid environment variables format"
            }
        return {
            "success": False,
            "message": f"Invalid environment variables format: {env_vars}"
        }
        
    @staticmethod
    def validate_compose_config(compose_content: str) -> Dict:
        """Validate Docker Compose configuration.
        
        Args:
            compose_content: Docker Compose YAML content to validate
            
        Returns:
            Validation result dictionary
        """
        try:
            import yaml
            compose_dict = yaml.safe_load(compose_content)
            
            # Basic structure validation
            if not isinstance(compose_dict, dict):
                return {
                    "success": False,
                    "message": "Invalid Docker Compose format: root must be a mapping"
                }
                
            if 'version' not in compose_dict:
                return {
                    "success": False,
                    "message": "Docker Compose configuration must specify version"
                }
                
            if 'services' not in compose_dict:
                return {
                    "success": False,
                    "message": "Docker Compose configuration must contain services"
                }
                
            if not isinstance(compose_dict['services'], dict):
                return {
                    "success": False,
                    "message": "Services must be a mapping"
                }
                
            # Validate each service
            for service_name, service in compose_dict['services'].items():
                if not isinstance(service, dict):
                    return {
                        "success": False,
                        "message": f"Service '{service_name}' must be a mapping"
                    }
                    
                if 'image' not in service and 'build' not in service:
                    return {
                        "success": False,
                        "message": f"Service '{service_name}' must specify image or build"
                    }
                    
            return {
                "success": True,
                "message": "Valid Docker Compose configuration"
            }
            
        except yaml.YAMLError as e:
            return {
                "success": False,
                "message": f"Invalid YAML syntax in Docker Compose configuration: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error validating Docker Compose configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating Docker Compose configuration: {str(e)}"
            }
            
    @staticmethod
    def validate_backup_config(backup_config: Dict) -> Dict:
        """Validate Docker service backup configuration.
        
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
                
            # Validate volumes if specified
            if 'volumes' in backup_config:
                if not isinstance(backup_config['volumes'], list):
                    return {
                        "success": False,
                        "message": "Volumes must be a list"
                    }
                    
                for volume in backup_config['volumes']:
                    if not isinstance(volume, dict):
                        return {
                            "success": False,
                            "message": "Each volume must be a dictionary"
                        }
                        
                    if 'name' not in volume or 'backup_path' not in volume:
                        return {
                            "success": False,
                            "message": "Volume configuration must include name and backup_path"
                        }
                        
                    if 'exclude' in volume and not isinstance(volume['exclude'], list):
                        return {
                            "success": False,
                            "message": "Volume exclude must be a list"
                        }
                        
            # Validate commands if specified
            for field in ['pre_backup_commands', 'post_backup_commands']:
                if field in backup_config:
                    if not isinstance(backup_config[field], list):
                        return {
                            "success": False,
                            "message": f"{field} must be a list"
                        }
                        
                    for cmd in backup_config[field]:
                        if not isinstance(cmd, str):
                            return {
                                "success": False,
                                "message": f"Commands in {field} must be strings"
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
        """Validate complete Docker deployment configuration.
        
        Args:
            deployment_config: Deployment configuration dictionary
            
        Returns:
            Validation result dictionary
        """
        try:
            if deployment_config.get('docker_image'):
                # Validate Docker image deployment
                image_result = cls.validate_image_name(deployment_config['docker_image'])
                if not image_result["success"]:
                    return image_result
                    
                # Validate optional configurations
                if 'port_mappings' in deployment_config:
                    port_result = cls.validate_port_mappings(deployment_config['port_mappings'])
                    if not port_result["success"]:
                        return port_result
                        
                if 'volume_mappings' in deployment_config:
                    volume_result = cls.validate_volume_mappings(deployment_config['volume_mappings'])
                    if not volume_result["success"]:
                        return volume_result
                        
                if 'environment_vars' in deployment_config:
                    env_result = cls.validate_environment_vars(deployment_config['environment_vars'])
                    if not env_result["success"]:
                        return env_result
                        
            elif deployment_config.get('docker_compose'):
                # Validate Docker Compose deployment
                return cls.validate_compose_config(deployment_config['docker_compose'])
                
            # Add backup configuration validation
            if 'backup' in deployment_config:
                backup_result = cls.validate_backup_config(deployment_config['backup'])
                if not backup_result["success"]:
                    return backup_result
        
            return {
                "success": True,
                "message": "Valid Docker deployment configuration"
            }
            
        except Exception as e:
            logger.error(f"Error validating Docker deployment configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating Docker deployment configuration: {str(e)}"
            }