"""
User manager module for handling user preferences and activity tracking.
"""
from .base_nli import BaseNLI

class UserManager(BaseNLI):
    def _load_user_context(self, user_id):
        """Load user preferences into the context manager"""
        if not user_id:
            return
            
        try:
            # Load favorite VMs
            favorite_vms = self.user_preferences.get_favorite_vms(user_id)
            if favorite_vms:
                self.nlu.context_manager.set_context({'favorite_vms': favorite_vms})
                
            # Load favorite nodes
            favorite_nodes = self.user_preferences.get_favorite_nodes(user_id)
            if favorite_nodes:
                self.nlu.context_manager.set_context({'favorite_nodes': favorite_nodes})
                
            # Load quick access services
            quick_services = self.user_preferences.get_quick_access_services(user_id)
            if quick_services:
                self.nlu.context_manager.set_context({'quick_services': quick_services})
                
            # Load general preferences
            all_prefs = self.user_preferences.get_all_preferences(user_id)
            if all_prefs:
                self.nlu.context_manager.set_context({'user_preferences': all_prefs})
        except Exception as e:
            import logging
            logging.error(f"Error loading user preferences: {e}")
    
    def set_user_preference(self, user_id, key, value):
        """Set a user preference"""
        if not user_id:
            return {"success": False, "message": "User ID is required to set preferences"}
            
        success = self.user_preferences.set_preference(user_id, key, value)
        if success:
            return {"success": True, "message": f"Preference '{key}' has been set successfully"}
        return {"success": False, "message": f"Failed to set preference '{key}'"}
    
    def get_user_preferences(self, user_id):
        """Get all preferences for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to get preferences"}
            
        prefs = self.user_preferences.get_all_preferences(user_id)
        return {"success": True, "preferences": prefs}
    
    def get_user_statistics(self, user_id):
        """Get usage statistics for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to get statistics"}
            
        favorite_vms = self.user_preferences.get_favorite_vms(user_id)
        favorite_nodes = self.user_preferences.get_favorite_nodes(user_id)
        frequent_commands = self.user_preferences.get_frequent_commands(user_id)
        quick_services = self.user_preferences.get_quick_access_services(user_id)
        
        return {
            "success": True,
            "stats": {
                "favorite_vms_count": len(favorite_vms),
                "favorite_nodes_count": len(favorite_nodes),
                "frequent_commands_count": len(frequent_commands),
                "quick_services_count": len(quick_services),
                "favorite_vms": favorite_vms,
                "favorite_nodes": favorite_nodes,
                "frequent_commands": frequent_commands,
                "quick_services": quick_services
            }
        }

    def get_recent_activity(self, limit=100):
        """Get recent command executions"""
        return self.audit_logger.get_recent_logs(limit)

    def get_user_activity(self, user, limit=100):
        """Get recent activity for a specific user"""
        return self.audit_logger.get_user_activity(user, limit)

    def get_failed_commands(self, limit=100):
        """Get recent failed command executions"""
        return self.audit_logger.get_failed_commands(limit)