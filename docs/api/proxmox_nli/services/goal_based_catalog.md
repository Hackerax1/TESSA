# goal_based_catalog

Goal-Based Service Catalog for TESSA
Organizes services by user goals rather than technical categories

**Module Path**: `proxmox_nli.services.goal_based_catalog`

## Classes

### GoalBasedCatalog

Organizes services by user goals instead of technical categories.
Provides interfaces for browsing and discovering services based on what
the user wants to accomplish rather than technical implementation details.

#### __init__(service_catalog, goal_mapper = None)

Initialize the goal-based catalog with a service catalog and goal mapper

Args:
    service_catalog: The technical service catalog instance
    goal_mapper: The goal mapper instance that defines user goals

#### build_indexes()

Build indexes for quick goal-based and replacement-based lookups

#### get_goals_with_services()

Get all defined user goals with available services

Returns:
    List of goal dictionaries with their services

**Returns**: `List[Dict]`

#### get_services_for_goal(goal_id: str)

Get services that help achieve a specific user goal

Args:
    goal_id: The ID of the user goal
    
Returns:
    List of service dictionaries

**Returns**: `List[Dict]`

#### get_services_for_cloud_replacement(cloud_id: str)

Get services that can replace a specific cloud service

Args:
    cloud_id: The ID of the cloud service to replace
    
Returns:
    List of service dictionaries

**Returns**: `List[Dict]`

#### get_cloud_replacements_with_services()

Get all defined cloud services with available replacements

Returns:
    List of cloud service dictionaries with their replacement services

**Returns**: `List[Dict]`

#### find_services_by_goal_keywords(query: str)

Find services and goals matching the given keywords in the query

Args:
    query: The search query containing keywords
    
Returns:
    List of dictionaries with goal and matching services

**Returns**: `List[Dict]`

#### get_service_info_with_goals(service_id: str)

Get service information including associated goals

Args:
    service_id: The ID of the service
    
Returns:
    Service dictionary with goal information

**Returns**: `Dict`

#### get_service_recommendations_by_goal(goal_ids: List[str], include_personality: bool)

Get service recommendations for multiple goals

Args:
    goal_ids: List of goal IDs to get recommendations for
    include_personality: Whether to include personality-driven recommendations
    
Returns:
    Dictionary mapping service IDs to recommendation information

**Returns**: `Dict[(str, Dict)]`

#### get_service_recommendations_for_cloud(cloud_service_ids: List[str], include_personality: bool)

Get service recommendations for replacing cloud services

Args:
    cloud_service_ids: List of cloud service IDs to replace
    include_personality: Whether to include personality-driven recommendations
    
Returns:
    Dictionary mapping service IDs to recommendation information

**Returns**: `Dict[(str, Dict)]`

#### categorize_service_catalog()

Categorize the entire service catalog by primary user goals
Instead of technical categories, group by what users want to accomplish

Returns:
    Dictionary mapping goal categories to lists of services

**Returns**: `Dict[(str, Dict)]`

