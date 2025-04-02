#!/usr/bin/env python3
"""
User Experience Controller
Manages the integration of personalized setup journeys, knowledge system, and configuration validation
"""

import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Set, Tuple

from proxmox_nli.core.knowledge_system import KnowledgeSystem
from proxmox_nli.core.config_validation import ConfigValidator
from proxmox_nli.services.personalized_setup import PersonalizedSetupJourney
from proxmox_nli.services.goal_based_setup import GoalBasedSetupWizard

logger = logging.getLogger(__name__)

class UserExperienceController:
    """
    Controller that integrates personalized setup journeys, knowledge system,
    and configuration validation to provide a cohesive user experience
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the user experience controller
        
        Args:
            config_dir: Directory where configurations are stored
        """
        self.config_dir = config_dir or os.path.join(os.path.expanduser("~"), ".tessa", "configs")
        
        # Initialize components
        self.knowledge_system = KnowledgeSystem()
        self.config_validator = ConfigValidator(self.config_dir)
        self.goal_based_wizard = GoalBasedSetupWizard()
        self.personalized_journey = PersonalizedSetupJourney(
            knowledge_system=self.knowledge_system,
            goal_based_catalog=self.goal_based_wizard
        )
        
        # User state tracking
        self.user_states = {}
        
    def initialize_user(self, user_id: str) -> Dict:
        """
        Initialize a new user in the system
        
        Args:
            user_id: User ID to initialize
            
        Returns:
            User state dictionary
        """
        # Check if user already exists
        if user_id in self.user_states:
            return self.user_states[user_id]
            
        # Initialize knowledge profile
        knowledge_profile = self.knowledge_system.initialize_user(user_id)
        
        # Create user state
        user_state = {
            "user_id": user_id,
            "created_at": int(time.time()),
            "last_active": int(time.time()),
            "knowledge_profile": knowledge_profile,
            "active_journey": None,
            "completed_journeys": [],
            "configuration_history": [],
            "ui_preferences": {
                "theme": "light",
                "simplification": True,
                "explanation_detail": "basic",
                "automation_level": "high"
            }
        }
        
        # Store user state
        self.user_states[user_id] = user_state
        
        return user_state
        
    def get_user_state(self, user_id: str) -> Dict:
        """
        Get the current state for a user
        
        Args:
            user_id: User ID to get state for
            
        Returns:
            User state dictionary
        """
        if user_id not in self.user_states:
            return self.initialize_user(user_id)
            
        return self.user_states[user_id]
        
    def update_user_activity(self, user_id: str) -> None:
        """
        Update the last activity timestamp for a user
        
        Args:
            user_id: User ID to update
        """
        if user_id in self.user_states:
            self.user_states[user_id]["last_active"] = int(time.time())
            
    def start_personalized_journey(self, user_id: str, expertise_level: str = None) -> Dict:
        """
        Start a personalized setup journey for a user
        
        Args:
            user_id: User ID to start journey for
            expertise_level: Optional expertise level override
            
        Returns:
            Journey state dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Start journey
        journey = self.personalized_journey.start_journey(user_id, expertise_level)
        
        # Update user state
        self.user_states[user_id]["active_journey"] = journey["journey_id"]
        self.update_user_activity(user_id)
        
        return journey
        
    def get_current_journey_step(self, user_id: str) -> Dict:
        """
        Get the current step in the user's journey
        
        Args:
            user_id: User ID to get step for
            
        Returns:
            Current step dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            return None
            
        # Get current step
        return self.personalized_journey.get_current_step(user_id)
        
    def advance_journey(self, user_id: str) -> Dict:
        """
        Advance to the next step in the user's journey
        
        Args:
            user_id: User ID to advance journey for
            
        Returns:
            Updated journey state dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            return None
            
        # Advance journey
        journey = self.personalized_journey.advance_to_next_step(user_id)
        
        # Update user state
        if journey and journey["status"] == "completed":
            self.user_states[user_id]["completed_journeys"].append(journey["journey_id"])
            self.user_states[user_id]["active_journey"] = None
            
        self.update_user_activity(user_id)
        
        return journey
        
    def get_journey_progress(self, user_id: str) -> Dict:
        """
        Get the progress of the user's journey
        
        Args:
            user_id: User ID to get progress for
            
        Returns:
            Journey progress dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            return None
            
        # Get journey progress
        return self.personalized_journey.get_journey_progress(user_id)
        
    def customize_journey(self, user_id: str, customizations: Dict) -> Dict:
        """
        Customize the user's journey
        
        Args:
            user_id: User ID to customize journey for
            customizations: Dictionary of customizations
            
        Returns:
            Updated journey state dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            return None
            
        # Customize journey
        journey = self.personalized_journey.customize_journey(user_id, customizations)
        
        self.update_user_activity(user_id)
        
        return journey
        
    def validate_configuration(self, config_type: str, config_id: str, config_data: Dict) -> Dict:
        """
        Validate a configuration and create a backup if valid
        
        Args:
            config_type: Type of configuration (vm, container, etc.)
            config_id: ID of the configuration
            config_data: Configuration data
            
        Returns:
            Validation result dictionary
        """
        # Validate configuration
        is_valid, errors, backup_id = self.config_validator.validate_and_backup(
            config_type, config_id, config_data
        )
        
        result = {
            "valid": is_valid,
            "errors": errors,
            "backup_id": backup_id
        }
        
        # Check dependencies if basic validation passed
        if is_valid:
            deps_valid, dep_errors = self.config_validator.validate_dependencies(
                config_type, config_data
            )
            
            result["dependencies_valid"] = deps_valid
            result["dependency_errors"] = dep_errors
            
        return result
        
    def rollback_configuration(self, user_id: str, backup_id: str) -> Dict:
        """
        Rollback to a previous configuration
        
        Args:
            user_id: User ID performing the rollback
            backup_id: ID of the backup to rollback to
            
        Returns:
            Rollback result dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            return {"success": False, "message": "User not found"}
            
        # Rollback configuration
        success, message = self.config_validator.rollback_config(backup_id)
        
        # Update user state
        if success:
            backup = self.config_validator.get_backup(backup_id)
            
            if backup:
                self.user_states[user_id]["configuration_history"].append({
                    "action": "rollback",
                    "timestamp": int(time.time()),
                    "config_type": backup["metadata"]["config_type"],
                    "config_id": backup["metadata"]["config_id"],
                    "backup_id": backup_id
                })
                
        self.update_user_activity(user_id)
        
        return {
            "success": success,
            "message": message
        }
        
    def get_configuration_history(self, user_id: str, config_type: str = None, config_id: str = None) -> List[Dict]:
        """
        Get the history of configuration changes for a user
        
        Args:
            user_id: User ID to get history for
            config_type: Optional type of configuration to filter by
            config_id: Optional ID of configuration to filter by
            
        Returns:
            List of configuration history entries
        """
        # Ensure user exists
        if user_id not in self.user_states:
            return []
            
        history = self.user_states[user_id]["configuration_history"]
        
        # Apply filters
        if config_type:
            history = [entry for entry in history if entry["config_type"] == config_type]
            
        if config_id:
            history = [entry for entry in history if entry["config_id"] == config_id]
            
        return history
        
    def get_configuration_backups(self, config_type: str = None, config_id: str = None) -> List[Dict]:
        """
        Get available configuration backups
        
        Args:
            config_type: Optional type of configuration to filter by
            config_id: Optional ID of configuration to filter by
            
        Returns:
            List of backup metadata
        """
        return self.config_validator.list_backups(config_type, config_id)
        
    def compare_configurations(self, current_config: Dict, backup_id: str) -> Dict:
        """
        Compare current configuration with a backup
        
        Args:
            current_config: Current configuration data
            backup_id: ID of the backup to compare with
            
        Returns:
            Dictionary of differences
        """
        backup = self.config_validator.get_backup(backup_id)
        
        if not backup:
            return {"error": f"Backup {backup_id} not found"}
            
        return self.config_validator.compare_configs(backup["config"], current_config)
        
    def update_ui_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """
        Update UI preferences for a user
        
        Args:
            user_id: User ID to update preferences for
            preferences: Dictionary of preferences
            
        Returns:
            Updated UI preferences dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Update preferences
        for key, value in preferences.items():
            if key in self.user_states[user_id]["ui_preferences"]:
                self.user_states[user_id]["ui_preferences"][key] = value
                
        self.update_user_activity(user_id)
        
        return self.user_states[user_id]["ui_preferences"]
        
    def get_ui_adaptations(self, user_id: str) -> Dict:
        """
        Get UI adaptation recommendations for a user
        
        Args:
            user_id: User ID to get adaptations for
            
        Returns:
            UI adaptation dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Get adaptations
        adaptations = self.personalized_journey.adapt_ui_for_user(user_id)
        
        self.update_user_activity(user_id)
        
        return adaptations
        
    def record_learning_activity(self, user_id: str, knowledge_area: str, activity_type: str, details: Dict = None) -> Dict:
        """
        Record a learning activity for a user
        
        Args:
            user_id: User ID to record activity for
            knowledge_area: Knowledge area the activity relates to
            activity_type: Type of activity (lesson, practice, etc.)
            details: Optional details about the activity
            
        Returns:
            Updated knowledge area dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Record activity
        result = self.knowledge_system.record_learning_activity(
            user_id, knowledge_area, activity_type, details or {}
        )
        
        self.update_user_activity(user_id)
        
        return result
        
    def get_learning_recommendations(self, user_id: str) -> List[Dict]:
        """
        Get learning recommendations for a user
        
        Args:
            user_id: User ID to get recommendations for
            
        Returns:
            List of recommended learning activities
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Get recommendations
        recommendations = self.knowledge_system.get_learning_recommendations(user_id)
        
        self.update_user_activity(user_id)
        
        return recommendations
        
    def get_expertise_summary(self, user_id: str) -> Dict:
        """
        Get a summary of the user's expertise
        
        Args:
            user_id: User ID to get summary for
            
        Returns:
            Expertise summary dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Get expertise summary
        summary = self.knowledge_system.get_expertise_summary(user_id)
        
        self.update_user_activity(user_id)
        
        return summary
        
    def start_goal_based_setup(self, user_id: str) -> Dict:
        """
        Start a goal-based setup for a user
        
        Args:
            user_id: User ID to start setup for
            
        Returns:
            Setup state dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Start setup
        setup_state = self.goal_based_wizard.start_setup()
        
        self.update_user_activity(user_id)
        
        return setup_state
        
    def process_goal_selection(self, user_id: str, goals: List[str]) -> Dict:
        """
        Process goal selection for a user
        
        Args:
            user_id: User ID to process goals for
            goals: List of selected goals
            
        Returns:
            Updated setup state dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Process goal selection
        setup_state = self.goal_based_wizard.process_goal_selection(goals)
        
        self.update_user_activity(user_id)
        
        return setup_state
        
    def get_goal_based_recommendations(self, user_id: str) -> Dict:
        """
        Get service recommendations based on user goals
        
        Args:
            user_id: User ID to get recommendations for
            
        Returns:
            Recommendations dictionary
        """
        # Ensure user exists
        if user_id not in self.user_states:
            self.initialize_user(user_id)
            
        # Get recommendations
        recommendations = self.goal_based_wizard.get_recommendations()
        
        # Adapt recommendations based on user expertise
        expertise_level = self.knowledge_system.get_user_expertise_level(user_id)
        
        # Simplify recommendations for beginners
        if expertise_level == "beginner":
            # Filter out complex services
            if "services" in recommendations:
                recommendations["services"] = [
                    service for service in recommendations["services"]
                    if service.get("complexity", "advanced") != "advanced"
                ]
                
            # Add beginner-friendly notes
            recommendations["beginner_notes"] = True
            
        self.update_user_activity(user_id)
        
        return recommendations
