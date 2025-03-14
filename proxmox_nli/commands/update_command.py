"""
Update command module for Proxmox NLI.
Provides commands for managing service updates through natural language.
"""
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class UpdateCommand:
    """Handles commands for checking and applying service updates."""
    
    def __init__(self, base_nli):
        """Initialize the update command handler.
        
        Args:
            base_nli: The base NLI instance with access to system components
        """
        self.base_nli = base_nli
        self.service_manager = base_nli.service_manager if hasattr(base_nli, 'service_manager') else None
        self.update_manager = base_nli.update_manager if hasattr(base_nli, 'update_manager') else None
        
    def check_updates(self, args=None):
        """Check for available updates across all services or for a specific service.
        
        Args:
            args: Optional dictionary containing:
                service_id: ID of a specific service to check (optional)
                
        Returns:
            Dictionary with update check results
        """
        if not self.update_manager:
            return {
                "success": False,
                "message": "Update manager not available"
            }
            
        service_id = args.get("service_id") if args else None
        
        if service_id:
            # Check specific service
            result = self.update_manager.check_service_for_updates_now(service_id)
            
            # Format message for NLI response
            if result.get("success"):
                if result.get("has_updates"):
                    return {
                        "success": True,
                        "message": f"Updates available for {result.get('service_name', service_id)}",
                        "details": result.get("updates", []),
                        "report": result.get("report")
                    }
                else:
                    return {
                        "success": True,
                        "message": f"No updates available for {result.get('service_name', service_id)}",
                        "report": result.get("report")
                    }
            else:
                return {
                    "success": False,
                    "message": result.get("message", f"Failed to check updates for {service_id}"),
                    "report": result.get("report")
                }
        else:
            # Check all services
            success = self.update_manager.check_all_services_for_updates()
            
            if success:
                # Generate report after checking all services
                report = self.update_manager.generate_update_report()
                
                return {
                    "success": True,
                    "message": "Checked for updates across all services",
                    "report": report.get("report"),
                    "services_with_updates": len(report.get("services", [])),
                    "total_updates": report.get("total_updates", 0)
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to check for updates across all services"
                }
                
    def list_updates(self, args=None):
        """List available updates for all services or a specific service.
        
        Args:
            args: Optional dictionary containing:
                service_id: ID of a specific service to list updates for (optional)
                
        Returns:
            Dictionary with available updates
        """
        if not self.update_manager:
            return {
                "success": False,
                "message": "Update manager not available"
            }
            
        service_id = args.get("service_id") if args else None
        
        if service_id:
            # Get updates for specific service
            update_info = self.update_manager.get_service_update_status(service_id)
            
            if not update_info:
                return {
                    "success": False,
                    "message": f"No update information available for service '{service_id}'",
                    "report": f"I don't have any update information for {service_id}. Try running 'check for updates for {service_id}' first."
                }
                
            if not update_info.get("available_updates"):
                return {
                    "success": True,
                    "message": f"No updates available for {update_info.get('name', service_id)}",
                    "report": f"{update_info.get('name', service_id)} is up to date. No updates are currently available."
                }
                
            updates = update_info.get("available_updates", [])
            service_name = update_info.get("name", service_id)
            
            # Format report
            report = f"Updates available for {service_name}:\n\n"
            for update in updates:
                severity = update.get("severity", "normal")
                severity_marker = "❗" if severity == "critical" else "⚠️" if severity == "warning" else "ℹ️"
                report += f"- {severity_marker} {update['description']}\n"
                
            return {
                "success": True,
                "message": f"Found {len(updates)} updates for {service_name}",
                "service_id": service_id,
                "service_name": service_name,
                "updates": updates,
                "report": report
            }
        else:
            # List all available updates
            report = self.update_manager.generate_update_report()
            
            return {
                "success": True,
                "message": "Listed all available updates",
                "report": report.get("report"),
                "services": report.get("services", []),
                "total_updates": report.get("total_updates", 0)
            }
            
    def apply_updates(self, args=None):
        """Apply updates to a service or all services with available updates.
        
        Args:
            args: Optional dictionary containing:
                service_id: ID of a specific service to update (optional)
                all: Boolean flag to update all services (optional)
                
        Returns:
            Dictionary with update results
        """
        if not self.update_manager:
            return {
                "success": False,
                "message": "Update manager not available"
            }
            
        service_id = args.get("service_id") if args else None
        update_all = args.get("all", False) if args else False
        
        if service_id:
            # Update specific service
            result = self.update_manager.apply_updates(service_id)
            return result
        elif update_all:
            # Update all services with available updates
            report = self.update_manager.generate_update_report()
            services_to_update = report.get("services", [])
            
            if not services_to_update:
                return {
                    "success": True,
                    "message": "All services are already up to date",
                    "report": "All services are up to date. No updates were applied."
                }
                
            # Apply updates to each service
            successful_updates = []
            failed_updates = []
            
            for service in services_to_update:
                service_id = service.get("service_id")
                service_name = service.get("name", service_id)
                
                result = self.update_manager.apply_updates(service_id)
                
                if result.get("success"):
                    successful_updates.append({
                        "service_id": service_id,
                        "service_name": service_name
                    })
                else:
                    failed_updates.append({
                        "service_id": service_id,
                        "service_name": service_name,
                        "error": result.get("message")
                    })
            
            # Generate combined report
            if not failed_updates:
                report = f"Successfully updated all {len(successful_updates)} services with available updates."
            else:
                report = f"Updated {len(successful_updates)} services successfully, but {len(failed_updates)} updates failed:\n\n"
                for failed in failed_updates:
                    report += f"- {failed['service_name']}: {failed['error']}\n"
                    
            return {
                "success": len(successful_updates) > 0,
                "message": f"Updated {len(successful_updates)} services, {len(failed_updates)} failed",
                "report": report,
                "successful": successful_updates,
                "failed": failed_updates
            }
        else:
            return {
                "success": False,
                "message": "Please specify a service to update or use 'all' to update all services",
                "report": "I need to know which service to update. Please specify a service name or tell me to update all services."
            }
            
    def update_settings(self, args=None):
        """Update settings for the update manager.
        
        Args:
            args: Optional dictionary containing:
                auto_check: Boolean to enable/disable automatic update checks
                check_interval: Interval in hours between update checks
                
        Returns:
            Dictionary with result
        """
        if not self.update_manager:
            return {
                "success": False,
                "message": "Update manager not available"
            }
            
        if not args:
            return {
                "success": False,
                "message": "No settings provided to update"
            }
            
        changes = []
        
        # Update auto-check setting
        if "auto_check" in args:
            auto_check = args["auto_check"]
            if auto_check:
                self.update_manager.start_checking()
                changes.append("Automatic update checks enabled")
            else:
                self.update_manager.stop_checking()
                changes.append("Automatic update checks disabled")
                
        # Update check interval
        if "check_interval" in args:
            hours = args["check_interval"]
            if isinstance(hours, (int, float)) and hours > 0:
                # Convert hours to seconds
                self.update_manager.check_interval = int(hours * 3600)
                changes.append(f"Update check interval set to {hours} hours")
            else:
                return {
                    "success": False,
                    "message": "Invalid check interval, must be a positive number"
                }
                
        if not changes:
            return {
                "success": False,
                "message": "No valid settings provided to update"
            }
            
        return {
            "success": True,
            "message": "Update settings updated",
            "changes": changes
        }

    def get_update_status(self, args=None):
        """Get the current update status and settings.
        
        Args:
            args: Optional arguments (not used)
            
        Returns:
            Dictionary with update status
        """
        if not self.update_manager:
            return {
                "success": False,
                "message": "Update manager not available"
            }
            
        # Get update status
        report = self.update_manager.generate_update_report()
        services_with_updates = report.get("services", [])
        total_updates = report.get("total_updates", 0)
        
        # Get settings
        auto_check = self.update_manager.checking_active
        check_interval_hours = self.update_manager.check_interval / 3600
        
        # Generate report
        status_report = "Update Status:\n\n"
        
        if total_updates > 0:
            status_report += f"There are {total_updates} updates available for {len(services_with_updates)} services.\n\n"
        else:
            status_report += "All services are up to date.\n\n"
            
        status_report += f"Automatic update checks are {'enabled' if auto_check else 'disabled'}.\n"
        status_report += f"Update check interval: {check_interval_hours:.1f} hours."
        
        return {
            "success": True,
            "message": "Retrieved update status",
            "report": status_report,
            "services_with_updates": len(services_with_updates),
            "total_updates": total_updates,
            "auto_check": auto_check,
            "check_interval_hours": check_interval_hours
        }