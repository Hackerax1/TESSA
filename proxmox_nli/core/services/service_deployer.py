"""
Service deployer module for Proxmox NLI core.

Handles high-level deployment logic and orchestration between different service 
deployment mechanisms. Acts as a facade for the more detailed deployment 
implementations in the services.deployment package.
"""

import logging
from typing import Dict, List, Optional
from ...services.service_manager import ServiceManager

logger = logging.getLogger(__name__)

class ServiceDeployer:
    """
    High-level service deployment orchestration for the NLI core.
    
    This class provides a simpler interface for the NLI system to deploy services
    and handles coordination with the main ServiceManager.
    """
    
    def __init__(self, base_nli):
        """Initialize the service deployer with the base NLI context"""
        self.service_manager = base_nli.service_manager
        self.user_preferences = base_nli.user_preferences
        self.nlu = base_nli.nlu
    
    def deploy_service(self, service_id: str, target_vm_id: Optional[str] = None, 
                      custom_params: Optional[Dict] = None) -> Dict:
        """
        Deploy a service with optional custom parameters
        
        Args:
            service_id: ID of the service to deploy
            target_vm_id: Optional ID of VM to deploy to (None creates a new VM)
            custom_params: Optional custom parameters for the deployment

        Returns:
            Deployment result dictionary
        """
        # Get user preferences for this service type
        if self.user_preferences and not custom_params:
            custom_params = self.user_preferences.get_service_preferences(service_id) or {}
            
        # Deploy the service using the service manager
        result = self.service_manager.deploy_service(service_id, target_vm_id, custom_params)
        
        # Update context with the deployed service info
        if result.get("success") and self.nlu:
            self.nlu.context_manager.set_context({
                'current_service': service_id,
                'current_service_vm': result.get('vm_id')
            })
            
        return result
        
    def deploy_services_group(self, service_ids: List[str], 
                             custom_params: Optional[Dict] = None) -> Dict:
        """
        Deploy multiple related services as a group with dependency resolution
        
        Args:
            service_ids: List of service IDs to deploy
            custom_params: Optional custom parameters for all deployments
            
        Returns:
            Deployment result dictionary
        """
        results = {
            "success": True,
            "deployed": [],
            "failed": []
        }
        
        # Get dependency manager from service_manager
        from ...services.dependency_manager import DependencyManager
        dependency_manager = DependencyManager(self.service_manager.catalog)
        
        # Build dependency graph
        dependency_manager.build_dependency_graph()
        
        # For each service, get ordered installation sequence
        for service_id in service_ids:
            try:
                # Get installation order for this service
                install_order = dependency_manager.get_installation_order(service_id)
                
                # Deploy each service in order
                for dep_id in install_order:
                    # Skip if already deployed
                    if dep_id in [s["id"] for s in results["deployed"]]:
                        continue
                        
                    # Get service-specific parameters
                    service_params = custom_params.get(dep_id, {}) if custom_params else {}
                    
                    # Deploy the service
                    result = self.deploy_service(dep_id, None, service_params)
                    
                    if result.get("success"):
                        results["deployed"].append({
                            "id": dep_id,
                            "vm_id": result.get("vm_id"),
                            "result": result
                        })
                    else:
                        results["failed"].append({
                            "id": dep_id,
                            "error": result.get("message"),
                            "result": result
                        })
                        results["success"] = False
                        break
                        
            except Exception as e:
                logger.error(f"Error deploying service group: {str(e)}")
                results["failed"].append({
                    "id": service_id,
                    "error": str(e)
                })
                results["success"] = False
        
        return results
        
    def stop_service(self, service_id: str, vm_id: str) -> Dict:
        """
        Stop a running service
        
        Args:
            service_id: ID of the service to stop
            vm_id: ID of the VM running the service
            
        Returns:
            Stop result dictionary
        """
        return self.service_manager.stop_service(service_id, vm_id)
        
    def remove_service(self, service_id: str, vm_id: str, remove_vm: bool = False) -> Dict:
        """
        Remove a deployed service
        
        Args:
            service_id: ID of the service to remove
            vm_id: ID of the VM running the service
            remove_vm: Whether to remove the VM as well
            
        Returns:
            Remove result dictionary
        """
        # Remove service using service manager
        result = self.service_manager.remove_service(service_id, vm_id, remove_vm)
        
        # Update context to remove the current service if it was the one removed
        if result.get("success") and self.nlu:
            context = self.nlu.context_manager.get_context()
            if (context.get('current_service') == service_id and 
                context.get('current_service_vm') == vm_id):
                self.nlu.context_manager.set_context({
                    'current_service': None,
                    'current_service_vm': None
                })
                
        return result