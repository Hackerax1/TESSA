"""
Dependency resolution module for Proxmox NLI.

This module provides a simplified facade to the more complex dependency management
functionality in the services package, making it easier for the NLI core to handle
service dependencies.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from ...services.dependency_manager import DependencyManager

logger = logging.getLogger(__name__)

class DependencyResolver:
    """
    Service dependency resolution for the NLI core.
    
    This class provides a simpler interface for the NLI system to resolve
    service dependencies and provides specialized NLI-related functions not
    present in the main DependencyManager.
    """
    
    def __init__(self, base_nli):
        """Initialize with the base NLI context"""
        self.service_catalog = base_nli.service_catalog if hasattr(base_nli, 'service_catalog') else None
        self.dependency_manager = None
        if self.service_catalog:
            self.dependency_manager = DependencyManager(self.service_catalog)
            self.dependency_manager.build_dependency_graph()
    
    def get_dependencies(self, service_id: str, required_only: bool = False) -> List[Dict]:
        """
        Get all dependencies for a service
        
        Args:
            service_id: ID of the service to get dependencies for
            required_only: Whether to include only required dependencies
            
        Returns:
            List of dependency dictionaries
        """
        if not self.dependency_manager:
            logger.error("No dependency manager available")
            return []
            
        try:
            if required_only:
                return [dep for dep in self.dependency_manager.get_all_required_dependencies(service_id)
                       if dep.get('required', True)]
            else:
                return self.dependency_manager.get_all_required_dependencies(service_id)
        except Exception as e:
            logger.error(f"Error getting dependencies: {str(e)}")
            return []
    
    def check_circular_dependencies(self, service_id: str) -> Tuple[bool, Optional[List[str]]]:
        """
        Check for circular dependencies for a service
        
        Args:
            service_id: ID of the service to check
            
        Returns:
            Tuple of (has_circular, circular_path)
        """
        if not self.dependency_manager:
            logger.error("No dependency manager available")
            return (False, None)
            
        try:
            cycles = self.dependency_manager.detect_circular_dependencies()
            for cycle in cycles:
                if service_id in cycle:
                    return (True, cycle)
            return (False, None)
        except Exception as e:
            logger.error(f"Error checking circular dependencies: {str(e)}")
            return (False, None)
    
    def get_installation_plan(self, service_ids: List[str]) -> Dict:
        """
        Generate an installation plan for multiple services
        
        Args:
            service_ids: List of service IDs to include in the plan
            
        Returns:
            Installation plan dictionary
        """
        if not self.dependency_manager:
            return {
                "success": False,
                "message": "Dependency manager not available"
            }
            
        try:
            # Collect all services that need to be installed
            ordered_services = []
            service_details = {}
            
            # Process each requested service
            for service_id in service_ids:
                # Skip if already in the plan
                if service_id in ordered_services:
                    continue
                    
                # Get the installation order for this service
                try:
                    install_order = self.dependency_manager.get_installation_order(service_id)
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Error resolving dependencies for {service_id}: {str(e)}",
                        "error": str(e)
                    }
                
                # Add each service in the installation order
                for dep_id in install_order:
                    if dep_id not in ordered_services:
                        ordered_services.append(dep_id)
                        
                        # Get service details
                        service = self.service_catalog.get_service(dep_id)
                        if service:
                            service_details[dep_id] = {
                                "name": service.get("name", dep_id),
                                "description": service.get("description", ""),
                                "is_dependency": dep_id != service_id and dep_id not in service_ids,
                                "vm_requirements": service.get("vm_requirements", {})
                            }
                        
            # Create the installation plan
            installation_steps = []
            for i, service_id in enumerate(ordered_services):
                details = service_details.get(service_id, {})
                installation_steps.append({
                    "step": i + 1,
                    "service_id": service_id,
                    "name": details.get("name", service_id),
                    "description": details.get("description", ""),
                    "is_dependency": details.get("is_dependency", False),
                    "vm_requirements": details.get("vm_requirements", {})
                })
                
            return {
                "success": True,
                "message": "Installation plan generated successfully",
                "services": installation_steps
            }
                
        except Exception as e:
            logger.error(f"Error generating installation plan: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating installation plan: {str(e)}"
            }
    
    def explain_dependencies(self, service_id: str) -> Dict:
        """
        Generate a human-readable explanation of service dependencies
        
        Args:
            service_id: ID of the service to explain dependencies for
            
        Returns:
            Dictionary with explanation
        """
        if not self.dependency_manager or not self.service_catalog:
            return {
                "success": False,
                "message": "Dependency manager not available"
            }
            
        try:
            # Get service details
            service = self.service_catalog.get_service(service_id)
            if not service:
                return {
                    "success": False,
                    "message": f"Service {service_id} not found"
                }
                
            # Get dependencies
            dependencies = self.get_dependencies(service_id)
            
            required_deps = [dep for dep in dependencies if dep.get("required", True)]
            optional_deps = [dep for dep in dependencies if not dep.get("required", True)]
            
            # Build explanation
            explanation = {
                "success": True,
                "service": {
                    "id": service_id,
                    "name": service.get("name", service_id),
                    "description": service.get("description", "")
                },
                "required_dependencies": [],
                "optional_dependencies": [],
                "installation_order": self.dependency_manager.get_installation_order(service_id),
                "explanation": f"{service.get('name', service_id)} "
            }
            
            # Add dependency explanations
            for dep in required_deps:
                dep_service = self.service_catalog.get_service(dep.get("id"))
                if dep_service:
                    explanation["required_dependencies"].append({
                        "id": dep.get("id"),
                        "name": dep_service.get("name", dep.get("id")),
                        "description": dep_service.get("description", ""),
                        "reason": dep.get("description", "Required for operation")
                    })
                    
            for dep in optional_deps:
                dep_service = self.service_catalog.get_service(dep.get("id"))
                if dep_service:
                    explanation["optional_dependencies"].append({
                        "id": dep.get("id"),
                        "name": dep_service.get("name", dep.get("id")),
                        "description": dep_service.get("description", ""),
                        "reason": dep.get("description", "Enhances functionality")
                    })
            
            # Generate natural language explanation
            if not required_deps and not optional_deps:
                explanation["explanation"] += "does not have any dependencies and can be installed directly."
            elif required_deps and not optional_deps:
                explanation["explanation"] += f"requires {len(required_deps)} other service(s) to function properly."
            elif not required_deps and optional_deps:
                explanation["explanation"] += f"has {len(optional_deps)} optional service(s) that can enhance its functionality."
            else:
                explanation["explanation"] += (
                    f"requires {len(required_deps)} service(s) to function properly and has "
                    f"{len(optional_deps)} optional service(s) that can enhance its functionality."
                )
                
            return explanation
                
        except Exception as e:
            logger.error(f"Error explaining dependencies: {str(e)}")
            return {
                "success": False,
                "message": f"Error explaining dependencies: {str(e)}"
            }
    
    def get_dependency_diagram(self, service_id: Optional[str] = None) -> Dict:
        """
        Generate a dependency diagram for a service
        
        Args:
            service_id: Optional ID of the service to diagram
            
        Returns:
            Dictionary with diagram data
        """
        if not self.dependency_manager:
            return {
                "success": False,
                "message": "Dependency manager not available"
            }
            
        try:
            diagram_data = self.dependency_manager.visualize_dependencies(service_id)
            
            if not diagram_data:
                return {
                    "success": False,
                    "message": f"Could not generate dependency diagram for {service_id}"
                }
                
            return {
                "success": True,
                "diagram": diagram_data,
                "service_id": service_id
            }
                
        except Exception as e:
            logger.error(f"Error generating dependency diagram: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating dependency diagram: {str(e)}"
            }