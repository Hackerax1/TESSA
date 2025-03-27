# backup_scheduler

Backup scheduler module for Proxmox NLI.
Handles automated backup scheduling, recovery testing, and retention policy enforcement.

**Module Path**: `proxmox_nli.core.storage.backup_scheduler`

## Classes

### BackupScheduler

Scheduler for automated backups, testing, and maintenance.

#### __init__(api, backup_manager)

Initialize the backup scheduler.

Args:
    api: Proxmox API client
    backup_manager: Optional existing BackupManager instance

#### update_config(new_config: Dict)

Update scheduler configuration.

Args:
    new_config: New configuration dictionary
    
Returns:
    Update result dictionary

**Returns**: `Dict`

#### start()

Start the backup scheduler.

Returns:
    Start result dictionary

**Returns**: `Dict`

#### stop()

Stop the backup scheduler.

Returns:
    Stop result dictionary

**Returns**: `Dict`

#### get_status()

Get scheduler status.

Returns:
    Status dictionary

**Returns**: `Dict`

