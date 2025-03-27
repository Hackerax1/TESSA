# base_nli

Base NLI module providing core initialization and common functionality.

**Module Path**: `proxmox_nli.core.base_nli`

## Classes

### BaseNLI

#### __init__(host, user, password, realm, verify_ssl = 'pam')

Initialize the Base Natural Language Interface

#### load_custom_commands()

Load custom commands from the custom_commands directory

#### initialize_plugin_system()

Initialize the plugin system and load available plugins.

#### get_help_text()

Get the help text with all available commands

#### get_help()

Get help information

#### get_plugins()

Get information about installed plugins

#### enable_plugin(plugin_name)

Enable a plugin

#### disable_plugin(plugin_name)

Disable a plugin

