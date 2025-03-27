# zfs_handler

ZFS handler module for Proxmox NLI.
Manages ZFS pools, datasets, and features including snapshots and replication.

**Module Path**: `proxmox_nli.core.storage.zfs_handler`

## Classes

### ZFSHandler

#### __init__(api)

#### list_pools(node: str)

List all ZFS pools on a node

**Returns**: `Dict`

#### get_pool_status(node: str, pool: str)

Get status information for a ZFS pool

**Returns**: `Dict`

#### create_pool(node: str, pool_name: str, devices: List[str], raid_type: str)

Create a new ZFS pool

**Returns**: `Dict`

#### destroy_pool(node: str, pool_name: str)

Destroy a ZFS pool

**Returns**: `Dict`

#### list_datasets(node: str)

List all ZFS datasets

**Returns**: `Dict`

#### create_dataset(node: str, name: str, properties: Dict)

Create a new ZFS dataset

**Returns**: `Dict`

#### destroy_dataset(node: str, name: str, recursive: bool)

Destroy a ZFS dataset

**Returns**: `Dict`

#### set_property(node: str, name: str, property_name: str, value: str)

Set a property on a ZFS dataset or pool

**Returns**: `Dict`

#### get_properties(node: str, name: str)

Get properties of a ZFS dataset or pool

**Returns**: `Dict`

#### create_snapshot(node: str, dataset: str, snapshot_name: str, recursive: bool)

Create a ZFS snapshot

**Returns**: `Dict`

#### list_snapshots(node: str, dataset: str)

List ZFS snapshots

**Returns**: `Dict`

#### rollback_snapshot(node: str, snapshot: str, force: bool)

Rollback a ZFS dataset to a snapshot

**Returns**: `Dict`

#### destroy_snapshot(node: str, snapshot: str, recursive: bool)

Destroy a ZFS snapshot

**Returns**: `Dict`

#### send_receive(source_node: str, target_node: str, source_snapshot: str, target_dataset: str)

Send and receive a ZFS snapshot to replicate data

**Returns**: `Dict`

#### scrub_pool(node: str, pool_name: str)

Start a scrub operation on a ZFS pool

**Returns**: `Dict`

