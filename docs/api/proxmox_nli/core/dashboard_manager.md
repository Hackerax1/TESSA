# dashboard_manager

Dashboard management module for user-configurable dashboards.

**Module Path**: `proxmox_nli.core.dashboard_manager`

## Classes

### DashboardManager

#### __init__(data_dir: str)

Initialize the dashboard manager

Args:
    data_dir: Directory to store dashboard data. If None,
             defaults to the 'data' directory in the project root.

#### create_dashboard(user_id: str, name: str, is_default: bool, layout: str = False)

Create a new dashboard

Args:
    user_id: The user identifier
    name: Dashboard name
    is_default: Whether this is the default dashboard
    layout: Dashboard layout type ("grid", "free", etc.)
    
Returns:
    Optional[int]: Dashboard ID if successful, None otherwise

**Returns**: `Optional[int]`

#### get_dashboards(user_id: str)

Get all dashboards for a user

Args:
    user_id: The user identifier
    
Returns:
    List[Dict[str, Any]]: List of dashboard objects

**Returns**: `List[Dict[(str, Any)]]`

#### get_dashboard(dashboard_id: int)

Get a specific dashboard by ID

Args:
    dashboard_id: Dashboard ID
    
Returns:
    Optional[Dict[str, Any]]: Dashboard object if found, None otherwise

**Returns**: `Optional[Dict[(str, Any)]]`

#### update_dashboard(dashboard_id: int, name: str, is_default: bool = None, layout: str = None)

Update dashboard properties

Args:
    dashboard_id: Dashboard ID
    name: Optional new dashboard name
    is_default: Optional default status
    layout: Optional new layout
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### delete_dashboard(dashboard_id: int)

Delete a dashboard

Args:
    dashboard_id: Dashboard ID
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### add_panel(dashboard_id: int, panel_type: str, title: str, config: Dict, position_x: int = None, position_y: int = 0, width: int = 0, height: int = 6)

Add a new panel to a dashboard

Args:
    dashboard_id: Dashboard ID
    panel_type: Panel type (chart, metrics, vm_list, etc.)
    title: Panel title
    config: Panel configuration
    position_x: X position in grid
    position_y: Y position in grid
    width: Panel width (grid units)
    height: Panel height (grid units)
    
Returns:
    Optional[int]: Panel ID if successful, None otherwise

**Returns**: `Optional[int]`

#### update_panel(panel_id: int, title: str, config: Dict = None, position_x: int = None, position_y: int = None, width: int = None, height: int = None)

Update panel properties

Args:
    panel_id: Panel ID
    title: Optional new title
    config: Optional new config
    position_x: Optional new X position
    position_y: Optional new Y position
    width: Optional new width
    height: Optional new height
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### delete_panel(panel_id: int)

Delete a panel

Args:
    panel_id: Panel ID
    
Returns:
    bool: True if successful, False otherwise

**Returns**: `bool`

#### initialize_default_dashboard(user_id: str)

Create a default dashboard for a user

Args:
    user_id: The user identifier
    
Returns:
    Optional[int]: Dashboard ID if successful, None otherwise

**Returns**: `Optional[int]`

#### sync_user_dashboards(user_id: str, remote_dashboards: List[Dict])

Sync dashboards with remote data for cross-device support.

Args:
    user_id: The user identifier
    remote_dashboards: List of dashboard configurations from remote
    
Returns:
    bool: True if sync successful, False otherwise

**Returns**: `bool`

