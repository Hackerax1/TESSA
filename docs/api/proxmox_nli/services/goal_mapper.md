# goal_mapper

Goal Mapper Service for TESSA
Maps user goals to recommended services and provides explanations

**Module Path**: `proxmox_nli.services.goal_mapper`

## Classes

### GoalMapper

Maps user goals to recommended services

#### __init__(catalog_dir)

Initialize the goal mapper with the service catalog directory

#### load_services()

Load all services from the catalog directory

#### get_service_by_id(service_id)

Get service details by ID

#### is_foss_service(service)

Determine if a service is FOSS (Free and Open Source Software)

Args:
    service (dict): Service definition dictionary
    
Returns:
    bool: True if service is FOSS, False otherwise

**Returns**: `bool: True if service is FOSS, False otherwise`

#### is_excluded_service(service_id)

Check if a service should be excluded from recommendations

Args:
    service_id (str): Service ID to check
    
Returns:
    bool: True if service should be excluded, False otherwise

**Returns**: `bool: True if service should be excluded, False otherwise`

#### get_recommended_services(goals, include_personality)

Get recommended services based on user goals

Args:
    goals (list): List of goal IDs selected by the user
    include_personality (bool): Whether to include personality-driven recommendations
    
Returns:
    dict: Dictionary with recommended services and explanations

**Returns**: `dict: Dictionary with recommended services and explanations`

#### get_cloud_replacement_services(service_names, include_personality)

Get recommended services to replace specific cloud services

Args:
    service_names (list): List of cloud service IDs to replace
    include_personality (bool): Whether to include personality-driven recommendations
    
Returns:
    dict: Dictionary with recommended services and explanations

**Returns**: `dict: Dictionary with recommended services and explanations`

#### estimate_resource_requirements(service_ids)

Estimate total resource requirements for a set of services

Args:
    service_ids (list): List of service IDs
    
Returns:
    dict: Dictionary with total resource requirements

**Returns**: `dict: Dictionary with total resource requirements`

#### get_service_dependencies(service_id)

Get all dependencies for a specific service

Args:
    service_id (str): Service ID to get dependencies for
    
Returns:
    list: List of dependency dictionaries

**Returns**: `list: List of dependency dictionaries`

#### get_all_required_dependencies(service_id, processed_services)

Get all required dependencies for a service, including transitive dependencies

Args:
    service_id (str): Service ID to get dependencies for
    processed_services (list): List of already processed service IDs (to prevent cycles)
    
Returns:
    list: List of dependency dictionaries

**Returns**: `list: List of dependency dictionaries`

#### get_all_goals()

Get all defined user goals

Returns:
    dict: Dictionary of all goals with their descriptions

**Returns**: `dict: Dictionary of all goals with their descriptions`

#### get_all_cloud_services()

Get all defined cloud services that can be replaced

Returns:
    dict: Dictionary of all cloud services with their descriptions

**Returns**: `dict: Dictionary of all cloud services with their descriptions`

