# backup_manager

Backup management module for Proxmox NLI.
Handles automated backups, verification, and disaster recovery.

**Module Path**: `proxmox_nli.core.storage.backup_manager`

## Classes

### BackupManager

#### __init__(api, base_dir)

#### configure_backup(vm_id: str, schedule: Dict, location: str = None)

Configure automated backups for a VM

**Returns**: `Dict`

#### create_backup(vm_id: str, mode: str)

Create a backup of a VM

**Returns**: `Dict`

#### verify_backup(vm_id: str, backup_file: str)

Verify a backup's integrity using advanced verification techniques

**Returns**: `Dict`

#### restore_backup(vm_id: str, backup_file: str, target_node: str = None)

Restore a VM from backup

**Returns**: `Dict`

#### configure_remote_storage(storage_type: str, config: Dict)

Configure remote backup storage (S3, B2, etc.)

**Returns**: `Dict`

#### get_backup_status(vm_id: str)

Get backup status for VMs

**Returns**: `Dict`

#### cleanup_old_backups()

Clean up old backups based on retention policy

**Returns**: `Dict`

#### test_backup_recovery(vm_id: str, backup_file: str)

Test backup recovery by creating a temporary VM and restoring the backup.

Args:
    vm_id: VM ID to test backup for
    backup_file: Optional specific backup file to test, otherwise uses latest
    
Returns:
    Test result dictionary

**Returns**: `Dict`

#### configure_retention_policy(policy: Dict)

Configure backup retention policy.

Args:
    policy: Retention policy configuration with hourly, daily, weekly, monthly counts
    
Returns:
    Configuration result dictionary

**Returns**: `Dict`

#### implement_data_deduplication(vm_id: str)

Implement data deduplication for backups.

Args:
    vm_id: Optional VM ID to deduplicate backups for
    
Returns:
    Deduplication result dictionary

**Returns**: `Dict`

