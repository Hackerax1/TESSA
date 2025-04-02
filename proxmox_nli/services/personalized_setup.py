#!/usr/bin/env python3
"""
Personalized Setup Journey for TESSA
Provides customized setup experiences based on user expertise
"""

import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Set

from proxmox_nli.core.knowledge_system import KnowledgeSystem

logger = logging.getLogger(__name__)

class PersonalizedSetupJourney:
    """
    A system for providing personalized setup journeys based on user expertise,
    integrating with the knowledge system to adapt the experience.
    """
    
    def __init__(self, knowledge_system: KnowledgeSystem = None, goal_based_catalog=None):
        """
        Initialize the personalized setup journey
        
        Args:
            knowledge_system: Knowledge system instance
            goal_based_catalog: Goal-based catalog instance
        """
        self.knowledge_system = knowledge_system
        self.goal_based_catalog = goal_based_catalog
        self.journey_templates = self._load_journey_templates()
        self.active_journeys = {}
        
    def _load_journey_templates(self) -> Dict:
        """
        Load journey templates from the built-in definitions
        
        Returns:
            Dictionary of journey templates
        """
        # Define the journey templates for different expertise levels
        return {
            "beginner": {
                "name": "Beginner's Journey",
                "description": "A guided journey for those new to self-hosting and Proxmox",
                "steps": [
                    {
                        "id": "intro",
                        "name": "Introduction to TESSA",
                        "description": "Learn about TESSA and how it can help you manage your home server",
                        "type": "tutorial",
                        "content": "Welcome to TESSA! This guided journey will help you set up your home server with ease. We'll start with the basics and gradually introduce more advanced concepts as you become comfortable.",
                        "duration_minutes": 5
                    },
                    {
                        "id": "goals",
                        "name": "Define Your Goals",
                        "description": "Identify what you want to accomplish with your home server",
                        "type": "interactive",
                        "content": "Let's start by understanding what you want to accomplish with your home server. This will help us recommend the right services and configurations for you.",
                        "action": "goal_selection",
                        "duration_minutes": 10
                    },
                    {
                        "id": "hardware_check",
                        "name": "Hardware Check",
                        "description": "Verify your hardware is compatible and properly configured",
                        "type": "interactive",
                        "content": "Let's check your hardware to make sure it's compatible with the services you want to run. We'll also help you optimize your hardware configuration.",
                        "action": "hardware_check",
                        "duration_minutes": 15
                    },
                    {
                        "id": "networking_basics",
                        "name": "Networking Basics",
                        "description": "Learn about basic networking concepts for your home server",
                        "type": "tutorial",
                        "content": "Understanding basic networking concepts is important for setting up your home server. We'll cover IP addresses, ports, and basic network configuration.",
                        "knowledge_area": "networking",
                        "duration_minutes": 20
                    },
                    {
                        "id": "service_selection",
                        "name": "Service Selection",
                        "description": "Choose services based on your goals",
                        "type": "interactive",
                        "content": "Based on your goals, we'll recommend services that will help you accomplish them. You can select which ones you want to install.",
                        "action": "service_selection",
                        "duration_minutes": 15
                    },
                    {
                        "id": "installation",
                        "name": "Installation",
                        "description": "Install selected services",
                        "type": "interactive",
                        "content": "Now we'll install the services you selected. This may take some time depending on your internet connection and hardware.",
                        "action": "installation",
                        "duration_minutes": 30
                    },
                    {
                        "id": "basic_usage",
                        "name": "Basic Usage",
                        "description": "Learn how to use your newly installed services",
                        "type": "tutorial",
                        "content": "Now that your services are installed, let's learn how to use them. We'll cover the basics of accessing and managing your services.",
                        "duration_minutes": 20
                    },
                    {
                        "id": "next_steps",
                        "name": "Next Steps",
                        "description": "Learn about what to do next",
                        "type": "tutorial",
                        "content": "Congratulations on setting up your home server! Here are some next steps you might want to consider to get the most out of your setup.",
                        "duration_minutes": 10
                    }
                ],
                "total_duration_minutes": 125,
                "ui_simplification": True,
                "explanation_detail": "basic",
                "automation_level": "high"
            },
            "intermediate": {
                "name": "Intermediate Journey",
                "description": "A balanced journey for those with some experience in self-hosting or Proxmox",
                "steps": [
                    {
                        "id": "intro",
                        "name": "Introduction to TESSA",
                        "description": "Learn about TESSA's capabilities",
                        "type": "tutorial",
                        "content": "Welcome to TESSA! This journey is designed for users with some experience in self-hosting or Proxmox. We'll help you set up a robust home server environment tailored to your needs.",
                        "duration_minutes": 3
                    },
                    {
                        "id": "goals",
                        "name": "Define Your Goals",
                        "description": "Identify what you want to accomplish with your home server",
                        "type": "interactive",
                        "content": "Let's start by understanding your specific goals for your home server. This will help us recommend the right services and configurations.",
                        "action": "goal_selection",
                        "duration_minutes": 8
                    },
                    {
                        "id": "hardware_optimization",
                        "name": "Hardware Optimization",
                        "description": "Optimize your hardware configuration",
                        "type": "interactive",
                        "content": "Let's optimize your hardware configuration for the services you plan to run. We'll help you allocate resources efficiently.",
                        "action": "hardware_optimization",
                        "duration_minutes": 12
                    },
                    {
                        "id": "networking_setup",
                        "name": "Network Configuration",
                        "description": "Configure networking for optimal performance and security",
                        "type": "interactive",
                        "content": "Now let's configure your network settings for optimal performance and security. We'll cover VLANs, firewall rules, and reverse proxy setup.",
                        "action": "network_configuration",
                        "knowledge_area": "networking",
                        "duration_minutes": 20
                    },
                    {
                        "id": "service_selection",
                        "name": "Service Selection and Configuration",
                        "description": "Choose and configure services based on your goals",
                        "type": "interactive",
                        "content": "Based on your goals, we'll recommend services that will help you accomplish them. You can select which ones you want to install and configure them to your needs.",
                        "action": "service_selection_config",
                        "duration_minutes": 20
                    },
                    {
                        "id": "installation",
                        "name": "Installation and Integration",
                        "description": "Install selected services and integrate them",
                        "type": "interactive",
                        "content": "Now we'll install the services you selected and help you integrate them with each other. This may take some time depending on your internet connection and hardware.",
                        "action": "installation_integration",
                        "duration_minutes": 25
                    },
                    {
                        "id": "backup_setup",
                        "name": "Backup Configuration",
                        "description": "Set up automated backups for your services",
                        "type": "interactive",
                        "content": "Let's set up automated backups for your services to ensure your data is protected. We'll help you configure backup schedules and retention policies.",
                        "action": "backup_configuration",
                        "knowledge_area": "backup",
                        "duration_minutes": 15
                    },
                    {
                        "id": "monitoring_setup",
                        "name": "Monitoring Setup",
                        "description": "Configure monitoring for your services",
                        "type": "interactive",
                        "content": "Now let's set up monitoring for your services to keep track of their health and performance. We'll help you configure alerts for important events.",
                        "action": "monitoring_setup",
                        "duration_minutes": 15
                    },
                    {
                        "id": "advanced_features",
                        "name": "Advanced Features",
                        "description": "Explore advanced features of your services",
                        "type": "tutorial",
                        "content": "Now that your services are set up, let's explore some advanced features that can enhance your experience.",
                        "duration_minutes": 15
                    }
                ],
                "total_duration_minutes": 133,
                "ui_simplification": False,
                "explanation_detail": "detailed",
                "automation_level": "medium"
            },
            "advanced": {
                "name": "Advanced Journey",
                "description": "An in-depth journey for experienced users who want to build a sophisticated setup",
                "steps": [
                    {
                        "id": "intro",
                        "name": "Introduction to TESSA's Advanced Capabilities",
                        "description": "Learn about TESSA's advanced features",
                        "type": "tutorial",
                        "content": "Welcome to TESSA's advanced setup journey. This path is designed for experienced users who want to build a sophisticated home server environment with advanced configurations and optimizations.",
                        "duration_minutes": 2
                    },
                    {
                        "id": "goals",
                        "name": "Define Your Goals and Requirements",
                        "description": "Specify detailed goals and technical requirements",
                        "type": "interactive",
                        "content": "Let's start by defining your specific goals and technical requirements. This will help us create a tailored setup that meets your advanced needs.",
                        "action": "detailed_goal_selection",
                        "duration_minutes": 10
                    },
                    {
                        "id": "architecture_planning",
                        "name": "Architecture Planning",
                        "description": "Design your server architecture",
                        "type": "interactive",
                        "content": "Let's design your server architecture to meet your requirements. We'll help you plan VM/container distribution, resource allocation, and network topology.",
                        "action": "architecture_planning",
                        "duration_minutes": 25
                    },
                    {
                        "id": "network_design",
                        "name": "Network Design",
                        "description": "Design your network topology",
                        "type": "interactive",
                        "content": "Now let's design your network topology. We'll help you plan VLANs, subnets, routing, and firewall rules for optimal security and performance.",
                        "action": "network_design",
                        "knowledge_area": "networking",
                        "duration_minutes": 30
                    },
                    {
                        "id": "storage_planning",
                        "name": "Storage Planning",
                        "description": "Design your storage architecture",
                        "type": "interactive",
                        "content": "Let's design your storage architecture. We'll help you plan storage pools, volumes, and backup strategies based on your performance and reliability requirements.",
                        "action": "storage_planning",
                        "knowledge_area": "storage",
                        "duration_minutes": 20
                    },
                    {
                        "id": "service_selection",
                        "name": "Service Selection and Integration",
                        "description": "Choose services and plan their integration",
                        "type": "interactive",
                        "content": "Based on your architecture, let's select services and plan their integration. We'll help you identify dependencies and potential conflicts.",
                        "action": "advanced_service_selection",
                        "duration_minutes": 20
                    },
                    {
                        "id": "deployment",
                        "name": "Deployment",
                        "description": "Deploy your architecture with Infrastructure as Code",
                        "type": "interactive",
                        "content": "Now we'll deploy your architecture using Infrastructure as Code principles. This approach ensures reproducibility and version control of your configuration.",
                        "action": "iac_deployment",
                        "duration_minutes": 40
                    },
                    {
                        "id": "security_hardening",
                        "name": "Security Hardening",
                        "description": "Implement advanced security measures",
                        "type": "interactive",
                        "content": "Let's implement advanced security measures to protect your environment. We'll cover authentication, authorization, encryption, and intrusion detection.",
                        "action": "security_hardening",
                        "knowledge_area": "security",
                        "duration_minutes": 30
                    },
                    {
                        "id": "monitoring_and_alerting",
                        "name": "Advanced Monitoring and Alerting",
                        "description": "Set up comprehensive monitoring and alerting",
                        "type": "interactive",
                        "content": "Let's set up comprehensive monitoring and alerting for your environment. We'll help you configure metrics collection, visualization, and alert routing.",
                        "action": "advanced_monitoring",
                        "duration_minutes": 25
                    },
                    {
                        "id": "disaster_recovery",
                        "name": "Disaster Recovery Planning",
                        "description": "Create a disaster recovery plan",
                        "type": "interactive",
                        "content": "Let's create a disaster recovery plan for your environment. We'll help you design backup strategies, recovery procedures, and testing protocols.",
                        "action": "disaster_recovery",
                        "knowledge_area": "backup",
                        "duration_minutes": 20
                    },
                    {
                        "id": "automation",
                        "name": "Automation",
                        "description": "Implement automation for routine tasks",
                        "type": "interactive",
                        "content": "Let's implement automation for routine tasks in your environment. We'll help you create scripts and workflows for common operations.",
                        "action": "automation_setup",
                        "duration_minutes": 25
                    }
                ],
                "total_duration_minutes": 247,
                "ui_simplification": False,
                "explanation_detail": "technical",
                "automation_level": "low"
            },
            "expert": {
                "name": "Expert Journey",
                "description": "A customizable journey for experts who want full control over their setup",
                "steps": [
                    {
                        "id": "intro",
                        "name": "Expert Mode Overview",
                        "description": "Overview of expert mode capabilities",
                        "type": "tutorial",
                        "content": "Welcome to TESSA's expert mode. This mode provides maximum flexibility and control over your setup, with minimal hand-holding. You'll have access to all advanced features and configuration options.",
                        "duration_minutes": 2
                    },
                    {
                        "id": "custom_architecture",
                        "name": "Custom Architecture Definition",
                        "description": "Define your custom architecture",
                        "type": "interactive",
                        "content": "Define your custom architecture using our advanced tools. You can specify VM/container distribution, resource allocation, network topology, and storage architecture.",
                        "action": "custom_architecture",
                        "duration_minutes": 30
                    },
                    {
                        "id": "infrastructure_as_code",
                        "name": "Infrastructure as Code Setup",
                        "description": "Set up Infrastructure as Code for your environment",
                        "type": "interactive",
                        "content": "Set up Infrastructure as Code for your environment. You can use Terraform, Ansible, or custom scripts to define and deploy your infrastructure.",
                        "action": "iac_setup",
                        "duration_minutes": 45
                    },
                    {
                        "id": "custom_deployment",
                        "name": "Custom Deployment",
                        "description": "Deploy your custom architecture",
                        "type": "interactive",
                        "content": "Deploy your custom architecture using your preferred methods. You have full control over the deployment process.",
                        "action": "custom_deployment",
                        "duration_minutes": 60
                    },
                    {
                        "id": "advanced_integration",
                        "name": "Advanced Integration",
                        "description": "Integrate your services with external systems",
                        "type": "interactive",
                        "content": "Integrate your services with external systems and custom workflows. You can define complex integration patterns and data flows.",
                        "action": "advanced_integration",
                        "duration_minutes": 40
                    },
                    {
                        "id": "custom_monitoring",
                        "name": "Custom Monitoring and Observability",
                        "description": "Set up custom monitoring and observability",
                        "type": "interactive",
                        "content": "Set up custom monitoring and observability for your environment. You can define custom metrics, dashboards, and alerting rules.",
                        "action": "custom_monitoring",
                        "duration_minutes": 35
                    }
                ],
                "total_duration_minutes": 212,
                "ui_simplification": False,
                "explanation_detail": "comprehensive",
                "automation_level": "minimal"
            }
        }
        
    def start_journey(self, user_id: str, expertise_level: str = None) -> Dict:
        """
        Start a personalized setup journey for a user
        
        Args:
            user_id: User ID to start journey for
            expertise_level: Optional expertise level override
            
        Returns:
            Journey state dictionary
        """
        # Determine expertise level
        if not expertise_level and self.knowledge_system:
            expertise_level = self.knowledge_system.get_user_expertise_level(user_id)
        
        if not expertise_level or expertise_level not in self.journey_templates:
            expertise_level = "beginner"  # Default to beginner if no valid level provided
            
        # Create journey state
        journey = {
            "user_id": user_id,
            "journey_id": f"journey_{user_id}_{int(time.time())}",
            "template_id": expertise_level,
            "template_name": self.journey_templates[expertise_level]["name"],
            "current_step_index": 0,
            "steps": self.journey_templates[expertise_level]["steps"],
            "completed_steps": [],
            "started_at": int(time.time()),
            "last_updated": int(time.time()),
            "status": "in_progress",
            "ui_settings": {
                "simplification": self.journey_templates[expertise_level]["ui_simplification"],
                "explanation_detail": self.journey_templates[expertise_level]["explanation_detail"],
                "automation_level": self.journey_templates[expertise_level]["automation_level"]
            }
        }
        
        # Store active journey
        self.active_journeys[user_id] = journey
        
        return journey
        
    def get_current_step(self, user_id: str) -> Dict:
        """
        Get the current step in the user's journey
        
        Args:
            user_id: User ID to get step for
            
        Returns:
            Current step dictionary
        """
        if user_id not in self.active_journeys:
            return None
            
        journey = self.active_journeys[user_id]
        
        if journey["current_step_index"] >= len(journey["steps"]):
            return None
            
        return journey["steps"][journey["current_step_index"]]
        
    def advance_to_next_step(self, user_id: str) -> Dict:
        """
        Advance to the next step in the user's journey
        
        Args:
            user_id: User ID to advance journey for
            
        Returns:
            Updated journey state dictionary
        """
        if user_id not in self.active_journeys:
            return None
            
        journey = self.active_journeys[user_id]
        
        # Mark current step as completed
        current_step = self.get_current_step(user_id)
        if current_step:
            journey["completed_steps"].append({
                "step_id": current_step["id"],
                "completed_at": int(time.time())
            })
            
            # Update knowledge if applicable
            if self.knowledge_system and "knowledge_area" in current_step:
                self.knowledge_system.record_completed_lesson(
                    user_id, 
                    current_step["knowledge_area"],
                    current_step["id"]
                )
            
        # Advance to next step
        journey["current_step_index"] += 1
        journey["last_updated"] = int(time.time())
        
        # Check if journey is complete
        if journey["current_step_index"] >= len(journey["steps"]):
            journey["status"] = "completed"
            journey["completed_at"] = int(time.time())
            
        return journey
        
    def go_to_step(self, user_id: str, step_id: str) -> Dict:
        """
        Go to a specific step in the user's journey
        
        Args:
            user_id: User ID to update journey for
            step_id: Step ID to go to
            
        Returns:
            Updated journey state dictionary
        """
        if user_id not in self.active_journeys:
            return None
            
        journey = self.active_journeys[user_id]
        
        # Find step index
        step_index = next((i for i, step in enumerate(journey["steps"]) if step["id"] == step_id), None)
        
        if step_index is None:
            return journey
            
        # Update current step
        journey["current_step_index"] = step_index
        journey["last_updated"] = int(time.time())
        
        return journey
        
    def get_journey_progress(self, user_id: str) -> Dict:
        """
        Get the progress of the user's journey
        
        Args:
            user_id: User ID to get progress for
            
        Returns:
            Journey progress dictionary
        """
        if user_id not in self.active_journeys:
            return None
            
        journey = self.active_journeys[user_id]
        
        # Calculate progress
        total_steps = len(journey["steps"])
        completed_steps = len(journey["completed_steps"])
        
        if total_steps == 0:
            percent_complete = 0
        else:
            percent_complete = (completed_steps / total_steps) * 100
            
        # Calculate estimated time remaining
        if journey["status"] == "completed":
            time_remaining_minutes = 0
        else:
            remaining_steps = journey["steps"][journey["current_step_index"]:]
            time_remaining_minutes = sum(step.get("duration_minutes", 10) for step in remaining_steps)
            
        return {
            "journey_id": journey["journey_id"],
            "template_name": journey["template_name"],
            "current_step_index": journey["current_step_index"],
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "percent_complete": percent_complete,
            "time_remaining_minutes": time_remaining_minutes,
            "status": journey["status"]
        }
        
    def customize_journey(self, user_id: str, customizations: Dict) -> Dict:
        """
        Customize the user's journey
        
        Args:
            user_id: User ID to customize journey for
            customizations: Dictionary of customizations
            
        Returns:
            Updated journey state dictionary
        """
        if user_id not in self.active_journeys:
            return None
            
        journey = self.active_journeys[user_id]
        
        # Apply customizations
        if "add_steps" in customizations:
            for step in customizations["add_steps"]:
                journey["steps"].append(step)
                
        if "remove_steps" in customizations:
            journey["steps"] = [step for step in journey["steps"] if step["id"] not in customizations["remove_steps"]]
            
        if "reorder_steps" in customizations:
            # Create a new ordered list based on the provided order
            new_order = customizations["reorder_steps"]
            ordered_steps = []
            
            # Add steps in the specified order
            for step_id in new_order:
                step = next((s for s in journey["steps"] if s["id"] == step_id), None)
                if step:
                    ordered_steps.append(step)
                    
            # Add any remaining steps not specified in the order
            for step in journey["steps"]:
                if step["id"] not in new_order:
                    ordered_steps.append(step)
                    
            journey["steps"] = ordered_steps
            
        if "ui_settings" in customizations:
            for key, value in customizations["ui_settings"].items():
                if key in journey["ui_settings"]:
                    journey["ui_settings"][key] = value
                    
        # Update journey
        journey["last_updated"] = int(time.time())
        journey["is_customized"] = True
        
        return journey
        
    def get_recommended_journey(self, user_id: str) -> str:
        """
        Get the recommended journey template for a user
        
        Args:
            user_id: User ID to get recommendation for
            
        Returns:
            Recommended journey template ID
        """
        if not self.knowledge_system:
            return "beginner"
            
        # Get expertise level from knowledge system
        expertise_level = self.knowledge_system.get_user_expertise_level(user_id)
        
        # Map expertise level to journey template
        if expertise_level == "beginner":
            return "beginner"
        elif expertise_level == "intermediate":
            return "intermediate"
        elif expertise_level == "advanced":
            return "advanced"
        else:  # expert
            return "expert"
            
    def adapt_ui_for_user(self, user_id: str) -> Dict:
        """
        Get UI adaptation recommendations for a user
        
        Args:
            user_id: User ID to get adaptations for
            
        Returns:
            UI adaptation dictionary
        """
        if not self.knowledge_system:
            return {
                "simplification": True,
                "explanation_detail": "basic",
                "automation_level": "high",
                "show_advanced_features": False
            }
            
        # Get expertise level from knowledge system
        expertise_level = self.knowledge_system.get_user_expertise_level(user_id)
        
        # Create UI adaptations based on expertise
        adaptations = {
            "simplification": expertise_level == "beginner",
            "explanation_detail": self.knowledge_system.get_explanation_detail_level(user_id),
            "automation_level": "high" if expertise_level == "beginner" else "medium" if expertise_level == "intermediate" else "low",
            "show_advanced_features": self.knowledge_system.should_show_advanced_features(user_id)
        }
        
        # Add specific area adaptations
        adaptations["area_adaptations"] = {}
        
        for area_id in ["virtualization", "containers", "networking", "storage", "security", "backup"]:
            show_advanced = self.knowledge_system.should_show_advanced_features(user_id, area_id)
            explanation_level = self.knowledge_system.get_explanation_detail_level(user_id, area_id)
            
            adaptations["area_adaptations"][area_id] = {
                "show_advanced_features": show_advanced,
                "explanation_detail": explanation_level
            }
            
        return adaptations
