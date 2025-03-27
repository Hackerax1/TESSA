# zfs_manager

ZFS storage management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.storage.zfs_manager`

## Classes

### ZFSManager

#### __init__(api)

#### create_pool(node: str, name: str, devices: List[str], raid_level: str)

Create a ZFS storage pool

Args:
    node: Node name
    name: Pool name
    devices: List of device paths
    raid_level: ZFS raid level (mirror, raidz, raidz2, etc.)

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### list_pools(node: str)

List ZFS pools

Args:
    node: Node name

Returns:
    Dict with pool information

**Returns**: `Dict[(str, Any)]`

#### list_datasets(node: str, pool: Optional[str])

List ZFS datasets

Args:
    node: Node name
    pool: Optional pool name to filter

Returns:
    Dict with dataset information

**Returns**: `Dict[(str, Any)]`

#### create_dataset(node: str, name: str, options: Optional[Dict[(str, str)]])

Create a ZFS dataset

Args:
    node: Node name
    name: Dataset name
    options: Optional dataset properties

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### set_properties(node: str, dataset: str, properties: Dict[(str, str)])

Set ZFS dataset properties

Args:
    node: Node name
    dataset: Dataset name
    properties: Properties to set

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### create_snapshot(node: str, dataset: str, snapshot_name: str, recursive: bool)

Create a ZFS snapshot

Args:
    node: Node name
    dataset: Dataset name
    snapshot_name: Snapshot name
    recursive: Whether to create recursive snapshot

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### list_snapshots(node: str, dataset: Optional[str])

List ZFS snapshots

Args:
    node: Node name
    dataset: Optional dataset name to filter

Returns:
    Dict with snapshot information

**Returns**: `Dict[(str, Any)]`

#### delete_snapshot(node: str, snapshot: str, recursive: bool)

Delete a ZFS snapshot

Args:
    node: Node name
    snapshot: Snapshot name (dataset@snapshot)
    recursive: Whether to delete recursively

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### rollback_snapshot(node: str, snapshot: str, force: bool)

Rollback to a ZFS snapshot

Args:
    node: Node name
    snapshot: Snapshot name (dataset@snapshot)
    force: Whether to force rollback, destroying later snapshots

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### setup_auto_snapshots(node: str, dataset: str, schedule: str)

Configure automatic snapshots

Args:
    node: Node name
    dataset: Dataset name
    schedule: Schedule type (hourly, daily, weekly, monthly)

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### get_pool_status(node: str, pool: str)

Get detailed pool status

Args:
    node: Node name
    pool: Pool name

Returns:
    Dict with pool status

**Returns**: `Dict[(str, Any)]`

#### scrub_pool(node: str, pool: str)

Start pool scrub

Args:
    node: Node name
    pool: Pool name

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### get_scrub_status(node: str, pool: str)

Get pool scrub status

Args:
    node: Node name
    pool: Pool name

Returns:
    Dict with scrub status

**Returns**: `Dict[(str, Any)]`

#### create_mirror(node: str, pool: str, devices: List[str])

Create a mirror in an existing pool

Args:
    node: Node name
    pool: Pool name
    devices: List of device paths

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### replace_device(node: str, pool: str, old_device: str, new_device: str)

Replace a device in a pool

Args:
    node: Node name
    pool: Pool name
    old_device: Path to old device
    new_device: Path to new device

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### get_device_health(node: str, device: str)

Get SMART health information for a device

Args:
    node: Node name
    device: Device path

Returns:
    Dict with device health information

**Returns**: `Dict[(str, Any)]`

