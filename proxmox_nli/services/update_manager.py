"""
Update management for Proxmox NLI services.
Provides functionality to check for updates and manage service updates through NLI commands.
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

class UpdateManager:
    """Manager for service updates."""
    
    def __init__(self, service_manager, check_interval: int = 86400):
        """Initialize the update manager.
        
        Args:
            service_manager: ServiceManager instance to interact with services
            check_interval: Interval in seconds between update checks (default: 24 hours)
        """
        self.service_manager = service_manager
        self.check_interval = check_interval
        self.update_data = {}
        self.checking_thread = None
        self.checking_active = False
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data', 'updates')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing update data if available
        self._load_update_data()
        
    def _load_update_data(self):
        """Load update data from disk."""
        try:
            update_file = os.path.join(self.data_dir, 'update_data.json')
            if os.path.exists(update_file):
                with open(update_file, 'r') as f:
                    self.update_data = json.load(f)
                logger.info(f"Loaded update data for {len(self.update_data)} services")
        except Exception as e:
            logger.error(f"Error loading update data: {str(e)}")
            self.update_data = {}
            
    def _save_update_data(self):
        """Save update data to disk."""
        try:
            update_file = os.path.join(self.data_dir, 'update_data.json')
            with open(update_file, 'w') as f:
                json.dump(self.update_data, f)
            logger.debug("Update data saved to disk")
        except Exception as e:
            logger.error(f"Error saving update data: {str(e)}")
    
    def start_checking(self):
        """Start the update checking thread."""
        if self.checking_thread and self.checking_thread.is_alive():
            logger.warning("Update checking already running")
            return False
            
        self.checking_active = True
        self.checking_thread = threading.Thread(target=self._checking_loop, daemon=True)
        self.checking_thread.start()
        logger.info("Started service update checking")
        return True
        
    def stop_checking(self):
        """Stop the update checking thread."""
        self.checking_active = False
        if self.checking_thread:
            self.checking_thread.join(timeout=10)
            logger.info("Stopped service update checking")
            return True
        return False
    
    def _checking_loop(self):
        """Main loop to check for updates periodically."""
        while self.checking_active:
            try:
                self.check_all_services_for_updates()
                self._save_update_data()
            except Exception as e:
                logger.error(f"Error in update checking loop: {str(e)}")
                
            # Sleep for the check interval
            for _ in range(self.check_interval):
                if not self.checking_active:
                    break
                time.sleep(1)
    
    def check_all_services_for_updates(self):
        """Check all deployed services for available updates."""
        # Get list of all deployed services
        deployed_services = self.service_manager.list_deployed_services()
        if not deployed_services.get("success", False):
            logger.error("Failed to get deployed services list for update check")
            return False
            
        now = datetime.now().isoformat()
        updated_count = 0
        
        # Check each service
        for service in deployed_services.get("services", []):
            service_id = service["service_id"]
            vm_id = service["vm_id"]
            
            # Initialize update data for new services
            if service_id not in self.update_data:
                self.update_data[service_id] = {
                    "name": service["name"],
                    "vm_id": vm_id,
                    "checks": [],
                    "available_updates": [],
                    "last_updated": None
                }
            
            # Check for updates
            update_info = self._check_service_for_updates(service_id, vm_id)
            update_info["timestamp"] = now
            
            # Update service update data
            service_update = self.update_data[service_id]
            service_update["vm_id"] = vm_id  # Update VM ID in case it changed
            service_update["checks"].append({
                "timestamp": now,
                "has_updates": update_info["has_updates"]
            })
            
            # If updates are available, add them to the list
            if update_info["has_updates"]:
                service_update["available_updates"] = update_info["updates"]
                updated_count += 1
            
            # Keep only the last 20 checks
            if len(service_update["checks"]) > 20:
                service_update["checks"] = service_update["checks"][-20:]
                
        logger.info(f"Found updates for {updated_count} services")
        return True
        
    def _check_service_for_updates(self, service_id: str, vm_id: str) -> Dict:
        """Check a specific service for available updates.
        
        Args:
            service_id: ID of the service to check
            vm_id: ID of the VM running the service
            
        Returns:
            Update information dictionary
        """
        service_def = self.service_manager.catalog.get_service(service_id)
        if not service_def:
            return {"has_updates": False, "updates": [], "error": "Service not found"}
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        updates = []
        
        try:
            # For Docker services
            if deployment_method == 'docker':
                image = service_def['deployment'].get('image', '')
                if not image:
                    return {"has_updates": False, "updates": [], "error": "No Docker image specified"}
                
                # Pull the latest image from registry
                pull_result = self.service_manager.docker_deployer.run_command(vm_id,
                    f"docker pull {image}")
                
                # Check if there are updates available
                if pull_result.get("success"):
                    output = pull_result.get("output", "")
                    if "Image is up to date" in output:
                        # No updates available
                        return {"has_updates": False, "updates": []}
                    elif "Downloaded newer image" in output or "Pulling from" in output:
                        # New version available
                        updates.append({
                            "type": "docker_image",
                            "name": image,
                            "description": f"Newer version of {image} is available",
                            "severity": "normal"
                        })
                    
                # Check if the container is running with an old image
                inspect_result = self.service_manager.docker_deployer.run_command(vm_id,
                    f"docker inspect --format='{{{{.Config.Image}}}}' {service_id}")
                
                if inspect_result.get("success"):
                    current_image = inspect_result.get("output", "").strip()
                    if current_image and current_image != image:
                        updates.append({
                            "type": "container_config",
                            "name": "image_mismatch",
                            "description": f"Container is running with image {current_image} instead of {image}",
                            "severity": "warning"
                        })
                        
            # For script-deployed services
            elif deployment_method == 'script':
                if 'update_check' in service_def['deployment']:
                    # Use custom update check if defined
                    update_check = service_def['deployment']['update_check']
                    result = self.service_manager.script_deployer.run_command(vm_id, update_check)
                    
                    if result.get("success") and result.get("output"):
                        # If the update check returns anything, assume updates are available
                        updates.append({
                            "type": "software_update",
                            "name": service_def['name'],
                            "description": f"Updates available: {result.get('output')}",
                            "severity": "normal"
                        })
                else:
                    # Default check for Linux updates
                    # First check if apt or yum is available
                    apt_result = self.service_manager.script_deployer.run_command(vm_id,
                        "command -v apt-get > /dev/null && echo 'apt' || echo 'none'")
                    
                    if apt_result.get("success") and "apt" in apt_result.get("output", ""):
                        # Check for updates with apt
                        update_result = self.service_manager.script_deployer.run_command(vm_id,
                            "apt-get update && apt-get -s upgrade | grep -c 'Inst'")
                        
                        if update_result.get("success"):
                            try:
                                update_count = int(update_result.get("output", "0").strip())
                                if update_count > 0:
                                    updates.append({
                                        "type": "system_update",
                                        "name": "apt_packages",
                                        "description": f"{update_count} system package updates available",
                                        "severity": "normal"
                                    })
                            except ValueError:
                                pass
                    else:
                        # Try yum if apt is not available
                        yum_result = self.service_manager.script_deployer.run_command(vm_id,
                            "command -v yum > /dev/null && echo 'yum' || echo 'none'")
                        
                        if yum_result.get("success") and "yum" in yum_result.get("output", ""):
                            # Check for updates with yum
                            update_result = self.service_manager.script_deployer.run_command(vm_id,
                                "yum check-update -q | grep -v '^$' | wc -l")
                            
                            if update_result.get("success"):
                                try:
                                    update_count = int(update_result.get("output", "0").strip())
                                    if update_count > 0:
                                        updates.append({
                                            "type": "system_update",
                                            "name": "yum_packages",
                                            "description": f"{update_count} system package updates available",
                                            "severity": "normal"
                                        })
                                except ValueError:
                                    pass
            
        except Exception as e:
            logger.error(f"Error checking for updates for {service_id}: {str(e)}")
            return {"has_updates": False, "updates": [], "error": str(e)}
            
        return {"has_updates": len(updates) > 0, "updates": updates}
    
    def get_service_update_status(self, service_id: str) -> Optional[Dict]:
        """Get update information for a specific service.
        
        Args:
            service_id: ID of the service to get update info for
            
        Returns:
            Service update dictionary or None if not found
        """
        return self.update_data.get(service_id)
    
    def apply_updates(self, service_id: str) -> Dict:
        """Apply available updates to a service.
        
        Args:
            service_id: ID of the service to update
            
        Returns:
            Update result dictionary
        """
        update_info = self.get_service_update_status(service_id)
        if not update_info:
            return {
                "success": False,
                "message": f"No update information available for service '{service_id}'",
                "report": f"I don't have any update information for {service_id} yet. Please run an update check first."
            }
            
        if not update_info.get("available_updates"):
            return {
                "success": False,
                "message": f"No updates available for service '{service_id}'",
                "report": f"There are no updates available for {update_info.get('name', service_id)}."
            }
            
        vm_id = update_info["vm_id"]
        service_def = self.service_manager.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found",
                "report": f"I couldn't find the service definition for {service_id}."
            }
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        try:
            # For Docker services
            if deployment_method == 'docker':
                # Stop the container
                stop_result = self.service_manager.stop_service(service_id, vm_id)
                if not stop_result.get("success", False):
                    return {
                        "success": False,
                        "message": f"Failed to stop service: {stop_result.get('message', '')}",
                        "report": f"I tried to update {update_info.get('name', service_id)} but couldn't stop the service."
                    }
                    
                # Remove the container (but keep volumes)
                remove_result = self.service_manager.docker_deployer.run_command(vm_id,
                    f"docker rm {service_id}")
                
                if not remove_result.get("success", False):
                    return {
                        "success": False,
                        "message": f"Failed to remove container: {remove_result.get('output', '')}",
                        "report": f"I tried to update {update_info.get('name', service_id)} but couldn't remove the old container."
                    }
                
                # Deploy the service again (with the new image)
                deploy_result = self.service_manager.deploy_service(service_id, vm_id)
                
                if not deploy_result.get("success", False):
                    return {
                        "success": False,
                        "message": f"Failed to redeploy service: {deploy_result.get('message', '')}",
                        "report": f"I tried to update {update_info.get('name', service_id)} but encountered an error while redeploying: {deploy_result.get('message', '')}"
                    }
                
            # For script-deployed services
            elif deployment_method == 'script':
                if 'update_command' in service_def['deployment']:
                    # Use custom update command if defined
                    update_command = service_def['deployment']['update_command']
                    result = self.service_manager.script_deployer.run_command(vm_id, update_command)
                    
                    if not result.get("success", False):
                        return {
                            "success": False,
                            "message": f"Update command failed: {result.get('error', '')}",
                            "report": f"I tried to update {update_info.get('name', service_id)} but the update command failed: {result.get('error', '')}"
                        }
                else:
                    # Default to system updates with apt or yum
                    # First try apt
                    apt_result = self.service_manager.script_deployer.run_command(vm_id,
                        "command -v apt-get > /dev/null && echo 'apt' || echo 'none'")
                    
                    if apt_result.get("success") and "apt" in apt_result.get("output", ""):
                        # Update with apt
                        update_result = self.service_manager.script_deployer.run_command(vm_id,
                            "apt-get update && apt-get -y upgrade")
                        
                        if not update_result.get("success", False):
                            return {
                                "success": False,
                                "message": f"Apt upgrade failed: {update_result.get('error', '')}",
                                "report": f"I tried to update {update_info.get('name', service_id)} but the system update failed: {update_result.get('error', '')}"
                            }
                    else:
                        # Try yum if apt is not available
                        yum_result = self.service_manager.script_deployer.run_command(vm_id,
                            "command -v yum > /dev/null && echo 'yum' || echo 'none'")
                        
                        if yum_result.get("success") and "yum" in yum_result.get("output", ""):
                            # Update with yum
                            update_result = self.service_manager.script_deployer.run_command(vm_id,
                                "yum -y update")
                                
                            if not update_result.get("success", False):
                                return {
                                    "success": False,
                                    "message": f"Yum update failed: {update_result.get('error', '')}",
                                    "report": f"I tried to update {update_info.get('name', service_id)} but the system update failed: {update_result.get('error', '')}"
                                }
                        else:
                            return {
                                "success": False,
                                "message": "No known package manager found (apt or yum)",
                                "report": f"I tried to update {update_info.get('name', service_id)} but I couldn't find a supported package manager on the system."
                            }
                
                # Restart the service if needed
                restart_result = self.service_manager.script_deployer.run_command(vm_id,
                    service_def['deployment'].get('restart_command', f"systemctl restart {service_id}"))
                
                if not restart_result.get("success", False):
                    logger.warning(f"Failed to restart service after update: {restart_result.get('error', '')}")
            
            # Update successful - record the update time
            now = datetime.now().isoformat()
            update_info["last_updated"] = now
            update_info["available_updates"] = []  # Clear the updates list
            update_info["checks"].append({
                "timestamp": now,
                "has_updates": False
            })
            self._save_update_data()
            
            return {
                "success": True,
                "message": f"Successfully updated {update_info.get('name', service_id)}",
                "report": f"Successfully updated {update_info.get('name', service_id)} to the latest version.",
                "service_id": service_id,
                "timestamp": now
            }
            
        except Exception as e:
            logger.error(f"Error applying updates to {service_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating service: {str(e)}",
                "report": f"I encountered an error while trying to update {update_info.get('name', service_id)}: {str(e)}"
            }
    
    def generate_update_report(self) -> Dict:
        """Generate a natural language report on available updates.
        
        Returns:
            Dictionary with natural language report on updates
        """
        services_with_updates = []
        
        for service_id, update_data in self.update_data.items():
            if update_data.get("available_updates"):
                services_with_updates.append({
                    "service_id": service_id,
                    "name": update_data.get("name", service_id),
                    "updates": update_data.get("available_updates", []),
                    "vm_id": update_data.get("vm_id")
                })
                
        if not services_with_updates:
            return {
                "success": True,
                "report": "All services are up to date. No updates are currently available.",
                "services": []
            }
            
        # Generate natural language report
        total_updates = sum(len(s["updates"]) for s in services_with_updates)
        
        report = f"There are updates available for {len(services_with_updates)} services:\n\n"
        
        for service in services_with_updates:
            report += f"- {service['name']}:\n"
            for update in service["updates"]:
                severity = update.get("severity", "normal")
                severity_marker = "❗" if severity == "critical" else "⚠️" if severity == "warning" else "ℹ️"
                report += f"  {severity_marker} {update['description']}\n"
            report += "\n"
            
        report += "You can apply these updates using natural language commands like 'update nextcloud' or 'apply all available updates'."
        
        return {
            "success": True,
            "report": report,
            "services": services_with_updates,
            "total_updates": total_updates
        }
    
    def check_service_for_updates_now(self, service_id: str) -> Dict:
        """Check a specific service for updates immediately.
        
        Args:
            service_id: ID of the service to check
            
        Returns:
            Update check result dictionary
        """
        # Get service VM ID
        service_info = None
        deployed_services = self.service_manager.list_deployed_services()
        if deployed_services.get("success", False):
            for service in deployed_services.get("services", []):
                if service["service_id"] == service_id:
                    service_info = service
                    break
                    
        if not service_info:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found or not deployed",
                "report": f"I couldn't find a deployed service with ID {service_id}."
            }
            
        vm_id = service_info["vm_id"]
        now = datetime.now().isoformat()
        
        # Initialize update data for new services
        if service_id not in self.update_data:
            self.update_data[service_id] = {
                "name": service_info["name"],
                "vm_id": vm_id,
                "checks": [],
                "available_updates": [],
                "last_updated": None
            }
        
        # Check for updates
        update_info = self._check_service_for_updates(service_id, vm_id)
        update_info["timestamp"] = now
        
        # Update service update data
        service_update = self.update_data[service_id]
        service_update["vm_id"] = vm_id  # Update VM ID in case it changed
        service_update["checks"].append({
            "timestamp": now,
            "has_updates": update_info["has_updates"]
        })
        
        # If updates are available, add them to the list
        if update_info["has_updates"]:
            service_update["available_updates"] = update_info["updates"]
            
        # Keep only the last 20 checks
        if len(service_update["checks"]) > 20:
            service_update["checks"] = service_update["checks"][-20:]
            
        self._save_update_data()
        
        # Generate report
        service_name = service_update.get("name", service_id)
        
        if update_info["has_updates"]:
            updates_list = ""
            for update in update_info["updates"]:
                severity = update.get("severity", "normal")
                severity_marker = "❗" if severity == "critical" else "⚠️" if severity == "warning" else "ℹ️"
                updates_list += f"\n- {severity_marker} {update['description']}"
                
            report = f"I found updates available for {service_name}:{updates_list}"
        else:
            report = f"{service_name} is up to date. No updates are currently available."
            
        return {
            "success": True,
            "report": report,
            "service_id": service_id,
            "service_name": service_name,
            "has_updates": update_info["has_updates"],
            "updates": update_info.get("updates", [])
        }
    
    def get_update_summary(self, service_id: str = None) -> Dict:
        """Get a summary of available updates in natural language.
        
        Args:
            service_id: Optional service ID to get update summary for.
                       If None, generates summary for all services.
                        
        Returns:
            Dictionary with update summary
        """
        if service_id and service_id not in self.update_data:
            return {
                "success": False,
                "message": f"No update data available for service '{service_id}'"
            }
            
        summaries = []
        services_to_summarize = [service_id] if service_id else list(self.update_data.keys())
        
        for sid in services_to_summarize:
            service_updates = self.update_data[sid]
            service_name = service_updates.get("name", sid)
            
            # Check if there are available updates
            available_updates = service_updates.get("available_updates", [])
            
            if not available_updates:
                summary = f"{service_name} is up to date."
                update_status = "up_to_date"
            else:
                # Count updates by type and severity
                update_types = {}
                critical_count = 0
                warning_count = 0
                normal_count = 0
                
                for update in available_updates:
                    update_type = update.get("type", "unknown")
                    if update_type not in update_types:
                        update_types[update_type] = 0
                    update_types[update_type] += 1
                    
                    severity = update.get("severity", "normal")
                    if severity == "critical":
                        critical_count += 1
                    elif severity == "warning":
                        warning_count += 1
                    else:
                        normal_count += 1
                
                # Generate natural language summary
                if len(available_updates) == 1:
                    update = available_updates[0]
                    summary = f"{service_name} has 1 update available: {update.get('description', 'Unknown update')}"
                else:
                    summary = f"{service_name} has {len(available_updates)} updates available"
                    
                    # Add details about update types
                    type_descriptions = []
                    for update_type, count in update_types.items():
                        if update_type == "docker_image":
                            type_descriptions.append(f"{count} image update{'s' if count > 1 else ''}")
                        elif update_type == "container_config":
                            type_descriptions.append(f"{count} configuration update{'s' if count > 1 else ''}")
                        elif update_type == "dependency":
                            type_descriptions.append(f"{count} dependency update{'s' if count > 1 else ''}")
                        else:
                            type_descriptions.append(f"{count} {update_type} update{'s' if count > 1 else ''}")
                    
                    if type_descriptions:
                        summary += f" ({', '.join(type_descriptions)})"
                
                # Add severity assessment
                if critical_count > 0:
                    update_status = "critical"
                    summary += f"\nThere {'is' if critical_count == 1 else 'are'} {critical_count} critical update{'s' if critical_count > 1 else ''} that should be applied immediately."
                elif warning_count > 0:
                    update_status = "warning"
                    summary += f"\nThere {'is' if warning_count == 1 else 'are'} {warning_count} update{'s' if warning_count > 1 else ''} marked as important."
                else:
                    update_status = "normal"
                
                # Add last check time if available
                if service_updates.get("checks"):
                    last_check = service_updates["checks"][-1]
                    if "timestamp" in last_check:
                        try:
                            check_time = datetime.fromisoformat(last_check["timestamp"])
                            now = datetime.now()
                            days_ago = (now - check_time).days
                            
                            if days_ago == 0:
                                summary += "\nLast checked today."
                            elif days_ago == 1:
                                summary += "\nLast checked yesterday."
                            else:
                                summary += f"\nLast checked {days_ago} days ago."
                        except (ValueError, TypeError):
                            pass
            
            summaries.append({
                "service_id": sid,
                "service_name": service_name,
                "update_status": update_status,
                "summary": summary,
                "updates_count": len(available_updates),
                "updates": available_updates
            })
        
        return {
            "success": True,
            "summaries": summaries,
            "timestamp": datetime.now().isoformat()
        }
    
    def apply_updates(self, service_id: str, update_ids: List[str] = None) -> Dict:
        """Apply updates to a service.
        
        Args:
            service_id: ID of the service to update
            update_ids: Optional list of specific update IDs to apply.
                        If None, applies all available updates.
                        
        Returns:
            Dictionary with update result
        """
        if service_id not in self.update_data:
            return {
                "success": False,
                "message": f"No update data available for service '{service_id}'"
            }
            
        service_updates = self.update_data[service_id]
        service_name = service_updates.get("name", service_id)
        vm_id = service_updates.get("vm_id")
        
        if not vm_id:
            return {
                "success": False,
                "message": f"VM ID not found for service '{service_id}'"
            }
            
        # Get available updates
        available_updates = service_updates.get("available_updates", [])
        if not available_updates:
            return {
                "success": False,
                "message": f"No updates available for service '{service_id}'"
            }
            
        # Filter updates if specific IDs are provided
        if update_ids:
            updates_to_apply = [u for u in available_updates if u.get("id") in update_ids]
            if not updates_to_apply:
                return {
                    "success": False,
                    "message": f"No matching updates found for the provided update IDs"
                }
        else:
            updates_to_apply = available_updates
            
        # Get service definition
        service_def = self.service_manager.catalog.get_service(service_id)
        if not service_def:
            return {
                "success": False,
                "message": f"Service definition not found for '{service_id}'"
            }
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        # Apply updates based on deployment method
        applied_updates = []
        failed_updates = []
        
        try:
            # For Docker services
            if deployment_method == 'docker':
                # Pull latest image
                pull_result = self.service_manager.docker_deployer.run_command(vm_id,
                    f"docker pull {service_def['deployment'].get('image', '')}")
                
                if not pull_result.get("success"):
                    return {
                        "success": False,
                        "message": f"Failed to pull latest image: {pull_result.get('error', '')}"
                    }
                
                # Stop the container
                stop_result = self.service_manager.docker_deployer.run_command(vm_id,
                    f"docker stop {service_id}")
                
                if not stop_result.get("success"):
                    return {
                        "success": False,
                        "message": f"Failed to stop container: {stop_result.get('error', '')}"
                    }
                
                # Remove the container
                rm_result = self.service_manager.docker_deployer.run_command(vm_id,
                    f"docker rm {service_id}")
                
                # Redeploy with the same parameters
                deploy_result = self.service_manager.deploy_service(service_id, vm_id)
                
                if deploy_result.get("success"):
                    # Mark all updates as applied
                    for update in updates_to_apply:
                        applied_updates.append(update)
                else:
                    # All updates failed
                    for update in updates_to_apply:
                        failed_updates.append({
                            "update": update,
                            "error": deploy_result.get("message", "Deployment failed")
                        })
                    
                    return {
                        "success": False,
                        "message": f"Failed to redeploy service: {deploy_result.get('message', '')}",
                        "applied_updates": applied_updates,
                        "failed_updates": failed_updates
                    }
            
            elif deployment_method == 'script':
                # For script-based services, run the update script if defined
                if 'update_script' in service_def['deployment']:
                    update_script = service_def['deployment']['update_script']
                    update_result = self.service_manager.script_deployer.run_command(vm_id, update_script)
                    
                    if update_result.get("success"):
                        # Mark all updates as applied
                        for update in updates_to_apply:
                            applied_updates.append(update)
                    else:
                        # All updates failed
                        for update in updates_to_apply:
                            failed_updates.append({
                                "update": update,
                                "error": update_result.get("error", "Update script failed")
                            })
                        
                        return {
                            "success": False,
                            "message": f"Update script failed: {update_result.get('error', '')}",
                            "applied_updates": applied_updates,
                            "failed_updates": failed_updates
                        }
                else:
                    return {
                        "success": False,
                        "message": "No update script defined for this service"
                    }
            
            # Update the service update data
            if applied_updates:
                # Remove applied updates from available updates
                service_updates["available_updates"] = [u for u in available_updates if u not in applied_updates]
                
                # Update last_updated timestamp
                service_updates["last_updated"] = datetime.now().isoformat()
                
                # Save update data
                self._save_update_data()
            
            return {
                "success": True,
                "message": f"Successfully applied {len(applied_updates)} updates to {service_name}",
                "applied_updates": applied_updates,
                "failed_updates": failed_updates
            }
            
        except Exception as e:
            logger.error(f"Error applying updates: {str(e)}")
            return {
                "success": False,
                "message": f"Error applying updates: {str(e)}",
                "applied_updates": applied_updates,
                "failed_updates": failed_updates
            }
    
    def generate_update_plan(self, service_id: str = None) -> Dict:
        """Generate a natural language update plan.
        
        Args:
            service_id: Optional service ID to generate plan for.
                        If None, generates plan for all services with updates.
                        
        Returns:
            Dictionary with update plan
        """
        # Get update summary first
        summary_result = self.get_update_summary(service_id)
        if not summary_result.get("success", False):
            return summary_result
            
        summaries = summary_result["summaries"]
        
        # Filter services that have updates
        services_with_updates = [s for s in summaries if s["updates_count"] > 0]
        
        if not services_with_updates:
            return {
                "success": True,
                "message": "All services are up to date",
                "plan": "No updates are needed at this time.",
                "services": []
            }
            
        # Generate plan
        plan = "Here's the recommended update plan:\n\n"
        
        # Sort services by update status (critical first, then warning, then normal)
        services_with_updates.sort(key=lambda s: 0 if s["update_status"] == "critical" else 
                                              (1 if s["update_status"] == "warning" else 2))
        
        for service in services_with_updates:
            service_name = service["service_name"]
            update_status = service["update_status"]
            updates_count = service["updates_count"]
            
            # Add service section to plan
            if update_status == "critical":
                plan += f"## {service_name} (CRITICAL - {updates_count} updates)\n"
                plan += "These updates should be applied immediately for security or stability reasons.\n\n"
            elif update_status == "warning":
                plan += f"## {service_name} (IMPORTANT - {updates_count} updates)\n"
                plan += "These updates are important and should be applied soon.\n\n"
            else:
                plan += f"## {service_name} ({updates_count} updates)\n"
                plan += "These are routine updates that can be applied during your next maintenance window.\n\n"
            
            # Add update details
            for update in service["updates"]:
                plan += f"- {update.get('description', 'Unknown update')}"
                if update.get("severity") == "critical":
                    plan += " (CRITICAL)"
                elif update.get("severity") == "warning":
                    plan += " (IMPORTANT)"
                plan += "\n"
            
            plan += "\n"
            
        # Add recommendations
        plan += "## Recommendations\n\n"
        
        if any(s["update_status"] == "critical" for s in services_with_updates):
            plan += "- Apply all CRITICAL updates as soon as possible\n"
            plan += "- Consider taking a backup before updating\n"
            plan += "- Test services after updating to ensure they're working correctly\n"
        else:
            plan += "- Schedule updates during a maintenance window\n"
            plan += "- Take backups before updating\n"
            plan += "- Test services after updating to ensure they're working correctly\n"
        
        return {
            "success": True,
            "plan": plan,
            "services": services_with_updates,
            "timestamp": datetime.now().isoformat()
        }