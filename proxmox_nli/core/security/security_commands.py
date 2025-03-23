"""
Security Commands for Proxmox NLI.
Provides natural language command handling for security management.
"""
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from .security_manager import SecurityManager
from .certificate_manager import CertificateManager
from .security_auditor import SecurityAuditor
from .security_posture import SecurityPostureAssessor

logger = logging.getLogger(__name__)

class SecurityCommands:
    """Command handler for security-related natural language commands"""
    
    def __init__(self, api, base_nli=None):
        """Initialize the security commands handler
        
        Args:
            api: Proxmox API client
            base_nli: Base NLI instance for accessing other components
        """
        self.api = api
        self.base_nli = base_nli
        self.security_manager = SecurityManager(api, base_nli)
        self.certificate_manager = CertificateManager(api, base_nli)
        self.security_auditor = SecurityAuditor(api, base_nli)
        self.security_posture = SecurityPostureAssessor(api, base_nli)
    
    def handle_command(self, command: str) -> Dict[str, Any]:
        """Handle a natural language security command
        
        Args:
            command: Natural language command
            
        Returns:
            Dictionary with command result
        """
        # Determine command type
        if re.search(r"audit|check security", command, re.IGNORECASE):
            return self._handle_audit_command(command)
        elif re.search(r"permission|role|access", command, re.IGNORECASE):
            return self._handle_permission_command(command)
        elif re.search(r"certificate|ssl|tls", command, re.IGNORECASE):
            return self._handle_certificate_command(command)
        elif re.search(r"firewall|port|rule", command, re.IGNORECASE):
            return self._handle_firewall_command(command)
        elif re.search(r"posture|assess|evaluate", command, re.IGNORECASE):
            return self._handle_posture_command(command)
        else:
            return {
                "success": False,
                "message": "I'm not sure what security operation you want to perform. Please try a more specific command."
            }
    
    def _handle_audit_command(self, command: str) -> Dict[str, Any]:
        """Handle a security audit command
        
        Args:
            command: Natural language command
            
        Returns:
            Dictionary with command result
        """
        interpreted = self.security_auditor.interpret_audit_command(command)
        action = interpreted.get("action")
        params = interpreted.get("params", {})
        
        if action == "run":
            # Run a security audit
            scope = params.get("scope", "full")
            audit_result = self.security_auditor.run_full_audit()
            
            if audit_result.get("success", False):
                # Generate natural language response
                risk_level = audit_result.get("risk_level", "unknown")
                finding_count = len(audit_result.get("findings", []))
                
                response = f"I've completed a security audit of your system. "
                
                if risk_level == "high":
                    response += f"I found {finding_count} security issues that need attention. The overall risk level is HIGH."
                elif risk_level == "medium":
                    response += f"I found {finding_count} security issues. The overall risk level is MEDIUM."
                elif risk_level == "low":
                    response += f"I found {finding_count} minor security issues. The overall risk level is LOW."
                else:
                    response += f"I found {finding_count} security issues."
                
                # Add recommendations
                if audit_result.get("recommendations"):
                    response += "\n\nHere are my recommendations:\n"
                    for recommendation in audit_result.get("recommendations"):
                        response += f"- {recommendation}\n"
                
                return {
                    "success": True,
                    "message": response,
                    "audit_result": audit_result
                }
            else:
                return {
                    "success": False,
                    "message": f"I couldn't complete the security audit: {audit_result.get('message', 'Unknown error')}"
                }
        elif action == "history":
            # Get audit history
            limit = params.get("limit", 5)
            history = self.security_auditor.get_audit_history(limit)
            
            if history.get("success", False):
                audit_count = len(history.get("history", []))
                
                if audit_count == 0:
                    return {
                        "success": True,
                        "message": "I don't have any security audit history yet. Would you like me to run a security audit now?"
                    }
                else:
                    response = f"Here are the last {audit_count} security audits:\n\n"
                    
                    for i, audit in enumerate(history.get("history", []), 1):
                        timestamp = datetime.fromisoformat(audit.get("timestamp")).strftime("%Y-%m-%d %H:%M:%S")
                        risk_level = audit.get("risk_level", "unknown").upper()
                        finding_count = audit.get("finding_count", 0)
                        
                        response += f"{i}. {timestamp} - Risk Level: {risk_level}, Findings: {finding_count}\n"
                    
                    return {
                        "success": True,
                        "message": response,
                        "history": history.get("history", [])
                    }
            else:
                return {
                    "success": False,
                    "message": f"I couldn't retrieve the audit history: {history.get('message', 'Unknown error')}"
                }
        else:
            return {
                "success": False,
                "message": "I'm not sure what audit operation you want to perform. Try 'run a security audit' or 'show audit history'."
            }
    
    def _handle_permission_command(self, command: str) -> Dict[str, Any]:
        """Handle a permission management command
        
        Args:
            command: Natural language command
            
        Returns:
            Dictionary with command result
        """
        interpreted = self.security_manager.interpret_permission_command(command)
        action = interpreted.get("action")
        params = interpreted.get("params", {})
        
        if action == "add":
            # Add permission
            user = params.get("user")
            role = params.get("role")
            permission = params.get("permission")
            
            if not user or not role:
                return {
                    "success": False,
                    "message": "I need both a user and a role to add permissions. Please specify both."
                }
            
            # Get permission handler from base_nli if available
            permission_handler = None
            if self.base_nli and hasattr(self.base_nli, "permission_handler"):
                permission_handler = self.base_nli.permission_handler
            
            if permission_handler:
                # Add role to user
                result = self.api.api_request('PUT', f'access/acl', {
                    'path': '/',
                    'roles': role,
                    'users': user
                })
                
                if result.get("success", False):
                    return {
                        "success": True,
                        "message": f"I've given user '{user}' the '{role}' role."
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't add the permission: {result.get('message', 'Unknown error')}"
                    }
            else:
                return {
                    "success": False,
                    "message": "I couldn't access the permission handler. This feature may not be available."
                }
        elif action == "remove":
            # Remove permission
            user = params.get("user")
            role = params.get("role")
            
            if not user or not role:
                return {
                    "success": False,
                    "message": "I need both a user and a role to remove permissions. Please specify both."
                }
            
            # Get permission handler from base_nli if available
            permission_handler = None
            if self.base_nli and hasattr(self.base_nli, "permission_handler"):
                permission_handler = self.base_nli.permission_handler
            
            if permission_handler:
                # Remove role from user
                result = self.api.api_request('DELETE', f'access/acl', {
                    'path': '/',
                    'roles': role,
                    'users': user
                })
                
                if result.get("success", False):
                    return {
                        "success": True,
                        "message": f"I've removed the '{role}' role from user '{user}'."
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't remove the permission: {result.get('message', 'Unknown error')}"
                    }
            else:
                return {
                    "success": False,
                    "message": "I couldn't access the permission handler. This feature may not be available."
                }
        elif action == "list":
            # List permissions
            user = params.get("user")
            
            if user:
                # List permissions for specific user
                result = self.api.api_request('GET', f'access/permissions?path=/&userid={user}')
                
                if result.get("success", False):
                    permissions = result.get("data", [])
                    
                    if permissions:
                        response = f"Here are the permissions for user '{user}':\n\n"
                        
                        for permission in permissions:
                            path = permission.get("path", "/")
                            role = permission.get("roleid", "unknown")
                            
                            response += f"- Path: {path}, Role: {role}\n"
                        
                        return {
                            "success": True,
                            "message": response,
                            "permissions": permissions
                        }
                    else:
                        return {
                            "success": True,
                            "message": f"User '{user}' doesn't have any permissions."
                        }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't list the permissions: {result.get('message', 'Unknown error')}"
                    }
            else:
                # List all permissions
                result = self.api.api_request('GET', 'access/acl')
                
                if result.get("success", False):
                    permissions = result.get("data", [])
                    
                    if permissions:
                        response = "Here are all the permissions in the system:\n\n"
                        
                        for permission in permissions:
                            path = permission.get("path", "/")
                            role = permission.get("roleid", "unknown")
                            user = permission.get("userid", "unknown")
                            
                            response += f"- User: {user}, Path: {path}, Role: {role}\n"
                        
                        return {
                            "success": True,
                            "message": response,
                            "permissions": permissions
                        }
                    else:
                        return {
                            "success": True,
                            "message": "There are no permissions configured in the system."
                        }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't list the permissions: {result.get('message', 'Unknown error')}"
                    }
        else:
            return {
                "success": False,
                "message": "I'm not sure what permission operation you want to perform. Try 'add permission', 'remove permission', or 'list permissions'."
            }
    
    def _handle_certificate_command(self, command: str) -> Dict[str, Any]:
        """Handle a certificate management command
        
        Args:
            command: Natural language command
            
        Returns:
            Dictionary with command result
        """
        interpreted = self.certificate_manager.interpret_certificate_command(command)
        action = interpreted.get("action")
        params = interpreted.get("params", {})
        
        if action == "list":
            # List certificates
            certificates = self.certificate_manager.list_certificates()
            
            if certificates.get("success", False):
                cert_count = certificates.get("count", 0)
                
                if cert_count == 0:
                    return {
                        "success": True,
                        "message": "I don't see any SSL certificates in the system. Would you like me to generate one?"
                    }
                else:
                    response = f"I found {cert_count} SSL certificates:\n\n"
                    
                    for cert in certificates.get("certificates", []):
                        subject = cert.get("subject", "Unknown")
                        status = cert.get("status", "unknown")
                        days = cert.get("days_until_expiry")
                        
                        status_text = "Unknown"
                        if status == "valid":
                            status_text = f"Valid (expires in {days} days)"
                        elif status == "expiring_soon":
                            status_text = f"Expiring soon ({days} days left)"
                        elif status == "expired":
                            status_text = f"Expired ({abs(days)} days ago)"
                        
                        response += f"- {subject}: {status_text}\n"
                    
                    return {
                        "success": True,
                        "message": response,
                        "certificates": certificates.get("certificates", [])
                    }
            else:
                return {
                    "success": False,
                    "message": f"I couldn't list the certificates: {certificates.get('message', 'Unknown error')}"
                }
        elif action == "generate_self_signed":
            # Generate self-signed certificate
            domain = params.get("domain")
            email = params.get("email")
            
            if not domain:
                return {
                    "success": False,
                    "message": "I need a domain name to generate a certificate. Please specify a domain."
                }
            
            result = self.certificate_manager.generate_self_signed_certificate(domain, email)
            
            if result.get("success", False):
                return {
                    "success": True,
                    "message": f"I've generated a self-signed SSL certificate for {domain}."
                }
            else:
                return {
                    "success": False,
                    "message": f"I couldn't generate the certificate: {result.get('message', 'Unknown error')}"
                }
        elif action == "request_lets_encrypt":
            # Request Let's Encrypt certificate
            domain = params.get("domain")
            email = params.get("email")
            
            if not domain or not email:
                return {
                    "success": False,
                    "message": "I need both a domain name and an email address to request a Let's Encrypt certificate. Please specify both."
                }
            
            result = self.certificate_manager.request_lets_encrypt_certificate(domain, email)
            
            if result.get("success", False):
                return {
                    "success": True,
                    "message": f"I've requested a Let's Encrypt SSL certificate for {domain}. The certificate will be issued shortly."
                }
            else:
                return {
                    "success": False,
                    "message": f"I couldn't request the certificate: {result.get('message', 'Unknown error')}"
                }
        elif action == "check":
            # Generate certificate report
            report = self.certificate_manager.generate_certificate_report()
            
            if report.get("success", False):
                return {
                    "success": True,
                    "message": report.get("report", "Certificate check completed."),
                    "report": report
                }
            else:
                return {
                    "success": False,
                    "message": f"I couldn't check the certificates: {report.get('message', 'Unknown error')}"
                }
        else:
            return {
                "success": False,
                "message": "I'm not sure what certificate operation you want to perform. Try 'list certificates', 'generate certificate', or 'check certificates'."
            }
    
    def _handle_firewall_command(self, command: str) -> Dict[str, Any]:
        """Handle a firewall management command
        
        Args:
            command: Natural language command
            
        Returns:
            Dictionary with command result
        """
        interpreted = self.security_manager.interpret_firewall_command(command)
        action = interpreted.get("action")
        params = interpreted.get("params", {})
        
        # Get firewall manager from base_nli if available
        firewall_manager = None
        if self.base_nli and hasattr(self.base_nli, "firewall_manager"):
            firewall_manager = self.base_nli.firewall_manager
        else:
            # Import here to avoid circular imports
            from ..network.firewall_manager import FirewallManager
            firewall_manager = FirewallManager(self.api)
        
        if action == "list":
            # List firewall rules
            rules = firewall_manager.list_rules()
            
            if rules.get("success", False):
                rule_count = len(rules.get("data", []))
                
                if rule_count == 0:
                    return {
                        "success": True,
                        "message": "There are no firewall rules defined. Would you like me to add some basic rules?"
                    }
                else:
                    response = f"I found {rule_count} firewall rules:\n\n"
                    
                    for rule in rules.get("data", []):
                        pos = rule.get("pos", "?")
                        action = rule.get("action", "?")
                        type_val = rule.get("type", "?")
                        proto = rule.get("proto", "any")
                        dport = rule.get("dport", "any")
                        source = rule.get("source", "any")
                        comment = rule.get("comment", "")
                        
                        response += f"{pos}. {action} {type_val} proto={proto} dport={dport} source={source}"
                        if comment:
                            response += f" ({comment})"
                        response += "\n"
                    
                    return {
                        "success": True,
                        "message": response,
                        "rules": rules.get("data", [])
                    }
            else:
                return {
                    "success": False,
                    "message": f"I couldn't list the firewall rules: {rules.get('message', 'Unknown error')}"
                }
        elif action == "allow":
            # Add allow rule
            port = params.get("port")
            protocol = params.get("protocol", "tcp")
            service = params.get("service")
            source = params.get("source", "")
            
            if not port and not service:
                return {
                    "success": False,
                    "message": "I need either a port or a service to add a firewall rule. Please specify at least one."
                }
            
            if service:
                # Add rules for common service
                ports = []
                if service.lower() == "http":
                    ports = [80]
                elif service.lower() == "https":
                    ports = [443]
                elif service.lower() == "ssh":
                    ports = [22]
                elif service.lower() == "ftp":
                    ports = [21]
                elif service.lower() == "smtp":
                    ports = [25]
                elif service.lower() == "dns":
                    ports = [53]
                else:
                    return {
                        "success": False,
                        "message": f"I don't know the ports for service '{service}'. Please specify the port directly."
                    }
                
                sources = [source] if source else None
                result = firewall_manager.add_service_rules(service, ports, sources)
                
                if result.get("success", False):
                    return {
                        "success": True,
                        "message": f"I've added firewall rules to allow {service} traffic."
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't add the firewall rules: {result.get('message', 'Unknown error')}"
                    }
            else:
                # Add rule for specific port
                rule = {
                    "action": "ACCEPT",
                    "type": "in",
                    "proto": protocol,
                    "dport": port,
                    "comment": f"Allow {protocol.upper()} port {port}"
                }
                
                if source:
                    rule["source"] = source
                
                result = firewall_manager.add_rule(rule)
                
                if result.get("success", False):
                    return {
                        "success": True,
                        "message": f"I've added a firewall rule to allow {protocol.upper()} traffic on port {port}."
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't add the firewall rule: {result.get('message', 'Unknown error')}"
                    }
        elif action == "deny":
            # Add deny rule
            port = params.get("port")
            protocol = params.get("protocol", "tcp")
            service = params.get("service")
            source = params.get("source", "")
            
            if not port and not service:
                return {
                    "success": False,
                    "message": "I need either a port or a service to add a firewall rule. Please specify at least one."
                }
            
            if service:
                # Determine ports for common service
                ports = []
                if service.lower() == "http":
                    ports = [80]
                elif service.lower() == "https":
                    ports = [443]
                elif service.lower() == "ssh":
                    ports = [22]
                elif service.lower() == "ftp":
                    ports = [21]
                elif service.lower() == "smtp":
                    ports = [25]
                elif service.lower() == "dns":
                    ports = [53]
                else:
                    return {
                        "success": False,
                        "message": f"I don't know the ports for service '{service}'. Please specify the port directly."
                    }
                
                # Add deny rule for each port
                results = []
                for port in ports:
                    rule = {
                        "action": "DROP",
                        "type": "in",
                        "proto": protocol,
                        "dport": str(port),
                        "comment": f"Block {service} ({port}/{protocol})"
                    }
                    
                    if source:
                        rule["source"] = source
                    
                    result = firewall_manager.add_rule(rule)
                    results.append(result)
                
                success = all(r.get("success", False) for r in results)
                
                if success:
                    return {
                        "success": True,
                        "message": f"I've added firewall rules to block {service} traffic."
                    }
                else:
                    return {
                        "success": False,
                        "message": "I couldn't add all the firewall rules. Some may have been added."
                    }
            else:
                # Add deny rule for specific port
                rule = {
                    "action": "DROP",
                    "type": "in",
                    "proto": protocol,
                    "dport": port,
                    "comment": f"Block {protocol.upper()} port {port}"
                }
                
                if source:
                    rule["source"] = source
                
                result = firewall_manager.add_rule(rule)
                
                if result.get("success", False):
                    return {
                        "success": True,
                        "message": f"I've added a firewall rule to block {protocol.upper()} traffic on port {port}."
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't add the firewall rule: {result.get('message', 'Unknown error')}"
                    }
        elif action == "delete":
            # Delete firewall rule
            # This requires a rule ID, which is not easily extracted from natural language
            # For now, just return a message suggesting to list rules first
            return {
                "success": False,
                "message": "To delete a firewall rule, I need the rule number. Please list the rules first, then tell me which one to delete by number."
            }
        else:
            return {
                "success": False,
                "message": "I'm not sure what firewall operation you want to perform. Try 'list firewall rules', 'allow port', or 'block port'."
            }
    
    def _handle_posture_command(self, command: str) -> Dict[str, Any]:
        """Handle a security posture command
        
        Args:
            command: Natural language command
            
        Returns:
            Dictionary with command result
        """
        interpreted = self.security_posture.interpret_posture_command(command)
        action = interpreted.get("action")
        params = interpreted.get("params", {})
        
        if action == "assess":
            # Assess security posture
            area = params.get("area")
            
            if area:
                # Assess specific area
                assessment = self.security_posture.assess_security_posture()
                
                if assessment.get("success", False):
                    area_data = assessment.get("areas", {}).get(area)
                    
                    if area_data:
                        area_name = area_data.get("display_name", area)
                        score = area_data.get("score", 0)
                        
                        response = f"I've assessed your {area_name.lower()} security. Your score is {score}/100.\n\n"
                        
                        if area_data.get("strengths"):
                            response += "Strengths:\n"
                            for strength in area_data.get("strengths"):
                                response += f"- {strength}\n"
                            response += "\n"
                        
                        if area_data.get("weaknesses"):
                            response += "Weaknesses:\n"
                            for weakness in area_data.get("weaknesses"):
                                response += f"- {weakness}\n"
                            response += "\n"
                        
                        if area_data.get("recommendations"):
                            response += "Recommendations:\n"
                            for recommendation in area_data.get("recommendations"):
                                response += f"- {recommendation}\n"
                        
                        return {
                            "success": True,
                            "message": response,
                            "assessment": area_data
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"I couldn't assess the {area} security area. Try 'assess security posture' for a full assessment."
                        }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't assess your security posture: {assessment.get('message', 'Unknown error')}"
                    }
            else:
                # Assess overall posture
                assessment = self.security_posture.assess_security_posture()
                
                if assessment.get("success", False):
                    posture_level = assessment.get("posture_level", "unknown")
                    score = assessment.get("overall_score", 0)
                    
                    response = f"I've assessed your overall security posture. Your security level is {posture_level.upper()} with a score of {score}/100.\n\n"
                    
                    if assessment.get("strengths"):
                        response += "Key strengths:\n"
                        for strength in assessment.get("strengths")[:3]:  # Show top 3 strengths
                            response += f"- {strength}\n"
                        response += "\n"
                    
                    if assessment.get("weaknesses"):
                        response += "Key weaknesses:\n"
                        for weakness in assessment.get("weaknesses")[:3]:  # Show top 3 weaknesses
                            response += f"- {weakness}\n"
                        response += "\n"
                    
                    if assessment.get("recommendations"):
                        response += "Top recommendations:\n"
                        for recommendation in assessment.get("recommendations")[:3]:  # Show top 3 recommendations
                            response += f"- {recommendation}\n"
                        
                        if len(assessment.get("recommendations", [])) > 3:
                            response += "\nWould you like to see the full security report with all recommendations?"
                    
                    return {
                        "success": True,
                        "message": response,
                        "assessment": assessment
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't assess your security posture: {assessment.get('message', 'Unknown error')}"
                    }
        elif action == "report":
            # Generate security posture report
            report = self.security_posture.generate_posture_report()
            
            return {
                "success": True,
                "message": report,
                "report": report
            }
        elif action == "improve":
            # Provide improvement recommendations
            assessment = self.security_posture.assess_security_posture()
            
            if assessment.get("success", False):
                area = params.get("area")
                
                if area:
                    # Get recommendations for specific area
                    area_data = assessment.get("areas", {}).get(area)
                    
                    if area_data:
                        area_name = area_data.get("display_name", area)
                        recommendations = area_data.get("recommendations", [])
                        
                        if recommendations:
                            response = f"Here's how you can improve your {area_name.lower()} security:\n\n"
                            
                            for recommendation in recommendations:
                                response += f"- {recommendation}\n"
                            
                            return {
                                "success": True,
                                "message": response,
                                "recommendations": recommendations
                            }
                        else:
                            return {
                                "success": True,
                                "message": f"Your {area_name.lower()} security looks good! I don't have any specific recommendations at this time."
                            }
                    else:
                        return {
                            "success": False,
                            "message": f"I couldn't find recommendations for the {area} security area. Try 'improve security posture' for overall recommendations."
                        }
                else:
                    # Get overall recommendations
                    recommendations = assessment.get("recommendations", [])
                    
                    if recommendations:
                        response = "Here's how you can improve your overall security posture:\n\n"
                        
                        for recommendation in recommendations:
                            response += f"- {recommendation}\n"
                        
                        return {
                            "success": True,
                            "message": response,
                            "recommendations": recommendations
                        }
                    else:
                        return {
                            "success": True,
                            "message": "Your security posture looks good! I don't have any specific recommendations at this time."
                        }
            else:
                return {
                    "success": False,
                    "message": f"I couldn't assess your security posture to provide recommendations: {assessment.get('message', 'Unknown error')}"
                }
        else:
            return {
                "success": False,
                "message": "I'm not sure what security posture operation you want to perform. Try 'assess security posture', 'generate security report', or 'improve security posture'."
            }
