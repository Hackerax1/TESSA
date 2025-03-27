# service_catalog

Service catalog for storing and retrieving available service definitions.
This module provides a registry of services that can be installed via natural language commands.

**Module Path**: `proxmox_nli.services.service_catalog`

## Classes

### ServiceCatalog

A catalog of available services that can be installed.

#### __init__(catalog_dir: str)

Initialize the service catalog.

Args:
    catalog_dir: Directory containing service definitions. If None, uses default location.

#### get_all_services()

Get all available service definitions.

Returns:
    List of service definition dictionaries

**Returns**: `List[Dict]`

#### get_service(service_id: str)

Get a specific service by ID.

Args:
    service_id: The ID of the service to retrieve
    
Returns:
    Service definition dictionary or None if not found

**Returns**: `Optional[Dict]`

#### find_services_by_keywords(query: str)

Find services matching the given keywords in the query.

Args:
    query: The search query containing keywords
    
Returns:
    List of matching service definition dictionaries

**Returns**: `List[Dict]`

#### add_service_definition(service_def: Dict)

Add a new service definition to the catalog.

Args:
    service_def: Service definition dictionary
    
Returns:
    Result dictionary with success status and message

**Returns**: `Dict`

#### get_invalid_services()

Get list of invalid service definitions and their errors.

Returns:
    Dictionary mapping filenames to error messages

**Returns**: `Dict[(str, str)]`

#### get_service_dependencies(service_id: str)

Get all dependencies for a specific service.

Args:
    service_id: The ID of the service to get dependencies for
    
Returns:
    List of dependency dictionaries with service details

**Returns**: `List[Dict]`

#### get_all_required_dependencies(service_id: str, processed_services: List[str])

Get all required dependencies for a service, including transitive dependencies.

Args:
    service_id: The ID of the service to get dependencies for
    processed_services: List of already processed service IDs (to prevent cycles)
    
Returns:
    List of dependency dictionaries with service details

**Returns**: `List[Dict]`

#### get_services_by_goal(goal_id: str)

Get services that support a specific user goal.

Args:
    goal_id: The ID of the user goal
    
Returns:
    List of service dictionaries that support the goal

**Returns**: `List[Dict]`

#### get_replacement_services(cloud_service_id: str)

Get services that can replace a specific cloud service.

Args:
    cloud_service_id: The ID of the cloud service to replace
    
Returns:
    List of service dictionaries that can replace the cloud service

**Returns**: `List[Dict]`

