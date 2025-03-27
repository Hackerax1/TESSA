# dependency_visualizer

Service dependency visualization for Proxmox NLI.
Provides tools to visualize service dependencies and relationships.

**Module Path**: `proxmox_nli.services.dependency_visualizer`

## Classes

### DependencyVisualizer

Visualizes service dependencies and relationships.

#### __init__(service_manager, output_dir)

Initialize the dependency visualizer.

Args:
    service_manager: ServiceManager instance to interact with services
    output_dir: Directory to save visualization files (defaults to a subdirectory)

#### generate_dependency_graph(include_undeployed)

Generate a dependency graph of all services.

Args:
    include_undeployed: Whether to include undeployed services from the catalog
    
Returns:
    Dictionary with graph data

**Returns**: `Dict[(str, Any)]`

#### analyze_dependencies()

Analyze service dependencies to find potential issues.

Returns:
    Dictionary with analysis results

**Returns**: `Dict[(str, Any)]`

#### generate_dependency_report()

Generate a natural language report on service dependencies.

Returns:
    Report dictionary with natural language dependency assessment

**Returns**: `Dict[(str, Any)]`

#### generate_dot_graph(output_file)

Generate a DOT format graph for visualization with Graphviz.

Args:
    output_file: Optional file path to save the DOT file (defaults to 'service_dependencies.dot')
    
Returns:
    Dictionary with DOT format graph and file path

**Returns**: `Dict[(str, Any)]`

#### generate_mermaid_graph(output_file)

Generate a Mermaid format graph for visualization.

Args:
    output_file: Optional file path to save the Mermaid file (defaults to 'service_dependencies.mmd')
    
Returns:
    Dictionary with Mermaid format graph and file path

**Returns**: `Dict[(str, Any)]`

#### generate_interactive_visualization(include_undeployed)

Generate an interactive visualization of service dependencies.

Args:
    include_undeployed: Whether to include undeployed services from the catalog
    
Returns:
    Dictionary with visualization data

**Returns**: `Dict[(str, Any)]`

#### generate_natural_language_description(service_id: str)

Generate a natural language description of service dependencies.

Args:
    service_id: Optional service ID to focus on. If None, describes all services.
    
Returns:
    Dictionary with natural language description

**Returns**: `Dict[(str, Any)]`

#### get_service_impact(service_id: str)

Analyze the impact of a service failure.

Args:
    service_id: ID of the service to analyze impact for
    
Returns:
    Dictionary with impact analysis

**Returns**: `Dict[(str, Any)]`

#### generate_impact_report(service_id: str)

Generate a natural language report on the impact of a service failure.

Args:
    service_id: ID of the service to analyze impact for
    
Returns:
    Dictionary with natural language impact report

**Returns**: `Dict[(str, Any)]`

