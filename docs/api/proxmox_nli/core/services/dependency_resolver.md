# dependency_resolver

Dependency resolution module for Proxmox NLI.

This module provides a simplified facade to the more complex dependency management
functionality in the services package, making it easier for the NLI core to handle
service dependencies.

**Module Path**: `proxmox_nli.core.services.dependency_resolver`

## Classes

### DependencyResolver

Service dependency resolution for the NLI core.

This class provides a simpler interface for the NLI system to resolve
service dependencies and provides specialized NLI-related functions not
present in the main DependencyManager.

#### __init__(base_nli)

Initialize with the base NLI context

#### get_dependencies(service_id: str, required_only: bool)

Get all dependencies for a service

Args:
    service_id: ID of the service to get dependencies for
    required_only: Whether to include only required dependencies
    
Returns:
    List of dependency dictionaries

**Returns**: `List[Dict]`

#### check_circular_dependencies(service_id: str)

Check for circular dependencies for a service

Args:
    service_id: ID of the service to check
    
Returns:
    Tuple of (has_circular, circular_path)

**Returns**: `Tuple[(bool, Optional[List[str]])]`

#### get_installation_plan(service_ids: List[str])

Generate an installation plan for multiple services

Args:
    service_ids: List of service IDs to include in the plan
    
Returns:
    Installation plan dictionary

**Returns**: `Dict`

#### explain_dependencies(service_id: str)

Generate a human-readable explanation of service dependencies

Args:
    service_id: ID of the service to explain dependencies for
    
Returns:
    Dictionary with explanation

**Returns**: `Dict`

#### get_dependency_diagram(service_id: Optional[str])

Generate a dependency diagram for a service

Args:
    service_id: Optional ID of the service to diagram
    
Returns:
    Dictionary with diagram data

**Returns**: `Dict`

