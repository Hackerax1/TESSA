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
        
    def get_service_dependencies(self, service_id: str) -> List[Dict]:
        """Get all dependencies for a specific service.
        
        Args:
            service_id: The ID of the service to get dependencies for
            
        Returns:
            List of dependency dictionaries with service details
        """
        service = self.get_service(service_id)
        if not service or 'dependencies' not in service:
            return []
            
        dependencies = []
        for dep in service.get('dependencies', []):
            dep_service = self.get_service(dep['id'])
            if dep_service:
                dependencies.append({
                    'id': dep['id'],
                    'name': dep_service['name'],
                    'required': dep['required'],
                    'description': dep.get('description', ''),
                    'service': dep_service
                })
            else:
                # Dependency service not found in catalog
                dependencies.append({
                    'id': dep['id'],
                    'name': dep['id'],
                    'required': dep['required'],
                    'description': dep.get('description', ''),
                    'service': None
                })
                
        return dependencies
        
    def get_all_required_dependencies(self, service_id: str, processed_services: List[str] = None) -> List[Dict]:
        """Get all required dependencies for a service, including transitive dependencies.
        
        Args:
            service_id: The ID of the service to get dependencies for
            processed_services: List of already processed service IDs (to prevent cycles)
            
        Returns:
            List of dependency dictionaries with service details
        """
        if processed_services is None:
            processed_services = []
            
        if service_id in processed_services:
            return []  # Prevent circular dependencies
            
        processed_services.append(service_id)
        
        direct_deps = self.get_service_dependencies(service_id)
        all_deps = []
        
        for dep in direct_deps:
            if dep['required'] and dep['id'] not in [d['id'] for d in all_deps]:
                all_deps.append(dep)
                
                # Get transitive dependencies
                if dep['service']:
                    transitive_deps = self.get_all_required_dependencies(
                        dep['id'], processed_services.copy()
                    )
                    
                    # Add only new dependencies
                    for trans_dep in transitive_deps:
                        if trans_dep['id'] not in [d['id'] for d in all_deps]:
                            all_deps.append(trans_dep)
                            
        return all_deps
        
    def get_services_by_goal(self, goal_id: str) -> List[Dict]:
        """Get services that support a specific user goal.
        
        Args:
            goal_id: The ID of the user goal
            
        Returns:
            List of service dictionaries that support the goal
        """
        matching_services = []
        
        for service in self.services.values():
            if 'user_goals' in service:
                for goal in service.get('user_goals', []):
                    if goal['id'] == goal_id:
                        # Add relevance information to the service
                        service_copy = service.copy()
                        service_copy['goal_relevance'] = goal.get('relevance', 'medium')
                        service_copy['goal_reason'] = goal.get('reason', '')
                        matching_services.append(service_copy)
                        break
                        
        # Sort by relevance (high, medium, low)
        relevance_order = {'high': 0, 'medium': 1, 'low': 2}
        return sorted(matching_services, key=lambda s: relevance_order.get(s.get('goal_relevance'), 3))
        
    def get_replacement_services(self, cloud_service_id: str) -> List[Dict]:
        """Get services that can replace a specific cloud service.
        
        Args:
            cloud_service_id: The ID of the cloud service to replace
            
        Returns:
            List of service dictionaries that can replace the cloud service
        """
        matching_services = []
        
        for service in self.services.values():
            if 'replaces_services' in service:
                for replacement in service.get('replaces_services', []):
                    if replacement['id'] == cloud_service_id:
                        # Add replacement information to the service
                        service_copy = service.copy()
                        service_copy['replacement_quality'] = replacement.get('quality', 'good')
                        service_copy['replacement_reason'] = replacement.get('reason', '')
                        matching_services.append(service_copy)
                        break
                        
        # Sort by quality (excellent, good, fair, poor)
        quality_order = {'excellent': 0, 'good': 1, 'fair': 2, 'poor': 3}
        return sorted(matching_services, key=lambda s: quality_order.get(s.get('replacement_quality'), 4))