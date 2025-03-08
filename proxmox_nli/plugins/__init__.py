"""
Plugin system for Proxmox NLI.

This module provides a plugin system for extending the Proxmox NLI functionality
through third-party plugins.
"""

from .base_plugin import BasePlugin
from .plugin_manager import PluginManager
from .utils import (
    register_command,
    register_intent_handler,
    register_entity_extractor,
    register_web_route,
    add_service_to_catalog,
    get_plugin_data_path
)

__all__ = [
    'BasePlugin',
    'PluginManager',
    'register_command',
    'register_intent_handler',
    'register_entity_extractor',
    'register_web_route',
    'add_service_to_catalog',
    'get_plugin_data_path'
]