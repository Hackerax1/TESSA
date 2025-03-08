"""
Plugin manager for Proxmox NLI.

This module provides functionality for discovering, loading, and managing
plugins for the Proxmox NLI system.
"""
import os
import sys
import json
import logging
import importlib
import importlib.util
from typing import Dict, List, Any, Optional, Type, Set
from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class PluginManager:
    """
    Plugin manager for Proxmox NLI.
    
    This class handles plugin discovery, loading, initialization,
    and lifecycle management.
    """
    
    def __init__(self, base_nli):
        """
        Initialize the plugin manager.
        
        Args:
            base_nli: The BaseNLI instance that will be provided to plugins
        """
        self.base_nli = base_nli
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_dirs: List[str] = []
        self.disabled_plugins: Set[str] = set()
        self._setup_plugin_directories()
        self._load_plugin_config()
        
    def _setup_plugin_directories(self):
        """Set up the plugin directories."""
        # Get the base path of the project
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Built-in plugins directory
        built_in_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "builtin")
        
        # User plugins directory
        user_dir = os.path.join(base_path, "plugins")
        
        # Add directories if they exist
        if os.path.exists(built_in_dir) and os.path.isdir(built_in_dir):
            self.plugin_dirs.append(built_in_dir)
        
        if os.path.exists(user_dir) and os.path.isdir(user_dir):
            self.plugin_dirs.append(user_dir)
        
        # Create user plugins directory if it doesn't exist
        if not os.path.exists(user_dir):
            try:
                os.makedirs(user_dir)
                self.plugin_dirs.append(user_dir)
            except Exception as e:
                logger.error(f"Failed to create user plugins directory: {str(e)}")
    
    def _load_plugin_config(self):
        """Load the plugin configuration."""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")
        config_file = os.path.join(config_dir, "plugins.json")
        
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir)
            except Exception as e:
                logger.error(f"Failed to create config directory: {str(e)}")
                return
        
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    self.disabled_plugins = set(config.get("disabled_plugins", []))
            except Exception as e:
                logger.error(f"Failed to load plugin configuration: {str(e)}")
    
    def _save_plugin_config(self):
        """Save the plugin configuration."""
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")
        config_file = os.path.join(config_dir, "plugins.json")
        
        try:
            config = {
                "disabled_plugins": list(self.disabled_plugins)
            }
            
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save plugin configuration: {str(e)}")
    
    def discover_plugins(self) -> Dict[str, Type[BasePlugin]]:
        """
        Discover available plugins in the plugin directories.
        
        Returns:
            Dict[str, Type[BasePlugin]]: A dictionary of plugin names to plugin classes
        """
        discovered_plugins = {}
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir) or not os.path.isdir(plugin_dir):
                continue
                
            # Search for plugin modules in the directory
            for item in os.listdir(plugin_dir):
                item_path = os.path.join(plugin_dir, item)
                
                # Skip if not a directory or doesn't contain plugin.py
                plugin_module_path = os.path.join(item_path, "plugin.py")
                if not os.path.isdir(item_path) or not os.path.exists(plugin_module_path):
                    continue
                    
                # Try to load the plugin module
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"proxmox_nli_plugin_{item}",
                        plugin_module_path
                    )
                    if spec is None or spec.loader is None:
                        logger.error(f"Failed to load plugin {item}: invalid spec")
                        continue
                        
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = module
                    spec.loader.exec_module(module)
                    
                    # Find plugin class in the module
                    plugin_class = None
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) 
                            and issubclass(attr, BasePlugin) 
                            and attr is not BasePlugin):
                            plugin_class = attr
                            break
                    
                    if plugin_class:
                        discovered_plugins[item] = plugin_class
                    else:
                        logger.error(f"Failed to load plugin {item}: no plugin class found")
                        
                except Exception as e:
                    logger.error(f"Failed to load plugin {item}: {str(e)}")
        
        return discovered_plugins
    
    def load_plugins(self) -> None:
        """
        Load and initialize all discovered plugins.
        """
        discovered_plugins = self.discover_plugins()
        
        # Track plugins to initialize in dependency order
        to_initialize = {}
        
        for plugin_name, plugin_class in discovered_plugins.items():
            # Skip disabled plugins
            if plugin_name in self.disabled_plugins:
                logger.info(f"Skipping disabled plugin: {plugin_name}")
                continue
                
            try:
                # Instantiate the plugin
                plugin_instance = plugin_class()
                
                # Check for name conflicts
                if plugin_instance.name in self.plugins:
                    logger.error(f"Plugin name conflict: {plugin_instance.name} is already loaded")
                    continue
                
                # Add to initialization list
                to_initialize[plugin_instance.name] = {
                    'instance': plugin_instance,
                    'dependencies': plugin_instance.dependencies
                }
            
            except Exception as e:
                logger.error(f"Failed to instantiate plugin {plugin_name}: {str(e)}")
        
        # Initialize plugins in dependency order
        initialized = set()
        while to_initialize:
            progress = False
            
            # Find plugins with satisfied dependencies
            for plugin_name, plugin_data in list(to_initialize.items()):
                dependencies = plugin_data['dependencies']
                
                # Check if all dependencies are satisfied
                if all(dep in initialized or dep not in [p['instance'].name for p in to_initialize.values()] 
                       for dep in dependencies):
                    # Initialize the plugin
                    try:
                        plugin_data['instance'].initialize(self.base_nli)
                        self.plugins[plugin_name] = plugin_data['instance']
                        initialized.add(plugin_name)
                        del to_initialize[plugin_name]
                        progress = True
                        logger.info(f"Plugin loaded successfully: {plugin_name} v{plugin_data['instance'].version}")
                    except Exception as e:
                        logger.error(f"Failed to initialize plugin {plugin_name}: {str(e)}")
                        del to_initialize[plugin_name]
                        progress = True
            
            # If no progress made, there's a circular dependency
            if not progress and to_initialize:
                logger.error(f"Circular dependency detected in plugins: {', '.join(to_initialize.keys())}")
                break
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by name.
        
        Args:
            name (str): The name of the plugin
            
        Returns:
            Optional[BasePlugin]: The plugin instance, or None if not found
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        Get all loaded plugins.
        
        Returns:
            Dict[str, BasePlugin]: A dictionary of plugin names to plugin instances
        """
        return self.plugins.copy()
    
    def enable_plugin(self, name: str) -> bool:
        """
        Enable a disabled plugin.
        
        Args:
            name (str): The name of the plugin
            
        Returns:
            bool: True if the plugin was enabled, False otherwise
        """
        if name in self.disabled_plugins:
            self.disabled_plugins.remove(name)
            self._save_plugin_config()
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            name (str): The name of the plugin
            
        Returns:
            bool: True if the plugin was disabled, False otherwise
        """
        if name not in self.disabled_plugins:
            self.disabled_plugins.add(name)
            self._save_plugin_config()
            
            # Unload if it's loaded
            plugin = self.plugins.get(name)
            if plugin:
                try:
                    plugin.on_shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down plugin {name}: {str(e)}")
                del self.plugins[name]
            return True
        return False
    
    def shutdown(self) -> None:
        """
        Shut down all plugins.
        """
        for name, plugin in list(self.plugins.items()):
            try:
                plugin.on_shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin {name}: {str(e)}")
        self.plugins.clear()