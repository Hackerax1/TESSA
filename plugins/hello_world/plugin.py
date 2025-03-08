"""
Hello World plugin for Proxmox NLI.

This is a simple example plugin to demonstrate the Proxmox NLI plugin system.
"""
import logging
from proxmox_nli.plugins.base_plugin import BasePlugin
from proxmox_nli.plugins.utils import register_command

logger = logging.getLogger(__name__)

class HelloWorldPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "hello_world"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "A simple hello world plugin to demonstrate the plugin system"
    
    @property
    def author(self) -> str:
        return "Proxmox NLI Team"
    
    def initialize(self, nli, **kwargs) -> None:
        """Initialize the plugin with the Proxmox NLI instance."""
        logger.info("Initializing Hello World plugin")
        
        # Register commands
        register_command(
            nli, 
            "hello_world_greet", 
            self.greet_command,
            "Displays a greeting message. Usage: hello world [name]"
        )
        
        # Register an additional command with a different format
        register_command(
            nli,
            "hello_world_system_info",
            self.system_info_command,
            "Displays basic system information about Proxmox"
        )
        
        logger.info("Hello World plugin initialized successfully")
    
    def greet_command(self, **kwargs):
        """Command to greet the user."""
        try:
            entities = kwargs.get('entities', {})
            name = entities.get('NAME', 'World')
            
            message = f"👋 Hello, {name}! This is a custom greeting from the Hello World plugin."
            
            # Add some extra information to demonstrate plugin functionality
            message += "\n\nThis demonstrates how plugins can extend TESSA's functionality."
            message += "\nYou can create your own plugins to add custom features!"
            
            return {"success": True, "message": message}
            
        except Exception as e:
            logger.error(f"Error in greet command: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def system_info_command(self, **kwargs):
        """Command to display basic system information."""
        try:
            # Access the API from the base NLI instance
            api = kwargs.get('nli').api
            
            # Get Proxmox version info
            version_info = api.api_request('GET', 'version')
            
            if not version_info.get('success', False):
                return {"success": False, "message": "Failed to get system information"}
            
            version_data = version_info.get('data', {})
            
            message = "📊 **Proxmox System Information**\n\n"
            message += f"Version: {version_data.get('version', 'Unknown')}\n"
            message += f"Release: {version_data.get('release', 'Unknown')}\n"
            message += f"Repository: {version_data.get('repoid', 'Unknown')}\n"
            
            return {"success": True, "message": message}
            
        except Exception as e:
            logger.error(f"Error in system info command: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def on_shutdown(self) -> None:
        """Handle plugin shutdown."""
        logger.info("Shutting down Hello World plugin")