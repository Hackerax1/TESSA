# user_preferences

User preferences management module for Proxmox NLI.
Handles persistent storage of user environment preferences across sessions.

**Module Path**: `proxmox_nli.core.user_preferences`

## Classes

### UserPreferencesManager

#### __init__(data_dir: str)

Initialize the user preferences manager

Args:
    data_dir: Directory to store user preferences data. If None,
             defaults to the 'data' directory in the project root.

#### set_preference(user_id: str, key: str, value: Any)

Set a user preference

Args:
    user_id: The user identifier
    key: Preference key
    value: Preference value (will be JSON serialized)
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_preference(user_id: str, key: str, default: Any)

Get a user preference

Args:
    user_id: The user identifier
    key: Preference key
    default: Default value if preference not found
    
Returns:
    Any: The preference value or default if not found

**Returns**: `Any`

#### get_all_preferences(user_id: str)

Get all preferences for a user

Args:
    user_id: The user identifier
    
Returns:
    Dict[str, Any]: Dictionary of all user preferences

**Returns**: `Dict[(str, Any)]`

#### delete_preference(user_id: str, key: str)

Delete a user preference

Args:
    user_id: The user identifier
    key: Preference key
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### add_favorite_vm(user_id: str, vm_id: str, vm_name: Optional[str])

Add a VM to user favorites

Args:
    user_id: The user identifier
    vm_id: The VM ID
    vm_name: Optional name of the VM
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### remove_favorite_vm(user_id: str, vm_id: str)

Remove a VM from user favorites

Args:
    user_id: The user identifier
    vm_id: The VM ID
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_favorite_vms(user_id: str)

Get favorite VMs for a user

Args:
    user_id: The user identifier
    
Returns:
    List[Dict[str, Any]]: List of favorite VMs

**Returns**: `List[Dict[(str, Any)]]`

#### add_favorite_node(user_id: str, node_name: str)

Add a node to user favorites

Args:
    user_id: The user identifier
    node_name: The node name
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_favorite_nodes(user_id: str)

Get favorite nodes for a user

Args:
    user_id: The user identifier
    
Returns:
    List[Dict[str, Any]]: List of favorite nodes

**Returns**: `List[Dict[(str, Any)]]`

#### track_command_usage(user_id: str, command: str, intent: str)

Track usage of a command

Args:
    user_id: The user identifier
    command: The command string
    intent: The command intent
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_frequent_commands(user_id: str, limit: int)

Get frequently used commands for a user

Args:
    user_id: The user identifier
    limit: Maximum number of commands to return
    
Returns:
    List[Dict[str, Any]]: List of frequent commands

**Returns**: `List[Dict[(str, Any)]]`

#### add_quick_access_service(user_id: str, service_id: str, vm_id: Optional[str])

Add a service to quick access list

Args:
    user_id: The user identifier
    service_id: The service ID
    vm_id: Optional VM ID where the service is deployed
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_quick_access_services(user_id: str)

Get quick access services for a user

Args:
    user_id: The user identifier
    
Returns:
    List[Dict[str, Any]]: List of quick access services

**Returns**: `List[Dict[(str, Any)]]`

#### add_to_command_history(user_id: str, command: str, intent: str, entities: Dict = None, success: bool = None)

Add a command to the user's command history

Args:
    user_id: The user identifier
    command: The command text
    intent: Identified intent
    entities: Extracted entities
    success: Whether the command executed successfully
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_command_history(user_id: str, limit: int, successful_only: bool = 50)

Get command history for a user

Args:
    user_id: The user identifier
    limit: Maximum number of history items to return
    successful_only: Whether to return only successful commands
    
Returns:
    List[Dict[str, Any]]: List of command history items

**Returns**: `List[Dict[(str, Any)]]`

#### clear_command_history(user_id: str)

Clear command history for a user

Args:
    user_id: The user identifier
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### add_favorite_command(user_id: str, command_text: str, description: str)

Add a command to the user's favorites

Args:
    user_id: The user identifier
    command_text: The command text
    description: Optional description for the command
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_favorite_commands(user_id: str)

Get favorite commands for a user

Args:
    user_id: The user identifier
    
Returns:
    List[Dict[str, Any]]: List of favorite commands

**Returns**: `List[Dict[(str, Any)]]`

#### remove_favorite_command(user_id: str, command_id: int)

Remove a command from the user's favorites

Args:
    user_id: The user identifier
    command_id: The favorite command ID
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### set_notification_preference(user_id: str, event_type: str, channel: str, enabled: bool)

Set notification preference for a specific event and channel

Args:
    user_id: The user identifier
    event_type: The event type (e.g., vm_state_change, backup_complete, security_alert)
    channel: The notification channel (e.g., web, email, sms)
    enabled: Whether notifications are enabled for this event/channel
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_notification_preferences(user_id: str)

Get all notification preferences for a user

Args:
    user_id: The user identifier
    
Returns:
    List[Dict[str, Any]]: List of notification preferences

**Returns**: `List[Dict[(str, Any)]]`

#### get_notification_preference(user_id: str, event_type: str, channel: str)

Get a specific notification preference

Args:
    user_id: The user identifier
    event_type: The event type
    channel: The notification channel
    
Returns:
    Optional[bool]: Whether the notification is enabled, or None if not found

**Returns**: `Optional[bool]`

#### get_notification_channels_for_event(user_id: str, event_type: str)

Get enabled notification channels for a specific event

Args:
    user_id: The user identifier
    event_type: The event type
    
Returns:
    List[str]: List of enabled notification channels for this event

**Returns**: `List[str]`

#### initialize_default_notification_preferences(user_id: str)

Initialize default notification preferences for a new user

Args:
    user_id: The user identifier
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### delete_notification_preferences(user_id: str)

Delete all notification preferences for a user

Args:
    user_id: The user identifier
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### add_shortcut(user_id: str, name: str, command_text: str, description: str, shortcut_key: str = None, category: str = None, icon: str = None, position: int = None)

Add or update a shortcut for a user

Args:
    user_id: The user identifier
    name: The name of the shortcut
    command_text: The command text to execute
    description: Optional description of the shortcut
    shortcut_key: Optional keyboard shortcut (e.g., 'Ctrl+Alt+S')
    category: Optional category for organizing shortcuts
    icon: Optional icon name (e.g., 'bi-star' for Bootstrap icons)
    position: Optional position for display order
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_shortcuts(user_id: str, category: str)

Get shortcuts for a user

Args:
    user_id: The user identifier
    category: Optional category filter
    
Returns:
    List[Dict[str, Any]]: List of shortcuts

**Returns**: `List[Dict[(str, Any)]]`

#### get_shortcut(user_id: str, shortcut_id: int, name: str = None)

Get a specific shortcut by ID or name

Args:
    user_id: The user identifier
    shortcut_id: The shortcut ID (optional if name is provided)
    name: The shortcut name (optional if shortcut_id is provided)
    
Returns:
    Optional[Dict[str, Any]]: The shortcut or None if not found

**Returns**: `Optional[Dict[(str, Any)]]`

#### delete_shortcut(user_id: str, shortcut_id: int, name: str = None)

Delete a shortcut

Args:
    user_id: The user identifier
    shortcut_id: The shortcut ID (optional if name is provided)
    name: The shortcut name (optional if shortcut_id is provided)
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### get_shortcut_categories(user_id: str)

Get all shortcut categories for a user

Args:
    user_id: The user identifier
    
Returns:
    List[str]: List of category names

**Returns**: `List[str]`

#### update_shortcut_position(user_id: str, shortcut_id: int, position: int)

Update the position of a shortcut

Args:
    user_id: The user identifier
    shortcut_id: The shortcut ID
    position: The new position
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### initialize_default_shortcuts(user_id: str)

Initialize default shortcuts for a new user

Args:
    user_id: The user identifier
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

### UserManager

#### __init__(base_nli_or_data_dir)

Initialize the user manager

Args:
    base_nli_or_data_dir: Either the base NLI instance or a directory to store user data.
                         If None, defaults to the 'data' directory in the project root.

#### add_shortcut(user_id: str, name: str, command_text: str, description: str, shortcut_key: str = None, category: str = None, icon: str = None, position: int = None)

Add a shortcut for a user

Args:
    user_id: The user ID
    name: Name of the shortcut
    command_text: Command text (can include placeholders like {{param}})
    description: Optional description
    shortcut_key: Optional keyboard shortcut
    category: Optional category for grouping
    icon: Optional icon identifier
    position: Optional display position
    
Returns:
    Dict: Response with success status and message

**Returns**: `Dict`

#### get_shortcuts(user_id: str, category: str)

Get shortcuts for a user

Args:
    user_id: The user ID
    category: Optional category filter
    
Returns:
    Dict: Response with shortcuts data

**Returns**: `Dict`

#### get_shortcut(user_id: str, shortcut_id: int, name: str = None)

Get a specific shortcut

Args:
    user_id: The user ID
    shortcut_id: Optional shortcut ID
    name: Optional shortcut name (if ID not provided)
    
Returns:
    Dict: Response with shortcut data

**Returns**: `Dict`

#### delete_shortcut(user_id: str, shortcut_id: int, name: str = None)

Delete a shortcut

Args:
    user_id: The user ID
    shortcut_id: Optional shortcut ID
    name: Optional shortcut name (if ID not provided)
    
Returns:
    Dict: Response with success status

**Returns**: `Dict`

#### update_shortcut_position(user_id: str, shortcut_id: int, position: int)

Update position of a shortcut

Args:
    user_id: The user ID
    shortcut_id: The shortcut ID
    position: New position value
    
Returns:
    Dict: Response with success status

**Returns**: `Dict`

#### initialize_default_shortcuts(user_id: str)

Initialize default shortcuts for a user

Args:
    user_id: The user ID
    
Returns:
    Dict: Response with success status

**Returns**: `Dict`

#### get_shortcut_categories(user_id: str)

Get all shortcut categories for a user

Args:
    user_id: The user ID
    
Returns:
    Dict: Response with list of categories

**Returns**: `Dict`

