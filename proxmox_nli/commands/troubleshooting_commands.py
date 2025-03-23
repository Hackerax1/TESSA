"""
Troubleshooting Commands for Proxmox NLI.
Provides natural language interface for troubleshooting and diagnostic features.
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple

from ..core.troubleshooting import (
    TroubleshootingAssistant,
    LogAnalyzer,
    DiagnosticTools,
    NetworkDiagnostics,
    PerformanceAnalyzer,
    SelfHealingTools,
    ReportGenerator
)

logger = logging.getLogger(__name__)

class TroubleshootingCommands:
    """Commands for troubleshooting and diagnostics."""
    
    def __init__(self, api, proxmox_commands=None, service_manager=None, security_auditor=None, health_monitor=None):
        """Initialize troubleshooting commands.
        
        Args:
            api: Proxmox API client
            proxmox_commands: ProxmoxCommands instance for command delegation
            service_manager: ServiceManager instance for service-related operations
            security_auditor: SecurityAuditor instance for security-related operations
            health_monitor: ServiceHealthMonitor instance for health monitoring
        """
        self.api = api
        self.proxmox_commands = proxmox_commands
        
        # Initialize troubleshooting components
        self.troubleshooting_assistant = TroubleshootingAssistant(
            api, 
            service_manager=service_manager,
            security_auditor=security_auditor,
            health_monitor=health_monitor
        )
        
        # Command patterns for natural language processing
        self.command_patterns = {
            "diagnose": [
                r"diagnose\s+(?P<issue_type>vm|container|network|storage|service|security|performance)(?:\s+(?P<context>.+))?",
                r"troubleshoot\s+(?P<issue_type>vm|container|network|storage|service|security|performance)(?:\s+(?P<context>.+))?",
                r"check\s+(?P<issue_type>vm|container|network|storage|service|security|performance)(?:\s+(?P<context>.+))?",
                r"analyze\s+(?P<issue_type>vm|container|network|storage|service|security|performance)(?:\s+(?P<context>.+))?"
            ],
            "analyze_logs": [
                r"analyze\s+logs(?:\s+for\s+(?P<log_type>vm|container|node|cluster|service))?(?:\s+(?P<context>.+))?",
                r"check\s+logs(?:\s+for\s+(?P<log_type>vm|container|node|cluster|service))?(?:\s+(?P<context>.+))?",
                r"view\s+logs(?:\s+for\s+(?P<log_type>vm|container|node|cluster|service))?(?:\s+(?P<context>.+))?"
            ],
            "network_diagnostics": [
                r"check\s+network\s+(?P<diagnostic_type>connectivity|dns|ports|visualization)(?:\s+(?P<context>.+))?",
                r"diagnose\s+network\s+(?P<diagnostic_type>connectivity|dns|ports|visualization)(?:\s+(?P<context>.+))?",
                r"test\s+network\s+(?P<diagnostic_type>connectivity|dns|ports|visualization)(?:\s+(?P<context>.+))?"
            ],
            "performance_analysis": [
                r"analyze\s+(?P<resource_type>cpu|memory|disk|network|all)\s+performance(?:\s+(?P<context>.+))?",
                r"check\s+(?P<resource_type>cpu|memory|disk|network|all)\s+performance(?:\s+(?P<context>.+))?",
                r"monitor\s+(?P<resource_type>cpu|memory|disk|network|all)\s+performance(?:\s+(?P<context>.+))?"
            ],
            "auto_resolve": [
                r"fix\s+(?P<issue_type>vm|container|network|storage|service|security|performance)(?:\s+(?P<context>.+))?",
                r"resolve\s+(?P<issue_type>vm|container|network|storage|service|security|performance)(?:\s+(?P<context>.+))?",
                r"repair\s+(?P<issue_type>vm|container|network|storage|service|security|performance)(?:\s+(?P<context>.+))?",
                r"auto[\s-]heal\s+(?P<issue_type>vm|container|network|storage|service|security|performance)(?:\s+(?P<context>.+))?"
            ],
            "generate_report": [
                r"generate\s+(?P<format>text|html|json)?\s*report(?:\s+for\s+(?P<issue_type>vm|container|network|storage|service|security|performance))?(?:\s+(?P<context>.+))?",
                r"create\s+(?P<format>text|html|json)?\s*report(?:\s+for\s+(?P<issue_type>vm|container|network|storage|service|security|performance))?(?:\s+(?P<context>.+))?"
            ],
            "view_history": [
                r"show\s+troubleshooting\s+history(?:\s+for\s+(?P<issue_type>vm|container|network|storage|service|security|performance))?(?:\s+limit\s+(?P<limit>\d+))?",
                r"view\s+troubleshooting\s+history(?:\s+for\s+(?P<issue_type>vm|container|network|storage|service|security|performance))?(?:\s+limit\s+(?P<limit>\d+))?",
                r"get\s+troubleshooting\s+history(?:\s+for\s+(?P<issue_type>vm|container|network|storage|service|security|performance))?(?:\s+limit\s+(?P<limit>\d+))?"
            ]
        }
    
    def process_command(self, command: str) -> Dict:
        """Process a natural language troubleshooting command.
        
        Args:
            command: Natural language command
            
        Returns:
            Dict with command results
        """
        command = command.lower().strip()
        
        # Check each command pattern
        for cmd_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, command)
                if match:
                    # Extract parameters from the match
                    params = match.groupdict()
                    
                    # Process command based on type
                    if cmd_type == "diagnose":
                        return self.diagnose_issue(params.get("issue_type"), params.get("context"))
                    elif cmd_type == "analyze_logs":
                        return self.analyze_logs(params.get("log_type"), params.get("context"))
                    elif cmd_type == "network_diagnostics":
                        return self.run_network_diagnostics(params.get("diagnostic_type"), params.get("context"))
                    elif cmd_type == "performance_analysis":
                        return self.analyze_performance(params.get("resource_type"), params.get("context"))
                    elif cmd_type == "auto_resolve":
                        return self.auto_resolve_issues(params.get("issue_type"), params.get("context"))
                    elif cmd_type == "generate_report":
                        return self.generate_report(params.get("format"), params.get("issue_type"), params.get("context"))
                    elif cmd_type == "view_history":
                        limit = int(params.get("limit", 10)) if params.get("limit") else 10
                        return self.view_troubleshooting_history(params.get("issue_type"), limit)
        
        # No matching command found
        return {
            "success": False,
            "message": "Unknown troubleshooting command",
            "help": self.get_help()
        }
    
    def diagnose_issue(self, issue_type: str, context_str: str = None) -> Dict:
        """Diagnose an issue using the troubleshooting assistant.
        
        Args:
            issue_type: Type of issue to diagnose
            context_str: String with additional context
            
        Returns:
            Dict with diagnostic results
        """
        # Parse context string into a dictionary
        context = self._parse_context(context_str)
        
        # Run diagnostics
        results = self.troubleshooting_assistant.guided_diagnostics(issue_type, context)
        
        # Format results for natural language output
        if results.get("success", False):
            recommendations = results.get("recommendations", [])
            
            # Format response message
            if recommendations:
                message = f"Diagnosed {issue_type} issue. Found {len(recommendations)} recommendations:\n"
                for i, rec in enumerate(recommendations, 1):
                    message += f"{i}. {rec}\n"
            else:
                message = f"Diagnosed {issue_type} issue. No issues found."
            
            return {
                "success": True,
                "message": message,
                "results": results
            }
        else:
            return {
                "success": False,
                "message": results.get("message", f"Failed to diagnose {issue_type} issue"),
                "results": results
            }
    
    def analyze_logs(self, log_type: str = None, context_str: str = None) -> Dict:
        """Analyze logs using the log analyzer.
        
        Args:
            log_type: Type of logs to analyze
            context_str: String with additional context
            
        Returns:
            Dict with log analysis results
        """
        # Parse context string into a dictionary
        context = self._parse_context(context_str)
        
        # Default to node logs if not specified
        log_type = log_type or "node"
        
        # Analyze logs
        results = self.troubleshooting_assistant.log_analyzer.analyze_logs(log_type, context)
        
        # Format results for natural language output
        if results.get("success", False):
            errors = results.get("errors", [])
            warnings = results.get("warnings", [])
            patterns = results.get("patterns", [])
            
            # Format response message
            message = f"Analyzed {log_type} logs.\n"
            
            if errors:
                message += f"Found {len(errors)} errors:\n"
                for i, error in enumerate(errors[:5], 1):
                    message += f"{i}. {error}\n"
                if len(errors) > 5:
                    message += f"... and {len(errors) - 5} more errors.\n"
            
            if warnings:
                message += f"Found {len(warnings)} warnings:\n"
                for i, warning in enumerate(warnings[:5], 1):
                    message += f"{i}. {warning}\n"
                if len(warnings) > 5:
                    message += f"... and {len(warnings) - 5} more warnings.\n"
            
            if patterns:
                message += f"Detected {len(patterns)} patterns in the logs.\n"
            
            if not errors and not warnings:
                message += "No issues found in the logs."
            
            return {
                "success": True,
                "message": message,
                "results": results
            }
        else:
            return {
                "success": False,
                "message": results.get("message", f"Failed to analyze {log_type} logs"),
                "results": results
            }
    
    def run_network_diagnostics(self, diagnostic_type: str, context_str: str = None) -> Dict:
        """Run network diagnostics.
        
        Args:
            diagnostic_type: Type of network diagnostic to run
            context_str: String with additional context
            
        Returns:
            Dict with network diagnostic results
        """
        # Parse context string into a dictionary
        context = self._parse_context(context_str)
        
        # Run appropriate network diagnostic
        if diagnostic_type == "connectivity":
            results = self.troubleshooting_assistant.network_diagnostics.check_connectivity(
                context.get("host", "8.8.8.8"),
                context.get("node", "pve")
            )
        elif diagnostic_type == "dns":
            results = self.troubleshooting_assistant.network_diagnostics.check_dns_resolution(
                context.get("domain", "google.com"),
                context.get("node", "pve")
            )
        elif diagnostic_type == "ports":
            results = self.troubleshooting_assistant.network_diagnostics.check_port(
                context.get("host", "localhost"),
                int(context.get("port", 22)),
                context.get("node", "pve")
            )
        elif diagnostic_type == "visualization":
            results = self.troubleshooting_assistant.network_diagnostics.visualize_network(
                context.get("node", "pve")
            )
        else:
            return {
                "success": False,
                "message": f"Unknown network diagnostic type: {diagnostic_type}",
                "help": "Available types: connectivity, dns, ports, visualization"
            }
        
        # Format results for natural language output
        if results.get("success", False):
            return {
                "success": True,
                "message": results.get("message", f"Completed {diagnostic_type} network diagnostic"),
                "results": results
            }
        else:
            return {
                "success": False,
                "message": results.get("message", f"Failed to run {diagnostic_type} network diagnostic"),
                "results": results
            }
    
    def analyze_performance(self, resource_type: str, context_str: str = None) -> Dict:
        """Analyze system performance.
        
        Args:
            resource_type: Type of resource to analyze
            context_str: String with additional context
            
        Returns:
            Dict with performance analysis results
        """
        # Parse context string into a dictionary
        context = self._parse_context(context_str)
        
        # Default to 'all' if not specified
        resource_type = resource_type or "all"
        
        # Analyze performance
        results = self.troubleshooting_assistant.performance_analyzer.analyze_performance(resource_type, context)
        
        # Format results for natural language output
        if results.get("success", False):
            bottlenecks = results.get("bottlenecks", [])
            recommendations = results.get("recommendations", [])
            
            # Format response message
            message = f"Analyzed {resource_type} performance.\n"
            
            if bottlenecks:
                message += f"Detected bottlenecks in: {', '.join(bottlenecks)}\n"
            else:
                message += "No performance bottlenecks detected.\n"
            
            if recommendations:
                message += f"Recommendations:\n"
                for i, rec in enumerate(recommendations, 1):
                    message += f"{i}. {rec}\n"
            
            return {
                "success": True,
                "message": message,
                "results": results
            }
        else:
            return {
                "success": False,
                "message": results.get("message", f"Failed to analyze {resource_type} performance"),
                "results": results
            }
    
    def auto_resolve_issues(self, issue_type: str, context_str: str = None) -> Dict:
        """Automatically resolve issues.
        
        Args:
            issue_type: Type of issue to resolve
            context_str: String with additional context
            
        Returns:
            Dict with resolution results
        """
        # Parse context string into a dictionary
        context = self._parse_context(context_str)
        
        # First, diagnose issues
        diagnostic_results = self.troubleshooting_assistant.guided_diagnostics(issue_type, context)
        
        if not diagnostic_results.get("success", False):
            return {
                "success": False,
                "message": f"Failed to diagnose {issue_type} issues before attempting resolution",
                "results": diagnostic_results
            }
        
        # Extract issues from diagnostic results
        issues = []
        for i, recommendation in enumerate(diagnostic_results.get("recommendations", [])):
            issues.append({
                "issue_id": f"{issue_type}_{i}",
                "description": recommendation
            })
        
        if not issues:
            return {
                "success": True,
                "message": f"No {issue_type} issues found to resolve",
                "results": diagnostic_results
            }
        
        # Attempt to resolve issues
        resolution_results = self.troubleshooting_assistant.auto_resolve_issues(issue_type, issues, context)
        
        # Format results for natural language output
        if resolution_results.get("success", False):
            message = f"Successfully resolved all {len(issues)} {issue_type} issues.\n"
            
            for i, resolved in enumerate(resolution_results.get("resolved", []), 1):
                message += f"{i}. {resolved.get('description')}\n"
                if resolved.get("actions_taken"):
                    message += f"   Actions: {', '.join(resolved.get('actions_taken'))}\n"
        else:
            resolved_count = len(resolution_results.get("resolved", []))
            failed_count = len(resolution_results.get("failed", []))
            
            message = f"Resolved {resolved_count} out of {resolved_count + failed_count} {issue_type} issues.\n"
            
            if resolved_count > 0:
                message += f"Successfully resolved:\n"
                for i, resolved in enumerate(resolution_results.get("resolved", []), 1):
                    message += f"{i}. {resolved.get('description')}\n"
            
            if failed_count > 0:
                message += f"Failed to resolve:\n"
                for i, failed in enumerate(resolution_results.get("failed", []), 1):
                    message += f"{i}. {failed.get('description')}: {failed.get('reason')}\n"
        
        return {
            "success": resolution_results.get("success", False),
            "message": message,
            "results": resolution_results
        }
    
    def generate_report(self, report_format: str = None, issue_type: str = None, context_str: str = None) -> Dict:
        """Generate a troubleshooting report.
        
        Args:
            report_format: Format of the report (text, html, json)
            issue_type: Type of issue to include in the report
            context_str: String with additional context
            
        Returns:
            Dict with report generation results
        """
        # Parse context string into a dictionary
        context = self._parse_context(context_str)
        
        # Default to text format if not specified
        report_format = report_format or "text"
        
        # If issue_type is specified, run diagnostics first
        if issue_type:
            # Set flag to generate report
            context["generate_report"] = True
            context["report_format"] = report_format
            
            # Run diagnostics with report generation
            results = self.troubleshooting_assistant.guided_diagnostics(issue_type, context)
            
            if not results.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to diagnose {issue_type} issues for report generation",
                    "results": results
                }
            
            # Extract report from results
            report_results = results.get("results", {}).get("report", {})
            
            if not report_results.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to generate {report_format} report for {issue_type} issues",
                    "results": report_results
                }
            
            return {
                "success": True,
                "message": f"Generated {report_format} report for {issue_type} issues",
                "report_file": report_results.get("report_file"),
                "results": report_results
            }
        else:
            # Get the most recent troubleshooting session
            history = self.troubleshooting_assistant.get_troubleshooting_history(limit=1)
            
            if not history:
                return {
                    "success": False,
                    "message": "No troubleshooting history found for report generation",
                    "help": "Run a diagnostic first or specify an issue type"
                }
            
            # Generate report from the most recent session
            report_results = self.troubleshooting_assistant.generate_report(history[0], report_format)
            
            if not report_results.get("success", False):
                return {
                    "success": False,
                    "message": f"Failed to generate {report_format} report from history",
                    "results": report_results
                }
            
            return {
                "success": True,
                "message": f"Generated {report_format} report from most recent troubleshooting session",
                "report_file": report_results.get("report_file"),
                "results": report_results
            }
    
    def view_troubleshooting_history(self, issue_type: str = None, limit: int = 10) -> Dict:
        """View troubleshooting history.
        
        Args:
            issue_type: Type of issue to filter by
            limit: Maximum number of history entries to return
            
        Returns:
            Dict with troubleshooting history
        """
        # Get troubleshooting history
        history = self.troubleshooting_assistant.get_troubleshooting_history(issue_type, limit)
        
        if not history:
            return {
                "success": True,
                "message": "No troubleshooting history found",
                "history": []
            }
        
        # Format history for natural language output
        message = f"Found {len(history)} troubleshooting history entries"
        if issue_type:
            message += f" for {issue_type} issues"
        message += ":\n"
        
        for i, entry in enumerate(history, 1):
            timestamp = entry.get("timestamp", "unknown")
            entry_issue_type = entry.get("issue_type", "unknown")
            
            message += f"{i}. [{timestamp}] {entry_issue_type.upper()}"
            
            if "recommendations" in entry and entry["recommendations"]:
                message += f" - {len(entry['recommendations'])} recommendations"
            
            message += "\n"
        
        return {
            "success": True,
            "message": message,
            "history": history
        }
    
    def get_help(self) -> Dict:
        """Get help information for troubleshooting commands.
        
        Returns:
            Dict with help information
        """
        help_text = """
Troubleshooting Commands:

1. Diagnostics:
   - diagnose vm <vm_id>
   - diagnose container <container_id>
   - diagnose network [interface]
   - diagnose storage [storage_id]
   - diagnose service <service_name>
   - diagnose security
   - diagnose performance

2. Log Analysis:
   - analyze logs [for vm|container|node|cluster|service] [context]
   - check logs [for vm|container|node|cluster|service] [context]

3. Network Diagnostics:
   - check network connectivity [host]
   - check network dns [domain]
   - check network ports <host> <port>
   - check network visualization

4. Performance Analysis:
   - analyze cpu performance [node]
   - analyze memory performance [node]
   - analyze disk performance [storage_id]
   - analyze network performance [interface]
   - analyze all performance [node]

5. Auto-Resolve Issues:
   - fix vm <vm_id>
   - fix container <container_id>
   - fix network [interface]
   - fix storage [storage_id]
   - fix service <service_name>
   - fix security
   - fix performance

6. Report Generation:
   - generate [text|html|json] report [for vm|container|network|storage|service|security|performance] [context]
   - create [text|html|json] report [for vm|container|network|storage|service|security|performance] [context]

7. View History:
   - show troubleshooting history [for vm|container|network|storage|service|security|performance] [limit <number>]
   - view troubleshooting history [for vm|container|network|storage|service|security|performance] [limit <number>]
"""
        
        return {
            "success": True,
            "message": help_text
        }
    
    def _parse_context(self, context_str: str) -> Dict:
        """Parse context string into a dictionary.
        
        Args:
            context_str: String with context parameters
            
        Returns:
            Dict with parsed context
        """
        context = {}
        
        if not context_str:
            return context
        
        # Parse key-value pairs
        # Format: key1=value1 key2=value2 or key1:value1 key2:value2
        for pair in re.findall(r'(\w+)[:=]([^\s]+)', context_str):
            key, value = pair
            context[key] = value
        
        # Parse VM ID, Container ID, etc.
        vm_id_match = re.search(r'vm[:\s]+(\d+)', context_str, re.IGNORECASE)
        if vm_id_match:
            context["vm_id"] = vm_id_match.group(1)
        
        container_id_match = re.search(r'container[:\s]+(\d+)', context_str, re.IGNORECASE)
        if container_id_match:
            context["container_id"] = container_id_match.group(1)
        
        node_match = re.search(r'node[:\s]+(\w+)', context_str, re.IGNORECASE)
        if node_match:
            context["node"] = node_match.group(1)
        
        storage_match = re.search(r'storage[:\s]+(\w+)', context_str, re.IGNORECASE)
        if storage_match:
            context["storage_id"] = storage_match.group(1)
        
        service_match = re.search(r'service[:\s]+(\w+)', context_str, re.IGNORECASE)
        if service_match:
            context["service_name"] = service_match.group(1)
        
        # If context_str is just a number, assume it's a VM ID
        if context_str.isdigit() and "vm_id" not in context and "container_id" not in context:
            context["vm_id"] = context_str
        
        return context
