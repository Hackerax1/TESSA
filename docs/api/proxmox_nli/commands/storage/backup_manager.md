# backup_manager

Backup management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.storage.backup_manager`

## Classes

### BackupManager

#### __init__(api)

#### create_backup(vm_id: str, mode: str, storage: Optional[str] = 'snapshot', compression: str = None, notes: Optional[str] = 'zstd')

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

#### restore_backup(vm_id: str, backup_file: str, target_storage: Optional[str], restore_options: Optional[Dict[(str, Any)]] = None)

Restore a VM from backup

Args:
    vm_id: VM ID
    backup_file: Backup file path
    target_storage: Target storage location
    restore_options: Additional restore options
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### list_backups(vm_id: Optional[str])

List available backups

Args:
    vm_id: Optional VM ID to filter backups
    
Returns:
    Dict with list of backups

**Returns**: `Dict[(str, Any)]`

#### delete_backup(backup_id: str)

Delete a backup

Args:
    backup_id: Backup ID/volume ID
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### verify_backup(vm_id: str, backup_file: Optional[str])

Verify a backup's integrity

Args:
    vm_id: VM ID
    backup_file: Optional specific backup file to verify
    
Returns:
    Dict with verification result

**Returns**: `Dict[(str, Any)]`

#### configure_backup_schedule(vm_id: str, schedule: Dict[(str, Any)])

Configure automated backup schedule

Args:
    vm_id: VM ID
    schedule: Schedule configuration with:
        - dow: Day of week (1-7)
        - hour: Hour (0-23)
        - minute: Minute (0-59)
        - retention: Number of backups to keep
        
Returns:
    Dict with configuration result

**Returns**: `Dict[(str, Any)]`

#### get_backup_schedule(vm_id: Optional[str])

Get backup schedule configuration

Args:
    vm_id: Optional VM ID to filter schedules
    
Returns:
    Dict with schedule configuration

**Returns**: `Dict[(str, Any)]`

#### remove_backup_schedule(vm_id: str)

Remove backup schedule

Args:
    vm_id: VM ID
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

