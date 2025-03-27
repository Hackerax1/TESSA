# template_manager

Service template manager for Proxmox NLI.
Provides functionality to create, customize and share service templates.

**Module Path**: `proxmox_nli.services.template_manager`

## Classes

### TemplateManager

Manager for service templates.

#### __init__(service_catalog)

Initialize the template manager.

Args:
    service_catalog: ServiceCatalog instance

#### get_template(template_id: str)

Get a specific template by ID.

Args:
    template_id: ID of the template to retrieve
    
Returns:
    Template dictionary or None if not found

**Returns**: `Optional[Dict]`

#### get_all_templates()

Get all available templates.

Returns:
    List of template dictionaries

**Returns**: `List[Dict]`

#### create_template_from_service(service_id: str, template_name: str, include_dependencies: bool)

Create a new template from an existing service.

Args:
    service_id: ID of the service to create template from
    template_name: Name for the new template
    include_dependencies: Whether to include dependencies in the template
    
Returns:
    Template creation result dictionary

**Returns**: `Dict`

#### create_custom_template(template_data: Dict)

Create a new custom template from scratch.

Args:
    template_data: Dictionary with template data
    
Returns:
    Template creation result dictionary

**Returns**: `Dict`

#### update_template(template_id: str, template_data: Dict)

Update an existing template.

Args:
    template_id: ID of the template to update
    template_data: New template data
    
Returns:
    Template update result dictionary

**Returns**: `Dict`

#### delete_template(template_id: str)

Delete a template.

Args:
    template_id: ID of the template to delete
    
Returns:
    Template deletion result dictionary

**Returns**: `Dict`

#### share_template(template_id: str)

Share a template by copying it to the shared directory.

Args:
    template_id: ID of the template to share
    
Returns:
    Template sharing result dictionary

**Returns**: `Dict`

#### unshare_template(template_id: str)

Unshare a template by moving it back to the local templates directory.

Args:
    template_id: ID of the template to unshare
    
Returns:
    Template unsharing result dictionary

**Returns**: `Dict`

#### export_template(template_id: str, output_path: str)

Export a template to a file.

Args:
    template_id: ID of the template to export
    output_path: Path to export to, or None to use a default location
    
Returns:
    Template export result dictionary

**Returns**: `Dict`

#### import_template(source_path: str, make_shared: bool)

Import a template from a file or URL.

Args:
    source_path: Path or URL to import from
    make_shared: Whether to import as a shared template
    
Returns:
    Template import result dictionary

**Returns**: `Dict`

#### create_service_from_template(template_id: str, service_id: str)

Create a new service from a template.

Args:
    template_id: ID of the template to use
    service_id: ID for the new service, or None to auto-generate
    
Returns:
    Service creation result dictionary

**Returns**: `Dict`

#### search_templates(query: str)

Search for templates matching a query.

Args:
    query: Search query
    
Returns:
    List of matching template dictionaries

**Returns**: `List[Dict]`

#### generate_template_report()

Generate a report on available templates.

Returns:
    Template report dictionary

**Returns**: `Dict`

#### generate_template_from_description(template_name: str, description: str)

Generate a service template from a natural language description.

Args:
    template_name: Name for the new template
    description: Natural language description of the service
    
Returns:
    Template creation result dictionary

**Returns**: `Dict`

#### get_template_recommendations(requirements: str)

Get template recommendations based on natural language requirements.

Args:
    requirements: Natural language description of requirements
    
Returns:
    Dictionary with recommended templates

**Returns**: `Dict`

#### generate_template_comparison(template_ids: List[str])

Generate a comparison between multiple templates.

Args:
    template_ids: List of template IDs to compare
    
Returns:
    Dictionary with comparison data

**Returns**: `Dict`

#### get_template_natural_language_description(template_id: str)

Get a natural language description of a template.

Args:
    template_id: ID of the template to describe
    
Returns:
    Dictionary with template description

**Returns**: `Dict`

