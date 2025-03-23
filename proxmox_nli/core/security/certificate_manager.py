"""
Certificate Manager for Proxmox NLI.
Provides natural language interfaces for SSL certificate management.
"""
import logging
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CertificateManager:
    """Manages SSL certificates with natural language interfaces"""
    
    def __init__(self, api, base_nli=None):
        """Initialize the certificate manager
        
        Args:
            api: Proxmox API client
            base_nli: Base NLI instance for accessing other components
        """
        self.api = api
        self.base_nli = base_nli
        self.cert_storage_path = "/etc/pve/local/pve-ssl"
        
    def list_certificates(self) -> Dict[str, Any]:
        """List all certificates in the system
        
        Returns:
            Dictionary with certificate information
        """
        try:
            # Get node certificates
            node_certs = self.api.api_request('GET', 'nodes/localhost/certificates')
            
            # Process certificate information
            certificates = []
            if node_certs.get("success", False):
                for cert in node_certs.get("data", []):
                    # Extract and add additional useful information
                    expiry_date = cert.get("notafter")
                    days_until_expiry = None
                    status = "unknown"
                    
                    if expiry_date:
                        try:
                            expiry = datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                            days_until_expiry = (expiry - datetime.now()).days
                            
                            if days_until_expiry < 0:
                                status = "expired"
                            elif days_until_expiry < 30:
                                status = "expiring_soon"
                            else:
                                status = "valid"
                        except Exception as e:
                            logger.error(f"Error parsing certificate date: {str(e)}")
                    
                    certificates.append({
                        "filename": cert.get("filename"),
                        "subject": cert.get("subject"),
                        "issuer": cert.get("issuer"),
                        "notbefore": cert.get("notbefore"),
                        "notafter": cert.get("notafter"),
                        "fingerprint": cert.get("fingerprint"),
                        "days_until_expiry": days_until_expiry,
                        "status": status
                    })
            
            return {
                "success": True,
                "certificates": certificates,
                "count": len(certificates)
            }
        except Exception as e:
            logger.error(f"Error listing certificates: {str(e)}")
            return {
                "success": False,
                "message": f"Error listing certificates: {str(e)}",
                "certificates": []
            }
    
    def generate_self_signed_certificate(self, domain: str, email: Optional[str] = None) -> Dict[str, Any]:
        """Generate a self-signed certificate
        
        Args:
            domain: Domain name for the certificate
            email: Email address for the certificate
            
        Returns:
            Dictionary with generation result
        """
        try:
            params = {
                "force": 1,
                "nodes": "localhost"
            }
            
            if domain:
                params["domains"] = domain
            if email:
                params["email"] = email
                
            result = self.api.api_request('POST', 'nodes/localhost/certificates/custom', params)
            
            if result.get("success", False):
                return {
                    "success": True,
                    "message": f"Successfully generated self-signed certificate for {domain}",
                    "details": result.get("data", {})
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to generate certificate: {result.get('message', 'Unknown error')}"
                }
        except Exception as e:
            logger.error(f"Error generating self-signed certificate: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating self-signed certificate: {str(e)}"
            }
    
    def request_lets_encrypt_certificate(self, domain: str, email: str) -> Dict[str, Any]:
        """Request a Let's Encrypt certificate
        
        Args:
            domain: Domain name for the certificate
            email: Email address for Let's Encrypt account
            
        Returns:
            Dictionary with request result
        """
        try:
            params = {
                "force": 1,
                "domains": domain,
                "email": email
            }
            
            result = self.api.api_request('POST', 'nodes/localhost/certificates/acme/certificate', params)
            
            if result.get("success", False):
                return {
                    "success": True,
                    "message": f"Successfully requested Let's Encrypt certificate for {domain}",
                    "details": result.get("data", {})
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to request Let's Encrypt certificate: {result.get('message', 'Unknown error')}"
                }
        except Exception as e:
            logger.error(f"Error requesting Let's Encrypt certificate: {str(e)}")
            return {
                "success": False,
                "message": f"Error requesting Let's Encrypt certificate: {str(e)}"
            }
    
    def interpret_certificate_command(self, command: str) -> Dict[str, Any]:
        """Interpret a natural language certificate command
        
        Args:
            command: Natural language command for certificate management
            
        Returns:
            Dictionary with interpreted command and parameters
        """
        # Extract domain and email information
        domain_match = re.search(r"domain[s]?\s+([a-zA-Z0-9.-]+)", command, re.IGNORECASE)
        email_match = re.search(r"email\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", command, re.IGNORECASE)
        
        # Determine the action
        action = None
        if re.search(r"create|generate|new", command, re.IGNORECASE):
            if re.search(r"let'?s encrypt|acme", command, re.IGNORECASE):
                action = "request_lets_encrypt"
            else:
                action = "generate_self_signed"
        elif re.search(r"list|show|display", command, re.IGNORECASE):
            action = "list"
        elif re.search(r"renew|update", command, re.IGNORECASE):
            action = "renew"
        elif re.search(r"delete|remove", command, re.IGNORECASE):
            action = "delete"
        elif re.search(r"check|verify|validate", command, re.IGNORECASE):
            action = "check"
        
        # Extract parameters
        params = {}
        if domain_match:
            params["domain"] = domain_match.group(1)
        if email_match:
            params["email"] = email_match.group(1)
        
        return {
            "action": action,
            "params": params,
            "original_command": command
        }
    
    def generate_certificate_report(self) -> Dict[str, Any]:
        """Generate a report on certificate status
        
        Returns:
            Dictionary with certificate report
        """
        try:
            certificates = self.list_certificates()
            
            if not certificates.get("success", False):
                return {
                    "success": False,
                    "message": "Failed to generate certificate report: couldn't retrieve certificates"
                }
            
            cert_list = certificates.get("certificates", [])
            
            # Analyze certificates
            expired = []
            expiring_soon = []
            valid = []
            
            for cert in cert_list:
                if cert["status"] == "expired":
                    expired.append(cert)
                elif cert["status"] == "expiring_soon":
                    expiring_soon.append(cert)
                elif cert["status"] == "valid":
                    valid.append(cert)
            
            # Generate natural language report
            report = []
            
            if not cert_list:
                report.append("No certificates found in the system.")
            else:
                report.append(f"Found {len(cert_list)} certificates in the system.")
                
                if expired:
                    report.append(f"{len(expired)} certificates have expired and need immediate attention.")
                    for cert in expired:
                        report.append(f"- {cert['subject']} expired {abs(cert['days_until_expiry'])} days ago")
                
                if expiring_soon:
                    report.append(f"{len(expiring_soon)} certificates will expire soon and should be renewed.")
                    for cert in expiring_soon:
                        report.append(f"- {cert['subject']} will expire in {cert['days_until_expiry']} days")
                
                if valid:
                    report.append(f"{len(valid)} certificates are valid.")
                    
            return {
                "success": True,
                "report": "\n".join(report),
                "expired": len(expired),
                "expiring_soon": len(expiring_soon),
                "valid": len(valid),
                "total": len(cert_list)
            }
        except Exception as e:
            logger.error(f"Error generating certificate report: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating certificate report: {str(e)}"
            }
