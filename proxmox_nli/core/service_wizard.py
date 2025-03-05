"""
Service deployment wizard for Proxmox NLI.
Provides interactive guidance for deploying services with best practices.
"""
import logging
from typing import Dict, List, Optional
from ..services.service_catalog import ServiceCatalog

logger = logging.getLogger(__name__)

class ServiceWizard:
    def __init__(self, api, service_catalog=None):
        self.api = api
        self.catalog = service_catalog if service_catalog else ServiceCatalog()
        
    def start_wizard(self, service_type: str) -> Dict:
        """Start the service deployment wizard"""
        # Find matching services
        matches = self.catalog.find_services_by_keywords(service_type)
        if not matches:
            return {
                "success": False,
                "message": f"No matching services found for '{service_type}'"
            }
        
        # Get service definition
        service_def = matches[0]  # Use first match for now
        
        # Generate deployment questions
        questions = self._generate_questions(service_def)
        
        return {
            "success": True,
            "message": "Service wizard started",
            "service": service_def,
            "questions": questions
        }
    
    def _generate_questions(self, service_def: Dict) -> List[Dict]:
        """Generate configuration questions based on service definition"""
        questions = []
        
        # Resource allocation questions
        if 'vm_requirements' in service_def:
            questions.extend([
                {
                    "id": "memory",
                    "type": "number",
                    "message": "How much memory (in GB) do you want to allocate?",
                    "default": service_def['vm_requirements'].get('memory', 1024) / 1024,
                    "min": 0.5,
                    "recommendations": [
                        {"value": 1, "description": "Minimal (testing only)"},
                        {"value": 2, "description": "Standard usage"},
                        {"value": 4, "description": "Heavy usage"}
                    ]
                },
                {
                    "id": "cores",
                    "type": "number",
                    "message": "How many CPU cores do you want to allocate?",
                    "default": service_def['vm_requirements'].get('cores', 1),
                    "min": 1,
                    "recommendations": [
                        {"value": 1, "description": "Basic usage"},
                        {"value": 2, "description": "Standard usage"},
                        {"value": 4, "description": "High performance"}
                    ]
                },
                {
                    "id": "disk",
                    "type": "number",
                    "message": "How much disk space (in GB) do you need?",
                    "default": service_def['vm_requirements'].get('disk', 10),
                    "min": 5,
                    "recommendations": [
                        {"value": 10, "description": "Minimal"},
                        {"value": 20, "description": "Standard"},
                        {"value": 50, "description": "Large"}
                    ]
                }
            ])
        
        # Network configuration questions
        questions.extend([
            {
                "id": "network_type",
                "type": "choice",
                "message": "What type of network access does this service need?",
                "choices": [
                    {"id": "internal", "name": "Internal only (no external access)"},
                    {"id": "external", "name": "External access (internet facing)"},
                    {"id": "isolated", "name": "Isolated network (custom VLAN)"}
                ],
                "default": "internal"
            }
        ])
        
        # Security questions
        questions.extend([
            {
                "id": "security_level",
                "type": "choice",
                "message": "What security level do you need?",
                "choices": [
                    {"id": "basic", "name": "Basic (standard firewall rules)"},
                    {"id": "enhanced", "name": "Enhanced (with intrusion detection)"},
                    {"id": "maximum", "name": "Maximum (with auditing and monitoring)"}
                ],
                "default": "enhanced"
            },
            {
                "id": "backup_enabled",
                "type": "boolean",
                "message": "Do you want to enable automated backups?",
                "default": True
            }
        ])
        
        # Service-specific questions
        if 'configuration_options' in service_def:
            for option in service_def['configuration_options']:
                questions.append({
                    "id": option['id'],
                    "type": option.get('type', 'string'),
                    "message": option['message'],
                    "default": option.get('default'),
                    "choices": option.get('choices'),
                    "required": option.get('required', False)
                })
        
        return questions
    
    def process_answers(self, service_def: Dict, answers: Dict) -> Dict:
        """Process wizard answers and generate deployment configuration"""
        try:
            # Validate answers
            if not self._validate_answers(answers):
                return {
                    "success": False,
                    "message": "Invalid or incomplete answers provided"
                }
            
            # Generate VM configuration
            vm_config = {
                'memory': int(float(answers['memory']) * 1024),  # Convert GB to MB
                'cores': int(answers['cores']),
                'disk': int(answers['disk'])
            }
            
            # Generate network configuration
            network_config = self._generate_network_config(answers['network_type'])
            
            # Generate security configuration
            security_config = self._generate_security_config(answers['security_level'])
            
            # Generate backup configuration
            backup_config = None
            if answers.get('backup_enabled', True):
                backup_config = {
                    "schedule": {
                        "frequency": "daily",
                        "time": "02:00",
                        "retention": {
                            "daily": 7,
                            "weekly": 4,
                            "monthly": 2
                        }
                    }
                }
            
            # Combine configurations
            deployment_config = {
                "service": service_def['id'],
                "vm": vm_config,
                "network": network_config,
                "security": security_config,
                "backup": backup_config,
                "custom_config": {
                    k: v for k, v in answers.items() 
                    if k not in ['memory', 'cores', 'disk', 'network_type', 'security_level', 'backup_enabled']
                }
            }
            
            return {
                "success": True,
                "message": "Deployment configuration generated successfully",
                "config": deployment_config,
                "next_steps": self._generate_next_steps(deployment_config)
            }
            
        except Exception as e:
            logger.error(f"Error processing wizard answers: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing answers: {str(e)}"
            }
    
    def _validate_answers(self, answers: Dict) -> bool:
        """Validate wizard answers"""
        required_fields = ['memory', 'cores', 'disk', 'network_type', 'security_level']
        return all(field in answers for field in required_fields)
    
    def _generate_network_config(self, network_type: str) -> Dict:
        """Generate network configuration based on type"""
        configs = {
            "internal": {
                "type": "internal",
                "firewall": {
                    "incoming": "reject",
                    "outgoing": "accept",
                    "rules": [
                        {"action": "accept", "source": "internal"}
                    ]
                },
                "dns": "internal"
            },
            "external": {
                "type": "external",
                "firewall": {
                    "incoming": "reject",
                    "outgoing": "accept",
                    "rules": [
                        {"action": "accept", "source": "internal"},
                        {"action": "accept", "source": "external", "dest_port": "80,443"}
                    ]
                },
                "dns": "public"
            },
            "isolated": {
                "type": "isolated",
                "vlan": self._get_next_vlan_id(),
                "firewall": {
                    "incoming": "reject",
                    "outgoing": "reject",
                    "rules": [
                        {"action": "accept", "source": "internal", "dest": "isolated"}
                    ]
                },
                "dns": "custom"
            }
        }
        return configs.get(network_type, configs["internal"])
    
    def _generate_security_config(self, security_level: str) -> Dict:
        """Generate security configuration based on level"""
        configs = {
            "basic": {
                "firewall": True,
                "selinux": "permissive",
                "updates": "security",
                "monitoring": "basic"
            },
            "enhanced": {
                "firewall": True,
                "selinux": "enforcing",
                "updates": "all",
                "monitoring": "enhanced",
                "ids": True,
                "fail2ban": True
            },
            "maximum": {
                "firewall": True,
                "selinux": "enforcing",
                "updates": "all",
                "monitoring": "full",
                "ids": True,
                "fail2ban": True,
                "audit": True,
                "rootkit_detection": True,
                "vulnerability_scanning": True
            }
        }
        return configs.get(security_level, configs["basic"])
    
    def _get_next_vlan_id(self) -> int:
        """Get next available VLAN ID"""
        # This is a placeholder - actual implementation would check existing VLANs
        return 100
    
    def _generate_next_steps(self, config: Dict) -> List[str]:
        """Generate list of next steps for deployment"""
        steps = [
            "1. Review the generated configuration",
            "2. Create the VM with specified resources",
            "3. Apply network configuration",
            "4. Set up security measures",
        ]
        
        if config['network']['type'] == "external":
            steps.extend([
                "5. Configure reverse proxy",
                "6. Set up SSL certificates"
            ])
        
        if config.get('backup'):
            steps.append("7. Initialize backup configuration")
        
        steps.extend([
            f"8. Deploy {config['service']} service",
            "9. Verify service is running correctly",
            "10. Test security measures"
        ])
        
        return steps