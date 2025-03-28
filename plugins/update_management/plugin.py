"""
Update management plugin implementation.

This module registers update management commands with the Proxmox NLI system
and sets up the necessary intent handlers and entity extractors.
"""
import logging
from typing import Dict, List, Any, Optional

from proxmox_nli.commands.update_command import UpdateCommand
from proxmox_nli.services.update_manager import UpdateManager
from proxmox_nli.plugins.utils import (
    register_command, 
    register_intent_handler,
    register_entity_extractor
)

logger = logging.getLogger(__name__)

# Command handlers
def check_for_updates(nli, args, entities):
    """Check for updates for services."""
    # Extract service_id if specified
    service_id = None
    if "service" in entities:
        service_id = entities["service"]
    
    result = nli.update_command.check_updates(service_id)
    return {
        "success": True,
        "message": "Update check complete",
        "report": result.get("report", "Update check completed successfully."),
        "data": result
    }

def list_available_updates(nli, args, entities):
    """List available updates for services."""
    # Extract service_id if specified
    service_id = None
    if "service" in entities:
        service_id = entities["service"]
    
    result = nli.update_command.list_updates(service_id)
    return {
        "success": True,
        "message": "Updates listed",
        "report": result.get("report", "Here are the available updates."),
        "data": result
    }

def apply_updates(nli, args, entities):
    """Apply updates to services."""
    # Extract service_id if specified
    service_id = None
    specific_updates = None
    
    if "service" in entities:
        service_id = entities["service"]
    
    if "update_ids" in entities:
        specific_updates = entities["update_ids"]
    
    # Ask for confirmation before applying updates
    confirm_message = f"Are you sure you want to apply updates to {service_id if service_id else 'all services'}?"
    
    # Register the confirmation handler
    def confirmed_apply_updates():
        result = nli.update_command.apply_updates(service_id, specific_updates)
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Update operation completed."),
            "report": result.get("report", "Updates have been applied."),
            "data": result
        }
    
    return {
        "success": True,
        "requires_confirmation": True,
        "confirmation_message": confirm_message,
        "confirmation_handler": confirmed_apply_updates
    }

def generate_update_plan(nli, args, entities):
    """Generate an update plan for services."""
    # Extract service_id if specified
    service_id = None
    if "service" in entities:
        service_id = entities["service"]
    
    result = nli.update_command.generate_update_plan(service_id)
    return {
        "success": True,
        "message": "Update plan generated",
        "report": result.get("plan", "Here is the update plan."),
        "data": result
    }

def get_update_status(nli, args, entities):
    """Get the current status of the update system."""
    result = nli.update_command.get_update_status()
    return {
        "success": True,
        "message": "Update status retrieved",
        "report": result.get("report", "Here is the current update status."),
        "data": result
    }

def schedule_updates(nli, args, entities):
    """Schedule updates to be applied at a specified time."""
    # Extract service_id and schedule_time if specified
    service_id = None
    schedule_time = None
    
    if "service" in entities:
        service_id = entities["service"]
    
    if "time" in entities:
        schedule_time = entities["time"]
    
    result = nli.update_command.schedule_updates(service_id, schedule_time)
    return {
        "success": True,
        "message": "Updates scheduled",
        "report": result.get("report", f"Updates for {service_id if service_id else 'all services'} have been scheduled."),
        "data": result
    }

# Plugin initialization
def initialize(nli):
    """
    Initialize the update management plugin.
    
    Args:
        nli: The Proxmox NLI instance
    """
    try:
        logger.info("Initializing update management plugin")
        
        # Create the update manager instance
        if not hasattr(nli, "update_manager"):
            # Get the service manager from the NLI instance
            service_manager = getattr(nli, "service_manager", None)
            if not service_manager:
                logger.error("Service manager not found in NLI instance")
                return False
                
            nli.update_manager = UpdateManager(service_manager)
            
        # Create the update command instance
        if not hasattr(nli, "update_command"):
            nli.update_command = UpdateCommand(nli.update_manager)
        
        # Register commands
        register_command(nli, "check_updates", check_for_updates, 
                        "Check for updates for services")
        register_command(nli, "list_updates", list_available_updates,
                        "List available updates for services")
        register_command(nli, "apply_updates", apply_updates,
                        "Apply updates to services")
        register_command(nli, "update_plan", generate_update_plan,
                        "Generate an update plan for services")
        register_command(nli, "update_status", get_update_status,
                        "Get the current status of the update system")
        register_command(nli, "schedule_updates", schedule_updates,
                        "Schedule updates to be applied at a specified time")
        
        # Register intent handlers
        register_intent_handler(nli, "check_for_updates", check_for_updates)
        register_intent_handler(nli, "list_updates", list_available_updates)
        register_intent_handler(nli, "apply_updates", apply_updates)
        register_intent_handler(nli, "generate_update_plan", generate_update_plan)
        register_intent_handler(nli, "get_update_status", get_update_status)
        register_intent_handler(nli, "schedule_updates", schedule_updates)
        
        # Register entity extractors for update-related entities
        register_entity_extractor(nli, "service", [
            r"for\s+(\w+)",
            r"to\s+(\w+)",
            r"update\s+(\w+)",
            r"(\w+)\s+service",
            r"service\s+(\w+)"
        ])
        
        register_entity_extractor(nli, "time", [
            r"at\s+([\w\s:]+)",
            r"on\s+([\w\s:]+)",
            r"during\s+([\w\s]+)",
            r"(tonight|tomorrow|later|next week)",
            r"(\d{1,2}(?::\d{2})?\s*(?:am|pm))",
            r"(\d{1,2}(?::\d{2})?\s*(?:AM|PM))"
        ])
        
        register_entity_extractor(nli, "update_ids", [
            r"updates?\s+(\d+(?:,\s*\d+)*)",
            r"ids?\s+(\d+(?:,\s*\d+)*)"
        ])
        
        # Start the update checking thread
        nli.update_manager.start_checking()
        
        logger.info("Update management plugin initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize update management plugin: {str(e)}")
        return False

def cleanup(nli):
    """
    Clean up the update management plugin.
    
    Args:
        nli: The Proxmox NLI instance
    """
    try:
        if hasattr(nli, "update_manager"):
            nli.update_manager.stop_checking()
        logger.info("Update management plugin cleaned up")
        return True
    except Exception as e:
        logger.error(f"Failed to clean up update management plugin: {str(e)}")
        return False