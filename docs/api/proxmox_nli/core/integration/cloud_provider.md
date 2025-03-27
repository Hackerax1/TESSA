# cloud_provider

Cloud Provider integration module for connecting TESSA with major cloud providers.

**Module Path**: `proxmox_nli.core.integration.cloud_provider`

## Classes

### CloudProviderBase

Abstract base class for cloud provider implementations

#### authenticate()

Authenticate with the cloud provider

**Returns**: `Dict[(str, Any)]`

#### list_resources()

List available cloud resources

**Returns**: `Dict[(str, Any)]`

#### import_resources(resources: List[Dict])

Import selected cloud resources

**Returns**: `Dict[(str, Any)]`

#### sync_status()

Get sync status between cloud and local resources

**Returns**: `Dict[(str, Any)]`

### CloudProvider

Main class for managing cloud provider integrations

#### __init__(config_dir: str)

Initialize with optional config directory path

#### configure_provider(provider: str, credentials: Dict[(str, Any)])

Configure a cloud provider with credentials

**Returns**: `Dict[(str, Any)]`

#### get_provider_status(provider: str)

Get status of configured providers

**Returns**: `Dict[(str, Any)]`

#### sync_cloud_resources(provider: str)

Sync resources with specified cloud provider or all enabled providers

**Returns**: `Dict[(str, Any)]`

#### import_cloud_resources(provider: str, resources: List[Dict])

Import specific resources from a cloud provider

**Returns**: `Dict[(str, Any)]`

#### update_sync_settings(settings: Dict[(str, Any)])

Update cloud synchronization settings

**Returns**: `Dict[(str, Any)]`

