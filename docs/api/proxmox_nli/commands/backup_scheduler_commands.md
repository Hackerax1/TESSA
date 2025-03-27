# backup_scheduler_commands

Backup scheduler command handlers for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.backup_scheduler_commands`

## Classes

### BackupSchedulerCommands

Command handlers for backup scheduler operations.

#### __init__(api, backup_manager)

Initialize the backup scheduler commands.

Args:
    api: Proxmox API client
    backup_manager: Optional existing BackupManager instance

#### start_scheduler()

Start the backup scheduler.

Returns:
    Start result dictionary

**Returns**: `Dict`

#### stop_scheduler()

Stop the backup scheduler.

Returns:
    Stop result dictionary

**Returns**: `Dict`

#### get_scheduler_status()

Get scheduler status.

Returns:
    Status dictionary

**Returns**: `Dict`

#### update_scheduler_config(config: Dict)

Update scheduler configuration.

Args:
    config: New configuration dictionary
    
Returns:
    Update result dictionary

**Returns**: `Dict`

#### configure_backup_schedule(vm_id: str, schedule: Dict)

Configure backup schedule for a VM.

Args:
    vm_id: VM ID
    schedule: Schedule configuration
    
Returns:
    Configuration result dictionary

**Returns**: `Dict`

#### configure_recovery_testing(config: Dict)

Configure recovery testing.

Args:
    config: Recovery testing configuration
    
Returns:
    Configuration result dictionary

**Returns**: `Dict`

#### configure_retention_policy(vm_id: str, policy: Dict)

Configure retention policy for a VM.

Args:
    vm_id: VM ID
    policy: Retention policy configuration
    
Returns:
    Configuration result dictionary

**Returns**: `Dict`

#### configure_notifications(config: Dict)

Configure notifications.

Args:
    config: Notification configuration
    
Returns:
    Configuration result dictionary

**Returns**: `Dict`

#### run_backup_now(vm_id: str)

Run backup immediately.

Args:
    vm_id: VM ID
    
Returns:
    Backup result dictionary

**Returns**: `Dict`

#### run_recovery_testing_now(vm_ids: Optional[List[str]])

Run recovery testing immediately.

Args:
    vm_ids: Optional list of VM IDs to test
    
Returns:
    Testing result dictionary

**Returns**: `Dict`

#### run_retention_enforcement_now()

Run retention policy enforcement immediately.

Returns:
    Enforcement result dictionary

**Returns**: `Dict`

#### run_deduplication_now()

Run data deduplication immediately.

Returns:
    Deduplication result dictionary

**Returns**: `Dict`

