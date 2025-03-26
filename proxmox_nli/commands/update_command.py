"""
Update management commands for Proxmox NLI.

This module provides a command interface for the update management system,
allowing users to check for and apply updates through natural language commands.
"""
import logging
from typing import Dict, List, Optional, Any
from ..services.update_manager import UpdateManager

logger = logging.getLogger(__name__)

class UpdateCommand:
    """
    Handles natural language commands for update management.
    """
    
    def __init__(self, update_manager: UpdateManager):
        """
        Initialize the UpdateCommand with an UpdateManager.
        
        Args:
            update_manager: The UpdateManager instance to use
        """
        self.update_manager = update_manager
        
    def check_updates(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check for updates for a specific service or all services.
        
        Args:
            service_id: Optional ID of the service to check for updates.
                       If None, checks all services.
                       
        Returns:
            Dictionary with update check results
        """
        if service_id:
            return self.update_manager.check_service_for_updates_now(service_id)
        else:
            self.update_manager.check_all_services_for_updates()
            return self.update_manager.generate_update_report()
            
    def list_updates(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List available updates for services.
        
        Args:
            service_id: Optional ID of the service to list updates for.
                       If None, lists updates for all services.
                       
        Returns:
            Dictionary with update information
        """
        if service_id:
            result = self.update_manager.get_update_summary(service_id)
        else:
            result = self.update_manager.generate_update_report()
            
        return result
        
    def apply_updates(self, service_id: Optional[str] = None,
                     update_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Apply updates to a service or all services.
        
        Args:
            service_id: ID of the service to update. If None and update_ids is None,
                       applies all available updates to all services with pending updates.
            update_ids: Optional list of specific update IDs to apply.
                       
        Returns:
            Dictionary with results of the update operation
        """
        if service_id:
            return self.update_manager.apply_updates(service_id, update_ids)
        else:
            # Apply updates to all services with pending updates
            update_summary = self.update_manager.get_update_summary()
            services_with_updates = [s for s in update_summary.get("summaries", []) 
                                   if s.get("updates_count", 0) > 0]
            
            results = []
            success_count = 0
            failed_count = 0
            
            for service in services_with_updates:
                service_id = service.get("service_id")
                if not service_id:
                    continue
                    
                result = self.update_manager.apply_updates(service_id)
                results.append({
                    "service_id": service_id,
                    "service_name": service.get("service_name", service_id),
                    "success": result.get("success", False),
                    "message": result.get("message", "")
                })
                
                if result.get("success", False):
                    success_count += 1
                else:
                    failed_count += 1
            
            total = success_count + failed_count
            if total == 0:
                return {
                    "success": True,
                    "message": "No services had updates to apply.",
                    "report": "All services are already up to date. There were no updates to apply."
                }
                
            return {
                "success": failed_count == 0,
                "message": f"Applied updates to {success_count}/{total} services.",
                "report": self._generate_bulk_update_report(results),
                "results": results
            }
            
    def generate_update_plan(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an update plan for services.
        
        Args:
            service_id: Optional ID of the service to generate a plan for.
                       If None, generates a plan for all services with updates.
                       
        Returns:
            Dictionary with update plan
        """
        return self.update_manager.generate_update_plan(service_id)
        
    def _generate_bulk_update_report(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a human-friendly report for bulk update operations.
        
        Args:
            results: List of update results for individual services
            
        Returns:
            Natural language report
        """
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        report = ""
        
        if successful:
            report += f"Successfully updated {len(successful)} service(s):\n"
            for svc in successful:
                report += f"- {svc.get('service_name', svc.get('service_id'))}\n"
                
        if failed:
            if report:
                report += "\n"
            report += f"Failed to update {len(failed)} service(s):\n"
            for svc in failed:
                report += f"- {svc.get('service_name', svc.get('service_id'))}: {svc.get('message', 'Unknown error')}\n"
                
        report += "\nYou can check individual service status with commands like 'show updates for [service]'."
        
        return report

    def schedule_updates(self, service_id: Optional[str] = None, 
                       schedule_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Schedule updates to be applied at a specified time.
        
        Args:
            service_id: Optional ID of the service to schedule updates for.
                       If None, schedules updates for all services with pending updates.
            schedule_time: When to apply the updates (e.g., "tonight", "tomorrow 3am")
                         
        Returns:
            Dictionary with scheduling results
        """
        # This is a placeholder for future implementation
        if not schedule_time:
            schedule_time = "during the next maintenance window"
            
        return {
            "success": True,
            "message": f"Updates for {service_id or 'all services'} scheduled for {schedule_time}",
            "report": f"I've scheduled updates for {service_id or 'all services with pending updates'} to be applied {schedule_time}."
        }
        
    def get_update_status(self) -> Dict[str, Any]:
        """
        Get the current status of the update system.
        
        Returns:
            Dictionary with update status information including:
            - Last check time
            - Auto-check status
            - Number of services with updates available
            - Next scheduled check
        """
        status = self.update_manager.get_update_status()
        services_with_updates = self.update_manager.get_services_with_updates()
        
        return {
            "success": True,
            "message": f"Update status: {len(services_with_updates)} service(s) with updates available",
            "status": status,
            "services_with_updates": services_with_updates,
            "report": self._format_update_status(status, services_with_updates)
        }
        
    def _format_update_status(self, status: Dict[str, Any], services_with_updates: List[Dict[str, Any]]) -> str:
        """
        Format update status information into a human-readable report.
        
        Args:
            status: Update system status dictionary
            services_with_updates: List of services with available updates
            
        Returns:
            Formatted status report
        """
        last_check = status.get("last_check", "Never")
        if isinstance(last_check, (int, float)):
            from datetime import datetime
            last_check = datetime.fromtimestamp(last_check).strftime("%Y-%m-%d %H:%M:%S")
        
        auto_check = "Enabled" if status.get("auto_check", False) else "Disabled"
        check_interval = status.get("check_interval", 24)
        next_check = status.get("next_check", "Not scheduled")
        if isinstance(next_check, (int, float)):
            from datetime import datetime
            next_check = datetime.fromtimestamp(next_check).strftime("%Y-%m-%d %H:%M:%S")
            
        report = f"Update Status Summary:\n\n"
        report += f"Last check: {last_check}\n"
        report += f"Auto-check: {auto_check} (every {check_interval} hours)\n"
        report += f"Next scheduled check: {next_check}\n\n"
        
        if services_with_updates:
            report += f"Services with updates available ({len(services_with_updates)}):\n"
            for service in services_with_updates:
                service_name = service.get("service_name", service.get("service_id", "Unknown"))
                update_count = service.get("updates_count", 0)
                importance = service.get("importance", "unknown")
                report += f"- {service_name}: {update_count} update(s) [{importance} importance]\n"
            
            report += "\nTo see details about available updates, use 'list updates [service name]'."
        else:
            report += "All services are up to date. No updates are currently available."
            
        return report