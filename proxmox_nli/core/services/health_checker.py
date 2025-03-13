"""
Service health checking module for Proxmox NLI.

Provides service health monitoring and status reporting functionality.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HealthChecker:
    """
    Health monitoring for deployed services.
    
    Provides functionality to:
    - Check the health/status of deployed services
    - Monitor service metrics
    - Track uptime and reliability
    - Generate health reports
    """
    
    def __init__(self, base_nli):
        """Initialize the health checker with base NLI context"""
        self.service_manager = base_nli.service_manager if hasattr(base_nli, 'service_manager') else None
        self.service_catalog = base_nli.service_catalog if hasattr(base_nli, 'service_catalog') else None
        self.last_check = {}  # Timestamp of last health check by service
        self.health_history = {}  # History of health checks by service
    
    def check_service_health(self, service_id: str, vm_id: str) -> Dict[str, Any]:
        """
        Check the health of a specific deployed service
        
        Args:
            service_id: ID of the service to check
            vm_id: ID of the VM running the service
            
        Returns:
            Health check result dictionary
        """
        if not self.service_manager:
            return {
                "success": False,
                "message": "Service manager not available"
            }
            
        # Get current service status
        status = self.service_manager.get_service_status(service_id, vm_id)
        
        # Record the check
        self._record_check(service_id, vm_id, status)
        
        # Enhance the status with additional health information
        if status.get("success"):
            status["health"] = {
                "last_checked": datetime.now().isoformat(),
                "uptime": self._calculate_uptime(service_id, vm_id),
                "reliability": self._calculate_reliability(service_id, vm_id)
            }
        
        return status
    
    def check_all_services_health(self) -> Dict[str, Any]:
        """
        Check the health of all deployed services
        
        Returns:
            Dictionary with health status of all services
        """
        if not self.service_manager:
            return {
                "success": False,
                "message": "Service manager not available"
            }
        
        # Get list of deployed services
        deployed = self.service_manager.list_deployed_services()
        if not deployed.get("success"):
            return deployed
            
        results = {
            "success": True,
            "healthy": [],
            "unhealthy": [],
            "total": len(deployed.get("services", [])),
            "timestamp": datetime.now().isoformat()
        }
        
        # Check each service
        for service in deployed.get("services", []):
            service_id = service.get("service_id")
            vm_id = service.get("vm_id")
            
            if not service_id or not vm_id:
                continue
                
            health = self.check_service_health(service_id, vm_id)
            
            if health.get("success") and health.get("status", "").lower().startswith("running"):
                results["healthy"].append({
                    "service_id": service_id,
                    "name": service.get("name", service_id),
                    "vm_id": vm_id,
                    "status": health.get("status", "Unknown"),
                    "health": health.get("health", {})
                })
            else:
                results["unhealthy"].append({
                    "service_id": service_id,
                    "name": service.get("name", service_id),
                    "vm_id": vm_id,
                    "status": health.get("status", "Not running"),
                    "error": health.get("message", "Unknown error"),
                    "health": health.get("health", {})
                })
                
        return results
    
    def get_service_metrics(self, service_id: str, vm_id: str) -> Dict[str, Any]:
        """
        Get detailed metrics for a specific service
        
        Args:
            service_id: ID of the service
            vm_id: ID of the VM running the service
            
        Returns:
            Dictionary with service metrics
        """
        if not self.service_manager:
            return {
                "success": False,
                "message": "Service manager not available"
            }
            
        # Check basic health first
        health = self.check_service_health(service_id, vm_id)
        if not health.get("success"):
            return health
            
        # Get service metrics using deployer's run_command functionality
        # We'll have different approaches based on deployment method
        service_def = None
        if self.service_catalog:
            service_def = self.service_catalog.get_service(service_id)
            
        metrics = {
            "success": True,
            "service_id": service_id,
            "vm_id": vm_id,
            "status": health.get("status", "Unknown"),
            "health": health.get("health", {}),
            "resource_usage": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Use different metrics collection based on deployment type
            deployment_method = service_def.get('deployment', {}).get('method', 'docker') if service_def else 'docker'
            
            if deployment_method == 'docker':
                # Get docker stats for the container
                docker_stats = self.service_manager.docker_deployer.run_command(
                    vm_id, 
                    f"docker stats {service_id} --no-stream --format '{{{{.CPUPerc}}}};{{{{.MemUsage}}}};{{{{.MemPerc}}}};{{{{.NetIO}}}};{{{{.BlockIO}}}}'"
                )
                
                if docker_stats.get("success") and docker_stats.get("output"):
                    parts = docker_stats.get("output", "").strip().split(';')
                    if len(parts) >= 5:
                        metrics["resource_usage"] = {
                            "cpu_percent": parts[0].replace('%', ''),
                            "memory_usage": parts[1].split('/')[0].strip(),
                            "memory_percent": parts[2].replace('%', ''),
                            "network_io": parts[3],
                            "disk_io": parts[4]
                        }
                        
            elif deployment_method == 'script':
                # For script-deployed services, use VM-level metrics
                vm_stats = self.service_manager.script_deployer.run_command(
                    vm_id,
                    "top -b -n 1 | head -n 5"
                )
                
                if vm_stats.get("success"):
                    metrics["resource_usage"]["system_load"] = vm_stats.get("output", "")
                    
                # Try to get process-specific stats if we know the process name
                process_name = service_def.get('process_name', service_id) if service_def else service_id
                proc_stats = self.service_manager.script_deployer.run_command(
                    vm_id,
                    f"ps aux | grep -v grep | grep {process_name} || echo 'Process not found'"
                )
                
                if proc_stats.get("success"):
                    metrics["resource_usage"]["process_stats"] = proc_stats.get("output", "")
                    
        except Exception as e:
            logger.error(f"Error getting service metrics: {str(e)}")
            metrics["resource_usage"]["error"] = str(e)
            
        return metrics
    
    def generate_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive health report for all services
        
        Returns:
            Health report dictionary
        """
        # Get current health status of all services
        health_status = self.check_all_services_health()
        
        report = {
            "success": health_status.get("success", False),
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "total_services": health_status.get("total", 0),
                "healthy_count": len(health_status.get("healthy", [])),
                "unhealthy_count": len(health_status.get("unhealthy", [])),
                "overall_health_percent": 0
            },
            "healthy_services": health_status.get("healthy", []),
            "unhealthy_services": health_status.get("unhealthy", []),
            "recommendations": []
        }
        
        # Calculate overall health percentage
        if report["overview"]["total_services"] > 0:
            report["overview"]["overall_health_percent"] = (
                report["overview"]["healthy_count"] / report["overview"]["total_services"] * 100
            )
            
        # Generate recommendations for unhealthy services
        for service in health_status.get("unhealthy", []):
            service_id = service.get("service_id")
            status = service.get("status", "").lower()
            
            if "not running" in status:
                report["recommendations"].append({
                    "service_id": service_id,
                    "service_name": service.get("name", service_id),
                    "issue": "Service not running",
                    "recommendation": f"Try restarting the service with: deploy {service_id} {service.get('vm_id')}"
                })
            elif "error" in status:
                report["recommendations"].append({
                    "service_id": service_id,
                    "service_name": service.get("name", service_id),
                    "issue": f"Service error: {service.get('error', 'Unknown error')}",
                    "recommendation": "Check service logs and configuration"
                })
            
        return report
    
    def _record_check(self, service_id: str, vm_id: str, status: Dict[str, Any]):
        """Record a health check in the history"""
        service_key = f"{service_id}_{vm_id}"
        self.last_check[service_key] = datetime.now()
        
        # Initialize history for this service if needed
        if service_key not in self.health_history:
            self.health_history[service_key] = []
            
        # Add the check to history, limited to 100 entries
        self.health_history[service_key].append({
            "timestamp": datetime.now().isoformat(),
            "status": status.get("status", "Unknown"),
            "success": status.get("success", False)
        })
        
        # Limit history size
        if len(self.health_history[service_key]) > 100:
            self.health_history[service_key] = self.health_history[service_key][-100:]
    
    def _calculate_uptime(self, service_id: str, vm_id: str) -> float:
        """Calculate approximate uptime percentage based on health check history"""
        service_key = f"{service_id}_{vm_id}"
        
        if service_key not in self.health_history or not self.health_history[service_key]:
            return 0.0
            
        # Count successful checks
        total_checks = len(self.health_history[service_key])
        successful_checks = sum(1 for check in self.health_history[service_key] 
                               if check["success"] and "running" in check.get("status", "").lower())
                               
        if total_checks == 0:
            return 0.0
            
        return (successful_checks / total_checks) * 100
    
    def _calculate_reliability(self, service_id: str, vm_id: str) -> str:
        """Calculate service reliability based on health check history"""
        uptime = self._calculate_uptime(service_id, vm_id)
        
        if uptime >= 99.9:
            return "Excellent"
        elif uptime >= 99.0:
            return "Good"
        elif uptime >= 95.0:
            return "Fair"
        elif uptime >= 90.0:
            return "Poor"
        else:
            return "Unreliable"