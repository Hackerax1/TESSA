# backup_handler

Backup handler for service configurations and data.

**Module Path**: `proxmox_nli.services.backup_handler`

## Classes

### ServiceBackupHandler

Handler for backing up and restoring service configurations.

#### __init__(backup_dir: str)

Initialize the backup handler.

Args:
    backup_dir: Directory for storing backups. If None, uses default location.

#### backup_service(service_def: Dict, vm_id: str, include_data: bool)

Create a backup of a service's configuration and optionally its data.

Args:
    service_def: Service definition dictionary
    vm_id: VM ID where the service is running
    include_data: Whether to include service data in backup
    
Returns:
    Backup result dictionary

**Returns**: `Dict`

#### restore_service(backup_id: str, target_vm_id: Optional[str])

Restore a service from backup.

Args:
    backup_id: ID of the backup to restore
    target_vm_id: Optional VM ID to restore to. If None, uses original VM ID.
    
Returns:
    Restore result dictionary

**Returns**: `Dict`

#### list_backups(service_id: Optional[str])

List available backups.

Args:
    service_id: Optional service ID to filter backups
    
Returns:
    Dictionary with list of backups

**Returns**: `Dict`

