# identity_provider

Identity Provider integration module for managing authentication and identity services.

**Module Path**: `proxmox_nli.core.integration.identity_provider`

## Classes

### IdentityBackendBase

Abstract base class for identity backend implementations

#### configure(settings: Dict[(str, Any)])

Configure the identity backend

**Returns**: `Dict[(str, Any)]`

#### test_connection()

Test connection to the identity backend

**Returns**: `Dict[(str, Any)]`

#### authenticate_user(username: str, credentials: Dict[(str, Any)])

Authenticate a user with the backend

**Returns**: `Dict[(str, Any)]`

#### get_user_groups(username: str)

Get groups for a user

**Returns**: `Dict[(str, Any)]`

#### sync_users()

Sync users from the backend

**Returns**: `Dict[(str, Any)]`

### IdentityProvider

Main class for managing identity provider integrations

#### __init__(config_dir: str)

Initialize with optional config directory path

#### configure_backend(backend: str, settings: Dict[(str, Any)])

Configure an identity backend with settings

**Returns**: `Dict[(str, Any)]`

#### add_group_mapping(external_group: str, local_group: str, backend: str)

Add a mapping between external and local groups

**Returns**: `Dict[(str, Any)]`

#### authenticate(username: str, credentials: Dict[(str, Any)], backend: str)

Authenticate a user with specified or all enabled backends

**Returns**: `Dict[(str, Any)]`

#### sync_users(backend: str)

Sync users from specified or all enabled backends

**Returns**: `Dict[(str, Any)]`

#### get_user_info(username: str, backend: str)

Get user information from specified or default backend

**Returns**: `Dict[(str, Any)]`

#### test_backend(backend: str)

Test connection to an identity backend

**Returns**: `Dict[(str, Any)]`

