"""
Service manager for deploying and managing services via Proxmox VE.
This module handles the actual deployment of services defined in the service catalog.
"""
import logging
import os
from typing import Dict, List, Optional, Tuple

from ..api.proxmox_api import ProxmoxAPI
from .service_catalog import ServiceCatalog
from .deployment import DockerDeployer, ScriptDeployer

logger = logging.getLogger(__name__)

class ServiceManager:
    """Manager for deploying and managing services on Proxmox VE."""
    
    def __init__(self, proxmox_api: ProxmoxAPI, service_catalog: ServiceCatalog = None):
        """Initialize the service manager.
        
        Args:
            proxmox_api: ProxmoxAPI instance for interacting with Proxmox VE
            service_catalog: ServiceCatalog instance, or None to create a new one
        """
        self.api = proxmox_api
        self.catalog = service_catalog if service_catalog else ServiceCatalog()
        
        # Initialize deployers
        self.docker_deployer = DockerDeployer(proxmox_api)
        self.script_deployer = ScriptDeployer(proxmox_api)
        
    def find_service(self, query: str) -> List[Dict]:
        """Find services matching the user's query.
        
        Args:
            query: Natural language query describing desired service
            
        Returns:
            List of matching service definitions
        """
        return self.catalog.find_services_by_keywords(query)
        
    def deploy_service(self, service_id: str, target_vm_id: str = None, 
                     custom_params: Dict = None) -> Dict:
        """Deploy a service on a target VM.
        
        Args:
            service_id: ID of the service to deploy
            target_vm_id: ID of the VM to deploy the service on. If None, creates a new VM.
            custom_params: Custom parameters for service deployment
            
        Returns:
            Dictionary with deployment result
        """
        # Get service definition
        service_def = self.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        # Check if target VM exists and is running, or create a new one
        vm_id = target_vm_id
        if not vm_id:
            # Create a new VM based on service requirements
            vm_params = service_def.get('vm_requirements', {})
            vm_params['name'] = f"{service_def['id']}-vm"
            
            # Apply custom VM params if provided
            if custom_params and 'vm_params' in custom_params:
                vm_params.update(custom_params['vm_params'])
                
            # Call Proxmox API to create VM
            try:
                vm_result = self.api.api_request('POST', 'nodes/localhost/qemu', vm_params)
                if not vm_result['success']:
                    return {
                        "success": False,
                        "message": f"Failed to create VM: {vm_result.get('message', '')}"
                    }
                vm_id = vm_result['data']['vmid']
            except Exception as e:
                logger.error(f"Error creating VM: {str(e)}")
                return {
                    "success": False, 
                    "message": f"Failed to create VM: {str(e)}"
                }
        
        # Get appropriate deployer based on deployment method
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        if deployment_method == 'docker':
            return self.docker_deployer.deploy(service_def, vm_id, custom_params)
        elif deployment_method == 'script':
            return self.script_deployer.deploy(service_def, vm_id, custom_params)
        else:
            return {
                "success": False,
                "message": f"Unsupported deployment method: {deployment_method}"
            }
    
    def get_service_status(self, service_id: str, vm_id: str) -> Dict:
        """Get status of a deployed service.
        
        Args:
            service_id: ID of the service to check
            vm_id: ID of the VM running the service
            
        Returns:
            Status information dictionary
        """
        service_def = self.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        try:
            if deployment_method == 'docker':
                result = self.docker_deployer.run_command(vm_id, 
                    f"docker ps -a --filter name={service_id} --format '{{{{.Status}}}}'")
                
                if result["success"]:
                    return {
                        "success": True,
                        "status": result.get("output", "Unknown"),
                        "service_id": service_id,
                        "vm_id": vm_id
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to get Docker container status: {result.get('error', '')}"
                    }
            elif deployment_method == 'script':
                if 'status_check' in service_def['deployment']:
                    result = self.script_deployer.run_command(vm_id, 
                        service_def['deployment']['status_check'])
                    
                    return {
                        "success": True,
                        "status": "Running" if result.get("success") else "Not running",
                        "service_id": service_id,
                        "vm_id": vm_id
                    }
                else:
                    # Default to checking if the service process is running
                    result = self.script_deployer.run_command(vm_id, 
                        f"ps aux | grep -v grep | grep {service_def.get('process_name', service_id)}")
                    
                    return {
                        "success": True,
                        "status": "Running" if result.get("output") else "Not running",
                        "service_id": service_id,
                        "vm_id": vm_id
                    }
                    
        except Exception as e:
            logger.error(f"Error checking service status: {str(e)}")
            return {
                "success": False,
                "message": f"Error checking service status: {str(e)}"
            }
            
    def list_deployed_services(self) -> Dict:
        """List all deployed services.
        
        Returns:
            Dictionary with deployed services information
        """
        try:
            # Get all VMs
            vms = self.api.api_request('GET', 'cluster/resources?type=vm')
            if not vms['success']:
                return {
                    "success": False,
                    "message": "Failed to get VM list"
                }
                
            services = []
            for vm in vms['data']:
                # Check for services by container name pattern
                result = self.docker_deployer.run_command(vm['vmid'], 
                    "docker ps --format '{{.Names}}'")
                
                if result["success"] and result["output"]:
                    for container in result["output"].split('\n'):
                        service = self.catalog.get_service(container.strip())
                        if service:
                            services.append({
                                "service_id": service['id'],
                                "name": service['name'],
                                "vm_id": vm['vmid']
                            })
                            
            return {
                "success": True,
                "services": services
            }
            
        except Exception as e:
            logger.error(f"Error listing services: {str(e)}")
            return {
                "success": False,
                "message": f"Error listing services: {str(e)}"
            }
    
    def stop_service(self, service_id: str, vm_id: str) -> Dict:
        """Stop a running service.
        
        Args:
            service_id: ID of the service to stop
            vm_id: ID of the VM running the service
            
        Returns:
            Stop result dictionary
        """
        service_def = self.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        if deployment_method == 'docker':
            return self.docker_deployer.stop_service(service_def, vm_id)
        elif deployment_method == 'script':
            return self.script_deployer.stop_service(service_def, vm_id)
        else:
            return {
                "success": False,
                "message": f"Unsupported deployment method: {deployment_method}"
            }
    
    def remove_service(self, service_id: str, vm_id: str, remove_vm: bool = False) -> Dict:
        """Remove a deployed service.
        
        Args:
            service_id: ID of the service to remove
            vm_id: ID of the VM running the service
            remove_vm: Whether to remove the VM as well
            
        Returns:
            Remove result dictionary
        """
        service_def = self.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        try:
            # Remove the service first
            if deployment_method == 'docker':
                result = self.docker_deployer.remove_service(service_def, vm_id)
            elif deployment_method == 'script':
                result = self.script_deployer.remove_service(service_def, vm_id)
            else:
                return {
                    "success": False,
                    "message": f"Unsupported deployment method: {deployment_method}"
                }
                
            if not result["success"]:
                return result
                
            # Remove VM if requested
            if remove_vm:
                try:
                    vm_result = self.api.api_request('DELETE', f'nodes/localhost/qemu/{vm_id}')
                    if not vm_result['success']:
                        return {
                            "success": False,
                            "message": f"Failed to remove VM {vm_id}: {vm_result.get('message', '')}"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Error removing VM {vm_id}: {str(e)}"
                    }
                    
            return {
                "success": True,
                "message": f"Successfully removed {service_def['name']}" + 
                          (f" and VM {vm_id}" if remove_vm else ""),
                "service_id": service_id,
                "vm_id": vm_id
            }
                    
        except Exception as e:
            logger.error(f"Error removing service: {str(e)}")
            return {
                "success": False,
                "message": f"Error removing service: {str(e)}"
            }

    def setup_cloudflare_service(self, domain_name, email, tunnel_name="homelab"):
        """
        Set up Cloudflare service with domain and tunnel configuration
        """
        # Import cloudflare manager
        from ..core.network.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        
        # First configure the domain
        domain_result = cf_manager.configure_domain(domain_name, email)
        if not domain_result["success"]:
            return domain_result
            
        # Then set up the tunnel
        tunnel_result = cf_manager.create_tunnel(domain_name, tunnel_name)
        if not tunnel_result["success"]:
            return tunnel_result
        
        # Deploy cloudflared service from catalog
        service_result = self.deploy_service("cloudflared", {
            "domain": domain_name,
            "tunnel_name": tunnel_name
        })
        
        return {
            "success": True,
            "message": "Cloudflare service setup complete",
            "domain_config": domain_result,
            "tunnel_config": tunnel_result,
            "service_deployment": service_result
        }

    def remove_cloudflare_service(self, domain_name):
        """
        Remove Cloudflare service configuration
        """
        from ..core.network.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        
        # Remove domain configuration
        result = cf_manager.remove_domain(domain_name)
        if not result["success"]:
            return result
        
        return {
            "success": True,
            "message": f"Cloudflare service removed for domain {domain_name}",
            "cleanup_steps": [
                "1. Remove DNS records from Cloudflare dashboard",
                "2. Update nameservers at your domain registrar if needed",
                "3. Clean up any local cloudflared configurations"
            ]
        }