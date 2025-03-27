# storage_manager

Storage manager module for Proxmox NLI.
Handles storage operations, including listing, creating, and managing storage resources.

**Module Path**: `proxmox_nli.core.storage.storage_manager`

## Classes

### StorageManager

#### __init__(api)

#### list_storage(node: str)

List all storage resources on the cluster or a specific node

**Returns**: `Dict`

#### get_storage_details(storage_id: str, node: str)

Get detailed information about a specific storage resource

**Returns**: `Dict`

#### create_storage(storage_id: str, storage_type: str, config: Dict)

Create a new storage resource

**Returns**: `Dict`

#### delete_storage(storage_id: str)

Delete a storage resource

**Returns**: `Dict`

#### update_storage(storage_id: str, config: Dict)

Update a storage resource configuration

**Returns**: `Dict`

#### get_storage_status(node: str)

Get storage status information for a node

**Returns**: `Dict`

#### get_content(storage_id: str, content_type: str)

Get content list of a storage

**Returns**: `Dict`

#### upload_content(node: str, storage_id: str, file_path: str, content_type: str)

Upload content to storage

**Returns**: `Dict`

