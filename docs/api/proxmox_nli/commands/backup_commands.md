# backup_commands

Backup-related commands for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.backup_commands`

## Classes

### BackupCommands

Handles all backup-related commands for Proxmox NLI.

#### __init__(api)

Initialize backup commands with API access.

Args:
    api: Proxmox API client

#### create_backup(vm_id: str, mode: str, storage: str = 'snapshot', compression: str = None, notes: str = 'zstd')

Create a backup of a VM.

Args:
    vm_id: VM ID
    mode: Backup mode (snapshot or suspend)
    storage: Storage location
    compression: Compression algorithm
    notes: Backup notes
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### restore_backup(vm_id: str, backup_file: str, target_storage: str, restore_options: Dict = None)

Restore a VM from backup.

Args:
    vm_id: VM ID
    backup_file: Backup file path
    target_storage: Target storage location
    restore_options: Additional restore options
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### list_backups(vm_id: str)

List available backups.

Args:
    vm_id: Optional VM ID to filter backups
    
Returns:
    Dict: List of backups

**Returns**: `Dict`

#### delete_backup(backup_id: str)

Delete a backup.

Args:
    backup_id: Backup ID
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### verify_backup(vm_id: str, backup_file: str)

Verify a backup's integrity.

Args:
    vm_id: VM ID
    backup_file: Optional backup file path
    
Returns:
    Dict: Verification result

**Returns**: `Dict`

#### start_backup_scheduler()

Start the backup scheduler service.

Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### stop_backup_scheduler()

Stop the backup scheduler service.

Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### get_scheduler_status()

Get the status of the backup scheduler.

Returns:
    Dict: Scheduler status information

**Returns**: `Dict`

#### schedule_backup(vm_id: str, schedule: Dict)

Configure backup schedule for a VM.

Args:
    vm_id: VM ID
    schedule: Schedule configuration with frequency, time, etc.
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### configure_recovery_testing(config: Dict)

Configure automated recovery testing.

Args:
    config: Recovery testing configuration
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### configure_retention_policy(vm_id: str, policy: Dict)

Configure backup retention policy for a VM.

Args:
    vm_id: VM ID
    policy: Retention policy configuration
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_backup_now(vm_id: str)

Run a backup immediately.

Args:
    vm_id: VM ID
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_recovery_test_now(vm_ids: Optional[List[str]])

Run a recovery test immediately.

Args:
    vm_ids: Optional list of VM IDs to test
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_retention_enforcement_now()

Run retention policy enforcement immediately.

Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_deduplication_now()

Run data deduplication immediately.

Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### configure_notifications(config: Dict)

Configure backup notifications.

Args:
    config: Notification configuration
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

