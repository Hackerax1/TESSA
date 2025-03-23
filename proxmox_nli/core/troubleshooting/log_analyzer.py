"""
Log Analyzer for Proxmox NLI.
Provides natural language analysis of system and service logs.
"""
import logging
import re
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import subprocess

logger = logging.getLogger(__name__)

class LogAnalyzer:
    """Analyzes logs using natural language processing to identify issues and patterns."""
    
    def __init__(self, api):
        """Initialize the log analyzer.
        
        Args:
            api: Proxmox API client
        """
        self.api = api
        
        # Common error patterns to look for in logs
        self.error_patterns = {
            "authentication": [
                r"authentication failure",
                r"failed login",
                r"permission denied",
                r"unauthorized access",
                r"auth failed"
            ],
            "disk": [
                r"no space left on device",
                r"disk full",
                r"i/o error",
                r"cannot write",
                r"read-only file system"
            ],
            "memory": [
                r"out of memory",
                r"cannot allocate memory",
                r"memory exhausted",
                r"oom killer",
                r"memory allocation failed"
            ],
            "network": [
                r"network unreachable",
                r"connection refused",
                r"no route to host",
                r"timeout",
                r"connection reset"
            ],
            "service": [
                r"service failed",
                r"failed to start",
                r"exited with code",
                r"terminated",
                r"crash"
            ],
            "security": [
                r"security breach",
                r"unauthorized access",
                r"suspicious activity",
                r"potential attack",
                r"intrusion detected"
            ]
        }
        
        # Common log paths
        self.log_paths = {
            "system": "/var/log/syslog",
            "auth": "/var/log/auth.log",
            "proxmox": "/var/log/pve",
            "kernel": "/var/log/kern.log",
            "apache": "/var/log/apache2/error.log",
            "nginx": "/var/log/nginx/error.log",
            "docker": "/var/log/docker.log"
        }
    
    def analyze_logs(self, log_type: str, context: Dict = None) -> Dict:
        """Analyze logs using natural language processing.
        
        Args:
            log_type: Type of logs to analyze (system, vm, container, service)
            context: Additional context for log analysis (e.g., VM ID, service name)
            
        Returns:
            Dict with log analysis results
        """
        context = context or {}
        
        if log_type == "system":
            return self.analyze_system_logs(context)
        elif log_type == "vm":
            return self.analyze_vm_logs(context.get("vm_id"), context.get("node", "pve"))
        elif log_type == "container":
            return self.analyze_container_logs(context.get("container_id"), context.get("node", "pve"))
        elif log_type == "service":
            return self.analyze_service_logs(context.get("service_id"), context.get("vm_id"))
        else:
            return {
                "success": False,
                "message": f"Unknown log type: {log_type}",
                "recommendations": ["Please specify a valid log type: system, vm, container, service"]
            }
    
    def analyze_system_logs(self, context: Dict = None) -> Dict:
        """Analyze system logs for issues.
        
        Args:
            context: Additional context for log analysis
            
        Returns:
            Dict with log analysis results
        """
        context = context or {}
        results = {
            "success": True,
            "message": "Analyzed system logs",
            "errors": [],
            "warnings": [],
            "summary": "",
            "time_period": context.get("time_period", "24h")
        }
        
        # Determine time period for log analysis
        time_period = context.get("time_period", "24h")
        since_arg = f"--since=\"{time_period}\""
        
        try:
            # Analyze syslog
            syslog_cmd = f"journalctl -p err {since_arg} --no-pager"
            syslog_output = self._run_command(syslog_cmd)
            
            # Extract errors and warnings
            errors, warnings = self._extract_issues(syslog_output)
            results["errors"].extend(errors)
            results["warnings"].extend(warnings)
            
            # Analyze auth log
            auth_cmd = f"journalctl -p err -t auth {since_arg} --no-pager"
            auth_output = self._run_command(auth_cmd)
            
            # Extract auth errors
            auth_errors, auth_warnings = self._extract_issues(auth_output)
            results["errors"].extend(auth_errors)
            results["warnings"].extend(auth_warnings)
            
            # Analyze Proxmox logs
            proxmox_cmd = f"journalctl -p err -t pve {since_arg} --no-pager"
            proxmox_output = self._run_command(proxmox_cmd)
            
            # Extract Proxmox errors
            proxmox_errors, proxmox_warnings = self._extract_issues(proxmox_output)
            results["errors"].extend(proxmox_errors)
            results["warnings"].extend(proxmox_warnings)
            
            # Generate summary
            results["summary"] = self._generate_log_summary(results["errors"], results["warnings"])
            
            # Categorize issues
            results["categories"] = self._categorize_issues(results["errors"] + results["warnings"])
            
        except Exception as e:
            logger.error(f"Error analyzing system logs: {str(e)}")
            results["success"] = False
            results["message"] = f"Error analyzing system logs: {str(e)}"
        
        return results
    
    def analyze_vm_logs(self, vm_id: str, node: str = "pve") -> Dict:
        """Analyze VM logs for issues.
        
        Args:
            vm_id: ID of the VM to analyze logs for
            node: Node where the VM is running
            
        Returns:
            Dict with log analysis results
        """
        if not vm_id:
            return {"success": False, "message": "VM ID is required for VM log analysis"}
        
        results = {
            "success": True,
            "message": f"Analyzed logs for VM {vm_id}",
            "errors": [],
            "warnings": [],
            "summary": ""
        }
        
        try:
            # Get VM logs from Proxmox API
            vm_logs = self.api.nodes(node).qemu(vm_id).status.current.get()
            
            # Extract issues from VM logs
            # This is a simplified example - actual implementation would depend on API structure
            if "errors" in vm_logs:
                results["errors"].extend(vm_logs["errors"])
            
            if "warnings" in vm_logs:
                results["warnings"].extend(vm_logs["warnings"])
            
            # Generate summary
            results["summary"] = self._generate_log_summary(results["errors"], results["warnings"])
            
            # Categorize issues
            results["categories"] = self._categorize_issues(results["errors"] + results["warnings"])
            
        except Exception as e:
            logger.error(f"Error analyzing VM logs for VM {vm_id}: {str(e)}")
            results["success"] = False
            results["message"] = f"Error analyzing VM logs: {str(e)}"
        
        return results
    
    def analyze_container_logs(self, container_id: str, node: str = "pve") -> Dict:
        """Analyze container logs for issues.
        
        Args:
            container_id: ID of the container to analyze logs for
            node: Node where the container is running
            
        Returns:
            Dict with log analysis results
        """
        if not container_id:
            return {"success": False, "message": "Container ID is required for container log analysis"}
        
        results = {
            "success": True,
            "message": f"Analyzed logs for container {container_id}",
            "errors": [],
            "warnings": [],
            "summary": ""
        }
        
        try:
            # Get container logs from Proxmox API
            container_logs = self.api.nodes(node).lxc(container_id).status.current.get()
            
            # Extract issues from container logs
            # This is a simplified example - actual implementation would depend on API structure
            if "errors" in container_logs:
                results["errors"].extend(container_logs["errors"])
            
            if "warnings" in container_logs:
                results["warnings"].extend(container_logs["warnings"])
            
            # Generate summary
            results["summary"] = self._generate_log_summary(results["errors"], results["warnings"])
            
            # Categorize issues
            results["categories"] = self._categorize_issues(results["errors"] + results["warnings"])
            
        except Exception as e:
            logger.error(f"Error analyzing container logs for container {container_id}: {str(e)}")
            results["success"] = False
            results["message"] = f"Error analyzing container logs: {str(e)}"
        
        return results
    
    def analyze_service_logs(self, service_id: str, vm_id: str = None) -> Dict:
        """Analyze service logs for issues.
        
        Args:
            service_id: ID of the service to analyze logs for
            vm_id: ID of the VM where the service is running
            
        Returns:
            Dict with log analysis results
        """
        if not service_id:
            return {"success": False, "message": "Service ID is required for service log analysis"}
        
        results = {
            "success": True,
            "message": f"Analyzed logs for service {service_id}",
            "errors": [],
            "warnings": [],
            "summary": ""
        }
        
        try:
            # This would typically involve SSH into the VM and analyzing service logs
            # For this example, we'll simulate log analysis
            
            # Simulate getting service logs
            service_logs = [
                f"[INFO] Service {service_id} started successfully",
                f"[WARNING] Service {service_id} high memory usage detected",
                f"[ERROR] Service {service_id} connection timeout"
            ]
            
            # Extract issues from service logs
            for log in service_logs:
                if "[ERROR]" in log:
                    results["errors"].append(log)
                elif "[WARNING]" in log:
                    results["warnings"].append(log)
            
            # Generate summary
            results["summary"] = self._generate_log_summary(results["errors"], results["warnings"])
            
            # Categorize issues
            results["categories"] = self._categorize_issues(results["errors"] + results["warnings"])
            
        except Exception as e:
            logger.error(f"Error analyzing service logs for service {service_id}: {str(e)}")
            results["success"] = False
            results["message"] = f"Error analyzing service logs: {str(e)}"
        
        return results
    
    def _run_command(self, command: str) -> str:
        """Run a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command execution failed: {str(e)}")
            return e.stdout if e.stdout else ""
    
    def _extract_issues(self, log_output: str) -> Tuple[List[str], List[str]]:
        """Extract errors and warnings from log output."""
        errors = []
        warnings = []
        
        for line in log_output.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # Check for error indicators
            if any(re.search(r"error", line, re.IGNORECASE) for r in ["error", "err", "exception", "fail", "critical"]):
                errors.append(line)
            # Check for warning indicators
            elif any(re.search(r"warn", line, re.IGNORECASE) for r in ["warning", "warn"]):
                warnings.append(line)
        
        return errors, warnings
    
    def _categorize_issues(self, issues: List[str]) -> Dict[str, List[str]]:
        """Categorize issues based on predefined patterns."""
        categories = {category: [] for category in self.error_patterns.keys()}
        
        for issue in issues:
            for category, patterns in self.error_patterns.items():
                if any(re.search(pattern, issue, re.IGNORECASE) for pattern in patterns):
                    categories[category].append(issue)
                    break
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _generate_log_summary(self, errors: List[str], warnings: List[str]) -> str:
        """Generate a natural language summary of log analysis."""
        if not errors and not warnings:
            return "No issues found in the logs. The system appears to be functioning normally."
        
        summary_parts = []
        
        if errors:
            summary_parts.append(f"Found {len(errors)} errors in the logs.")
            
            # Add details about the most recent errors (up to 3)
            if len(errors) > 0:
                summary_parts.append("Most recent errors:")
                for i, error in enumerate(errors[:3]):
                    summary_parts.append(f"  {i+1}. {error}")
        
        if warnings:
            summary_parts.append(f"Found {len(warnings)} warnings in the logs.")
            
            # Add details about the most recent warnings (up to 3)
            if len(warnings) > 0:
                summary_parts.append("Most recent warnings:")
                for i, warning in enumerate(warnings[:3]):
                    summary_parts.append(f"  {i+1}. {warning}")
        
        return "\n".join(summary_parts)
