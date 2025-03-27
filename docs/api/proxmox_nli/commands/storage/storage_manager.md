# storage_manager

Storage management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.storage.storage_manager`

## Classes

### StorageManager

#### __init__(api)

#### create_storage(node: str, name: str, storage_type: str, config: Dict[(str, Any)])

Create new storage

Args:
    node: Node name
    name: Storage name
    storage_type: Storage type (dir, nfs, zfs, lvm, etc)
    config: Storage configuration
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### create_zfs_pool(node: str, name: str, devices: List[str], raid_level: str)

Create ZFS storage pool

Args:
    node: Node name
    name: Pool name
    devices: List of devices
    raid_level: RAID level (mirror, raidz, raidz2, etc)
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### create_lvm_group(node: str, name: str, devices: List[str])

Create LVM volume group

Args:
    node: Node name
    name: Volume group name
    devices: List of devices
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### create_nfs_storage(node: str, name: str, server: str, export: str, options: Optional[str])

Create NFS storage

Args:
    node: Node name
    name: Storage name
    server: NFS server address
    export: NFS export path
    options: Optional mount options
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### create_cifs_storage(node: str, name: str, server: str, share: str, username: str, password: str = None)

Create CIFS/SMB storage

Args:
    node: Node name
    name: Storage name
    server: CIFS server address
    share: Share name
    username: Optional username
    password: Optional password
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### get_storage_info(node: str, storage: Optional[str])

Get storage information

Args:
    node: Node name
    storage: Optional specific storage name
    
Returns:
    Dict with storage information

**Returns**: `Dict[(str, Any)]`

#### get_zfs_info(node: str, pool: Optional[str])

Get ZFS information

Args:
    node: Node name
    pool: Optional specific pool name
    
Returns:
    Dict with ZFS information

**Returns**: `Dict[(str, Any)]`

#### get_lvm_info(node: str, vg: Optional[str])

Get LVM information

Args:
    node: Node name
    vg: Optional specific volume group name
    
Returns:
    Dict with LVM information

**Returns**: `Dict[(str, Any)]`

#### delete_storage(node: str, storage: str)

Delete storage configuration

Args:
    node: Node name
    storage: Storage name
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### resize_storage(node: str, storage: str, size: str)

Resize storage

Args:
    node: Node name
    storage: Storage name
    size: New size (e.g., '500G')
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### check_storage_health(node: str, storage: str)

Check storage health

Args:
    node: Node name
    storage: Storage name
    
Returns:
    Dict with health status

**Returns**: `Dict[(str, Any)]`

