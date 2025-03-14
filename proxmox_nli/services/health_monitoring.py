"""
Service health monitoring for Proxmox NLI.
Provides natural language status reports on service health.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import json
import os
from collections import defaultdict

logger = logging.getLogger(__name__)

class ServiceHealthMonitor:
    """Monitors health of deployed services and provides natural language status reports."""
    
    def __init__(self, service_manager, check_interval: int = 300):
        """Initialize the service health monitor.
        
        Args:
            service_manager: ServiceManager instance to interact with services
            check_interval: Interval in seconds between health checks (default: 5 minutes)
        """
        self.service_manager = service_manager
        self.check_interval = check_interval
        self.health_data = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data', 'health')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing health data if available
        self._load_health_data()
        
    def _load_health_data(self):
        """Load health data from disk."""
        try:
            health_file = os.path.join(self.data_dir, 'health_data.json')
            if os.path.exists(health_file):
                with open(health_file, 'r') as f:
                    self.health_data = json.load(f)
                logger.info(f"Loaded health data for {len(self.health_data)} services")
        except Exception as e:
            logger.error(f"Error loading health data: {str(e)}")
            self.health_data = {}
            
    def _save_health_data(self):
        """Save health data to disk."""
        try:
            health_file = os.path.join(self.data_dir, 'health_data.json')
            with open(health_file, 'w') as f:
                json.dump(self.health_data, f)
            logger.debug("Health data saved to disk")
        except Exception as e:
            logger.error(f"Error saving health data: {str(e)}")
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Health monitoring already running")
            return False
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started service health monitoring")
        return True
        
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
            logger.info("Stopped service health monitoring")
            return True
        return False
    
    def _monitoring_loop(self):
        """Main monitoring loop to check service health periodically."""
        while self.monitoring_active:
            try:
                self.check_services_health()
                self._save_health_data()
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {str(e)}")
                
            # Sleep for the check interval
            for _ in range(self.check_interval):
                if not self.monitoring_active:
                    break
                time.sleep(1)
    
    def check_services_health(self):
        """Check health of all deployed services."""
        # Get list of all deployed services
        deployed_services = self.service_manager.list_deployed_services()
        if not deployed_services.get("success", False):
            logger.error("Failed to get deployed services list for health check")
            return False
            
        now = datetime.now().isoformat()
        
        # Check each service
        for service in deployed_services.get("services", []):
            service_id = service["service_id"]
            vm_id = service["vm_id"]
            
            # Initialize health data for new services
            if service_id not in self.health_data:
                self.health_data[service_id] = {
                    "name": service["name"],
                    "vm_id": vm_id,
                    "checks": [],
                    "issues": [],
                    "last_uptime": None,
                    "status_history": []
                }
            
            # Get service status
            status = self.service_manager.get_service_status(service_id, vm_id)
            
            # Get service metrics
            metrics = self._collect_service_metrics(service_id, vm_id)
            
            # Add health check record
            health_check = {
                "timestamp": now,
                "status": status.get("status", "Unknown"),
                "success": status.get("success", False),
                "metrics": metrics
            }
            
            # Update service health data
            service_health = self.health_data[service_id]
            service_health["vm_id"] = vm_id  # Update VM ID in case it changed
            service_health["checks"].append(health_check)
            service_health["status_history"].append({
                "timestamp": now,
                "status": status.get("status", "Unknown")
            })
            
            # Keep only the last 50 checks for history
            if len(service_health["checks"]) > 50:
                service_health["checks"] = service_health["checks"][-50:]
            if len(service_health["status_history"]) > 100:
                service_health["status_history"] = service_health["status_history"][-100:]
                
            # Check for issues based on status and metrics
            self._detect_issues(service_id, health_check)
            
            # Calculate uptime if possible
            self._calculate_uptime(service_id)
            
        return True
        
    def _collect_service_metrics(self, service_id: str, vm_id: str) -> Dict:
        """Collect metrics for a specific service."""
        service_def = self.service_manager.catalog.get_service(service_id)
        metrics = {}
        
        if not service_def:
            return metrics
            
        deployment_method = service_def['deployment'].get('method', 'docker')
        
        try:
            # Basic container/service metrics
            if deployment_method == 'docker':
                # Get container stats
                result = self.service_manager.docker_deployer.run_command(vm_id, 
                    f"docker stats --no-stream --format '{{{{.Container}}}},{{{{.CPUPerc}}}},{{{{.MemUsage}}}},{{{{.NetIO}}}},{{{{.BlockIO}}}}' {service_id}")
                
                if result.get("success") and result.get("output"):
                    parts = result.get("output", "").split(',')
                    if len(parts) >= 5:
                        metrics["cpu_usage"] = parts[1].strip()
                        metrics["memory_usage"] = parts[2].strip()
                        metrics["network_io"] = parts[3].strip()
                        metrics["disk_io"] = parts[4].strip()
                
                # Get logs (last few lines)
                logs_result = self.service_manager.docker_deployer.run_command(vm_id,
                    f"docker logs --tail 5 {service_id}")
                if logs_result.get("success"):
                    metrics["recent_logs"] = logs_result.get("output", "")
            
            elif deployment_method == 'script':
                # Use custom metrics collection if defined
                if 'metrics_collection' in service_def['deployment']:
                    metrics_cmd = service_def['deployment']['metrics_collection']
                    result = self.service_manager.script_deployer.run_command(vm_id, metrics_cmd)
                    if result.get("success"):
                        metrics["custom"] = result.get("output", "")
                
                # Get basic system metrics for the process
                if 'process_name' in service_def:
                    process_name = service_def['process_name']
                    result = self.service_manager.script_deployer.run_command(vm_id,
                        f"ps aux | grep -v grep | grep {process_name}")
                    if result.get("success") and result.get("output"):
                        metrics["process_info"] = result.get("output", "")
                    
                    # Get memory usage for the process
                    mem_result = self.service_manager.script_deployer.run_command(vm_id,
                        f"ps -o pid,pcpu,pmem,vsz,rss -p $(pgrep -f {process_name})")
                    if mem_result.get("success"):
                        metrics["resource_usage"] = mem_result.get("output", "")
            
        except Exception as e:
            logger.error(f"Error collecting metrics for {service_id}: {str(e)}")
            
        return metrics
        
    def _detect_issues(self, service_id: str, health_check: Dict):
        """Detect issues based on the health check data."""
        service_health = self.health_data[service_id]
        status = health_check.get("status", "Unknown")
        
        # Check status issues
        if status == "Not running" or not health_check.get("success", False):
            issue = {
                "timestamp": health_check["timestamp"],
                "type": "status",
                "description": f"Service appears to be down or not responding",
                "resolved": False
            }
            service_health["issues"].append(issue)
        
        # Check resource issues if metrics available
        metrics = health_check.get("metrics", {})
        if "cpu_usage" in metrics:
            cpu_value = metrics["cpu_usage"].strip('%')
            try:
                cpu_percent = float(cpu_value)
                if cpu_percent > 90:
                    issue = {
                        "timestamp": health_check["timestamp"],
                        "type": "resource",
                        "description": f"High CPU usage: {cpu_percent}%",
                        "resolved": False
                    }
                    service_health["issues"].append(issue)
            except ValueError:
                pass
                
        if "memory_usage" in metrics:
            mem_info = metrics["memory_usage"]
            if " / " in mem_info:
                used, total = mem_info.split(" / ")
                used_value = used.rstrip("MiB").rstrip("GiB").strip()
                total_value = total.rstrip("MiB").rstrip("GiB").strip()
                try:
                    used_unit = "GB" if "GiB" in used else "MB"
                    total_unit = "GB" if "GiB" in total else "MB"
                    used_float = float(used_value)
                    total_float = float(total_value)
                    
                    # Convert to same unit if needed
                    if used_unit != total_unit:
                        if used_unit == "MB" and total_unit == "GB":
                            used_float = used_float / 1024
                        elif used_unit == "GB" and total_unit == "MB":
                            used_float = used_float * 1024
                            
                    # Calculate percentage
                    mem_percent = (used_float / total_float) * 100
                    if mem_percent > 90:
                        issue = {
                            "timestamp": health_check["timestamp"],
                            "type": "resource",
                            "description": f"High memory usage: {mem_percent:.1f}%",
                            "resolved": False
                        }
                        service_health["issues"].append(issue)
                except ValueError:
                    pass
        
        # Check for resolved issues
        if status == "Running" and health_check.get("success", False):
            for issue in service_health["issues"]:
                if not issue["resolved"] and issue["type"] == "status":
                    issue["resolved"] = True
                    issue["resolved_at"] = health_check["timestamp"]
    
    def _calculate_uptime(self, service_id: str):
        """Calculate uptime percentage and add to service health data."""
        service_health = self.health_data[service_id]
        history = service_health.get("status_history", [])
        
        if not history:
            return
            
        # Calculate uptime over the last 24 hours or available history
        now = datetime.now()
        uptime_count = 0
        total_count = 0
        
        for entry in history:
            timestamp_str = entry.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                # Only include checks in the last 24 hours
                if (now - timestamp) <= timedelta(hours=24):
                    total_count += 1
                    if entry.get("status") == "Running" or "Up " in entry.get("status", ""):
                        uptime_count += 1
            except ValueError:
                pass
                
        if total_count > 0:
            uptime_percent = (uptime_count / total_count) * 100
            service_health["last_uptime"] = {
                "calculated_at": now.isoformat(),
                "percent": round(uptime_percent, 2),
                "period_hours": 24
            }
    
    def get_service_health(self, service_id: str) -> Optional[Dict]:
        """Get health information for a specific service.
        
        Args:
            service_id: ID of the service to get health for
            
        Returns:
            Service health dictionary or None if not found
        """
        return self.health_data.get(service_id)
    
    def get_health_report(self, service_id: str) -> Dict:
        """Generate a natural language health report for a service.
        
        Args:
            service_id: ID of the service to generate report for
            
        Returns:
            Report dictionary with natural language status
        """
        service_health = self.get_service_health(service_id)
        if not service_health:
            return {
                "success": False,
                "message": f"No health data available for service '{service_id}'",
                "report": f"I don't have any health information for {service_id} yet. The service may not be deployed or hasn't been monitored."
            }
            
        # Get service definition for more context
        service_def = self.service_manager.catalog.get_service(service_id)
        service_name = service_def['name'] if service_def else service_health.get("name", service_id)
        
        # Get the latest check
        latest_check = service_health["checks"][-1] if service_health["checks"] else None
        
        # Generate status summary
        status_summary = self._generate_status_summary(service_id, service_health, latest_check)
        
        # Generate resource usage report
        resource_report = self._generate_resource_report(service_health, latest_check)
        
        # Generate issues report
        issues_report = self._generate_issues_report(service_health)
        
        # Generate uptime report
        uptime_report = self._generate_uptime_report(service_health)
        
        # Full report combining all sections
        full_report = f"{status_summary}\n\n{resource_report}\n\n{uptime_report}"
        
        if issues_report:
            full_report += f"\n\n{issues_report}"
        
        return {
            "success": True,
            "service_id": service_id,
            "service_name": service_name,
            "report": full_report,
            "summary": status_summary,
            "status": latest_check.get("status", "Unknown") if latest_check else "Unknown",
            "timestamp": latest_check.get("timestamp", "") if latest_check else "",
            "has_issues": len([i for i in service_health.get("issues", []) if not i.get("resolved", False)]) > 0
        }
    
    def _generate_status_summary(self, service_id: str, service_health: Dict, latest_check: Dict) -> str:
        """Generate a natural language status summary."""
        if not latest_check:
            return f"I don't have any recent status information for {service_id}."
            
        status = latest_check.get("status", "Unknown")
        timestamp_str = latest_check.get("timestamp", "")
        
        try:
            check_time = datetime.fromisoformat(timestamp_str)
            time_diff = datetime.now() - check_time
            time_ago = self._format_time_ago(time_diff)
        except ValueError:
            time_ago = "an unknown time"
            
        service_name = service_health.get("name", service_id)
        
        if "Up " in status:
            # Docker-specific status that includes uptime
            runtime = status.replace("Up ", "")
            return f"{service_name} is running. It has been up for {runtime} as of {time_ago}."
        elif status == "Running":
            return f"{service_name} is running normally as of {time_ago}."
        elif status == "Not running":
            return f"{service_name} is currently not running. Last checked {time_ago}."
        else:
            return f"{service_name} status: {status}. Last checked {time_ago}."
    
    def _generate_resource_report(self, service_health: Dict, latest_check: Dict) -> str:
        """Generate a natural language resource usage report."""
        if not latest_check or "metrics" not in latest_check:
            return "No resource usage information is available."
            
        metrics = latest_check.get("metrics", {})
        
        # For Docker services
        if "cpu_usage" in metrics and "memory_usage" in metrics:
            cpu = metrics["cpu_usage"]
            memory = metrics["memory_usage"]
            network = metrics.get("network_io", "")
            disk = metrics.get("disk_io", "")
            
            report = f"Resource usage: CPU: {cpu}, Memory: {memory}"
            if network:
                report += f", Network I/O: {network}"
            if disk:
                report += f", Disk I/O: {disk}"
                
            return report
            
        # For custom script-deployed services
        if "resource_usage" in metrics:
            return f"Resource usage:\n{metrics['resource_usage']}"
            
        if "custom" in metrics:
            return f"Service metrics:\n{metrics['custom']}"
            
        return "Detailed resource usage information is not available."
    
    def _generate_issues_report(self, service_health: Dict) -> str:
        """Generate a natural language issues report."""
        issues = service_health.get("issues", [])
        
        # Filter to recent unresolved issues
        unresolved_issues = [i for i in issues if not i.get("resolved", False)]
        
        if not unresolved_issues:
            return ""  # No issues to report
            
        if len(unresolved_issues) == 1:
            issue = unresolved_issues[0]
            return f"There is 1 active issue: {issue['description']}"
        else:
            report = f"There are {len(unresolved_issues)} active issues:"
            for issue in unresolved_issues:
                report += f"\n- {issue['description']}"
            return report
    
    def _generate_uptime_report(self, service_health: Dict) -> str:
        """Generate a natural language uptime report."""
        uptime = service_health.get("last_uptime")
        if not uptime:
            return "Uptime information is not available yet."
            
        percent = uptime.get("percent", 0)
        period = uptime.get("period_hours", 24)
        
        if percent >= 99.9:
            return f"The service has been 100% reliable over the past {period} hours."
        elif percent >= 99:
            return f"The service has excellent uptime of {percent}% over the past {period} hours."
        elif percent >= 95:
            return f"The service has good uptime of {percent}% over the past {period} hours."
        elif percent >= 90:
            return f"The service has moderate uptime of {percent}% over the past {period} hours."
        else:
            return f"The service has been experiencing availability issues with only {percent}% uptime over the past {period} hours."
    
    def _format_time_ago(self, time_diff):
        """Format a timedelta into a natural language time ago string."""
        seconds = time_diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
    
    def get_all_services_health_summary(self) -> Dict:
        """Get a summary of health for all services.
        
        Returns:
            Dictionary with health summary for all monitored services
        """
        services_summary = []
        
        for service_id, health_data in self.health_data.items():
            latest_check = health_data["checks"][-1] if health_data["checks"] else None
            if not latest_check:
                continue
                
            # Count unresolved issues
            unresolved_issues = len([i for i in health_data.get("issues", []) if not i.get("resolved", False)])
            
            # Get uptime if available
            uptime = health_data.get("last_uptime", {}).get("percent", 0)
            
            summary = {
                "service_id": service_id,
                "name": health_data.get("name", service_id),
                "status": latest_check.get("status", "Unknown"),
                "latest_check": latest_check.get("timestamp", ""),
                "issues_count": unresolved_issues,
                "uptime_percent": uptime,
                "vm_id": health_data.get("vm_id")
            }
            
            services_summary.append(summary)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "services": services_summary,
            "total_count": len(services_summary),
            "issues_count": sum(s["issues_count"] for s in services_summary)
        }

    def generate_system_health_report(self) -> Dict:
        """Generate a natural language report on overall system health.
        
        Returns:
            Dictionary with natural language report on system health
        """
        summary = self.get_all_services_health_summary()
        services = summary.get("services", [])
        
        if not services:
            return {
                "success": True,
                "report": "No services are being monitored yet."
            }
        
        # Count services by status
        status_counts = defaultdict(int)
        for service in services:
            status = service["status"]
            if "Up " in status:
                status = "Running"  # Normalize Docker "Up X time" status
            status_counts[status] += 1
            
        total = len(services)
        running = status_counts.get("Running", 0)
        not_running = status_counts.get("Not running", 0)
        other = total - running - not_running
        
        # Generate overall health statement
        if running == total:
            overall = f"All {total} monitored services are running normally."
        elif running > 0:
            overall = f"{running} out of {total} monitored services are running normally."
            if not_running > 0:
                overall += f" {not_running} {'service is' if not_running == 1 else 'services are'} not running."
            if other > 0:
                overall += f" {other} {'service has' if other == 1 else 'services have'} another status."
        else:
            overall = f"None of the {total} monitored services are running!"
            
        # Count services with issues
        services_with_issues = [s for s in services if s["issues_count"] > 0]
        total_issues = summary.get("issues_count", 0)
        
        if total_issues > 0:
            issue_statement = f"There {'is' if total_issues == 1 else 'are'} {total_issues} active issue{'s' if total_issues != 1 else ''} "
            issue_statement += f"across {len(services_with_issues)} service{'s' if len(services_with_issues) != 1 else ''}."
            
            # List services with issues
            if services_with_issues:
                issue_statement += " Services with issues: " + ", ".join([s["name"] for s in services_with_issues])
        else:
            issue_statement = "There are no active issues in any services."
            
        # Generate uptime summary
        uptimes = [s["uptime_percent"] for s in services if s["uptime_percent"] > 0]
        if uptimes:
            avg_uptime = sum(uptimes) / len(uptimes)
            if avg_uptime >= 99:
                uptime_statement = f"Overall system reliability is excellent with {avg_uptime:.2f}% average uptime."
            elif avg_uptime >= 95:
                uptime_statement = f"Overall system reliability is good with {avg_uptime:.2f}% average uptime."
            elif avg_uptime >= 90:
                uptime_statement = f"Overall system reliability is moderate with {avg_uptime:.2f}% average uptime."
            else:
                uptime_statement = f"Overall system reliability needs attention with only {avg_uptime:.2f}% average uptime."
        else:
            uptime_statement = "Uptime information is not available yet."
        
        # Combine into full report
        full_report = f"{overall}\n\n{issue_statement}\n\n{uptime_statement}"
        
        return {
            "success": True,
            "report": full_report,
            "summary": overall,
            "services_total": total,
            "services_running": running,
            "issues_total": total_issues
        }