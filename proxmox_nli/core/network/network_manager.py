"""
Network management module for Proxmox NLI.
Handles network configuration, VLANs, firewall rules, and security.
"""
import logging
import ipaddress
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NetworkSegment:
    name: str
    vlan_id: int
    subnet: str
    purpose: str
    security_level: str
    allowed_services: List[str]

class NetworkManager:
    def __init__(self, api):
        self.api = api
        self.networks = {}
        self.default_networks = {
            "management": NetworkSegment(
                name="management",
                vlan_id=1,
                subnet="10.0.0.0/24",
                purpose="Proxmox management network",
                security_level="high",
                allowed_services=["ssh", "https"]
            ),
            "storage": NetworkSegment(
                name="storage",
                vlan_id=2,
                subnet="10.0.1.0/24",
                purpose="Storage network for backups and replication",
                security_level="high",
                allowed_services=["nfs", "iscsi"]
            ),
            "services": NetworkSegment(
                name="services",
                vlan_id=10,
                subnet="10.0.10.0/24",
                purpose="Internal services network",
                security_level="medium",
                allowed_services=["http", "https", "dns"]
            ),
            "dmz": NetworkSegment(
                name="dmz",
                vlan_id=20,
                subnet="10.0.20.0/24",
                purpose="DMZ for external-facing services",
                security_level="high",
                allowed_services=["http", "https"]
            )
        }

    def setup_network_segmentation(self) -> Dict:
        """Set up initial network segmentation with VLANs"""
        try:
            # Create bridge for each network segment
            for segment in self.default_networks.values():
                result = self.create_network_segment(segment)
                if not result["success"]:
                    return result

            return {
                "success": True,
                "message": "Network segmentation configured successfully",
                "segments": list(self.default_networks.values())
            }
        except Exception as e:
            logger.error(f"Error setting up network segmentation: {str(e)}")
            return {
                "success": False,
                "message": f"Error setting up network segmentation: {str(e)}"
            }

    def create_network_segment(self, segment: NetworkSegment) -> Dict:
        """Create a new network segment with VLAN"""
        try:
            # Check if bridge exists
            bridge_name = f"vmbr{segment.vlan_id}"
            bridge_exists = self.api.api_request('GET', f'nodes/localhost/network')
            if bridge_exists['success']:
                for net in bridge_exists['data']:
                    if net.get('iface') == bridge_name:
                        return {
                            "success": True,
                            "message": f"Bridge {bridge_name} already exists",
                            "segment": segment
                        }

            # Create bridge
            create_result = self.api.api_request('POST', 'nodes/localhost/network', {
                'type': 'bridge',
                'iface': bridge_name,
                'autostart': 1,
                'vlan_aware': 1
            })

            if not create_result['success']:
                return create_result

            # Configure firewall for segment
            fw_config = self._generate_firewall_config(segment)
            fw_result = self.api.api_request('POST', f'nodes/localhost/firewall/rules', fw_config)

            if not fw_result['success']:
                return fw_result

            self.networks[segment.name] = segment
            return {
                "success": True,
                "message": f"Network segment {segment.name} created successfully",
                "segment": segment
            }

        except Exception as e:
            logger.error(f"Error creating network segment: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating network segment: {str(e)}"
            }

    def get_network_recommendations(self, service_type: str) -> Dict:
        """Get network configuration recommendations for a service"""
        try:
            # Define service profiles
            profiles = {
                "web": {
                    "segment": "dmz",
                    "ports": [80, 443],
                    "security_level": "high"
                },
                "database": {
                    "segment": "services",
                    "ports": [3306, 5432],
                    "security_level": "high"
                },
                "cache": {
                    "segment": "services",
                    "ports": [6379, 11211],
                    "security_level": "medium"
                },
                "monitoring": {
                    "segment": "management",
                    "ports": [9090, 9100],
                    "security_level": "medium"
                }
            }

            profile = profiles.get(service_type, {
                "segment": "services",
                "ports": [],
                "security_level": "medium"
            })

            # Get segment details
            segment = self.default_networks.get(profile["segment"])
            if not segment:
                return {
                    "success": False,
                    "message": f"Network segment {profile['segment']} not found"
                }

            return {
                "success": True,
                "message": f"Network recommendations for {service_type}",
                "recommendations": {
                    "segment": segment,
                    "firewall_rules": self._generate_service_firewall_rules(profile),
                    "security_measures": self._get_security_recommendations(profile["security_level"])
                }
            }

        except Exception as e:
            logger.error(f"Error getting network recommendations: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting network recommendations: {str(e)}"
            }

    def configure_service_network(self, service_id: str, service_type: str, vm_id: str) -> Dict:
        """Configure network for a service"""
        try:
            # Get recommendations
            recommendations = self.get_network_recommendations(service_type)
            if not recommendations["success"]:
                return recommendations

            segment = recommendations["recommendations"]["segment"]
            
            # Configure VM network
            net_config = {
                'net0': f'virtio,bridge={segment.name},firewall=1,tag={segment.vlan_id}'
            }

            result = self.api.api_request('PUT', f'nodes/localhost/qemu/{vm_id}/config', net_config)
            if not result["success"]:
                return result

            # Apply firewall rules
            for rule in recommendations["recommendations"]["firewall_rules"]:
                fw_result = self.api.api_request('POST', f'nodes/localhost/qemu/{vm_id}/firewall/rules', rule)
                if not fw_result["success"]:
                    return fw_result

            return {
                "success": True,
                "message": f"Network configured for service {service_id}",
                "config": {
                    "segment": segment,
                    "firewall_rules": recommendations["recommendations"]["firewall_rules"],
                    "security_measures": recommendations["recommendations"]["security_measures"]
                }
            }

        except Exception as e:
            logger.error(f"Error configuring service network: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring service network: {str(e)}"
            }

    def analyze_network_security(self) -> Dict:
        """Analyze network security and provide recommendations"""
        try:
            issues = []
            recommendations = []

            # Check network segmentation
            if len(self.networks) < 2:
                issues.append("Limited network segmentation detected")
                recommendations.append("Implement network segmentation with VLANs")

            # Check firewall rules
            fw_result = self.api.api_request('GET', 'nodes/localhost/firewall/rules')
            if fw_result["success"]:
                rules = fw_result["data"]
                if not rules:
                    issues.append("No firewall rules defined")
                    recommendations.append("Configure basic firewall rules")
                else:
                    # Check for common security issues
                    for rule in rules:
                        if rule.get('action') == 'ACCEPT' and rule.get('source') == '0.0.0.0/0':
                            issues.append(f"Overly permissive firewall rule: {rule}")
                            recommendations.append("Restrict source IP ranges in firewall rules")

            return {
                "success": True,
                "message": "Network security analysis complete",
                "analysis": {
                    "issues": issues,
                    "recommendations": recommendations,
                    "security_score": self._calculate_security_score(issues)
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing network security: {str(e)}")
            return {
                "success": False,
                "message": f"Error analyzing network security: {str(e)}"
            }

    def _generate_firewall_config(self, segment: NetworkSegment) -> Dict:
        """Generate firewall configuration for a network segment"""
        rules = []

        # Basic rules
        rules.extend([
            {
                "action": "ACCEPT",
                "type": "in",
                "source": segment.subnet,
                "dest": "management",
                "proto": "tcp",
                "dport": "22,443",
                "comment": "Allow management access"
            }
        ])

        # Service-specific rules
        for service in segment.allowed_services:
            if service == "http":
                rules.append({
                    "action": "ACCEPT",
                    "type": "in",
                    "proto": "tcp",
                    "dport": "80"
                })
            elif service == "https":
                rules.append({
                    "action": "ACCEPT",
                    "type": "in",
                    "proto": "tcp",
                    "dport": "443"
                })
            # Add more service rules as needed

        # Default deny rule
        rules.append({
            "action": "DROP",
            "type": "in",
            "comment": "Default deny rule"
        })

        return {"rules": rules}

    def _generate_service_firewall_rules(self, profile: Dict) -> List[Dict]:
        """Generate firewall rules for a service"""
        rules = []
        
        # Allow specified ports
        for port in profile["ports"]:
            rules.append({
                "action": "ACCEPT",
                "type": "in",
                "proto": "tcp",
                "dport": str(port),
                "comment": f"Allow service port {port}"
            })

        # Add security-level based rules
        if profile["security_level"] == "high":
            rules.append({
                "action": "DROP",
                "type": "in",
                "proto": "tcp",
                "sport": "1-1024",
                "comment": "Block privileged ports"
            })

        return rules

    def _get_security_recommendations(self, security_level: str) -> List[str]:
        """Get security recommendations based on security level"""
        recommendations = [
            "Enable firewall for all interfaces",
            "Use strong passwords and key-based authentication",
            "Regularly update system and security patches"
        ]

        if security_level == "high":
            recommendations.extend([
                "Implement intrusion detection/prevention",
                "Enable detailed logging and monitoring",
                "Use TLS for all communications",
                "Implement rate limiting",
                "Regular security audits"
            ])

        return recommendations

    def _calculate_security_score(self, issues: List[str]) -> int:
        """Calculate security score based on issues"""
        base_score = 100
        deductions = {
            "Limited network segmentation detected": -20,
            "No firewall rules defined": -30,
            "Overly permissive firewall rule": -10
        }

        score = base_score
        for issue in issues:
            for pattern, deduction in deductions.items():
                if pattern in issue:
                    score += deduction
                    break

        return max(0, min(100, score))  # Ensure score is between 0 and 100