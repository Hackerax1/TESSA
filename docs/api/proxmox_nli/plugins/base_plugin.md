# base_plugin

Base plugin interface for Proxmox NLI.

This module defines the base plugin interface that all plugins must implement
to be compatible with the Proxmox NLI plugin system.

**Module Path**: `proxmox_nli.plugins.base_plugin`

## Classes

### BasePlugin

Base plugin interface for Proxmox NLI.

All plugins must inherit from this class and implement its methods
to be compatible with the Proxmox NLI plugin system.

#### name()

Get the name of the plugin.

Returns:
    str: The name of the plugin

**Returns**: `str`

#### version()

Get the version of the plugin.

Returns:
    str: The version of the plugin in semver format (e.g., "1.0.0")

**Returns**: `str`

#### description()

Get the description of the plugin.

Returns:
    str: A brief description of the plugin's functionality

**Returns**: `str`

#### author()

Get the author of the plugin.

Returns:
    str: The author of the plugin

**Returns**: `str`

#### dependencies()

Get the list of plugin dependencies.

Returns:
    List[str]: A list of plugin names that this plugin depends on

**Returns**: `List[str]`

#### initialize(nli)

Initialize the plugin with the Proxmox NLI instance.

This method is called when the plugin is loaded. Use it to register
commands, event handlers, or other components with the NLI system.

Args:
    nli: The Proxmox NLI instance
    **kwargs: Additional keyword arguments

**Returns**: `None`

#### get_config_schema()

Get the configuration schema for the plugin.

Returns:
    Dict[str, Any]: A dictionary describing the configuration schema
    in JSON Schema format

**Returns**: `Dict[(str, Any)]`

#### validate_config(config: Dict[(str, Any)])

Validate the plugin configuration.

Args:
    config (Dict[str, Any]): The plugin configuration to validate
    
Returns:
    Dict[str, List[str]]: Dictionary with field names as keys and lists of error
    messages as values. Empty dict means valid configuration.

**Returns**: `Dict[(str, List[str])]`

#### on_shutdown()

Handle plugin shutdown.

This method is called when the plugin is being unloaded.

**Returns**: `None`

