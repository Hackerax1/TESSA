#!/usr/bin/env python3
"""
Goal-Based Setup Workflow for TESSA
Guides users through service selection and setup based on their goals
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import json

logger = logging.getLogger(__name__)

class GoalBasedSetupWizard:
    """
    A wizard to guide users through setting up services based on their goals
    or cloud services they want to replace.
    """
    
    def __init__(self, goal_based_catalog=None, dependency_manager=None, service_manager=None):
        """
        Initialize the goal-based setup wizard
        
        Args:
            goal_based_catalog: The goal-based catalog instance
            dependency_manager: The dependency manager instance
            service_manager: The service deployment manager instance
        """
        self.goal_based_catalog = goal_based_catalog
        self.dependency_manager = dependency_manager
        self.service_manager = service_manager
        self.setup_state = {}
        self.reset_state()
        
    def reset_state(self):
        """Reset the wizard state to defaults"""
        self.setup_state = {
            'stage': 'start',
            'approach': None,  # 'goals' or 'replacement'
            'selected_goals': [],
            'selected_replacements': [],
            'selected_services': {},
            'deployment_plan': [],
            'dependency_resolution': {},
            'resource_estimates': {},
            'current_step': 0,
            'total_steps': 5,
            'messages': []
        }
        
    def get_goal_categories(self) -> List[Dict]:
        """
        Get all available goal categories
        
        Returns:
            List of goal dictionaries
        """
        if not self.goal_based_catalog:
            return []
            
        goals = self.goal_based_catalog.get_goals_with_services()
        
        # Only include goals with services
        return [goal for goal in goals if goal['service_count'] > 0]
        
    def get_cloud_replacements(self) -> List[Dict]:
        """
        Get all available cloud service replacements
        
        Returns:
            List of cloud replacement dictionaries
        """
        if not self.goal_based_catalog:
            return []
            
        replacements = self.goal_based_catalog.get_cloud_replacements_with_services()
        
        # Only include cloud services with replacement options
        return [replacement for replacement in replacements if replacement['service_count'] > 0]
        
    def start_setup(self) -> Dict:
        """
        Begin the setup wizard
        
        Returns:
            State dictionary with welcome message and options
        """
        self.reset_state()
        self.setup_state['stage'] = 'approach_selection'
        self.setup_state['current_step'] = 1
        
        message = {
            "type": "welcome",
            "content": "Welcome to the TESSA goal-based setup wizard! I'll help you set up services based on what you want to accomplish.",
            "options": [
                {
                    "id": "goals",
                    "name": "I have specific goals I want to achieve",
                    "description": "Set up services based on what you want to accomplish, like managing photos or hosting a website."
                },
                {
                    "id": "replacement",
                    "name": "I want to replace cloud services",
                    "description": "Set up alternatives to specific cloud services like Google Drive, Dropbox, or Spotify."
                }
            ]
        }
        
        self.setup_state['messages'].append(message)
        return self.setup_state
        
    def select_approach(self, approach: str) -> Dict:
        """
        Select the setup approach (goals or replacements)
        
        Args:
            approach: Either 'goals' or 'replacement'
            
        Returns:
            Updated state dictionary
        """
        if approach not in ['goals', 'replacement']:
            self.setup_state['messages'].append({
                "type": "error",
                "content": f"Invalid approach: {approach}. Please select either 'goals' or 'replacement'."
            })
            return self.setup_state
            
        self.setup_state['approach'] = approach
        self.setup_state['current_step'] = 2
        
        if approach == 'goals':
            self.setup_state['stage'] = 'goal_selection'
            
            # Get available goal categories
            goals = self.get_goal_categories()
            
            message = {
                "type": "goal_options",
                "content": "What would you like to accomplish? Select one or more goals:",
                "options": []
            }
            
            for goal in goals:
                message["options"].append({
                    "id": goal['id'],
                    "name": goal['name'],
                    "description": goal['description'],
                    "service_count": goal['service_count']
                })
                
            self.setup_state['messages'].append(message)
            
        else:  # replacement
            self.setup_state['stage'] = 'replacement_selection'
            
            # Get available cloud replacements
            replacements = self.get_cloud_replacements()
            
            message = {
                "type": "replacement_options",
                "content": "Which cloud services would you like to replace? Select one or more:",
                "options": []
            }
            
            for replacement in replacements:
                message["options"].append({
                    "id": replacement['id'],
                    "name": replacement['name'],
                    "description": replacement['description'],
                    "service_count": replacement['service_count']
                })
                
            self.setup_state['messages'].append(message)
            
        return self.setup_state
            
    def select_goals(self, goal_ids: List[str]) -> Dict:
        """
        Select user goals
        
        Args:
            goal_ids: List of goal IDs
            
        Returns:
            Updated state dictionary
        """
        if self.setup_state['stage'] != 'goal_selection':
            self.setup_state['messages'].append({
                "type": "error",
                "content": "Invalid operation at current stage. Expected 'goal_selection'."
            })
            return self.setup_state
            
        # Validate goal IDs
        available_goals = self.get_goal_categories()
        available_goal_ids = [goal['id'] for goal in available_goals]
        
        valid_goal_ids = [goal_id for goal_id in goal_ids if goal_id in available_goal_ids]
        
        if not valid_goal_ids:
            self.setup_state['messages'].append({
                "type": "error",
                "content": "No valid goals selected. Please select at least one goal."
            })
            return self.setup_state
            
        self.setup_state['selected_goals'] = valid_goal_ids
        
        # Move to service selection
        return self._move_to_service_selection()
        
    def select_replacements(self, replacement_ids: List[str]) -> Dict:
        """
        Select cloud services to replace
        
        Args:
            replacement_ids: List of cloud service IDs
            
        Returns:
            Updated state dictionary
        """
        if self.setup_state['stage'] != 'replacement_selection':
            self.setup_state['messages'].append({
                "type": "error",
                "content": "Invalid operation at current stage. Expected 'replacement_selection'."
            })
            return self.setup_state
            
        # Validate replacement IDs
        available_replacements = self.get_cloud_replacements()
        available_replacement_ids = [r['id'] for r in available_replacements]
        
        valid_replacement_ids = [r_id for r_id in replacement_ids if r_id in available_replacement_ids]
        
        if not valid_replacement_ids:
            self.setup_state['messages'].append({
                "type": "error",
                "content": "No valid cloud services selected. Please select at least one service to replace."
            })
            return self.setup_state
            
        self.setup_state['selected_replacements'] = valid_replacement_ids
        
        # Move to service selection
        return self._move_to_service_selection()
        
    def _move_to_service_selection(self) -> Dict:
        """
        Internal method to move to the service selection stage
        
        Returns:
            Updated state dictionary
        """
        self.setup_state['stage'] = 'service_selection'
        self.setup_state['current_step'] = 3
        
        recommended_services = {}
        
        # Get recommended services based on approach
        if self.setup_state['approach'] == 'goals':
            # Get services for selected goals
            for goal_id in self.setup_state['selected_goals']:
                services = self.goal_based_catalog.get_services_for_goal(goal_id)
                
                for service in services:
                    service_id = service['id']
                    if service_id not in recommended_services:
                        recommended_services[service_id] = {
                            'id': service_id,
                            'name': service['name'],
                            'description': service['description'],
                            'goals': [],
                            'relevance': 'low',  # Will be updated to highest relevance
                            'replaces': []
                        }
                    
                    # Find the relevance for this goal
                    relevance = 'medium'
                    if 'user_goals' in service:
                        for goal in service['user_goals']:
                            if goal['id'] == goal_id:
                                relevance = goal.get('relevance', 'medium')
                                break
                                
                    # Use the highest relevance if this service meets multiple goals
                    relevance_order = {'high': 0, 'medium': 1, 'low': 2}
                    current_relevance = recommended_services[service_id]['relevance']
                    if relevance_order.get(relevance, 2) < relevance_order.get(current_relevance, 2):
                        recommended_services[service_id]['relevance'] = relevance
                        
                    # Add goal to service
                    goal_info = next((g for g in self.get_goal_categories() if g['id'] == goal_id), {})
                    recommended_services[service_id]['goals'].append({
                        'id': goal_id,
                        'name': goal_info.get('name', goal_id),
                        'relevance': relevance
                    })
                    
        else:  # replacement approach
            # Get services for selected cloud replacements
            for cloud_id in self.setup_state['selected_replacements']:
                services = self.goal_based_catalog.get_services_for_cloud_replacement(cloud_id)
                
                for service in services:
                    service_id = service['id']
                    if service_id not in recommended_services:
                        recommended_services[service_id] = {
                            'id': service_id,
                            'name': service['name'],
                            'description': service['description'],
                            'goals': [],
                            'relevance': 'low',
                            'replaces': []
                        }
                    
                    # Find the quality for this replacement
                    quality = 'good'
                    if 'replaces_services' in service:
                        for replacement in service['replaces_services']:
                            if replacement['id'] == cloud_id:
                                quality = replacement.get('quality', 'good')
                                break
                                
                    # Add replacement to service
                    cloud_info = next((r for r in self.get_cloud_replacements() if r['id'] == cloud_id), {})
                    recommended_services[service_id]['replaces'].append({
                        'id': cloud_id,
                        'name': cloud_info.get('name', cloud_id),
                        'quality': quality
                    })
        
        # Sort recommended services by relevance or number of replacements
        sorted_services = []
        
        if self.setup_state['approach'] == 'goals':
            # Sort by relevance and then by number of goals
            relevance_order = {'high': 0, 'medium': 1, 'low': 2}
            sorted_services = sorted(
                recommended_services.values(),
                key=lambda s: (relevance_order.get(s['relevance'], 2), -len(s['goals']))
            )
        else:
            # Sort by number of cloud services replaced
            sorted_services = sorted(
                recommended_services.values(),
                key=lambda s: -len(s['replaces'])
            )
        
        # Create service selection message
        message = {
            "type": "service_options",
            "content": "Based on your selections, here are the recommended services. Select the ones you want to install:",
            "options": sorted_services
        }
        
        self.setup_state['messages'].append(message)
        return self.setup_state
        
    def select_services(self, service_ids: List[str]) -> Dict:
        """
        Select services to install
        
        Args:
            service_ids: List of service IDs to install
            
        Returns:
            Updated state dictionary
        """
        if self.setup_state['stage'] != 'service_selection':
            self.setup_state['messages'].append({
                "type": "error",
                "content": "Invalid operation at current stage. Expected 'service_selection'."
            })
            return self.setup_state
        
        # Get the full service information for selected services
        selected_services = {}
        for service_id in service_ids:
            service = self.goal_based_catalog.service_catalog.get_service(service_id)
            if service:
                selected_services[service_id] = service
        
        if not selected_services:
            self.setup_state['messages'].append({
                "type": "error",
                "content": "No valid services selected. Please select at least one service to install."
            })
            return self.setup_state
            
        self.setup_state['selected_services'] = selected_services
        
        # Move to dependency resolution
        return self._resolve_dependencies_and_create_plan()
        
    def _resolve_dependencies_and_create_plan(self) -> Dict:
        """
        Internal method to resolve dependencies and create a deployment plan
        
        Returns:
            Updated state dictionary
        """
        self.setup_state['stage'] = 'review_plan'
        self.setup_state['current_step'] = 4
        
        # Build dependency graph
        if self.dependency_manager:
            self.dependency_manager.build_dependency_graph()
        
        # Create deployment plan with dependencies
        deployment_plan = []
        dependency_services = {}
        
        for service_id in self.setup_state['selected_services']:
            # Skip if already in the plan
            if service_id in [s['id'] for s in deployment_plan]:
                continue
                
            # Get full service information
            service = self.goal_based_catalog.service_catalog.get_service(service_id)
            
            if not service:
                continue
                
            # Add to plan
            service_entry = {
                'id': service_id,
                'name': service['name'],
                'description': service['description'],
                'is_dependency': False,
                'required_by': [],
                'vm_requirements': service.get('vm_requirements', {})
            }
            deployment_plan.append(service_entry)
            
            # Resolve dependencies if dependency manager exists
            if self.dependency_manager:
                # Get all required dependencies
                dependencies = self.dependency_manager.get_all_required_dependencies(service_id)
                
                for dep in dependencies:
                    dep_id = dep['id']
                    dep_service = self.goal_based_catalog.service_catalog.get_service(dep_id)
                    
                    if not dep_service:
                        continue
                        
                    # Check if dependency is already in the plan
                    existing_dep = next((s for s in deployment_plan if s['id'] == dep_id), None)
                    
                    if existing_dep:
                        # Update the existing dependency
                        existing_dep['is_dependency'] = True
                        existing_dep['required_by'].append(service_id)
                    else:
                        # Add new dependency to the plan
                        dep_entry = {
                            'id': dep_id,
                            'name': dep_service['name'],
                            'description': dep_service['description'],
                            'is_dependency': True,
                            'required_by': [service_id],
                            'vm_requirements': dep_service.get('vm_requirements', {})
                        }
                        deployment_plan.append(dep_entry)
                        
                    # Add to dependency services
                    dependency_services[dep_id] = dep_service
        
        # Get installation order if dependency manager exists
        if self.dependency_manager and deployment_plan:
            # Create a set of all service IDs in the plan
            all_service_ids = {s['id'] for s in deployment_plan}
            
            # Get installation order for all services
            final_plan = []
            for service_id in all_service_ids:
                # Get installation order for this service
                install_order = self.dependency_manager.get_installation_order(service_id)
                
                # Add services to final plan in order (if they're in our deployment plan)
                for dep_id in install_order:
                    if dep_id in all_service_ids:
                        service_entry = next((s for s in deployment_plan if s['id'] == dep_id), None)
                        if service_entry and service_entry not in final_plan:
                            final_plan.append(service_entry)
            
            # Replace deployment plan with ordered plan
            deployment_plan = final_plan
        
        # Calculate total resource requirements
        total_resources = {
            'cores': 0,
            'memory': 0,  # MB
            'disk': 0      # GB
        }
        
        for service in deployment_plan:
            requirements = service.get('vm_requirements', {})
            total_resources['cores'] += requirements.get('cores', 0)
            total_resources['memory'] += requirements.get('memory', 0)
            total_resources['disk'] += requirements.get('disk', 0)
        
        # Update state
        self.setup_state['deployment_plan'] = deployment_plan
        self.setup_state['dependency_services'] = dependency_services
        self.setup_state['resource_estimates'] = total_resources
        
        # Create deployment plan message
        message = {
            "type": "deployment_plan",
            "content": "Here's your deployment plan. Review it and confirm to proceed with installation:",
            "plan": deployment_plan,
            "resource_estimates": total_resources
        }
        
        self.setup_state['messages'].append(message)
        return self.setup_state
        
    def confirm_plan(self, confirmed: bool) -> Dict:
        """
        Confirm the deployment plan and start installation
        
        Args:
            confirmed: Whether the user confirmed the plan
            
        Returns:
            Updated state dictionary
        """
        if self.setup_state['stage'] != 'review_plan':
            self.setup_state['messages'].append({
                "type": "error",
                "content": "Invalid operation at current stage. Expected 'review_plan'."
            })
            return self.setup_state
            
        if not confirmed:
            self.setup_state['messages'].append({
                "type": "info",
                "content": "Installation canceled. You can start over or modify your selections."
            })
            return self.setup_state
            
        # Move to installation stage
        self.setup_state['stage'] = 'installation'
        self.setup_state['current_step'] = 5
        
        # Start installation if service manager exists
        if self.service_manager:
            installation_results = []
            
            # Install services in the order specified in the deployment plan
            for service in self.setup_state['deployment_plan']:
                service_id = service['id']
                
                try:
                    # Install the service
                    result = self.service_manager.deploy_service(service_id)
                    
                    installation_results.append({
                        'id': service_id,
                        'name': service['name'],
                        'success': result.get('success', False),
                        'message': result.get('message', 'Unknown result')
                    })
                    
                except Exception as e:
                    installation_results.append({
                        'id': service_id,
                        'name': service['name'],
                        'success': False,
                        'message': str(e)
                    })
                    
            # Update state with installation results
            self.setup_state['installation_results'] = installation_results
            
            # Create installation results message
            success_count = sum(1 for r in installation_results if r['success'])
            
            message = {
                "type": "installation_results",
                "content": f"Installation complete. Successfully installed {success_count} of {len(installation_results)} services.",
                "results": installation_results
            }
            
            self.setup_state['messages'].append(message)
            
        else:
            # No service manager, just show simulation message
            message = {
                "type": "installation_simulation",
                "content": "No service manager available. In a real deployment, the following services would be installed:",
                "services": [{'id': s['id'], 'name': s['name']} for s in self.setup_state['deployment_plan']]
            }
            
            self.setup_state['messages'].append(message)
            
        # Move to completion stage
        self.setup_state['stage'] = 'complete'
        
        # Add completion message
        message = {
            "type": "completion",
            "content": "Setup complete! Your services have been deployed based on your goals."
        }
        
        self.setup_state['messages'].append(message)
        return self.setup_state
        
    def get_current_state(self) -> Dict:
        """
        Get the current state of the setup wizard
        
        Returns:
            Current state dictionary
        """
        return self.setup_state
        
    def to_json(self) -> str:
        """
        Convert the current state to JSON
        
        Returns:
            JSON string representation of the state
        """
        return json.dumps(self.setup_state)
        
    @classmethod
    def from_json(cls, json_str: str, goal_based_catalog=None, dependency_manager=None, service_manager=None):
        """
        Create a wizard instance from a JSON state
        
        Args:
            json_str: JSON string representation of the state
            goal_based_catalog: The goal-based catalog instance
            dependency_manager: The dependency manager instance
            service_manager: The service deployment manager instance
            
        Returns:
            GoalBasedSetupWizard instance with restored state
        """
        wizard = cls(goal_based_catalog, dependency_manager, service_manager)
        
        try:
            wizard.setup_state = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error restoring wizard state: {str(e)}")
            
        return wizard