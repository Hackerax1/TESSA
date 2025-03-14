"""
Service template manager for Proxmox NLI.
Provides functionality to create, customize and share service templates.
"""
import logging
import json
import os
import yaml
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil
import requests
import tempfile
import zipfile

logger = logging.getLogger(__name__)

class TemplateManager:
    """Manager for service templates."""
    
    def __init__(self, service_catalog):
        """Initialize the template manager.
        
        Args:
            service_catalog: ServiceCatalog instance
        """
        self.service_catalog = service_catalog
        
        # Create template directories if they don't exist
        self.templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        os.makedirs(self.templates_dir, exist_ok=True)
        
        self.shared_dir = os.path.join(self.templates_dir, 'shared')
        os.makedirs(self.shared_dir, exist_ok=True)
        
        # Dictionary to track created templates
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """Load custom templates from the templates directory."""
        try:
            # Load local templates
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.yml') or filename.endswith('.yaml'):
                    template_path = os.path.join(self.templates_dir, filename)
                    try:
                        with open(template_path, 'r') as f:
                            template = yaml.safe_load(f)
                            if 'template_id' in template:
                                self.templates[template['template_id']] = {
                                    'template': template,
                                    'path': template_path,
                                    'type': 'local'
                                }
                    except Exception as e:
                        logger.error(f"Error loading template {filename}: {str(e)}")
                        
            # Load shared templates
            for filename in os.listdir(self.shared_dir):
                if filename.endswith('.yml') or filename.endswith('.yaml'):
                    template_path = os.path.join(self.shared_dir, filename)
                    try:
                        with open(template_path, 'r') as f:
                            template = yaml.safe_load(f)
                            if 'template_id' in template:
                                self.templates[template['template_id']] = {
                                    'template': template,
                                    'path': template_path,
                                    'type': 'shared'
                                }
                    except Exception as e:
                        logger.error(f"Error loading shared template {filename}: {str(e)}")
                        
            logger.info(f"Loaded {len(self.templates)} templates")
        except Exception as e:
            logger.error(f"Error loading templates: {str(e)}")
            
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            Template dictionary or None if not found
        """
        if template_id in self.templates:
            return self.templates[template_id]['template']
        return None
        
    def get_all_templates(self) -> List[Dict]:
        """Get all available templates.
        
        Returns:
            List of template dictionaries
        """
        return [data['template'] for data in self.templates.values()]
        
    def create_template_from_service(self, service_id: str, template_name: str, 
                                   include_dependencies: bool = False) -> Dict:
        """Create a new template from an existing service.
        
        Args:
            service_id: ID of the service to create template from
            template_name: Name for the new template
            include_dependencies: Whether to include dependencies in the template
            
        Returns:
            Template creation result dictionary
        """
        service = self.service_catalog.get_service(service_id)
        if not service:
            return {
                "success": False,
                "message": f"Service with ID '{service_id}' not found"
            }
            
        # Create a template ID
        template_id = f"template_{str(uuid.uuid4())[:8]}"
        
        # Start with a copy of the service
        template = service.copy()
        
        # Update template-specific fields
        template['template_id'] = template_id
        template['template_name'] = template_name
        template['created_from'] = service_id
        template['created_at'] = datetime.now().isoformat()
        
        # If not including dependencies, remove them
        if not include_dependencies:
            template['dependencies'] = []
            
        # Remove any fields that shouldn't be in templates
        if 'id' in template:
            del template['id']
            
        # Save the template to disk
        template_filename = f"{template_id}.yml"
        template_path = os.path.join(self.templates_dir, template_filename)
        
        try:
            with open(template_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False)
                
            # Add to templates dictionary
            self.templates[template_id] = {
                'template': template,
                'path': template_path,
                'type': 'local'
            }
            
            return {
                "success": True,
                "message": f"Successfully created template '{template_name}' from service '{service_id}'",
                "template_id": template_id,
                "template": template
            }
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create template: {str(e)}"
            }
            
    def create_custom_template(self, template_data: Dict) -> Dict:
        """Create a new custom template from scratch.
        
        Args:
            template_data: Dictionary with template data
            
        Returns:
            Template creation result dictionary
        """
        if not template_data.get('template_name'):
            return {
                "success": False,
                "message": "Template name is required"
            }
            
        # Create a template ID if not provided
        if 'template_id' not in template_data:
            template_data['template_id'] = f"template_{str(uuid.uuid4())[:8]}"
            
        template_id = template_data['template_id']
        
        # Add creation timestamp
        if 'created_at' not in template_data:
            template_data['created_at'] = datetime.now().isoformat()
            
        # Save the template to disk
        template_filename = f"{template_id}.yml"
        template_path = os.path.join(self.templates_dir, template_filename)
        
        try:
            with open(template_path, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False)
                
            # Add to templates dictionary
            self.templates[template_id] = {
                'template': template_data,
                'path': template_path,
                'type': 'local'
            }
            
            return {
                "success": True,
                "message": f"Successfully created custom template '{template_data['template_name']}'",
                "template_id": template_id,
                "template": template_data
            }
        except Exception as e:
            logger.error(f"Error creating custom template: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create custom template: {str(e)}"
            }
            
    def update_template(self, template_id: str, template_data: Dict) -> Dict:
        """Update an existing template.
        
        Args:
            template_id: ID of the template to update
            template_data: New template data
            
        Returns:
            Template update result dictionary
        """
        if template_id not in self.templates:
            return {
                "success": False,
                "message": f"Template with ID '{template_id}' not found"
            }
            
        template_info = self.templates[template_id]
        
        # Don't allow updating shared templates
        if template_info['type'] == 'shared':
            return {
                "success": False,
                "message": f"Cannot update shared template '{template_id}'"
            }
            
        # Ensure template_id is preserved
        template_data['template_id'] = template_id
        
        # Add updated timestamp
        template_data['updated_at'] = datetime.now().isoformat()
        
        # Save the template to disk
        template_path = template_info['path']
        
        try:
            with open(template_path, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False)
                
            # Update templates dictionary
            self.templates[template_id] = {
                'template': template_data,
                'path': template_path,
                'type': 'local'
            }
            
            return {
                "success": True,
                "message": f"Successfully updated template '{template_data.get('template_name', template_id)}'",
                "template_id": template_id,
                "template": template_data
            }
        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update template: {str(e)}"
            }
            
    def delete_template(self, template_id: str) -> Dict:
        """Delete a template.
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            Template deletion result dictionary
        """
        if template_id not in self.templates:
            return {
                "success": False,
                "message": f"Template with ID '{template_id}' not found"
            }
            
        template_info = self.templates[template_id]
        
        # Don't allow deleting shared templates
        if template_info['type'] == 'shared':
            return {
                "success": False,
                "message": f"Cannot delete shared template '{template_id}'. Use unshare_template instead."
            }
            
        template_path = template_info['path']
        template_name = template_info['template'].get('template_name', template_id)
        
        try:
            # Remove the file
            os.remove(template_path)
            
            # Remove from templates dictionary
            del self.templates[template_id]
            
            return {
                "success": True,
                "message": f"Successfully deleted template '{template_name}'",
                "template_id": template_id
            }
        except Exception as e:
            logger.error(f"Error deleting template: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to delete template: {str(e)}"
            }
            
    def share_template(self, template_id: str) -> Dict:
        """Share a template by copying it to the shared directory.
        
        Args:
            template_id: ID of the template to share
            
        Returns:
            Template sharing result dictionary
        """
        if template_id not in self.templates:
            return {
                "success": False,
                "message": f"Template with ID '{template_id}' not found"
            }
            
        template_info = self.templates[template_id]
        
        # Already shared
        if template_info['type'] == 'shared':
            return {
                "success": True,
                "message": f"Template '{template_id}' is already shared",
                "template_id": template_id
            }
            
        template = template_info['template']
        template_name = template.get('template_name', template_id)
        
        # Add sharing metadata
        template['shared'] = True
        template['shared_at'] = datetime.now().isoformat()
        
        # Save to shared directory
        shared_filename = f"{template_id}.yml"
        shared_path = os.path.join(self.shared_dir, shared_filename)
        
        try:
            with open(shared_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False)
                
            # Update templates dictionary
            self.templates[template_id] = {
                'template': template,
                'path': shared_path,
                'type': 'shared'
            }
            
            # Remove the original file
            if os.path.exists(template_info['path']):
                os.remove(template_info['path'])
            
            return {
                "success": True,
                "message": f"Successfully shared template '{template_name}'",
                "template_id": template_id,
                "template": template
            }
        except Exception as e:
            logger.error(f"Error sharing template: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to share template: {str(e)}"
            }
            
    def unshare_template(self, template_id: str) -> Dict:
        """Unshare a template by moving it back to the local templates directory.
        
        Args:
            template_id: ID of the template to unshare
            
        Returns:
            Template unsharing result dictionary
        """
        if template_id not in self.templates:
            return {
                "success": False,
                "message": f"Template with ID '{template_id}' not found"
            }
            
        template_info = self.templates[template_id]
        
        # Not shared
        if template_info['type'] != 'shared':
            return {
                "success": True,
                "message": f"Template '{template_id}' is not shared",
                "template_id": template_id
            }
            
        template = template_info['template']
        template_name = template.get('template_name', template_id)
        
        # Remove sharing metadata
        if 'shared' in template:
            del template['shared']
        if 'shared_at' in template:
            del template['shared_at']
        
        # Save to local directory
        local_filename = f"{template_id}.yml"
        local_path = os.path.join(self.templates_dir, local_filename)
        
        try:
            with open(local_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False)
                
            # Update templates dictionary
            self.templates[template_id] = {
                'template': template,
                'path': local_path,
                'type': 'local'
            }
            
            # Remove the shared file
            if os.path.exists(template_info['path']):
                os.remove(template_info['path'])
            
            return {
                "success": True,
                "message": f"Successfully unshared template '{template_name}'",
                "template_id": template_id,
                "template": template
            }
        except Exception as e:
            logger.error(f"Error unsharing template: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to unshare template: {str(e)}"
            }
            
    def export_template(self, template_id: str, output_path: str = None) -> Dict:
        """Export a template to a file.
        
        Args:
            template_id: ID of the template to export
            output_path: Path to export to, or None to use a default location
            
        Returns:
            Template export result dictionary
        """
        if template_id not in self.templates:
            return {
                "success": False,
                "message": f"Template with ID '{template_id}' not found"
            }
            
        template_info = self.templates[template_id]
        template = template_info['template']
        template_name = template.get('template_name', template_id)
        
        if not output_path:
            # Use a default location
            output_path = os.path.join(os.path.dirname(self.templates_dir), 'exports', f"{template_id}.zip")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Create a ZIP file
            with zipfile.ZipFile(output_path, 'w') as zipf:
                # Add the template YAML
                template_str = yaml.dump(template, default_flow_style=False)
                zipf.writestr(f"{template_id}.yml", template_str)
                
                # Add a README
                readme = f"# {template_name}\n\n"
                readme += f"This is a service template exported from Proxmox NLI.\n\n"
                readme += f"- Template ID: {template_id}\n"
                readme += f"- Created: {template.get('created_at', 'Unknown')}\n"
                
                if 'description' in template:
                    readme += f"\n## Description\n\n{template['description']}\n"
                    
                readme += "\n## Installation\n\n"
                readme += "To import this template, use the Proxmox NLI command:\n"
                readme += f"`import template from file <path-to-zip>`\n"
                
                zipf.writestr("README.md", readme)
            
            return {
                "success": True,
                "message": f"Successfully exported template '{template_name}'",
                "template_id": template_id,
                "output_path": output_path
            }
        except Exception as e:
            logger.error(f"Error exporting template: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export template: {str(e)}"
            }
            
    def import_template(self, source_path: str, make_shared: bool = False) -> Dict:
        """Import a template from a file or URL.
        
        Args:
            source_path: Path or URL to import from
            make_shared: Whether to import as a shared template
            
        Returns:
            Template import result dictionary
        """
        try:
            temp_dir = tempfile.mkdtemp()
            
            # Handle URL vs local file
            if source_path.startswith(('http://', 'https://')):
                # Download from URL
                try:
                    response = requests.get(source_path, timeout=30)
                    response.raise_for_status()
                    
                    download_path = os.path.join(temp_dir, "downloaded_template.zip")
                    with open(download_path, 'wb') as f:
                        f.write(response.content)
                        
                    source_path = download_path
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Failed to download template from URL: {str(e)}"
                    }
            
            # Extract the zip file
            try:
                with zipfile.ZipFile(source_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to extract template archive: {str(e)}"
                }
                
            # Find the template YAML file
            template_file = None
            for filename in os.listdir(temp_dir):
                if filename.endswith('.yml') or filename.endswith('.yaml'):
                    template_file = os.path.join(temp_dir, filename)
                    break
                    
            if not template_file:
                return {
                    "success": False,
                    "message": "No template YAML file found in the archive"
                }
                
            # Load the template
            try:
                with open(template_file, 'r') as f:
                    template = yaml.safe_load(f)
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to parse template YAML: {str(e)}"
                }
                
            if 'template_id' not in template:
                # Generate a new template ID
                template['template_id'] = f"template_{str(uuid.uuid4())[:8]}"
                
            template_id = template['template_id']
            template_name = template.get('template_name', template_id)
            
            # Save to the appropriate directory
            target_dir = self.shared_dir if make_shared else self.templates_dir
            target_path = os.path.join(target_dir, f"{template_id}.yml")
            
            with open(target_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False)
                
            # Add to templates dictionary
            self.templates[template_id] = {
                'template': template,
                'path': target_path,
                'type': 'shared' if make_shared else 'local'
            }
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {
                "success": True,
                "message": f"Successfully imported template '{template_name}'",
                "template_id": template_id,
                "template": template
            }
        except Exception as e:
            logger.error(f"Error importing template: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to import template: {str(e)}"
            }
            
    def create_service_from_template(self, template_id: str, service_id: str = None) -> Dict:
        """Create a new service from a template.
        
        Args:
            template_id: ID of the template to use
            service_id: ID for the new service, or None to auto-generate
            
        Returns:
            Service creation result dictionary
        """
        if template_id not in self.templates:
            return {
                "success": False,
                "message": f"Template with ID '{template_id}' not found"
            }
            
        template_info = self.templates[template_id]
        template = template_info['template']
        
        # Create a new service definition from the template
        service_def = template.copy()
        
        # Remove template-specific fields
        template_fields = ['template_id', 'template_name', 'created_at', 'updated_at', 
                           'shared', 'shared_at']
        for field in template_fields:
            if field in service_def:
                del service_def[field]
                
        # Set service ID
        if not service_id:
            # Generate an ID based on the name
            base_id = service_def.get('name', 'service').lower().replace(' ', '-')
            service_id = f"{base_id}-{str(uuid.uuid4())[:8]}"
            
        service_def['id'] = service_id
        
        # Add the service to the catalog
        result = self.service_catalog.add_service_definition(service_def)
        
        if result.get('success'):
            result['service_id'] = service_id
            result['service'] = service_def
            result['from_template'] = template_id
            
        return result
    
    def search_templates(self, query: str) -> List[Dict]:
        """Search for templates matching a query.
        
        Args:
            query: Search query
            
        Returns:
            List of matching template dictionaries
        """
        query = query.lower()
        matches = []
        
        for template_id, template_info in self.templates.items():
            template = template_info['template']
            
            # Check if query matches template name or description
            if (
                query in template_id.lower() or 
                query in template.get('template_name', '').lower() or
                query in template.get('description', '').lower()
            ):
                matches.append(template)
                
        return matches
    
    def generate_template_report(self) -> Dict:
        """Generate a report on available templates.
        
        Returns:
            Template report dictionary
        """
        local_templates = []
        shared_templates = []
        
        for template_id, template_info in self.templates.items():
            template = template_info['template']
            template_type = template_info['type']
            
            template_summary = {
                'id': template_id,
                'name': template.get('template_name', template_id),
                'created_at': template.get('created_at'),
                'type': template_type
            }
            
            if template_type == 'local':
                local_templates.append(template_summary)
            else:
                shared_templates.append(template_summary)
                
        return {
            "success": True,
            "local_count": len(local_templates),
            "shared_count": len(shared_templates),
            "total_count": len(self.templates),
            "local_templates": local_templates,
            "shared_templates": shared_templates
        }