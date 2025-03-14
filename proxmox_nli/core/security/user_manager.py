"""
User manager module for handling user preferences and activity tracking.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..user_preferences import UserPreferencesManager
from ..dashboard_manager import DashboardManager
from ..profile_sync import ProfileSyncManager

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self, base_nli):
        self.user_preferences = base_nli.user_preferences
        self.nlu = base_nli.nlu
        self.audit_logger = base_nli.audit_logger
        self.dashboard_manager = DashboardManager()
        self.profile_sync_manager = ProfileSyncManager()

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
                
            # Load favorite commands
            favorite_commands = self.user_preferences.get_favorite_commands(user_id)
            if favorite_commands:
                self.nlu.context_manager.set_context({'favorite_commands': favorite_commands})
                
            # Load notification preferences
            notification_prefs = self.user_preferences.get_notification_preferences(user_id)
            if notification_prefs:
                self.nlu.context_manager.set_context({'notification_preferences': notification_prefs})
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
        favorite_commands = self.user_preferences.get_favorite_commands(user_id)
        notification_prefs = self.user_preferences.get_notification_preferences(user_id)
        dashboards = self.dashboard_manager.get_dashboards(user_id)
        
        return {
            "success": True,
            "stats": {
                "favorite_vms_count": len(favorite_vms),
                "favorite_nodes_count": len(favorite_nodes),
                "frequent_commands_count": len(frequent_commands),
                "favorite_commands_count": len(favorite_commands),
                "quick_services_count": len(quick_services),
                "notification_preferences_count": len(notification_prefs),
                "dashboards_count": len(dashboards),
                "favorite_vms": favorite_vms,
                "favorite_nodes": favorite_nodes,
                "frequent_commands": frequent_commands,
                "favorite_commands": favorite_commands,
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
    
    # Command history methods
    def add_to_command_history(self, user_id, command, intent=None, entities=None, success=True):
        """Add a command to the user's command history"""
        if not user_id:
            return {"success": False, "message": "User ID is required to add to command history"}
            
        result = self.user_preferences.add_to_command_history(user_id, command, intent, entities, success)
        if result:
            return {"success": True, "message": "Command added to history successfully"}
        return {"success": False, "message": "Failed to add command to history"}
    
    def get_command_history(self, user_id, limit=50, successful_only=False):
        """Get command history for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to get command history"}
            
        history = self.user_preferences.get_command_history(user_id, limit, successful_only)
        return {"success": True, "history": history}
    
    def clear_command_history(self, user_id):
        """Clear command history for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to clear command history"}
            
        result = self.user_preferences.clear_command_history(user_id)
        if result:
            return {"success": True, "message": "Command history cleared successfully"}
        return {"success": False, "message": "Failed to clear command history"}
    
    # Favorite commands methods
    def add_favorite_command(self, user_id, command_text, description=None):
        """Add a command to the user's favorites"""
        if not user_id:
            return {"success": False, "message": "User ID is required to add favorite command"}
            
        if not command_text:
            return {"success": False, "message": "Command text is required"}
            
        result = self.user_preferences.add_favorite_command(user_id, command_text, description)
        if result:
            return {"success": True, "message": "Command added to favorites successfully"}
        return {"success": False, "message": "Failed to add command to favorites"}
    
    def get_favorite_commands(self, user_id):
        """Get favorite commands for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to get favorite commands"}
            
        commands = self.user_preferences.get_favorite_commands(user_id)
        return {"success": True, "commands": commands}
    
    def remove_favorite_command(self, user_id, command_id):
        """Remove a command from the user's favorites"""
        if not user_id:
            return {"success": False, "message": "User ID is required to remove favorite command"}
            
        if not command_id:
            return {"success": False, "message": "Command ID is required"}
            
        result = self.user_preferences.remove_favorite_command(user_id, command_id)
        if result:
            return {"success": True, "message": "Command removed from favorites successfully"}
        return {"success": False, "message": "Failed to remove command from favorites"}
    
    # Notification preferences methods
    def set_notification_preference(self, user_id, event_type, channel, enabled):
        """Set notification preference for a specific event and channel"""
        if not user_id:
            return {"success": False, "message": "User ID is required to set notification preferences"}
            
        result = self.user_preferences.set_notification_preference(user_id, event_type, channel, enabled)
        if result:
            return {"success": True, "message": f"Notification preference updated successfully"}
        return {"success": False, "message": "Failed to update notification preference"}
    
    def get_notification_preferences(self, user_id):
        """Get all notification preferences for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to get notification preferences"}
            
        preferences = self.user_preferences.get_notification_preferences(user_id)
        
        # Group preferences by event type for better organization
        grouped_preferences = {}
        for pref in preferences:
            event_type = pref['event_type']
            if event_type not in grouped_preferences:
                grouped_preferences[event_type] = []
            grouped_preferences[event_type].append(pref)
            
        return {"success": True, "preferences": preferences, "grouped_preferences": grouped_preferences}
    
    def initialize_default_notification_preferences(self, user_id):
        """Initialize default notification preferences for a new user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to initialize preferences"}
            
        result = self.user_preferences.initialize_default_notification_preferences(user_id)
        if result:
            return {"success": True, "message": "Default notification preferences initialized successfully"}
        return {"success": False, "message": "Failed to initialize default notification preferences"}
    
    def get_notification_channels_for_event(self, user_id, event_type):
        """Get enabled notification channels for a specific event"""
        if not user_id or not event_type:
            return {"success": False, "message": "User ID and event type are required"}
            
        channels = self.user_preferences.get_notification_channels_for_event(user_id, event_type)
        return {"success": True, "channels": channels}
    
    # Dashboard methods
    def create_dashboard(self, user_id, name, is_default=False, layout="grid"):
        """Create a new dashboard for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to create a dashboard"}
            
        dashboard_id = self.dashboard_manager.create_dashboard(user_id, name, is_default, layout)
        if dashboard_id:
            return {"success": True, "message": f"Dashboard '{name}' created successfully", "dashboard_id": dashboard_id}
        return {"success": False, "message": f"Failed to create dashboard '{name}'"}
    
    def get_dashboards(self, user_id):
        """Get all dashboards for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to get dashboards"}
            
        dashboards = self.dashboard_manager.get_dashboards(user_id)
        return {"success": True, "dashboards": dashboards}
    
    def get_dashboard(self, dashboard_id):
        """Get a specific dashboard by ID"""
        if not dashboard_id:
            return {"success": False, "message": "Dashboard ID is required"}
            
        dashboard = self.dashboard_manager.get_dashboard(dashboard_id)
        if dashboard:
            return {"success": True, "dashboard": dashboard}
        return {"success": False, "message": "Dashboard not found"}
    
    def update_dashboard(self, dashboard_id, name=None, is_default=None, layout=None):
        """Update dashboard properties"""
        if not dashboard_id:
            return {"success": False, "message": "Dashboard ID is required"}
            
        result = self.dashboard_manager.update_dashboard(dashboard_id, name, is_default, layout)
        if result:
            return {"success": True, "message": "Dashboard updated successfully"}
        return {"success": False, "message": "Failed to update dashboard"}
    
    def delete_dashboard(self, dashboard_id):
        """Delete a dashboard"""
        if not dashboard_id:
            return {"success": False, "message": "Dashboard ID is required"}
            
        result = self.dashboard_manager.delete_dashboard(dashboard_id)
        if result:
            return {"success": True, "message": "Dashboard deleted successfully"}
        return {"success": False, "message": "Failed to delete dashboard"}
    
    def add_dashboard_panel(self, dashboard_id, panel_type, title, config=None, position_x=0, position_y=0, width=6, height=4):
        """Add a panel to a dashboard"""
        if not dashboard_id:
            return {"success": False, "message": "Dashboard ID is required"}
            
        panel_id = self.dashboard_manager.add_panel(dashboard_id, panel_type, title, config, position_x, position_y, width, height)
        if panel_id:
            return {"success": True, "message": f"Panel '{title}' added successfully", "panel_id": panel_id}
        return {"success": False, "message": f"Failed to add panel '{title}'"}
    
    def update_dashboard_panel(self, panel_id, title=None, config=None, position_x=None, position_y=None, width=None, height=None):
        """Update panel properties"""
        if not panel_id:
            return {"success": False, "message": "Panel ID is required"}
            
        result = self.dashboard_manager.update_panel(panel_id, title, config, position_x, position_y, width, height)
        if result:
            return {"success": True, "message": "Panel updated successfully"}
        return {"success": False, "message": "Failed to update panel"}
    
    def delete_dashboard_panel(self, panel_id):
        """Delete a panel from a dashboard"""
        if not panel_id:
            return {"success": False, "message": "Panel ID is required"}
            
        result = self.dashboard_manager.delete_panel(panel_id)
        if result:
            return {"success": True, "message": "Panel deleted successfully"}
        return {"success": False, "message": "Failed to delete panel"}
    
    def initialize_default_dashboard(self, user_id):
        """Initialize a default dashboard for a new user"""
        if not user_id:
            return {"success": False, "message": "User ID is required to initialize dashboard"}
            
        dashboard_id = self.dashboard_manager.initialize_default_dashboard(user_id)
        if dashboard_id:
            return {"success": True, "message": "Default dashboard initialized successfully", "dashboard_id": dashboard_id}
        return {"success": False, "message": "Failed to initialize default dashboard"}
    
    # Profile synchronization methods
    def sync_profile(self, user_id, device_id, sync_data=None):
        """Synchronize profile data between devices"""
        if not user_id or not device_id:
            return {"success": False, "message": "User ID and device ID are required"}
            
        if sync_data:
            # Upload sync data
            result = self.profile_sync_manager.update_sync_data(user_id, device_id, sync_data)
            if not result:
                return {"success": False, "message": "Failed to update sync data"}
        
        # Get latest sync data
        sync_result = self.profile_sync_manager.get_latest_sync_data(user_id, device_id)
        
        if sync_result:
            return {
                "success": True, 
                "message": "Profile synchronized successfully",
                "sync_data": sync_result.get("data", {}),
                "last_sync": sync_result.get("last_sync")
            }
        return {"success": False, "message": "Failed to synchronize profile"}
    
    def register_device(self, user_id, device_id, device_name, device_type):
        """Register a new device for profile synchronization"""
        if not user_id or not device_id:
            return {"success": False, "message": "User ID and device ID are required"}
            
        result = self.profile_sync_manager.register_device(user_id, device_id, device_name, device_type)
        if result:
            return {"success": True, "message": f"Device '{device_name}' registered successfully"}
        return {"success": False, "message": "Failed to register device"}
    
    def get_user_devices(self, user_id):
        """Get all devices registered for a user"""
        if not user_id:
            return {"success": False, "message": "User ID is required"}
            
        devices = self.profile_sync_manager.get_user_devices(user_id)
        return {"success": True, "devices": devices}
    
    def remove_device(self, user_id, device_id):
        """Remove a device from synchronization"""
        if not user_id or not device_id:
            return {"success": False, "message": "User ID and device ID are required"}
            
        result = self.profile_sync_manager.remove_device(user_id, device_id)
        if result:
            return {"success": True, "message": "Device removed successfully"}
        return {"success": False, "message": "Failed to remove device"}