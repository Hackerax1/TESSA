"""
Utility functions for Proxmox NLI plugins.

This module provides helper functions for plugin developers to interact with
the Proxmox NLI system.
"""
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

logger = logging.getLogger(__name__)


def register_command(nli, command_name: str, command_func: Callable, help_text: str = None):
    """
    Register a new command with the NLI system.
    
    Args:
        nli: The Proxmox NLI instance
        command_name (str): The name of the command
        command_func (Callable): The function to execute for this command
        help_text (str, optional): Help text for the command
    
    Returns:
        bool: True if the command was registered successfully, False otherwise
    """
    try:
        # Make sure the command doesn't already exist
        if hasattr(nli.commands, command_name) or hasattr(nli.docker_commands, command_name):
            logger.error(f"Command {command_name} already exists")
            return False
            
        # Add command to nli.commands
        setattr(nli.commands, command_name, command_func)
        
        # Add help text if provided
        if help_text and hasattr(nli, "help_texts"):
            nli.help_texts[command_name] = help_text
            
        logger.info(f"Registered command: {command_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to register command {command_name}: {str(e)}")
        return False


def register_intent_handler(nli, intent_name: str, handler_func: Callable):
    """
    Register a new intent handler with the NLI system.
    
    Args:
        nli: The Proxmox NLI instance
        intent_name (str): The name of the intent
        handler_func (Callable): The function to execute for this intent
    
    Returns:
        bool: True if the intent handler was registered successfully, False otherwise
    """
    try:
        # Get the NLU engine
        nlu_engine = nli.nlu
        
        # Register the intent handler
        if hasattr(nlu_engine, "register_intent_handler"):
            nlu_engine.register_intent_handler(intent_name, handler_func)
            logger.info(f"Registered intent handler: {intent_name}")
            return True
        else:
            logger.error("NLU engine does not support registering intent handlers")
            return False
            
    except Exception as e:
        logger.error(f"Failed to register intent handler {intent_name}: {str(e)}")
        return False


def register_entity_extractor(nli, entity_type: str, patterns: List[str]):
    """
    Register a new entity extraction pattern with the NLU system.
    
    Args:
        nli: The Proxmox NLI instance
        entity_type (str): The type of entity to extract
        patterns (List[str]): List of regex patterns for extraction
    
    Returns:
        bool: True if the entity extractor was registered successfully, False otherwise
    """
    try:
        # Get the NLU engine
        nlu_engine = nli.nlu
        
        # Get the entity extractor
        if hasattr(nlu_engine, "entity_extractor"):
            entity_extractor = nlu_engine.entity_extractor
            
            # Register the entity type and patterns
            if hasattr(entity_extractor, "entity_types"):
                entity_extractor.entity_types.add(entity_type)
                
            if hasattr(entity_extractor, "patterns"):
                entity_extractor.patterns[entity_type] = patterns
                
            logger.info(f"Registered entity extractor: {entity_type}")
            return True
        else:
            logger.error("NLU engine does not have an entity extractor")
            return False
            
    except Exception as e:
        logger.error(f"Failed to register entity extractor {entity_type}: {str(e)}")
        return False


def register_web_route(nli, route_path: str, handler_func: Callable, methods: List[str] = None):
    """
    Register a new web route with the NLI system.
    
    Args:
        nli: The Proxmox NLI instance
        route_path (str): The URL path for the route (e.g., "/api/plugin/myfeature")
        handler_func (Callable): The function to handle requests to this route
        methods (List[str], optional): HTTP methods to allow (default: ["GET"])
    
    Returns:
        bool: True if the route was registered successfully, False otherwise
    """
    try:
        if not methods:
            methods = ["GET"]
            
        # Try to get the Flask app
        if hasattr(nli, "app"):
            app = nli.app
            app.route(route_path, methods=methods)(handler_func)
            logger.info(f"Registered web route: {route_path}")
            return True
        else:
            logger.error("NLI instance does not have a Flask app")
            return False
            
    except Exception as e:
        logger.error(f"Failed to register web route {route_path}: {str(e)}")
        return False


def add_service_to_catalog(nli, service_name: str, service_definition: Dict[str, Any]):
    """
    Add a new service to the service catalog.
    
    Args:
        nli: The Proxmox NLI instance
        service_name (str): The name of the service
        service_definition (Dict[str, Any]): The service definition
    
    Returns:
        bool: True if the service was added successfully, False otherwise
    """
    try:
        # Get the service catalog
        if hasattr(nli, "service_catalog"):
            service_catalog = nli.service_catalog
            
            # Add the service to the catalog
            if hasattr(service_catalog, "add_service"):
                service_catalog.add_service(service_name, service_definition)
                logger.info(f"Added service to catalog: {service_name}")
                return True
            else:
                logger.error("Service catalog does not support adding services")
                return False
        else:
            logger.error("NLI instance does not have a service catalog")
            return False
            
    except Exception as e:
        logger.error(f"Failed to add service to catalog {service_name}: {str(e)}")
        return False


def get_plugin_data_path(plugin_name: str) -> str:
    """
    Get the data directory path for a plugin.
    
    Args:
        plugin_name (str): The name of the plugin
    
    Returns:
        str: The absolute path to the plugin's data directory
    """
    import os
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    plugin_data_path = os.path.join(base_path, "data", "plugins", plugin_name)
    
    # Create the directory if it doesn't exist
    os.makedirs(plugin_data_path, exist_ok=True)
    
    return plugin_data_path