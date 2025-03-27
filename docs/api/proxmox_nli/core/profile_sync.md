# profile_sync

Profile synchronization module for cross-device support.

**Module Path**: `proxmox_nli.core.profile_sync`

## Classes

### ProfileSyncManager

Manages synchronization of user profiles and preferences across devices.

#### __init__(data_dir: str, dashboard_manager = None)

Initialize the profile sync manager.

Args:
    data_dir: Directory to store sync data
    dashboard_manager: DashboardManager instance for dashboard sync

#### start_sync_service()

Start the background sync service

#### stop_sync_service()

Stop the background sync service

#### queue_sync_task(user_id: str, task_type: str, data: Dict)

Queue a sync task for processing

Args:
    user_id: The user identifier
    task_type: Type of sync task ('dashboards', 'preferences', etc.)
    data: The data to sync

#### register_device(user_id: str, device_name: str)

Register a new device for sync

Args:
    user_id: The user identifier
    device_name: Name of the device
    
Returns:
    str: Device ID for the registered device

**Returns**: `str`

#### enable_sync(user_id: str, enabled: bool)

Enable or disable sync for a user

Args:
    user_id: The user identifier
    enabled: Whether sync should be enabled

