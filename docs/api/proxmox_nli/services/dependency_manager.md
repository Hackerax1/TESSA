# dependency_manager

Dependency Manager for service dependencies in TESSA
Handles dependency resolution, visualization, and installation ordering

**Module Path**: `proxmox_nli.services.dependency_manager`

## Classes

### DependencyManager

Manages service dependencies for the TESSA service catalog.
- Resolves dependency chains
- Creates installation order lists
- Detects circular dependencies
- Visualizes dependency graphs

#### __init__(service_catalog)

Initialize the dependency manager with a service catalog

#### build_dependency_graph()

Build a directed graph of all service dependencies in the catalog

#### get_installation_order(service_id: str)

Get the proper installation order for a service and its dependencies

Args:
    service_id: The ID of the service to install
    
Returns:
    List of service IDs in proper installation order

**Returns**: `List[str]`

#### detect_circular_dependencies()

Detect any circular dependencies in the service catalog

Returns:
    List of cycles, each a list of service IDs in the cycle

**Returns**: `List[List[str]]`

#### get_dependency_tree(service_id: str)

Get a hierarchical tree of dependencies for a service

Args:
    service_id: The ID of the service to get dependencies for
    
Returns:
    Nested dictionary representing the dependency tree

**Returns**: `Dict`

#### visualize_dependencies(service_id: str, include_optional: bool = None)

Generate a visualization of the dependency graph for a service

Args:
    service_id: The ID of the service to visualize dependencies for (or None for all services)
    include_optional: Whether to include optional dependencies in the visualization
    
Returns:
    Base64 encoded PNG image of the dependency graph or None if visualization fails

**Returns**: `Optional[str]`

#### can_install_service(service_id: str)

Determine if a service can be installed based on its dependencies

Args:
    service_id: The ID of the service to check
    
Returns:
    (bool, str): Tuple of (can_install, reason)

**Returns**: `Tuple[(bool, str)]`

