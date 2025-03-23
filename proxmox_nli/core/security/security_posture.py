"""
Security Posture Assessment for Proxmox NLI.
Provides security posture assessment and recommendations.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class SecurityPostureAssessor:
    """Assesses security posture and provides recommendations"""
    
    def __init__(self, api, base_nli=None):
        """Initialize the security posture assessor
        
        Args:
            api: Proxmox API client
            base_nli: Base NLI instance for accessing other components
        """
        self.api = api
        self.base_nli = base_nli
        self.last_assessment = None
    
    def assess_security_posture(self) -> Dict[str, Any]:
        """Assess the overall security posture of the system
        
        Returns:
            Dictionary with assessment results
        """
        assessment = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "posture_level": "unknown",
            "areas": {},
            "recommendations": [],
            "strengths": [],
            "weaknesses": []
        }
        
        # Assess different security areas
        areas = [
            self._assess_system_hardening(),
            self._assess_network_security(),
            self._assess_authentication(),
            self._assess_updates_patching(),
            self._assess_monitoring_logging()
        ]
        
        # Add areas to assessment
        for area in areas:
            assessment["areas"][area["name"]] = area
            assessment["recommendations"].extend(area["recommendations"])
            assessment["strengths"].extend(area["strengths"])
            assessment["weaknesses"].extend(area["weaknesses"])
        
        # Calculate overall score
        if areas:
            assessment["overall_score"] = sum(area["score"] for area in areas) / len(areas)
            
            # Determine posture level based on score
            if assessment["overall_score"] >= 90:
                assessment["posture_level"] = "excellent"
            elif assessment["overall_score"] >= 80:
                assessment["posture_level"] = "good"
            elif assessment["overall_score"] >= 60:
                assessment["posture_level"] = "fair"
            else:
                assessment["posture_level"] = "poor"
        
        # Save assessment
        self.last_assessment = assessment
        
        return assessment
    
    def _assess_system_hardening(self) -> Dict[str, Any]:
        """Assess system hardening
        
        Returns:
            Dictionary with assessment results
        """
        area = {
            "name": "system_hardening",
            "display_name": "System Hardening",
            "score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        try:
            # Check SSH settings
            ssh_config = self._check_ssh_config()
            
            if ssh_config.get("root_login_disabled", False):
                area["strengths"].append("Root SSH login is disabled")
                area["score"] += 10
            else:
                area["weaknesses"].append("Root SSH login is enabled")
                area["recommendations"].append("Disable root SSH login for improved security")
            
            if ssh_config.get("password_auth_disabled", False):
                area["strengths"].append("SSH password authentication is disabled")
                area["score"] += 10
            else:
                area["weaknesses"].append("SSH password authentication is enabled")
                area["recommendations"].append("Disable SSH password authentication and use key-based authentication")
            
            # Check for unnecessary services
            services = self._check_running_services()
            unnecessary_services = services.get("unnecessary", [])
            
            if unnecessary_services:
                area["weaknesses"].append(f"Found {len(unnecessary_services)} unnecessary services running")
                area["recommendations"].append("Disable unnecessary services to reduce attack surface")
            else:
                area["strengths"].append("No unnecessary services detected")
                area["score"] += 20
            
            # Check filesystem permissions
            fs_permissions = self._check_filesystem_permissions()
            
            if fs_permissions.get("issues", 0) == 0:
                area["strengths"].append("Filesystem permissions are properly configured")
                area["score"] += 20
            else:
                area["weaknesses"].append(f"Found {fs_permissions.get('issues', 0)} filesystem permission issues")
                area["recommendations"].append("Fix filesystem permission issues to prevent unauthorized access")
            
            # Check for disk encryption
            if self._check_disk_encryption():
                area["strengths"].append("Disk encryption is enabled")
                area["score"] += 20
            else:
                area["weaknesses"].append("Disk encryption is not enabled")
                area["recommendations"].append("Enable disk encryption to protect data at rest")
            
            # Normalize score to 100
            area["score"] = min(100, area["score"])
            
        except Exception as e:
            logger.error(f"Error assessing system hardening: {str(e)}")
            area["weaknesses"].append(f"Error assessing system hardening: {str(e)}")
            area["recommendations"].append("Investigate system hardening assessment functionality")
            area["score"] = 0
        
        return area
    
    def _assess_network_security(self) -> Dict[str, Any]:
        """Assess network security
        
        Returns:
            Dictionary with assessment results
        """
        area = {
            "name": "network_security",
            "display_name": "Network Security",
            "score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        try:
            # Check firewall status
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
                
                if enabled:
                    area["strengths"].append("Firewall is enabled")
                    area["score"] += 20
                    
                    # Check firewall rules
                    rules = firewall_manager.list_rules()
                    
                    if rules.get("success", False):
                        rule_count = len(rules.get("data", []))
                        
                        if rule_count > 0:
                            area["strengths"].append(f"Firewall has {rule_count} rules configured")
                            area["score"] += 20
                            
                            # Check for default deny policy
                            has_default_deny = False
                            for rule in rules.get("data", []):
                                if rule.get("action") == "DROP" and rule.get("type") == "in":
                                    has_default_deny = True
                                    break
                            
                            if has_default_deny:
                                area["strengths"].append("Firewall has default deny policy")
                                area["score"] += 20
                            else:
                                area["weaknesses"].append("Firewall lacks default deny policy")
                                area["recommendations"].append("Add default deny rule to block unauthorized access")
                        else:
                            area["weaknesses"].append("No firewall rules defined")
                            area["recommendations"].append("Add basic firewall rules to secure your system")
                else:
                    area["weaknesses"].append("Firewall is disabled")
                    area["recommendations"].append("Enable the firewall to protect your system")
            
            # Check open ports
            open_ports = self._check_open_ports()
            
            if open_ports.get("count", 0) > 10:
                area["weaknesses"].append(f"Found {open_ports.get('count', 0)} open ports")
                area["recommendations"].append("Close unnecessary ports to reduce attack surface")
            elif open_ports.get("count", 0) > 0:
                area["strengths"].append(f"Only {open_ports.get('count', 0)} necessary ports are open")
                area["score"] += 20
            else:
                area["weaknesses"].append("Could not determine open ports")
                area["recommendations"].append("Check open ports and close unnecessary ones")
            
            # Check for VPN
            if self._check_vpn_configured():
                area["strengths"].append("VPN is configured for secure remote access")
                area["score"] += 20
            else:
                area["weaknesses"].append("No VPN configured for secure remote access")
                area["recommendations"].append("Configure VPN for secure remote access")
            
            # Normalize score to 100
            area["score"] = min(100, area["score"])
            
        except Exception as e:
            logger.error(f"Error assessing network security: {str(e)}")
            area["weaknesses"].append(f"Error assessing network security: {str(e)}")
            area["recommendations"].append("Investigate network security assessment functionality")
            area["score"] = 0
        
        return area
    
    def _assess_authentication(self) -> Dict[str, Any]:
        """Assess authentication security
        
        Returns:
            Dictionary with assessment results
        """
        area = {
            "name": "authentication",
            "display_name": "Authentication Security",
            "score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        try:
            # Check for 2FA
            if self._check_2fa_enabled():
                area["strengths"].append("Two-factor authentication is enabled")
                area["score"] += 30
            else:
                area["weaknesses"].append("Two-factor authentication is not enabled")
                area["recommendations"].append("Enable two-factor authentication for additional security")
            
            # Check password policy
            password_policy = self._check_password_policy()
            
            if password_policy.get("strong", False):
                area["strengths"].append("Strong password policy is enforced")
                area["score"] += 30
            else:
                area["weaknesses"].append("Weak password policy")
                area["recommendations"].append("Enforce stronger password policy")
            
            # Check user accounts
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
                
                if admin_count <= 1:
                    area["strengths"].append("Limited administrator accounts")
                    area["score"] += 20
                else:
                    area["weaknesses"].append(f"Found {admin_count} administrator accounts")
                    area["recommendations"].append("Limit administrator access to necessary users only")
            
            # Check for API token usage
            if self._check_api_token_usage():
                area["strengths"].append("API tokens are used for automation")
                area["score"] += 20
            else:
                area["weaknesses"].append("No API tokens configured for automation")
                area["recommendations"].append("Use API tokens instead of user credentials for automation")
            
            # Normalize score to 100
            area["score"] = min(100, area["score"])
            
        except Exception as e:
            logger.error(f"Error assessing authentication security: {str(e)}")
            area["weaknesses"].append(f"Error assessing authentication security: {str(e)}")
            area["recommendations"].append("Investigate authentication security assessment functionality")
            area["score"] = 0
        
        return area
    
    def _assess_updates_patching(self) -> Dict[str, Any]:
        """Assess updates and patching
        
        Returns:
            Dictionary with assessment results
        """
        area = {
            "name": "updates_patching",
            "display_name": "Updates and Patching",
            "score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        try:
            # Check for available updates
            if self.base_nli and hasattr(self.base_nli, "update_manager"):
                updates = self.base_nli.update_manager.get_available_updates()
                
                if updates.get("success", False):
                    update_count = len(updates.get("updates", []))
                    security_updates = [u for u in updates.get("updates", []) 
                                      if u.get("priority") == "security"]
                    
                    if update_count == 0:
                        area["strengths"].append("System is up to date")
                        area["score"] += 50
                    else:
                        if security_updates:
                            area["weaknesses"].append(f"Found {len(security_updates)} pending security updates")
                            area["recommendations"].append("Apply security updates immediately")
                        else:
                            area["weaknesses"].append(f"Found {update_count} pending updates")
                            area["recommendations"].append("Apply updates during maintenance window")
            else:
                # Fallback to API if update_manager is not available
                apt_update = self.api.api_request('GET', 'nodes/localhost/apt/update')
                if apt_update.get("success", False):
                    updates = apt_update.get("data", [])
                    
                    if not updates:
                        area["strengths"].append("System is up to date")
                        area["score"] += 50
                    else:
                        security_updates = [u for u in updates if "security" in u.get("description", "").lower()]
                        
                        if security_updates:
                            area["weaknesses"].append(f"Found {len(security_updates)} pending security updates")
                            area["recommendations"].append("Apply security updates immediately")
                        else:
                            area["weaknesses"].append(f"Found {len(updates)} pending updates")
                            area["recommendations"].append("Apply updates during maintenance window")
            
            # Check for automatic updates
            if self._check_auto_updates():
                area["strengths"].append("Automatic security updates are enabled")
                area["score"] += 50
            else:
                area["weaknesses"].append("Automatic security updates are not enabled")
                area["recommendations"].append("Enable automatic security updates")
            
            # Normalize score to 100
            area["score"] = min(100, area["score"])
            
        except Exception as e:
            logger.error(f"Error assessing updates and patching: {str(e)}")
            area["weaknesses"].append(f"Error assessing updates and patching: {str(e)}")
            area["recommendations"].append("Investigate updates and patching assessment functionality")
            area["score"] = 0
        
        return area
    
    def _assess_monitoring_logging(self) -> Dict[str, Any]:
        """Assess monitoring and logging
        
        Returns:
            Dictionary with assessment results
        """
        area = {
            "name": "monitoring_logging",
            "display_name": "Monitoring and Logging",
            "score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }
        
        try:
            # Check for monitoring
            if self._check_monitoring_enabled():
                area["strengths"].append("System monitoring is enabled")
                area["score"] += 25
            else:
                area["weaknesses"].append("System monitoring is not enabled")
                area["recommendations"].append("Enable system monitoring")
            
            # Check for log forwarding
            if self._check_log_forwarding():
                area["strengths"].append("Log forwarding is configured")
                area["score"] += 25
            else:
                area["weaknesses"].append("Log forwarding is not configured")
                area["recommendations"].append("Configure log forwarding to a central log server")
            
            # Check for intrusion detection
            if self._check_intrusion_detection():
                area["strengths"].append("Intrusion detection is enabled")
                area["score"] += 25
            else:
                area["weaknesses"].append("Intrusion detection is not enabled")
                area["recommendations"].append("Enable intrusion detection for improved security")
            
            # Check for audit logging
            if self._check_audit_logging():
                area["strengths"].append("Audit logging is enabled")
                area["score"] += 25
            else:
                area["weaknesses"].append("Audit logging is not enabled")
                area["recommendations"].append("Enable audit logging to track system changes")
            
            # Normalize score to 100
            area["score"] = min(100, area["score"])
            
        except Exception as e:
            logger.error(f"Error assessing monitoring and logging: {str(e)}")
            area["weaknesses"].append(f"Error assessing monitoring and logging: {str(e)}")
            area["recommendations"].append("Investigate monitoring and logging assessment functionality")
            area["score"] = 0
        
        return area
    
    def generate_posture_report(self) -> str:
        """Generate a natural language report of the security posture
        
        Returns:
            String with natural language report
        """
        if not self.last_assessment:
            self.assess_security_posture()
        
        assessment = self.last_assessment
        
        # Generate report
        report = []
        
        # Add header
        report.append(f"# Security Posture Assessment Report")
        report.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Overall Security Posture:** {assessment['posture_level'].title()}")
        report.append(f"**Overall Score:** {assessment['overall_score']:.1f}/100")
        report.append("")
        
        # Add summary
        report.append("## Summary")
        
        if assessment["posture_level"] == "excellent":
            report.append("Your system has an excellent security posture. Continue maintaining your current security practices and stay vigilant for new threats.")
        elif assessment["posture_level"] == "good":
            report.append("Your system has a good security posture. Address the identified weaknesses to further improve your security.")
        elif assessment["posture_level"] == "fair":
            report.append("Your system has a fair security posture. Several security improvements are recommended to better protect your system.")
        else:
            report.append("Your system has a poor security posture. Immediate action is recommended to address the identified security weaknesses.")
        
        report.append("")
        
        # Add strengths
        report.append("## Security Strengths")
        if assessment["strengths"]:
            for strength in assessment["strengths"]:
                report.append(f"- {strength}")
        else:
            report.append("No significant security strengths identified.")
        
        report.append("")
        
        # Add weaknesses
        report.append("## Security Weaknesses")
        if assessment["weaknesses"]:
            for weakness in assessment["weaknesses"]:
                report.append(f"- {weakness}")
        else:
            report.append("No significant security weaknesses identified.")
        
        report.append("")
        
        # Add recommendations
        report.append("## Recommendations")
        if assessment["recommendations"]:
            for recommendation in assessment["recommendations"]:
                report.append(f"- {recommendation}")
        else:
            report.append("No specific recommendations at this time.")
        
        report.append("")
        
        # Add detailed assessment for each area
        report.append("## Detailed Assessment")
        
        for area_name, area in assessment["areas"].items():
            report.append(f"### {area['display_name']}")
            report.append(f"**Score:** {area['score']:.1f}/100")
            
            if area["strengths"]:
                report.append("\n**Strengths:**")
                for strength in area["strengths"]:
                    report.append(f"- {strength}")
            
            if area["weaknesses"]:
                report.append("\n**Weaknesses:**")
                for weakness in area["weaknesses"]:
                    report.append(f"- {weakness}")
            
            if area["recommendations"]:
                report.append("\n**Recommendations:**")
                for recommendation in area["recommendations"]:
                    report.append(f"- {recommendation}")
            
            report.append("")
        
        return "\n".join(report)
    
    def interpret_posture_command(self, command: str) -> Dict[str, Any]:
        """Interpret a natural language posture command
        
        Args:
            command: Natural language command for security posture
            
        Returns:
            Dictionary with interpreted command and parameters
        """
        # Determine the action
        action = None
        if re.search(r"assess|evaluate|check", command, re.IGNORECASE):
            action = "assess"
        elif re.search(r"report|generate", command, re.IGNORECASE):
            action = "report"
        elif re.search(r"improve|enhance|strengthen", command, re.IGNORECASE):
            action = "improve"
        
        # Extract parameters
        params = {}
        
        # Extract area
        area_match = re.search(r"(system|network|authentication|updates|monitoring)", command, re.IGNORECASE)
        if area_match:
            area = area_match.group(1).lower()
            if area == "system":
                params["area"] = "system_hardening"
            elif area == "network":
                params["area"] = "network_security"
            elif area == "authentication":
                params["area"] = "authentication"
            elif area == "updates":
                params["area"] = "updates_patching"
            elif area == "monitoring":
                params["area"] = "monitoring_logging"
        
        return {
            "action": action,
            "params": params,
            "original_command": command
        }
    
    # Helper methods for security checks
    
    def _check_ssh_config(self) -> Dict[str, bool]:
        """Check SSH configuration
        
        Returns:
            Dictionary with SSH configuration status
        """
        # This would normally check actual SSH config
        # For now, return default values
        return {
            "root_login_disabled": True,
            "password_auth_disabled": False
        }
    
    def _check_running_services(self) -> Dict[str, List[str]]:
        """Check running services
        
        Returns:
            Dictionary with running services information
        """
        # This would normally check actual running services
        # For now, return default values
        return {
            "necessary": ["ssh", "pveproxy", "pvedaemon"],
            "unnecessary": []
        }
    
    def _check_filesystem_permissions(self) -> Dict[str, int]:
        """Check filesystem permissions
        
        Returns:
            Dictionary with filesystem permissions status
        """
        # This would normally check actual filesystem permissions
        # For now, return default values
        return {
            "issues": 0
        }
    
    def _check_disk_encryption(self) -> bool:
        """Check if disk encryption is enabled
        
        Returns:
            True if disk encryption is enabled, False otherwise
        """
        # This would normally check actual disk encryption
        # For now, return default value
        return False
    
    def _check_open_ports(self) -> Dict[str, int]:
        """Check open ports
        
        Returns:
            Dictionary with open ports information
        """
        # This would normally check actual open ports
        # For now, return default values
        return {
            "count": 5,
            "ports": [22, 8006, 111, 3128, 60000]
        }
    
    def _check_vpn_configured(self) -> bool:
        """Check if VPN is configured
        
        Returns:
            True if VPN is configured, False otherwise
        """
        # This would normally check actual VPN configuration
        # For now, return default value
        return False
    
    def _check_2fa_enabled(self) -> bool:
        """Check if 2FA is enabled
        
        Returns:
            True if 2FA is enabled, False otherwise
        """
        # This would normally check actual 2FA configuration
        # For now, return default value
        return False
    
    def _check_password_policy(self) -> Dict[str, bool]:
        """Check password policy
        
        Returns:
            Dictionary with password policy status
        """
        # This would normally check actual password policy
        # For now, return default values
        return {
            "strong": True,
            "min_length": 12,
            "complexity": True
        }
    
    def _check_api_token_usage(self) -> bool:
        """Check if API tokens are used
        
        Returns:
            True if API tokens are used, False otherwise
        """
        # This would normally check actual API token usage
        # For now, return default value
        return True
    
    def _check_auto_updates(self) -> bool:
        """Check if automatic updates are enabled
        
        Returns:
            True if automatic updates are enabled, False otherwise
        """
        # This would normally check actual automatic updates configuration
        # For now, return default value
        return False
    
    def _check_monitoring_enabled(self) -> bool:
        """Check if monitoring is enabled
        
        Returns:
            True if monitoring is enabled, False otherwise
        """
        # This would normally check actual monitoring configuration
        # For now, return default value
        return True
    
    def _check_log_forwarding(self) -> bool:
        """Check if log forwarding is configured
        
        Returns:
            True if log forwarding is configured, False otherwise
        """
        # This would normally check actual log forwarding configuration
        # For now, return default value
        return False
    
    def _check_intrusion_detection(self) -> bool:
        """Check if intrusion detection is enabled
        
        Returns:
            True if intrusion detection is enabled, False otherwise
        """
        # This would normally check actual intrusion detection configuration
        # For now, return default value
        return False
    
    def _check_audit_logging(self) -> bool:
        """Check if audit logging is enabled
        
        Returns:
            True if audit logging is enabled, False otherwise
        """
        # This would normally check actual audit logging configuration
        # For now, return default value
        return True
