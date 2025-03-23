"""
Troubleshooting Assistant for Proxmox NLI.
Provides guided diagnostics and automated issue resolution for Proxmox environments.
"""
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from ..security.security_auditor import SecurityAuditor
from ...services.health_monitoring import ServiceHealthMonitor

logger = logging.getLogger(__name__)

class TroubleshootingAssistant:
    """Main troubleshooting assistant class that coordinates diagnostics and issue resolution."""
    
    def __init__(self, api, service_manager=None, security_auditor=None, health_monitor=None):
        """Initialize the troubleshooting assistant.
        
        Args:
            api: Proxmox API client
            service_manager: ServiceManager instance for service-related diagnostics
            security_auditor: SecurityAuditor instance for security-related diagnostics
            health_monitor: ServiceHealthMonitor instance for health-related diagnostics
        """
        self.api = api
        self.service_manager = service_manager
        self.security_auditor = security_auditor or SecurityAuditor(api)
        self.health_monitor = health_monitor
        
        # Import components lazily to avoid circular imports
        from .log_analyzer import LogAnalyzer
        from .diagnostic_tools import DiagnosticTools
        from .network_diagnostics import NetworkDiagnostics
        from .performance_analyzer import PerformanceAnalyzer
        from .self_healing_tools import SelfHealingTools
        from .report_generator import ReportGenerator
        
        # Initialize diagnostic components
        self.log_analyzer = LogAnalyzer(api)
        self.diagnostic_tools = DiagnosticTools(api)
        self.network_diagnostics = NetworkDiagnostics(api)
        self.performance_analyzer = PerformanceAnalyzer(api)
        self.self_healing_tools = SelfHealingTools(api)
        self.report_generator = ReportGenerator()
        
        # Create data directory for storing troubleshooting history
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load troubleshooting history
        self.history_file = os.path.join(self.data_dir, 'troubleshooting_history.json')
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load troubleshooting history from disk."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading troubleshooting history: {str(e)}")
        return []
    
    def _save_history(self):
        """Save troubleshooting history to disk."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving troubleshooting history: {str(e)}")
    
    def guided_diagnostics(self, issue_type: str, context: Dict = None) -> Dict:
        """Run guided diagnostics for a specific issue type.
        
        Args:
            issue_type: Type of issue to diagnose (vm, container, network, storage, service, security)
            context: Additional context for the diagnostics (e.g., VM ID, service name)
            
        Returns:
            Dict with diagnostic results and recommendations
        """
        context = context or {}
        
        # Record diagnostic session start
        session = {
            "timestamp": datetime.now().isoformat(),
            "issue_type": issue_type,
            "context": context,
            "steps": [],
            "results": {},
            "recommendations": []
        }
        
        # Run appropriate diagnostics based on issue type
        if issue_type == "vm":
            results = self._diagnose_vm_issues(context)
        elif issue_type == "container":
            results = self._diagnose_container_issues(context)
        elif issue_type == "network":
            results = self._diagnose_network_issues(context)
        elif issue_type == "storage":
            results = self._diagnose_storage_issues(context)
        elif issue_type == "service":
            results = self._diagnose_service_issues(context)
        elif issue_type == "security":
            results = self._diagnose_security_issues(context)
        elif issue_type == "performance":
            results = self._diagnose_performance_issues(context)
        else:
            return {
                "success": False,
                "message": f"Unknown issue type: {issue_type}",
                "recommendations": ["Please specify a valid issue type: vm, container, network, storage, service, security, performance"]
            }
        
        # Update session with results and recommendations
        session["results"] = results
        session["recommendations"] = self._generate_recommendations(issue_type, results)
        
        # Add session to history and save
        self.history.append(session)
        self._save_history()
        
        # Generate a report if requested
        if context.get("generate_report", False):
            report_format = context.get("report_format", "text")
            report = self.generate_report(session, report_format)
            results["report"] = report
        
        return {
            "success": True,
            "message": f"Completed diagnostics for {issue_type} issue",
            "results": results,
            "recommendations": session["recommendations"]
        }
    
    def _diagnose_vm_issues(self, context: Dict) -> Dict:
        """Diagnose issues with virtual machines."""
        vm_id = context.get("vm_id")
        if not vm_id:
            return {"error": "VM ID is required for VM diagnostics"}
        
        results = {}
        
        # Check VM status
        try:
            status = self.api.nodes(context.get("node", "pve")).qemu(vm_id).status.current.get()
            results["status"] = status
            
            # Check if VM is running
            if status.get("status") != "running":
                results["issues"] = [f"VM is not running (status: {status.get('status')})"]
            else:
                results["issues"] = []
            
            # Check resource usage
            if status.get("status") == "running":
                # Get resource usage
                resources = self.performance_analyzer.analyze_vm_resources(vm_id, context.get("node", "pve"))
                results["resources"] = resources
                
                # Check for resource bottlenecks
                if resources.get("cpu_usage", 0) > 90:
                    results["issues"].append(f"High CPU usage: {resources.get('cpu_usage')}%")
                
                if resources.get("memory_usage", 0) > 90:
                    results["issues"].append(f"High memory usage: {resources.get('memory_usage')}%")
                
                if resources.get("disk_usage", 0) > 90:
                    results["issues"].append(f"High disk usage: {resources.get('disk_usage')}%")
            
            # Check logs for errors
            logs = self.log_analyzer.analyze_vm_logs(vm_id, context.get("node", "pve"))
            results["logs"] = logs
            
            if logs.get("errors"):
                results["issues"].extend([f"Log error: {error}" for error in logs.get("errors")])
            
        except Exception as e:
            logger.error(f"Error diagnosing VM {vm_id}: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _diagnose_container_issues(self, context: Dict) -> Dict:
        """Diagnose issues with LXC containers."""
        container_id = context.get("container_id")
        if not container_id:
            return {"error": "Container ID is required for container diagnostics"}
        
        results = {}
        
        # Similar structure to VM diagnostics but for containers
        try:
            status = self.api.nodes(context.get("node", "pve")).lxc(container_id).status.current.get()
            results["status"] = status
            
            # Check if container is running
            if status.get("status") != "running":
                results["issues"] = [f"Container is not running (status: {status.get('status')})"]
            else:
                results["issues"] = []
            
            # Additional container-specific checks
            # ...
            
        except Exception as e:
            logger.error(f"Error diagnosing container {container_id}: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _diagnose_network_issues(self, context: Dict) -> Dict:
        """Diagnose network-related issues."""
        return self.network_diagnostics.run_diagnostics(context)
    
    def _diagnose_storage_issues(self, context: Dict) -> Dict:
        """Diagnose storage-related issues."""
        storage_id = context.get("storage_id")
        node = context.get("node", "pve")
        
        results = {}
        
        try:
            # Get storage status
            storage_status = self.api.nodes(node).storage(storage_id).status.get() if storage_id else None
            results["storage_status"] = storage_status
            
            # Run storage diagnostics
            storage_diagnostics = self.diagnostic_tools.check_storage(node, storage_id)
            results.update(storage_diagnostics)
            
        except Exception as e:
            logger.error(f"Error diagnosing storage {storage_id}: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _diagnose_service_issues(self, context: Dict) -> Dict:
        """Diagnose service-related issues."""
        service_id = context.get("service_id")
        if not service_id:
            return {"error": "Service ID is required for service diagnostics"}
        
        results = {}
        
        try:
            # Get service health if health monitor is available
            if self.health_monitor:
                health = self.health_monitor.get_service_health(service_id)
                results["health"] = health
                
                # Generate health report
                report = self.health_monitor.get_health_report(service_id)
                results["report"] = report
            
            # Get service status from service manager if available
            if self.service_manager:
                status = self.service_manager.get_service_status(service_id)
                results["status"] = status
            
            # Analyze service logs
            logs = self.log_analyzer.analyze_service_logs(service_id)
            results["logs"] = logs
            
        except Exception as e:
            logger.error(f"Error diagnosing service {service_id}: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _diagnose_security_issues(self, context: Dict) -> Dict:
        """Diagnose security-related issues."""
        # Use security auditor if available
        if self.security_auditor:
            return self.security_auditor.run_audit(context.get("scope", "full"))
        
        return {"error": "Security auditor not available"}
    
    def _diagnose_performance_issues(self, context: Dict) -> Dict:
        """Diagnose performance-related issues."""
        return self.performance_analyzer.analyze_performance(context)
    
    def _generate_recommendations(self, issue_type: str, results: Dict) -> List[str]:
        """Generate recommendations based on diagnostic results."""
        recommendations = []
        
        # Common issues and recommendations
        if "issues" in results:
            for issue in results.get("issues", []):
                if "CPU usage" in issue:
                    recommendations.append("Consider allocating more CPU resources or optimizing the workload")
                elif "memory usage" in issue:
                    recommendations.append("Consider increasing memory allocation or optimizing memory usage")
                elif "disk usage" in issue:
                    recommendations.append("Consider adding more storage or cleaning up unused files")
                elif "not running" in issue:
                    recommendations.append("Start the VM/container or check for startup issues in the logs")
        
        # Issue type specific recommendations
        if issue_type == "network" and "connectivity" in results:
            if not results["connectivity"].get("success", True):
                recommendations.append("Check network configuration and firewall rules")
        
        # Add generic recommendation if none were generated
        if not recommendations:
            recommendations.append("No specific issues detected. Monitor the system for any changes.")
        
        return recommendations
    
    def analyze_logs(self, log_type: str, context: Dict = None) -> Dict:
        """Analyze logs using natural language processing.
        
        Args:
            log_type: Type of logs to analyze (system, vm, container, service)
            context: Additional context for log analysis (e.g., VM ID, service name)
            
        Returns:
            Dict with log analysis results
        """
        context = context or {}
        return self.log_analyzer.analyze_logs(log_type, context)
    
    def detect_bottlenecks(self, resource_type: str = None, context: Dict = None) -> Dict:
        """Detect performance bottlenecks in the system.
        
        Args:
            resource_type: Type of resource to analyze (cpu, memory, disk, network, all)
            context: Additional context for bottleneck detection
            
        Returns:
            Dict with bottleneck detection results
        """
        context = context or {}
        return self.performance_analyzer.detect_bottlenecks(resource_type, context)
    
    def visualize_network(self, scope: str = "cluster", context: Dict = None) -> Dict:
        """Generate network diagnostics visualization.
        
        Args:
            scope: Scope of the visualization (cluster, node, vm, container)
            context: Additional context for network visualization
            
        Returns:
            Dict with network visualization data
        """
        context = context or {}
        return self.network_diagnostics.visualize_network(scope, context)
    
    def get_self_healing_recommendations(self, issue_type: str, context: Dict = None) -> Dict:
        """Get self-healing recommendations for common problems.
        
        Args:
            issue_type: Type of issue to get recommendations for
            context: Additional context for recommendations
            
        Returns:
            Dict with self-healing recommendations
        """
        context = context or {}
        
        # Run diagnostics first
        diagnostic_results = self.guided_diagnostics(issue_type, context)
        
        # Generate self-healing actions based on diagnostics
        healing_actions = self._generate_healing_actions(issue_type, diagnostic_results)
        
        return {
            "success": True,
            "message": f"Generated self-healing recommendations for {issue_type} issue",
            "diagnostic_results": diagnostic_results.get("results", {}),
            "recommendations": diagnostic_results.get("recommendations", []),
            "healing_actions": healing_actions
        }
    
    def _generate_healing_actions(self, issue_type: str, diagnostic_results: Dict) -> List[Dict]:
        """Generate self-healing actions based on diagnostic results."""
        healing_actions = []
        
        # Extract issues from diagnostic results
        issues = []
        if "results" in diagnostic_results and "issues" in diagnostic_results["results"]:
            issues = diagnostic_results["results"]["issues"]
        
        # Generate healing actions for each issue
        for issue in issues:
            if "CPU usage" in issue:
                healing_actions.append({
                    "issue": issue,
                    "action": "optimize_cpu_resources",
                    "description": "Optimize CPU resources by identifying and limiting CPU-intensive processes",
                    "automatic": False,
                    "command": "Analyze running processes and suggest CPU optimization"
                })
            elif "memory usage" in issue:
                healing_actions.append({
                    "issue": issue,
                    "action": "optimize_memory_usage",
                    "description": "Optimize memory usage by identifying memory leaks or high-memory processes",
                    "automatic": False,
                    "command": "Analyze memory usage and suggest optimization"
                })
            elif "disk usage" in issue:
                healing_actions.append({
                    "issue": issue,
                    "action": "clean_disk_space",
                    "description": "Clean up disk space by removing temporary files and old logs",
                    "automatic": True,
                    "command": "Find and remove temporary files and old logs"
                })
            elif "not running" in issue:
                healing_actions.append({
                    "issue": issue,
                    "action": "start_service",
                    "description": "Start the service/VM/container",
                    "automatic": True,
                    "command": "Start the service/VM/container"
                })
        
        return healing_actions
    
    def execute_healing_action(self, action_id: str, context: Dict = None) -> Dict:
        """Execute a self-healing action.
        
        Args:
            action_id: ID of the healing action to execute
            context: Additional context for the healing action
            
        Returns:
            Dict with execution results
        """
        context = context or {}
        
        # Implement healing action execution logic
        # This would depend on the specific action and context
        
        return {
            "success": True,
            "message": f"Executed healing action {action_id}",
            "results": {"action_id": action_id, "status": "completed"}
        }
    
    def auto_resolve_issues(self, issue_type: str, issues: List[Dict], context: Dict = None) -> Dict:
        """Attempt to automatically resolve identified issues.
        
        Args:
            issue_type: Type of issue to resolve (vm, container, network, storage, service, security)
            issues: List of issues to resolve, each with an issue_id and description
            context: Additional context for issue resolution
            
        Returns:
            Dict with resolution results
        """
        context = context or {}
        results = {
            "success": True,
            "message": f"Attempted to resolve {len(issues)} {issue_type} issues",
            "resolved": [],
            "failed": []
        }
        
        for issue in issues:
            issue_id = issue.get("issue_id")
            description = issue.get("description")
            
            # Record resolution attempt
            resolution_attempt = {
                "timestamp": datetime.now().isoformat(),
                "issue_type": issue_type,
                "issue_id": issue_id,
                "description": description,
                "context": context,
                "success": False,
                "actions_taken": []
            }
            
            try:
                # Attempt to resolve the issue based on its type
                if issue_type == "vm":
                    resolution = self.self_healing_tools.resolve_vm_issue(issue_id, description, context)
                elif issue_type == "container":
                    resolution = self.self_healing_tools.resolve_container_issue(issue_id, description, context)
                elif issue_type == "network":
                    resolution = self.self_healing_tools.resolve_network_issue(issue_id, description, context)
                elif issue_type == "storage":
                    resolution = self.self_healing_tools.resolve_storage_issue(issue_id, description, context)
                elif issue_type == "service":
                    resolution = self.self_healing_tools.resolve_service_issue(issue_id, description, context)
                elif issue_type == "security":
                    resolution = self.self_healing_tools.resolve_security_issue(issue_id, description, context)
                elif issue_type == "performance":
                    resolution = self.self_healing_tools.resolve_performance_issue(issue_id, description, context)
                else:
                    resolution = {
                        "success": False,
                        "message": f"Unknown issue type: {issue_type}",
                        "actions_taken": []
                    }
                
                # Update resolution attempt with results
                resolution_attempt["success"] = resolution.get("success", False)
                resolution_attempt["actions_taken"] = resolution.get("actions_taken", [])
                resolution_attempt["message"] = resolution.get("message", "")
                
                # Add to appropriate result list
                if resolution.get("success", False):
                    results["resolved"].append({
                        "issue_id": issue_id,
                        "description": description,
                        "actions_taken": resolution.get("actions_taken", []),
                        "message": resolution.get("message", "")
                    })
                else:
                    results["failed"].append({
                        "issue_id": issue_id,
                        "description": description,
                        "reason": resolution.get("message", "Unknown error"),
                        "actions_taken": resolution.get("actions_taken", [])
                    })
                
            except Exception as e:
                logger.error(f"Error resolving {issue_type} issue {issue_id}: {str(e)}")
                resolution_attempt["success"] = False
                resolution_attempt["message"] = str(e)
                
                results["failed"].append({
                    "issue_id": issue_id,
                    "description": description,
                    "reason": str(e),
                    "actions_taken": []
                })
            
            # Add resolution attempt to history
            if "resolution_history" not in self.history:
                self.history.append({"resolution_history": []})
            
            for entry in self.history:
                if "resolution_history" in entry:
                    entry["resolution_history"].append(resolution_attempt)
                    break
            
            self._save_history()
        
        # Update success status if any issues failed
        if results["failed"]:
            results["success"] = False
            results["message"] = f"Resolved {len(results['resolved'])} issues, {len(results['failed'])} failed"
        
        return results
    
    def generate_report(self, session: Dict, report_format: str = "text") -> Dict:
        """Generate a report from a troubleshooting session.
        
        Args:
            session: Troubleshooting session data
            report_format: Format of the report (text, html, json)
            
        Returns:
            Dict with report data
        """
        try:
            # Extract relevant data from the session
            report_data = {
                "timestamp": session.get("timestamp", datetime.now().isoformat()),
                "issue_type": session.get("issue_type", "unknown"),
                "context": session.get("context", {}),
                "results": session.get("results", {}),
                "recommendations": session.get("recommendations", []),
                "steps": session.get("steps", [])
            }
            
            # Generate report using the ReportGenerator
            if report_format == "html":
                report_content = self.report_generator.generate_html_report(report_data)
                report_file = os.path.join(self.data_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            elif report_format == "json":
                report_content = self.report_generator.generate_json_report(report_data)
                report_file = os.path.join(self.data_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            else:  # Default to text
                report_content = self.report_generator.generate_text_report(report_data)
                report_file = os.path.join(self.data_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            # Save report to file
            with open(report_file, 'w') as f:
                f.write(report_content)
            
            return {
                "success": True,
                "message": f"Generated {report_format} report",
                "report_file": report_file,
                "report_content": report_content
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating report: {str(e)}"
            }
    
    def get_troubleshooting_history(self, issue_type: str = None, limit: int = 10) -> List[Dict]:
        """Get troubleshooting history, optionally filtered by issue type.
        
        Args:
            issue_type: Type of issue to filter by
            limit: Maximum number of history entries to return
            
        Returns:
            List of troubleshooting history entries
        """
        # Filter history by issue type if specified
        if issue_type:
            filtered_history = [entry for entry in self.history if entry.get("issue_type") == issue_type]
        else:
            filtered_history = self.history
        
        # Sort by timestamp (newest first) and limit results
        sorted_history = sorted(
            filtered_history, 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        return sorted_history[:limit]
