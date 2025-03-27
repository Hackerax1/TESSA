# plugin_manager

Plugin manager for Proxmox NLI.

This module provides functionality for discovering, loading, and managing
plugins for the Proxmox NLI system.

**Module Path**: `proxmox_nli.plugins.plugin_manager`

## Classes

### PluginManager

Plugin manager for Proxmox NLI.

This class handles plugin discovery, loading, initialization,
and lifecycle management.

#### __init__(base_nli)

Initialize the plugin manager.

Args:
    base_nli: The BaseNLI instance that will be provided to plugins

#### discover_plugins()

Discover available plugins in the plugin directories.

Returns:
    Dict[str, Type[BasePlugin]]: A dictionary of plugin names to plugin classes

**Returns**: `Dict[(str, Type[BasePlugin])]`

#### load_plugins()

Load and initialize all discovered plugins.

**Returns**: `None`

#### get_plugin(name: str)

Get a plugin by name.

Args:
    name (str): The name of the plugin
    
Returns:
    Optional[BasePlugin]: The plugin instance, or None if not found

**Returns**: `Optional[BasePlugin]`

#### get_all_plugins()

Get all loaded plugins.

Returns:
    Dict[str, BasePlugin]: A dictionary of plugin names to plugin instances

**Returns**: `Dict[(str, BasePlugin)]`

#### enable_plugin(name: str)

Enable a disabled plugin.

Args:
    name (str): The name of the plugin
    
Returns:
    bool: True if the plugin was enabled, False otherwise

**Returns**: `bool`

#### disable_plugin(name: str)

Disable a plugin.

Args:
    name (str): The name of the plugin
    
Returns:
    bool: True if the plugin was disabled, False otherwise

**Returns**: `bool`

#### shutdown()

Shut down all plugins.

**Returns**: `None`

