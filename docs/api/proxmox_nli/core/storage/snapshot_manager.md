# snapshot_manager

Snapshot manager module for Proxmox NLI.
Handles VM snapshots for quick point-in-time recovery.

**Module Path**: `proxmox_nli.core.storage.snapshot_manager`

## Classes

### SnapshotManager

#### __init__(api)

#### list_snapshots(vm_id: str, node: str)

List all snapshots for a VM

**Returns**: `Dict`

#### create_snapshot(vm_id: str, name: str, description: str, include_ram: bool = None, node: str = False)

Create a snapshot of a VM

**Returns**: `Dict`

#### delete_snapshot(vm_id: str, snapshot_name: str, node: str)

Delete a snapshot

**Returns**: `Dict`

#### rollback_snapshot(vm_id: str, snapshot_name: str, node: str)

Rollback a VM to a snapshot

**Returns**: `Dict`

#### get_snapshot_details(vm_id: str, snapshot_name: str, node: str)

Get details of a specific snapshot

**Returns**: `Dict`

#### create_scheduled_snapshots(vm_id: str, schedule: Dict, node: str)

Configure scheduled snapshots for a VM

**Returns**: `Dict`

#### create_bulk_snapshots(vm_ids: List[str], name_prefix: str, description: str = None, include_ram: bool = None)

Create snapshots for multiple VMs at once

**Returns**: `Dict`

#### restore_from_snapshot(vm_id: str, snapshot_name: str, target_vm_id: str, target_node: str = None, node: str = None)

Restore a VM from a snapshot to a new VM

**Returns**: `Dict`

#### create_snapshot_policy(vm_ids: List[str], policy: Dict)

Create a snapshot policy for multiple VMs

**Returns**: `Dict`

