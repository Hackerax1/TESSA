"""
Service catalog for storing and retrieving available service definitions.
This module provides a registry of services that can be installed via natural language commands.
"""
import os
import json
import logging
import yaml
from typing import Dict, List, Optional
from .deployment.service_validator import ServiceValidator

logger = logging.getLogger(__name__)

class ServiceCatalog:
    """A catalog of available services that can be installed."""
    
    def __init__(self, catalog_dir: str = None):
        """Initialize the service catalog.
        
        Args:
            catalog_dir: Directory containing service definitions. If None, uses default location.
        """
        if catalog_dir is None:
            # Default to a directory within the package
            self.catalog_dir = os.path.join(os.path.dirname(__file__), 'catalog')
        else:
            self.catalog_dir = catalog_dir
            
        # Create the catalog directory if it doesn't exist
        os.makedirs(self.catalog_dir, exist_ok=True)
        
        # Dictionary to store loaded service definitions
        self.services = {}
        
        # Track invalid services for reporting
        self.invalid_services = {}
        
        # Load all services from catalog
        self._load_services()
    
    def _load_services(self) -> None:
        """Load all service definitions from the catalog directory."""
        for filename in os.listdir(self.catalog_dir):
            if filename.endswith('.yml') or filename.endswith('.yaml'):
                try:
                    service_path = os.path.join(self.catalog_dir, filename)
                    with open(service_path, 'r') as f:
                        service_def = yaml.safe_load(f)
                        
                    # Validate service definition
                    validation_result = ServiceValidator.validate_service_definition(service_def)
                    if validation_result["success"]:
                        self.services[service_def['id']] = service_def
                        logger.info(f"Loaded service definition: {service_def['name']}")
                    else:
                        self.invalid_services[filename] = validation_result["message"]
                        logger.warning(f"Invalid service definition in {filename}: {validation_result['message']}")
                
                except Exception as e:
                    self.invalid_services[filename] = str(e)
                    logger.error(f"Error loading service definition from {filename}: {str(e)}")
    
    def get_all_services(self) -> List[Dict]:
        """Get all available service definitions.
        
        Returns:
            List of service definition dictionaries
        """
        return list(self.services.values())
    
    def get_service(self, service_id: str) -> Optional[Dict]:
        """Get a specific service by ID.
        
        Args:
            service_id: The ID of the service to retrieve
            
        Returns:
            Service definition dictionary or None if not found
        """
        return self.services.get(service_id)
    
    def find_services_by_keywords(self, query: str) -> List[Dict]:
        """Find services matching the given keywords in the query.
        
        Args:
            query: The search query containing keywords
            
        Returns:
            List of matching service definition dictionaries
        """
        query_terms = query.lower().split()
        matches = []
        
        for service in self.services.values():
            # Check if any keywords match
            if any(keyword.lower() in query_terms for keyword in service['keywords']):
                matches.append(service)
            # Also check if service name is in the query
            elif service['name'].lower() in query.lower():
                matches.append(service)
                
        return matches
    
    def add_service_definition(self, service_def: Dict) -> Dict:
        """Add a new service definition to the catalog.
        
        Args:
            service_def: Service definition dictionary
            
        Returns:
            Result dictionary with success status and message
        """
        # Validate service definition
        validation_result = ServiceValidator.validate_service_definition(service_def)
        if not validation_result["success"]:
            return validation_result
            
        try:
            # Save to file
            filename = f"{service_def['id']}.yml"
            service_path = os.path.join(self.catalog_dir, filename)
            with open(service_path, 'w') as f:
                yaml.dump(service_def, f)
                
            # Add to in-memory catalog
            self.services[service_def['id']] = service_def
            logger.info(f"Added new service definition: {service_def['name']}")
            
            return {
                "success": True,
                "message": f"Successfully added service definition for {service_def['name']}"
            }
            
        except Exception as e:
            logger.error(f"Error adding service definition: {str(e)}")
            return {
                "success": False,
                "message": f"Error adding service definition: {str(e)}"
            }
            
    def get_invalid_services(self) -> Dict[str, str]:
        """Get list of invalid service definitions and their errors.
        
        Returns:
            Dictionary mapping filenames to error messages
        """
        return self.invalid_services