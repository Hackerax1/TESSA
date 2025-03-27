# utils

Utility functions for Proxmox NLI plugins.

This module provides helper functions for plugin developers to interact with
the Proxmox NLI system.

**Module Path**: `proxmox_nli.plugins.utils`

## Functions

### register_command(nli, command_name: str, command_func: Callable, help_text: str = None)

Register a new command with the NLI system.

Args:
    nli: The Proxmox NLI instance
    command_name (str): The name of the command
    command_func (Callable): The function to execute for this command
    help_text (str, optional): Help text for the command

Returns:
    bool: True if the command was registered successfully, False otherwise

**Returns**: `bool: True if the command was registered successfully, False otherwise`

### register_intent_handler(nli, intent_name: str, handler_func: Callable)

Register a new intent handler with the NLI system.

Args:
    nli: The Proxmox NLI instance
    intent_name (str): The name of the intent
    handler_func (Callable): The function to execute for this intent

Returns:
    bool: True if the intent handler was registered successfully, False otherwise

**Returns**: `bool: True if the intent handler was registered successfully, False otherwise`

### register_entity_extractor(nli, entity_type: str, patterns: List[str])

Register a new entity extraction pattern with the NLU system.

Args:
    nli: The Proxmox NLI instance
    entity_type (str): The type of entity to extract
    patterns (List[str]): List of regex patterns for extraction

Returns:
    bool: True if the entity extractor was registered successfully, False otherwise

**Returns**: `bool: True if the entity extractor was registered successfully, False otherwise`

### register_web_route(nli, route_path: str, handler_func: Callable, methods: List[str] = None)

Register a new web route with the NLI system.

Args:
    nli: The Proxmox NLI instance
    route_path (str): The URL path for the route (e.g., "/api/plugin/myfeature")
    handler_func (Callable): The function to handle requests to this route
    methods (List[str], optional): HTTP methods to allow (default: ["GET"])

Returns:
    bool: True if the route was registered successfully, False otherwise

**Returns**: `bool: True if the route was registered successfully, False otherwise`

### add_service_to_catalog(nli, service_name: str, service_definition: Dict[(str, Any)])

Add a new service to the service catalog.

Args:
    nli: The Proxmox NLI instance
    service_name (str): The name of the service
    service_definition (Dict[str, Any]): The service definition

Returns:
    bool: True if the service was added successfully, False otherwise

**Returns**: `bool: True if the service was added successfully, False otherwise`

### get_plugin_data_path(plugin_name: str)

Get the data directory path for a plugin.

Args:
    plugin_name (str): The name of the plugin

Returns:
    str: The absolute path to the plugin's data directory

**Returns**: `str`

