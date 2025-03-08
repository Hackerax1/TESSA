"""
Base plugin interface for Proxmox NLI.

This module defines the base plugin interface that all plugins must implement
to be compatible with the Proxmox NLI plugin system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BasePlugin(ABC):
    """
    Base plugin interface for Proxmox NLI.
    
    All plugins must inherit from this class and implement its methods
    to be compatible with the Proxmox NLI plugin system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the plugin.
        
        Returns:
            str: The name of the plugin
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get the version of the plugin.
        
        Returns:
            str: The version of the plugin in semver format (e.g., "1.0.0")
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description of the plugin.
        
        Returns:
            str: A brief description of the plugin's functionality
        """
        pass
    
    @property
    def author(self) -> str:
        """
        Get the author of the plugin.
        
        Returns:
            str: The author of the plugin
        """
        return "Unknown"
    
    @property
    def dependencies(self) -> List[str]:
        """
        Get the list of plugin dependencies.
        
        Returns:
            List[str]: A list of plugin names that this plugin depends on
        """
        return []
    
    @abstractmethod
    def initialize(self, nli, **kwargs) -> None:
        """
        Initialize the plugin with the Proxmox NLI instance.
        
        This method is called when the plugin is loaded. Use it to register
        commands, event handlers, or other components with the NLI system.
        
        Args:
            nli: The Proxmox NLI instance
            **kwargs: Additional keyword arguments
        """
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for the plugin.
        
        Returns:
            Dict[str, Any]: A dictionary describing the configuration schema
            in JSON Schema format
        """
        return {}
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate the plugin configuration.
        
        Args:
            config (Dict[str, Any]): The plugin configuration to validate
            
        Returns:
            Dict[str, List[str]]: Dictionary with field names as keys and lists of error
            messages as values. Empty dict means valid configuration.
        """
        return {}
    
    def on_shutdown(self) -> None:
        """
        Handle plugin shutdown.
        
        This method is called when the plugin is being unloaded.
        """
        pass