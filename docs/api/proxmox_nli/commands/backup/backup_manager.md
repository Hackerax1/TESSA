# backup_manager

Backup management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.backup.backup_manager`

## Classes

### BackupManager

#### __init__(api)

#### create_backup(vm_id: str, mode: str, storage: str = 'snapshot', compression: str = None, notes: str = 'zstd')

Create a backup of a VM

Args:
    vm_id: VM ID
    mode: Backup mode (snapshot or suspend)
    storage: Storage location
    compression: Compression algorithm
    notes: Backup notes

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### restore_backup(vm_id: str, backup_file: str, target_storage: str, restore_options: Dict = None)

Restore a VM from backup

Args:
    vm_id: VM ID
    backup_file: Backup file path
    target_storage: Target storage location
    restore_options: Additional restore options

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### list_backups(vm_id: str)

List available backups

Args:
    vm_id: Optional VM ID to filter backups

Returns:
    Dict with backup list

**Returns**: `Dict[(str, Any)]`

#### delete_backup(backup_id: str)

Delete a backup

Args:
    backup_id: Backup ID

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### verify_backup(vm_id: str, backup_file: str)

Verify a backup's integrity

Args:
    vm_id: VM ID
    backup_file: Optional specific backup file to verify

Returns:
    Dict with verification result

**Returns**: `Dict[(str, Any)]`

#### configure_backup(vm_id: str, schedule: Dict)

Configure automated backups for a VM

Args:
    vm_id: VM ID
    schedule: Schedule configuration with:
        - frequency: hourly, daily, weekly
        - time: Time to run
        - retention: Number of backups to keep

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### configure_recovery_testing(config: Dict)

Configure automated recovery testing

Args:
    config: Recovery testing configuration with:
        - frequency: How often to test
        - vms: List of VMs to test
        - verify_method: How to verify recovery

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### configure_retention_policy(vm_id: str, policy: Dict)

Configure backup retention policy

Args:
    vm_id: VM ID
    policy: Retention policy with:
        - keep_daily: Number of daily backups
        - keep_weekly: Number of weekly backups
        - keep_monthly: Number of monthly backups

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### run_backup_now(vm_id: str)

Run a backup immediately

Args:
    vm_id: VM ID

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### run_recovery_test_now(vm_ids: Optional[List[str]])

Run a recovery test immediately

Args:
    vm_ids: Optional list of VM IDs to test

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### run_retention_enforcement_now()

Run retention policy enforcement immediately

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### run_deduplication_now()

Run data deduplication immediately

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### configure_notifications(config: Dict)

Configure backup notifications

Args:
    config: Notification configuration with:
        - email: Email addresses
        - events: Events to notify on
        - methods: Notification methods

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

