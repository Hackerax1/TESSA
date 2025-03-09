"""
Service deployment wizard for Proxmox NLI.
Provides interactive guidance for deploying services with best practices.
"""
import logging
from typing import Dict, List, Optional
from ..services.service_catalog import ServiceCatalog
from ..services.dependency_manager import DependencyManager
from ..services.goal_based_catalog import GoalBasedCatalog
from ..services.goal_based_setup import GoalBasedSetupWizard
from ..services.goal_mapper import GoalMapper

logger = logging.getLogger(__name__)

class ServiceWizard:
    def __init__(self, api, service_catalog=None):
        self.api = api
        self.catalog = service_catalog if service_catalog else ServiceCatalog()
        self.dependency_manager = DependencyManager(self.catalog)
        self.goal_mapper = GoalMapper()
        self.goal_based_catalog = GoalBasedCatalog(self.catalog, self.goal_mapper)
        self.goal_based_wizard = None
        
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
        
    def start_goal_based_wizard(self) -> Dict:
        """
        Start the goal-based setup wizard to help users select services
        based on their goals or cloud services they want to replace.
        
        Returns:
            Dictionary with wizard state and initial options
        """
        # Initialize the goal-based wizard
        self.goal_based_wizard = GoalBasedSetupWizard(
            goal_based_catalog=self.goal_based_catalog,
            dependency_manager=self.dependency_manager,
            service_manager=self
        )
        
        # Start the wizard and get initial state
        wizard_state = self.goal_based_wizard.start_setup()
        
        return {
            "success": True,
            "message": "Goal-based setup wizard started",
            "wizard_state": wizard_state
        }
    
    def process_goal_wizard_step(self, action: str, data: Dict) -> Dict:
        """
        Process a step in the goal-based wizard flow
        
        Args:
            action: The action to perform (e.g., 'select_approach', 'select_goals')
            data: The data for the action
            
        Returns:
            Dictionary with updated wizard state
        """
        if not self.goal_based_wizard:
            return {
                "success": False,
                "message": "Goal-based wizard not initialized. Call start_goal_based_wizard first."
            }
            
        try:
            # Process the action based on the current wizard stage
            if action == 'select_approach':
                approach = data.get('approach')
                if not approach:
                    return {"success": False, "message": "No approach selected"}
                wizard_state = self.goal_based_wizard.select_approach(approach)
                
            elif action == 'select_goals':
                goal_ids = data.get('goal_ids', [])
                if not goal_ids:
                    return {"success": False, "message": "No goals selected"}
                wizard_state = self.goal_based_wizard.select_goals(goal_ids)
                
            elif action == 'select_replacements':
                replacement_ids = data.get('replacement_ids', [])
                if not replacement_ids:
                    return {"success": False, "message": "No cloud services selected"}
                wizard_state = self.goal_based_wizard.select_replacements(replacement_ids)
                
            elif action == 'select_services':
                service_ids = data.get('service_ids', [])
                if not service_ids:
                    return {"success": False, "message": "No services selected"}
                wizard_state = self.goal_based_wizard.select_services(service_ids)
                
            elif action == 'confirm_plan':
                confirmed = data.get('confirmed', False)
                wizard_state = self.goal_based_wizard.confirm_plan(confirmed)
                
            else:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}"
                }
                
            return {
                "success": True,
                "message": f"Processed {action} successfully",
                "wizard_state": wizard_state
            }
            
        except Exception as e:
            logger.error(f"Error processing goal wizard step: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing {action}: {str(e)}"
            }
    
    def get_available_goals(self) -> Dict:
        """
        Get all available user goals for the goal-based wizard
        
        Returns:
            Dictionary with available goals
        """
        goals = self.goal_based_catalog.get_goals_with_services()
        
        return {
            "success": True,
            "goals": goals
        }
        
    def get_available_cloud_replacements(self) -> Dict:
        """
        Get all available cloud service replacements for the goal-based wizard
        
        Returns:
            Dictionary with available cloud service replacements
        """
        replacements = self.goal_based_catalog.get_cloud_replacements_with_services()
        
        return {
            "success": True,
            "replacements": replacements
        }
    
    def deploy_service(self, service_id: str, config: Dict = None) -> Dict:
        """
        Deploy a service using the provided configuration
        
        Args:
            service_id: ID of the service to deploy
            config: Optional configuration for the service
            
        Returns:
            Dictionary with deployment result
        """
        try:
            # Get service definition
            service = self.catalog.get_service(service_id)
            if not service:
                return {
                    "success": False,
                    "message": f"Service '{service_id}' not found"
                }
                
            # Use default configuration if none provided
            if not config:
                config = self._generate_default_config(service)
                
            # Here you would actually deploy the service
            # This is a placeholder - actual implementation would use the API
            logger.info(f"Deploying service {service_id} with config: {config}")
            
            # Simulate successful deployment
            return {
                "success": True,
                "message": f"Service {service['name']} deployed successfully",
                "service_id": service_id,
                "config": config
            }
                
        except Exception as e:
            logger.error(f"Error deploying service {service_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Error deploying service: {str(e)}"
            }
    
    def _generate_default_config(self, service_def: Dict) -> Dict:
        """Generate default configuration for a service"""
        vm_requirements = service_def.get('vm_requirements', {})
        
        return {
            "vm": {
                "memory": vm_requirements.get('memory', 1024),  # MB
                "cores": vm_requirements.get('cores', 1),
                "disk": vm_requirements.get('disk', 10)  # GB
            },
            "network": self._generate_network_config("internal"),
            "security": self._generate_security_config("enhanced"),
            "backup": {
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