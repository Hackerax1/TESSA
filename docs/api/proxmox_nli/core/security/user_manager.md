# user_manager

User manager module for handling user preferences and activity tracking.

**Module Path**: `proxmox_nli.core.security.user_manager`

## Classes

### UserManager

#### __init__(base_nli)

#### set_user_preference(user_id, key, value)

Set a user preference

#### get_user_preferences(user_id)

Get all preferences for a user

#### get_user_statistics(user_id)

Get usage statistics for a user

#### get_recent_activity(limit)

Get recent command executions

#### get_user_activity(user, limit)

Get recent activity for a specific user

#### get_failed_commands(limit)

Get recent failed command executions

#### add_to_command_history(user_id, command, intent, entities = None, success = None)

Add a command to the user's command history

#### get_command_history(user_id, limit, successful_only = 50)

Get command history for a user

#### clear_command_history(user_id)

Clear command history for a user

#### add_favorite_command(user_id, command_text, description)

Add a command to the user's favorites

#### get_favorite_commands(user_id)

Get favorite commands for a user

#### remove_favorite_command(user_id, command_id)

Remove a command from the user's favorites

#### set_notification_preference(user_id, event_type, channel, enabled)

Set notification preference for a specific event and channel

#### get_notification_preferences(user_id)

Get all notification preferences for a user

#### initialize_default_notification_preferences(user_id)

Initialize default notification preferences for a new user

#### get_notification_channels_for_event(user_id, event_type)

Get enabled notification channels for a specific event

#### create_dashboard(user_id, name, is_default, layout = False)

Create a new dashboard for a user

#### get_dashboards(user_id)

Get all dashboards for a user

#### get_dashboard(dashboard_id)

Get a specific dashboard by ID

#### update_dashboard(dashboard_id, name, is_default = None, layout = None)

Update dashboard properties

#### delete_dashboard(dashboard_id)

Delete a dashboard

#### add_dashboard_panel(dashboard_id, panel_type, title, config, position_x = None, position_y = 0, width = 0, height = 6)

Add a panel to a dashboard

#### update_dashboard_panel(panel_id, title, config = None, position_x = None, position_y = None, width = None, height = None)

Update panel properties

#### delete_dashboard_panel(panel_id)

Delete a panel from a dashboard

#### initialize_default_dashboard(user_id)

Initialize a default dashboard for a new user

#### sync_profile(user_id, device_id, sync_data)

Synchronize profile data between devices

#### register_device(user_id, device_id, device_name, device_type)

Register a new device for profile synchronization

#### get_user_devices(user_id)

Get all devices registered for a user

#### remove_device(user_id, device_id)

Remove a device from synchronization

#### get_shortcuts(user_id, category)

Get shortcuts for a user, optionally filtered by category

#### add_shortcut(user_id, name, command, description, category = None, icon = None, color = None, shortcut_key = None)

Add or update a shortcut for a user

#### delete_shortcut(user_id, shortcut_id, name = None)

Delete a shortcut for a user by ID or name

#### update_shortcut_position(user_id, shortcut_id, position)

Update the position of a shortcut

#### get_shortcut_categories(user_id)

Get all shortcut categories for a user

#### initialize_default_shortcuts(user_id)

Initialize default shortcuts for a user

