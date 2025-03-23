"""
Security Manager for Proxmox NLI.
Provides natural language interfaces for security management.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from ..network.firewall_manager import FirewallManager

logger = logging.getLogger(__name__)

class SecurityManager:
    """Central manager for security-related functionality with natural language interfaces"""
    
    def __init__(self, api, base_nli=None):
        """Initialize the security manager
        
        Args:
            api: Proxmox API client
            base_nli: Base NLI instance for accessing other components
        """
        self.api = api
        self.base_nli = base_nli
        self.firewall_manager = FirewallManager(api)
        self.audit_logs = []
        
    def run_security_audit(self, scope: str = "full") -> Dict[str, Any]:
        """Run a security audit and generate a report
        
        Args:
            scope: Audit scope (full, firewall, permissions, certificates, updates)
            
        Returns:
            Dictionary with audit results
        """
        audit_results = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "findings": [],
            "risk_level": "low",
            "summary": "",
            "recommendations": []
        }
        
        # Check firewall status
        if scope in ["full", "firewall"]:
            firewall_status = self.firewall_manager.get_firewall_status()
            if firewall_status.get("success", False):
                enabled = firewall_status.get("data", {}).get("enable") == 1
                if not enabled:
                    audit_results["findings"].append({
                        "severity": "high",
                        "component": "firewall",
                        "finding": "Firewall is disabled",
                        "recommendation": "Enable the firewall to protect your system"
                    })
                    audit_results["risk_level"] = "high"
            
            # Check firewall rules
            rules = self.firewall_manager.list_rules()
            if rules.get("success", False):
                rule_count = len(rules.get("data", []))
                if rule_count == 0:
                    audit_results["findings"].append({
                        "severity": "medium",
                        "component": "firewall",
                        "finding": "No firewall rules defined",
                        "recommendation": "Add basic firewall rules to secure your system"
                    })
                    if audit_results["risk_level"] != "high":
                        audit_results["risk_level"] = "medium"
        
        # Generate summary based on findings
        finding_count = len(audit_results["findings"])
        if finding_count == 0:
            audit_results["summary"] = "No security issues found in the audited components."
        else:
            high_count = sum(1 for f in audit_results["findings"] if f["severity"] == "high")
            medium_count = sum(1 for f in audit_results["findings"] if f["severity"] == "medium")
            low_count = sum(1 for f in audit_results["findings"] if f["severity"] == "low")
            
            audit_results["summary"] = f"Found {finding_count} security issues: {high_count} high, {medium_count} medium, and {low_count} low severity."
            
            # Add overall recommendations
            if high_count > 0:
                audit_results["recommendations"].append("Address high severity findings immediately to secure your system")
            if medium_count > 0:
                audit_results["recommendations"].append("Review and address medium severity findings as part of your security maintenance")
            if low_count > 0:
                audit_results["recommendations"].append("Consider addressing low severity findings to improve your security posture")
        
        # Log the audit
        self._log_audit_event("security_audit", {
            "scope": scope,
            "risk_level": audit_results["risk_level"],
            "finding_count": finding_count
        })
        
        return audit_results
    
    def interpret_permission_command(self, command: str) -> Dict[str, Any]:
        """Interpret a natural language permission command
        
        Args:
            command: Natural language command for permission management
            
        Returns:
            Dictionary with interpreted command and parameters
        """
        # Extract user, role, and permission information from the command
        user_match = re.search(r"user[s]?\s+([a-zA-Z0-9_]+)", command, re.IGNORECASE)
        role_match = re.search(r"role[s]?\s+([a-zA-Z0-9_]+)", command, re.IGNORECASE)
        permission_match = re.search(r"permission[s]?\s+([a-zA-Z0-9_.]+)", command, re.IGNORECASE)
        
        # Determine the action (add, remove, list)
        action = None
        if re.search(r"add|grant|give", command, re.IGNORECASE):
            action = "add"
        elif re.search(r"remove|revoke|take", command, re.IGNORECASE):
            action = "remove"
        elif re.search(r"list|show|display", command, re.IGNORECASE):
            action = "list"
        
        # Extract parameters based on the matches
        params = {}
        if user_match:
            params["user"] = user_match.group(1)
        if role_match:
            params["role"] = role_match.group(1)
        if permission_match:
            params["permission"] = permission_match.group(1)
        
        return {
            "action": action,
            "params": params,
            "original_command": command
        }
    
    def interpret_firewall_command(self, command: str) -> Dict[str, Any]:
        """Interpret a natural language firewall command
        
        Args:
            command: Natural language command for firewall management
            
        Returns:
            Dictionary with interpreted command and parameters
        """
        # Extract port, protocol, and service information
        port_match = re.search(r"port[s]?\s+(\d+(?:-\d+)?)", command, re.IGNORECASE)
        protocol_match = re.search(r"protocol\s+(tcp|udp|icmp)", command, re.IGNORECASE)
        service_match = re.search(r"service\s+([a-zA-Z0-9_-]+)", command, re.IGNORECASE)
        source_match = re.search(r"from\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?)", command, re.IGNORECASE)
        
        # Determine the action
        action = None
        if re.search(r"allow|open|enable", command, re.IGNORECASE):
            action = "allow"
        elif re.search(r"block|deny|disable", command, re.IGNORECASE):
            action = "deny"
        elif re.search(r"list|show|display", command, re.IGNORECASE):
            action = "list"
        elif re.search(r"delete|remove", command, re.IGNORECASE):
            action = "delete"
        
        # Extract parameters
        params = {}
        if port_match:
            params["port"] = port_match.group(1)
        if protocol_match:
            params["protocol"] = protocol_match.group(1).lower()
        if service_match:
            params["service"] = service_match.group(1)
        if source_match:
            params["source"] = source_match.group(1)
        
        return {
            "action": action,
            "params": params,
            "original_command": command
        }
    
    def _log_audit_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log an audit event
        
        Args:
            event_type: Type of event
            details: Event details
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        self.audit_logs.append(event)
        logger.info(f"Security audit event: {event_type} - {details}")
        
        # If base_nli has an audit logger, use it
        if self.base_nli and hasattr(self.base_nli, "audit_logger"):
            self.base_nli.audit_logger.log_action(
                "system", 
                f"security_{event_type}", 
                details
            )
