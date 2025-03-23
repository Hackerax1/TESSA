"""
Security Auditor for Proxmox NLI.
Provides security auditing and reporting functionality.
"""
import logging
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Performs security audits and generates reports"""
    
    def __init__(self, api, base_nli=None):
        """Initialize the security auditor
        
        Args:
            api: Proxmox API client
            base_nli: Base NLI instance for accessing other components
        """
        self.api = api
        self.base_nli = base_nli
        self.audit_history = []
        self.audit_storage_path = os.path.join(os.path.dirname(__file__), "audit_history")
        
        # Create audit storage directory if it doesn't exist
        os.makedirs(self.audit_storage_path, exist_ok=True)
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run a comprehensive security audit
        
        Returns:
            Dictionary with audit results
        """
        audit_result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "overall_score": 0,
            "risk_level": "unknown",
            "findings": [],
            "recommendations": []
        }
        
        # Audit system updates
        update_audit = self._audit_system_updates()
        audit_result["components"]["updates"] = update_audit
        audit_result["findings"].extend(update_audit.get("findings", []))
        
        # Audit firewall
        firewall_audit = self._audit_firewall()
        audit_result["components"]["firewall"] = firewall_audit
        audit_result["findings"].extend(firewall_audit.get("findings", []))
        
        # Audit user permissions
        permissions_audit = self._audit_permissions()
        audit_result["components"]["permissions"] = permissions_audit
        audit_result["findings"].extend(permissions_audit.get("findings", []))
        
        # Audit SSL certificates
        certificates_audit = self._audit_certificates()
        audit_result["components"]["certificates"] = certificates_audit
        audit_result["findings"].extend(certificates_audit.get("findings", []))
        
        # Calculate overall score and risk level
        component_scores = [
            update_audit.get("score", 0),
            firewall_audit.get("score", 0),
            permissions_audit.get("score", 0),
            certificates_audit.get("score", 0)
        ]
        
        if component_scores:
            audit_result["overall_score"] = sum(component_scores) / len(component_scores)
            
            # Determine risk level based on score
            if audit_result["overall_score"] >= 90:
                audit_result["risk_level"] = "low"
            elif audit_result["overall_score"] >= 70:
                audit_result["risk_level"] = "medium"
            else:
                audit_result["risk_level"] = "high"
        
        # Generate recommendations based on findings
        audit_result["recommendations"] = self._generate_recommendations(audit_result["findings"])
        
        # Save audit result to history
        self._save_audit_result(audit_result)
        
        return audit_result
    
    def _audit_system_updates(self) -> Dict[str, Any]:
        """Audit system updates
        
        Returns:
            Dictionary with update audit results
        """
        audit_result = {
            "score": 0,
            "findings": []
        }
        
        try:
            # Get available updates
            if self.base_nli and hasattr(self.base_nli, "update_manager"):
                updates = self.base_nli.update_manager.get_available_updates()
                
                if updates.get("success", False):
                    security_updates = [u for u in updates.get("updates", []) 
                                      if u.get("priority") == "security"]
                    
                    if security_updates:
                        audit_result["findings"].append({
                            "severity": "high",
                            "component": "updates",
                            "finding": f"Found {len(security_updates)} pending security updates",
                            "recommendation": "Apply security updates immediately"
                        })
                        audit_result["score"] = max(0, 100 - (len(security_updates) * 10))
                    else:
                        regular_updates = updates.get("updates", [])
                        if regular_updates:
                            audit_result["findings"].append({
                                "severity": "low",
                                "component": "updates",
                                "finding": f"Found {len(regular_updates)} pending regular updates",
                                "recommendation": "Apply regular updates during maintenance window"
                            })
                            audit_result["score"] = max(0, 100 - (len(regular_updates) * 2))
                        else:
                            audit_result["score"] = 100
            else:
                # Fallback to API if update_manager is not available
                apt_update = self.api.api_request('GET', 'nodes/localhost/apt/update')
                if apt_update.get("success", False):
                    updates = apt_update.get("data", [])
                    security_updates = [u for u in updates if "security" in u.get("description", "").lower()]
                    
                    if security_updates:
                        audit_result["findings"].append({
                            "severity": "high",
                            "component": "updates",
                            "finding": f"Found {len(security_updates)} pending security updates",
                            "recommendation": "Apply security updates immediately"
                        })
                        audit_result["score"] = max(0, 100 - (len(security_updates) * 10))
                    else:
                        if updates:
                            audit_result["findings"].append({
                                "severity": "low",
                                "component": "updates",
                                "finding": f"Found {len(updates)} pending regular updates",
                                "recommendation": "Apply regular updates during maintenance window"
                            })
                            audit_result["score"] = max(0, 100 - (len(updates) * 2))
                        else:
                            audit_result["score"] = 100
        except Exception as e:
            logger.error(f"Error auditing system updates: {str(e)}")
            audit_result["findings"].append({
                "severity": "medium",
                "component": "updates",
                "finding": f"Error checking system updates: {str(e)}",
                "recommendation": "Investigate update system functionality"
            })
            audit_result["score"] = 50
        
        return audit_result
    
    def _audit_firewall(self) -> Dict[str, Any]:
        """Audit firewall configuration
        
        Returns:
            Dictionary with firewall audit results
        """
        audit_result = {
            "score": 0,
            "findings": []
        }
        
        try:
            # Check if firewall is enabled
            firewall_manager = None
            if self.base_nli and hasattr(self.base_nli, "firewall_manager"):
                firewall_manager = self.base_nli.firewall_manager
            else:
                # Import here to avoid circular imports
                from ..network.firewall_manager import FirewallManager
                firewall_manager = FirewallManager(self.api)
            
            firewall_status = firewall_manager.get_firewall_status()
            
            if firewall_status.get("success", False):
                enabled = firewall_status.get("data", {}).get("enable") == 1
                
                if not enabled:
                    audit_result["findings"].append({
                        "severity": "high",
                        "component": "firewall",
                        "finding": "Firewall is disabled",
                        "recommendation": "Enable the firewall to protect your system"
                    })
                    audit_result["score"] = 0
                else:
                    # Check firewall rules
                    rules = firewall_manager.list_rules()
                    
                    if rules.get("success", False):
                        rule_count = len(rules.get("data", []))
                        
                        if rule_count == 0:
                            audit_result["findings"].append({
                                "severity": "high",
                                "component": "firewall",
                                "finding": "No firewall rules defined",
                                "recommendation": "Add basic firewall rules to secure your system"
                            })
                            audit_result["score"] = 20
                        else:
                            # Check for default deny policy
                            has_default_deny = False
                            for rule in rules.get("data", []):
                                if rule.get("action") == "DROP" and rule.get("type") == "in":
                                    has_default_deny = True
                                    break
                            
                            if not has_default_deny:
                                audit_result["findings"].append({
                                    "severity": "medium",
                                    "component": "firewall",
                                    "finding": "No default deny rule found",
                                    "recommendation": "Add a default deny rule to block unauthorized access"
                                })
                                audit_result["score"] = 60
                            else:
                                audit_result["score"] = 100
            else:
                audit_result["findings"].append({
                    "severity": "medium",
                    "component": "firewall",
                    "finding": "Could not determine firewall status",
                    "recommendation": "Check firewall configuration"
                })
                audit_result["score"] = 50
        except Exception as e:
            logger.error(f"Error auditing firewall: {str(e)}")
            audit_result["findings"].append({
                "severity": "medium",
                "component": "firewall",
                "finding": f"Error checking firewall: {str(e)}",
                "recommendation": "Investigate firewall functionality"
            })
            audit_result["score"] = 50
        
        return audit_result
    
    def _audit_permissions(self) -> Dict[str, Any]:
        """Audit user permissions
        
        Returns:
            Dictionary with permissions audit results
        """
        audit_result = {
            "score": 0,
            "findings": []
        }
        
        try:
            # Get users
            users = self.api.api_request('GET', 'access/users')
            
            if users.get("success", False):
                user_count = len(users.get("data", []))
                admin_count = 0
                
                for user in users.get("data", []):
                    # Check if user is an admin
                    user_id = user.get("userid")
                    if user_id:
                        user_permissions = self.api.api_request('GET', f'access/permissions?path=/&userid={user_id}')
                        
                        if user_permissions.get("success", False):
                            for perm in user_permissions.get("data", []):
                                if perm.get("roleid") == "Administrator":
                                    admin_count += 1
                                    break
                
                if admin_count > 1:
                    audit_result["findings"].append({
                        "severity": "medium",
                        "component": "permissions",
                        "finding": f"Found {admin_count} users with administrator privileges",
                        "recommendation": "Limit administrator access to necessary users only"
                    })
                    audit_result["score"] = max(0, 100 - (admin_count * 10))
                else:
                    audit_result["score"] = 100
            else:
                audit_result["findings"].append({
                    "severity": "medium",
                    "component": "permissions",
                    "finding": "Could not retrieve user permissions",
                    "recommendation": "Check access to user management API"
                })
                audit_result["score"] = 50
        except Exception as e:
            logger.error(f"Error auditing permissions: {str(e)}")
            audit_result["findings"].append({
                "severity": "medium",
                "component": "permissions",
                "finding": f"Error checking permissions: {str(e)}",
                "recommendation": "Investigate permission management functionality"
            })
            audit_result["score"] = 50
        
        return audit_result
    
    def _audit_certificates(self) -> Dict[str, Any]:
        """Audit SSL certificates
        
        Returns:
            Dictionary with certificate audit results
        """
        audit_result = {
            "score": 0,
            "findings": []
        }
        
        try:
            # Check if certificate_manager is available
            if self.base_nli and hasattr(self.base_nli, "certificate_manager"):
                cert_manager = self.base_nli.certificate_manager
                certificates = cert_manager.list_certificates()
            else:
                # Import here to avoid circular imports
                from .certificate_manager import CertificateManager
                cert_manager = CertificateManager(self.api)
                certificates = cert_manager.list_certificates()
            
            if certificates.get("success", False):
                cert_list = certificates.get("certificates", [])
                
                expired = [c for c in cert_list if c.get("status") == "expired"]
                expiring_soon = [c for c in cert_list if c.get("status") == "expiring_soon"]
                
                if expired:
                    audit_result["findings"].append({
                        "severity": "high",
                        "component": "certificates",
                        "finding": f"Found {len(expired)} expired certificates",
                        "recommendation": "Renew expired certificates immediately"
                    })
                    audit_result["score"] = max(0, 100 - (len(expired) * 20))
                elif expiring_soon:
                    audit_result["findings"].append({
                        "severity": "medium",
                        "component": "certificates",
                        "finding": f"Found {len(expiring_soon)} certificates expiring soon",
                        "recommendation": "Plan to renew these certificates before they expire"
                    })
                    audit_result["score"] = max(0, 100 - (len(expiring_soon) * 5))
                else:
                    if not cert_list:
                        audit_result["findings"].append({
                            "severity": "low",
                            "component": "certificates",
                            "finding": "No SSL certificates found",
                            "recommendation": "Consider adding SSL certificates for secure communication"
                        })
                        audit_result["score"] = 70
                    else:
                        audit_result["score"] = 100
            else:
                audit_result["findings"].append({
                    "severity": "medium",
                    "component": "certificates",
                    "finding": "Could not retrieve certificate information",
                    "recommendation": "Check certificate management functionality"
                })
                audit_result["score"] = 50
        except Exception as e:
            logger.error(f"Error auditing certificates: {str(e)}")
            audit_result["findings"].append({
                "severity": "medium",
                "component": "certificates",
                "finding": f"Error checking certificates: {str(e)}",
                "recommendation": "Investigate certificate management functionality"
            })
            audit_result["score"] = 50
        
        return audit_result
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on findings
        
        Args:
            findings: List of findings from the audit
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Group findings by severity
        high_severity = [f for f in findings if f.get("severity") == "high"]
        medium_severity = [f for f in findings if f.get("severity") == "medium"]
        low_severity = [f for f in findings if f.get("severity") == "low"]
        
        # Add recommendations based on severity
        if high_severity:
            recommendations.append("Address the following high-severity issues immediately:")
            for finding in high_severity:
                recommendations.append(f"- {finding.get('recommendation')}")
        
        if medium_severity:
            recommendations.append("Address the following medium-severity issues soon:")
            for finding in medium_severity:
                recommendations.append(f"- {finding.get('recommendation')}")
        
        if low_severity:
            recommendations.append("Consider addressing these low-severity issues:")
            for finding in low_severity:
                recommendations.append(f"- {finding.get('recommendation')}")
        
        if not findings:
            recommendations.append("Your system appears to be well-secured. Continue to monitor for new security updates and vulnerabilities.")
        
        return recommendations
    
    def _save_audit_result(self, audit_result: Dict[str, Any]) -> None:
        """Save audit result to history
        
        Args:
            audit_result: Audit result to save
        """
        try:
            # Generate filename based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_{timestamp}.json"
            filepath = os.path.join(self.audit_storage_path, filename)
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(audit_result, f, indent=2)
            
            # Add to history
            self.audit_history.append({
                "timestamp": audit_result["timestamp"],
                "risk_level": audit_result["risk_level"],
                "overall_score": audit_result["overall_score"],
                "finding_count": len(audit_result["findings"]),
                "filename": filename
            })
            
            # Trim history to last 10 audits
            if len(self.audit_history) > 10:
                self.audit_history = self.audit_history[-10:]
                
            logger.info(f"Saved audit result to {filepath}")
        except Exception as e:
            logger.error(f"Error saving audit result: {str(e)}")
    
    def get_audit_history(self, limit: int = 5) -> Dict[str, Any]:
        """Get audit history
        
        Args:
            limit: Maximum number of audit results to return
            
        Returns:
            Dictionary with audit history
        """
        try:
            # Load audit files if history is empty
            if not self.audit_history:
                self._load_audit_history()
            
            # Sort by timestamp (newest first)
            sorted_history = sorted(self.audit_history, 
                                   key=lambda x: x.get("timestamp", ""), 
                                   reverse=True)
            
            return {
                "success": True,
                "history": sorted_history[:limit],
                "count": len(sorted_history)
            }
        except Exception as e:
            logger.error(f"Error getting audit history: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting audit history: {str(e)}",
                "history": []
            }
    
    def _load_audit_history(self) -> None:
        """Load audit history from files"""
        try:
            # Get all audit files
            files = [f for f in os.listdir(self.audit_storage_path) 
                    if f.startswith("audit_") and f.endswith(".json")]
            
            history = []
            for filename in files:
                filepath = os.path.join(self.audit_storage_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        audit_data = json.load(f)
                        history.append({
                            "timestamp": audit_data.get("timestamp"),
                            "risk_level": audit_data.get("risk_level"),
                            "overall_score": audit_data.get("overall_score"),
                            "finding_count": len(audit_data.get("findings", [])),
                            "filename": filename
                        })
                except Exception as e:
                    logger.error(f"Error loading audit file {filename}: {str(e)}")
            
            self.audit_history = history
        except Exception as e:
            logger.error(f"Error loading audit history: {str(e)}")
            self.audit_history = []
    
    def interpret_audit_command(self, command: str) -> Dict[str, Any]:
        """Interpret a natural language audit command
        
        Args:
            command: Natural language command for security audit
            
        Returns:
            Dictionary with interpreted command and parameters
        """
        # Determine the action
        action = None
        if re.search(r"run|perform|execute|start", command, re.IGNORECASE):
            action = "run"
        elif re.search(r"list|show|display|history", command, re.IGNORECASE):
            action = "history"
        elif re.search(r"compare|diff", command, re.IGNORECASE):
            action = "compare"
        
        # Extract parameters
        params = {}
        
        # Extract scope
        scope_match = re.search(r"(firewall|updates|certificates|permissions)", command, re.IGNORECASE)
        if scope_match:
            params["scope"] = scope_match.group(1).lower()
        
        # Extract limit for history
        limit_match = re.search(r"last\s+(\d+)", command, re.IGNORECASE)
        if limit_match:
            try:
                params["limit"] = int(limit_match.group(1))
            except ValueError:
                pass
        
        return {
            "action": action,
            "params": params,
            "original_command": command
        }
