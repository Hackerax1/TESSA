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
import re

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
        
        # Create community templates directory
        self.community_dir = os.path.join(self.templates_dir, 'community')
        os.makedirs(self.community_dir, exist_ok=True)
        
        # Dictionary to track created templates
        self.templates = {}
        self._load_templates()
        
        # Community repository URL (could be configurable)
        self.community_repo_url = "https://api.github.com/repos/proxmox-nli/community-templates/contents"
        
        # Template validation schema
        self.template_schema = {
            "required": ["template_id", "template_name", "description", "version"],
            "properties": {
                "template_id": {"type": "string"},
                "template_name": {"type": "string"},
                "description": {"type": "string"},
                "version": {"type": "string"},
                "author": {"type": "string"},
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "services": {"type": "array", "items": {"type": "object"}},
                "configuration": {"type": "object"},
                "dependencies": {"type": "array", "items": {"type": "string"}}
            }
        }
        
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
            
    def share_template(self, template_id: str, share_type: str = 'local') -> Dict:
        """Share a template with others.
        
        Args:
            template_id: ID of the template to share
            share_type: Type of sharing ('local', 'community')
            
        Returns:
            Template sharing result dictionary
        """
        if template_id not in self.templates:
            return {
                'success': False,
                'message': f'Template with ID {template_id} not found'
            }
            
        template_data = self.templates[template_id]
        template = template_data['template']
        
        # Update sharing metadata
        template['shared'] = True
        template['share_type'] = share_type
        template['shared_at'] = datetime.now().isoformat()
        
        if share_type == 'local':
            # Copy to shared directory
            shared_filename = f"{template_id}.yml"
            shared_path = os.path.join(self.shared_dir, shared_filename)
            
            try:
                with open(shared_path, 'w') as f:
                    yaml.dump(template, f, default_flow_style=False)
                    
                # Update template record
                self.templates[template_id] = {
                    'template': template,
                    'path': shared_path,
                    'type': 'shared'
                }
                
                return {
                    'success': True,
                    'message': f'Template {template["template_name"]} shared locally',
                    'template_id': template_id,
                    'share_url': f'file://{shared_path}'
                }
            except Exception as e:
                logger.error(f"Error sharing template locally: {str(e)}")
                return {
                    'success': False,
                    'message': f'Failed to share template locally: {str(e)}'
                }
        elif share_type == 'community':
            # This would typically involve uploading to a community repository
            # For now, we'll just copy to the community directory
            community_filename = f"{template_id}.yml"
            community_path = os.path.join(self.community_dir, community_filename)
            
            try:
                with open(community_path, 'w') as f:
                    yaml.dump(template, f, default_flow_style=False)
                    
                return {
                    'success': True,
                    'message': f'Template {template["template_name"]} shared with community',
                    'template_id': template_id,
                    'share_url': f'community://{template_id}'
                }
            except Exception as e:
                logger.error(f"Error sharing template with community: {str(e)}")
                return {
                    'success': False,
                    'message': f'Failed to share template with community: {str(e)}'
                }
        else:
            return {
                'success': False,
                'message': f'Unknown share type: {share_type}'
            }
    
    def import_template(self, source: str, source_type: str = 'file') -> Dict:
        """Import a template from an external source.
        
        Args:
            source: Source of the template (file path, URL, or ID)
            source_type: Type of source ('file', 'url', 'community')
            
        Returns:
            Template import result dictionary
        """
        try:
            if source_type == 'file':
                # Import from a local file
                if not os.path.exists(source):
                    return {
                        'success': False,
                        'message': f'File not found: {source}'
                    }
                    
                with open(source, 'r') as f:
                    template = yaml.safe_load(f)
            elif source_type == 'url':
                # Import from a URL
                response = requests.get(source)
                if response.status_code != 200:
                    return {
                        'success': False,
                        'message': f'Failed to download template: HTTP {response.status_code}'
                    }
                    
                template = yaml.safe_load(response.text)
            elif source_type == 'community':
                # Import from community repository
                community_url = f"{self.community_repo_url}/{source}.yml"
                response = requests.get(community_url)
                if response.status_code != 200:
                    return {
                        'success': False,
                        'message': f'Failed to download community template: HTTP {response.status_code}'
                    }
                    
                content = response.json().get('content', '')
                if content:
                    import base64
                    decoded_content = base64.b64decode(content).decode('utf-8')
                    template = yaml.safe_load(decoded_content)
                else:
                    return {
                        'success': False,
                        'message': 'Failed to get template content from community repository'
                    }
            else:
                return {
                    'success': False,
                    'message': f'Unknown source type: {source_type}'
                }
                
            # Validate template
            if not self._validate_template(template):
                return {
                    'success': False,
                    'message': 'Invalid template format'
                }
                
            # Check if template already exists
            template_id = template.get('template_id')
            if template_id in self.templates:
                # Update existing template
                existing_template = self.templates[template_id]['template']
                existing_version = existing_template.get('version', '0.0.0')
                new_version = template.get('version', '0.0.0')
                
                # Compare versions (simple string comparison for now)
                if new_version <= existing_version:
                    return {
                        'success': False,
                        'message': f'Template {template_id} already exists with same or newer version'
                    }
                    
            # Save the template
            template_filename = f"{template_id}.yml"
            template_path = os.path.join(self.templates_dir, template_filename)
            
            with open(template_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False)
                
            # Add to templates dictionary
            self.templates[template_id] = {
                'template': template,
                'path': template_path,
                'type': 'imported'
            }
            
            return {
                'success': True,
                'message': f'Successfully imported template {template.get("template_name")}',
                'template_id': template_id,
                'template': template
            }
        except Exception as e:
            logger.error(f"Error importing template: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to import template: {str(e)}'
            }
    
    def create_template_from_scratch(self, template_data: Dict) -> Dict:
        """Create a completely new template from scratch.
        
        Args:
            template_data: Template data including name, description, and configuration
            
        Returns:
            Template creation result dictionary
        """
        # Validate required fields
        required_fields = ['template_name', 'description']
        for field in required_fields:
            if field not in template_data:
                return {
                    'success': False,
                    'message': f'Missing required field: {field}'
                }
                
        # Create a template ID if not provided
        if 'template_id' not in template_data:
            template_data['template_id'] = f"template_{str(uuid.uuid4())[:8]}"
            
        template_id = template_data['template_id']
        
        # Add metadata
        if 'created_at' not in template_data:
            template_data['created_at'] = datetime.now().isoformat()
        if 'updated_at' not in template_data:
            template_data['updated_at'] = datetime.now().isoformat()
        if 'version' not in template_data:
            template_data['version'] = '1.0.0'
        if 'tags' not in template_data:
            template_data['tags'] = []
        if 'services' not in template_data:
            template_data['services'] = []
        if 'configuration' not in template_data:
            template_data['configuration'] = {}
            
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
                'success': True,
                'message': f'Successfully created template {template_data["template_name"]}',
                'template_id': template_id,
                'template': template_data
            }
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to create template: {str(e)}'
            }
    
    def search_community_templates(self, query: str = None, tags: List[str] = None) -> Dict:
        """Search for templates in the community repository.
        
        Args:
            query: Optional search query
            tags: Optional list of tags to filter by
            
        Returns:
            Dictionary with search results
        """
        try:
            # In a real implementation, this would query a community API
            # For now, we'll just list templates in the community directory
            templates = []
            
            for filename in os.listdir(self.community_dir):
                if filename.endswith('.yml') or filename.endswith('.yaml'):
                    template_path = os.path.join(self.community_dir, filename)
                    try:
                        with open(template_path, 'r') as f:
                            template = yaml.safe_load(f)
                            
                            # Apply query filter if provided
                            if query:
                                query_lower = query.lower()
                                name = template.get('template_name', '').lower()
                                description = template.get('description', '').lower()
                                
                                if query_lower not in name and query_lower not in description:
                                    continue
                                    
                            # Apply tag filter if provided
                            if tags:
                                template_tags = template.get('tags', [])
                                if not any(tag in template_tags for tag in tags):
                                    continue
                                    
                            templates.append(template)
                    except Exception as e:
                        logger.error(f"Error loading community template {filename}: {str(e)}")
            
            return {
                'success': True,
                'message': f'Found {len(templates)} community templates',
                'templates': templates
            }
        except Exception as e:
            logger.error(f"Error searching community templates: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to search community templates: {str(e)}'
            }
    
    def _validate_template(self, template: Dict) -> bool:
        """Validate a template against the schema.
        
        Args:
            template: Template to validate
            
        Returns:
            True if template is valid, False otherwise
        """
        # Check required fields
        for field in self.template_schema['required']:
            if field not in template:
                logger.error(f"Template missing required field: {field}")
                return False
                
        # Basic validation passed
        return True
    
    def get_template_categories(self) -> Dict:
        """Get categories of available templates.
        
        Returns:
            Dictionary with template categories
        """
        categories = {}
        
        for template_id, template_data in self.templates.items():
            template = template_data['template']
            tags = template.get('tags', [])
            
            for tag in tags:
                if tag not in categories:
                    categories[tag] = []
                    
                categories[tag].append(template_id)
                
        return {
            'success': True,
            'message': f'Found {len(categories)} template categories',
            'categories': categories
        }
    
    def clone_template(self, template_id: str, new_name: str = None) -> Dict:
        """Clone an existing template.
        
        Args:
            template_id: ID of the template to clone
            new_name: Optional new name for the cloned template
            
        Returns:
            Template cloning result dictionary
        """
        if template_id not in self.templates:
            return {
                'success': False,
                'message': f'Template with ID {template_id} not found'
            }
            
        template_data = self.templates[template_id]
        template = template_data['template'].copy()
        
        # Create a new template ID
        new_template_id = f"template_{str(uuid.uuid4())[:8]}"
        
        # Update template metadata
        template['template_id'] = new_template_id
        if new_name:
            template['template_name'] = new_name
        else:
            template['template_name'] = f"Clone of {template['template_name']}"
            
        template['cloned_from'] = template_id
        template['created_at'] = datetime.now().isoformat()
        template['updated_at'] = datetime.now().isoformat()
        
        # Save the template to disk
        template_filename = f"{new_template_id}.yml"
        template_path = os.path.join(self.templates_dir, template_filename)
        
        try:
            with open(template_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False)
                
            # Add to templates dictionary
            self.templates[new_template_id] = {
                'template': template,
                'path': template_path,
                'type': 'local'
            }
            
            return {
                'success': True,
                'message': f'Successfully cloned template to {template["template_name"]}',
                'template_id': new_template_id,
                'template': template
            }
        except Exception as e:
            logger.error(f"Error cloning template: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to clone template: {str(e)}'
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
    
    def generate_template_from_description(self, template_name: str, description: str) -> Dict:
        """Generate a service template from a natural language description.
        
        Args:
            template_name: Name for the new template
            description: Natural language description of the service
            
        Returns:
            Template creation result dictionary
        """
        # Create a template ID
        template_id = f"template_{str(uuid.uuid4())[:8]}"
        
        # Start with a basic template structure
        template = {
            'template_id': template_id,
            'template_name': template_name,
            'created_at': datetime.now().isoformat(),
            'description': description,
            'generated': True,
            'dependencies': [],
            'deployment': {
                'method': 'docker',
                'image': '',
                'ports': [],
                'environment': {},
                'volumes': []
            }
        }
        
        # Extract information from description
        # This is a simple implementation - in a real system, this would use NLP
        # to extract more detailed information from the description
        
        # Check for docker image
        if 'docker' in description.lower():
            # Look for image name patterns
            import re
            image_match = re.search(r'(docker\s+image|image)[\s:]+([a-zA-Z0-9_\-./]+:[a-zA-Z0-9_\-.]+|[a-zA-Z0-9_\-./]+)', description.lower())
            if image_match:
                template['deployment']['image'] = image_match.group(2)
                
        # Check for ports
        port_matches = re.findall(r'port\s+(\d+)', description.lower())
        for port in port_matches:
            template['deployment']['ports'].append({
                'container': int(port),
                'host': int(port)
            })
            
        # Check for environment variables
        env_matches = re.findall(r'(environment|env)[\s:]+([A-Z_][A-Z0-9_]*)[\s:=]+([^\s,]+)', description)
        for _, key, value in env_matches:
            template['deployment']['environment'][key] = value
            
        # Check for volumes
        volume_matches = re.findall(r'volume[\s:]+([^\s,]+):([^\s,]+)', description)
        for host_path, container_path in volume_matches:
            template['deployment']['volumes'].append({
                'host': host_path,
                'container': container_path
            })
            
        # Check for dependencies
        dep_matches = re.findall(r'depends\s+on\s+([a-zA-Z0-9_\-]+)', description.lower())
        for dep in dep_matches:
            template['dependencies'].append(dep)
            
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
                "message": f"Successfully created template '{template_name}' from description",
                "template_id": template_id,
                "template": template
            }
        except Exception as e:
            logger.error(f"Error creating template from description: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to create template: {str(e)}"
            }
    
    def get_template_recommendations(self, requirements: str) -> Dict:
        """Get template recommendations based on natural language requirements.
        
        Args:
            requirements: Natural language description of requirements
            
        Returns:
            Dictionary with recommended templates
        """
        # Get all available templates
        all_templates = self.get_all_templates()
        
        # Simple keyword matching for recommendations
        # In a real system, this would use more sophisticated NLP techniques
        keywords = requirements.lower().split()
        
        # Score templates based on keyword matches
        scored_templates = []
        for template in all_templates:
            score = 0
            
            # Check template name
            template_name = template.get('template_name', '').lower()
            for keyword in keywords:
                if keyword in template_name:
                    score += 3
            
            # Check template description
            description = template.get('description', '').lower()
            for keyword in keywords:
                if keyword in description:
                    score += 2
            
            # Check deployment details
            deployment = template.get('deployment', {})
            image = deployment.get('image', '').lower()
            for keyword in keywords:
                if keyword in image:
                    score += 1
            
            # Add to scored templates if there's any match
            if score > 0:
                scored_templates.append({
                    'template': template,
                    'score': score
                })
        
        # Sort templates by score
        scored_templates.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top recommendations
        recommendations = [item['template'] for item in scored_templates[:5]]
        
        return {
            "success": True,
            "recommendations": recommendations,
            "requirements": requirements,
            "total_matches": len(scored_templates)
        }
    
    def generate_template_comparison(self, template_ids: List[str]) -> Dict:
        """Generate a comparison between multiple templates.
        
        Args:
            template_ids: List of template IDs to compare
            
        Returns:
            Dictionary with comparison data
        """
        if not template_ids or len(template_ids) < 2:
            return {
                "success": False,
                "message": "At least two template IDs are required for comparison"
            }
            
        # Get templates
        templates = []
        for template_id in template_ids:
            template = self.get_template(template_id)
            if not template:
                return {
                    "success": False,
                    "message": f"Template with ID '{template_id}' not found"
                }
            templates.append(template)
            
        # Generate comparison
        comparison = {
            "templates": templates,
            "comparison_points": {}
        }
        
        # Compare basic properties
        comparison["comparison_points"]["basic"] = {
            "name": "Basic Information",
            "properties": [
                {
                    "name": "Template Name",
                    "values": [t.get('template_name', 'Unnamed') for t in templates]
                },
                {
                    "name": "Created At",
                    "values": [t.get('created_at', 'Unknown') for t in templates]
                },
                {
                    "name": "Description",
                    "values": [t.get('description', 'No description') for t in templates]
                }
            ]
        }
        
        # Compare deployment methods
        comparison["comparison_points"]["deployment"] = {
            "name": "Deployment",
            "properties": [
                {
                    "name": "Method",
                    "values": [t.get('deployment', {}).get('method', 'Unknown') for t in templates]
                },
                {
                    "name": "Docker Image",
                    "values": [t.get('deployment', {}).get('image', 'N/A') for t in templates]
                },
                {
                    "name": "Port Mappings",
                    "values": [
                        ", ".join([f"{p.get('container')}:{p.get('host')}" 
                                for p in t.get('deployment', {}).get('ports', [])]) or "None"
                        for t in templates
                    ]
                },
                {
                    "name": "Environment Variables",
                    "values": [
                        ", ".join([f"{k}={v}" 
                                for k, v in t.get('deployment', {}).get('environment', {}).items()]) or "None"
                        for t in templates
                    ]
                },
                {
                    "name": "Volumes",
                    "values": [
                        ", ".join([f"{v.get('host')}:{v.get('container')}" 
                                for v in t.get('deployment', {}).get('volumes', [])]) or "None"
                        for t in templates
                    ]
                }
            ]
        }
        
        # Compare dependencies
        comparison["comparison_points"]["dependencies"] = {
            "name": "Dependencies",
            "properties": [
                {
                    "name": "Dependencies",
                    "values": [
                        ", ".join(t.get('dependencies', [])) or "None"
                        for t in templates
                    ]
                },
                {
                    "name": "Dependency Count",
                    "values": [len(t.get('dependencies', [])) for t in templates]
                }
            ]
        }
        
        # Generate natural language summary
        summary = f"Comparison of {len(templates)} templates:\n\n"
        
        # Add template names
        for i, template in enumerate(templates):
            summary += f"Template {i+1}: {template.get('template_name', 'Unnamed')}\n"
        
        summary += "\n## Key Differences\n\n"
        
        # Find key differences
        differences = []
        
        # Check deployment method
        methods = [t.get('deployment', {}).get('method', 'Unknown') for t in templates]
        if len(set(methods)) > 1:
            differences.append(f"Deployment methods differ: {', '.join(methods)}")
            
        # Check Docker images
        images = [t.get('deployment', {}).get('image', 'N/A') for t in templates]
        if len(set(images)) > 1:
            differences.append(f"Docker images differ: {', '.join(images)}")
            
        # Check port counts
        port_counts = [len(t.get('deployment', {}).get('ports', [])) for t in templates]
        if len(set(port_counts)) > 1:
            differences.append(f"Number of exposed ports differ: {', '.join(map(str, port_counts))}")
            
        # Check dependency counts
        dep_counts = [len(t.get('dependencies', [])) for t in templates]
        if len(set(dep_counts)) > 1:
            differences.append(f"Number of dependencies differ: {', '.join(map(str, dep_counts))}")
            
        # Add differences to summary
        if differences:
            for diff in differences:
                summary += f"- {diff}\n"
        else:
            summary += "These templates are very similar in their core configuration.\n"
            
        # Add recommendation
        summary += "\n## Recommendation\n\n"
        
        # Simple recommendation based on dependencies and configuration
        if differences:
            # Find the template with the most complete configuration
            scores = []
            for i, template in enumerate(templates):
                score = 0
                # More dependencies might mean more complete
                score += len(template.get('dependencies', []))
                # More environment variables might mean more configurable
                score += len(template.get('deployment', {}).get('environment', {}))
                # More volumes might mean more data persistence
                score += len(template.get('deployment', {}).get('volumes', []))
                scores.append((i, score))
                
            # Get highest scoring template
            best_template_idx, _ = max(scores, key=lambda x: x[1])
            best_template = templates[best_template_idx]
            
            summary += f"Template '{best_template.get('template_name', 'Unnamed')}' appears to have the most complete configuration.\n"
            summary += "However, you should review the specific differences to ensure it meets your requirements.\n"
        else:
            # If templates are very similar, recommend the most recently created one
            created_times = []
            for i, template in enumerate(templates):
                try:
                    created_at = datetime.fromisoformat(template.get('created_at', '2000-01-01'))
                    created_times.append((i, created_at))
                except (ValueError, TypeError):
                    created_times.append((i, datetime.min))
                    
            # Get most recent template
            most_recent_idx, _ = max(created_times, key=lambda x: x[1])
            most_recent = templates[most_recent_idx]
            
            summary += f"Since these templates are very similar, the most recently created one ('{most_recent.get('template_name', 'Unnamed')}') is recommended.\n"
        
        comparison["summary"] = summary
        
        return {
            "success": True,
            "comparison": comparison
        }
    
    def get_template_natural_language_description(self, template_id: str) -> Dict:
        """Get a natural language description of a template.
        
        Args:
            template_id: ID of the template to describe
            
        Returns:
            Dictionary with template description
        """
        template = self.get_template(template_id)
        if not template:
            return {
                "success": False,
                "message": f"Template with ID '{template_id}' not found"
            }
            
        # Generate natural language description
        template_name = template.get('template_name', 'Unnamed template')
        description = f"# {template_name}\n\n"
        
        # Add basic information
        description += "## Basic Information\n\n"
        description += f"- **Template ID**: {template_id}\n"
        if 'created_at' in template:
            description += f"- **Created**: {template['created_at']}\n"
        if 'description' in template and template['description']:
            description += f"- **Description**: {template['description']}\n"
        if 'created_from' in template:
            description += f"- **Created from service**: {template['created_from']}\n"
            
        # Add deployment information
        description += "\n## Deployment Configuration\n\n"
        
        deployment = template.get('deployment', {})
        method = deployment.get('method', 'Unknown')
        description += f"- **Deployment method**: {method}\n"
        
        if method == 'docker':
            image = deployment.get('image', 'Not specified')
            description += f"- **Docker image**: {image}\n"
            
            # Add ports
            ports = deployment.get('ports', [])
            if ports:
                description += "- **Port mappings**:\n"
                for port in ports:
                    container_port = port.get('container', 'Unknown')
                    host_port = port.get('host', 'Unknown')
                    description += f"  - Container port {container_port} -> Host port {host_port}\n"
            else:
                description += "- **Port mappings**: None\n"
                
            # Add environment variables
            env_vars = deployment.get('environment', {})
            if env_vars:
                description += "- **Environment variables**:\n"
                for key, value in env_vars.items():
                    description += f"  - {key}={value}\n"
            else:
                description += "- **Environment variables**: None\n"
                
            # Add volumes
            volumes = deployment.get('volumes', [])
            if volumes:
                description += "- **Volumes**:\n"
                for volume in volumes:
                    host_path = volume.get('host', 'Unknown')
                    container_path = volume.get('container', 'Unknown')
                    description += f"  - Host path {host_path} -> Container path {container_path}\n"
            else:
                description += "- **Volumes**: None\n"
                
        elif method == 'script':
            # Add script details
            script = deployment.get('script', 'Not specified')
            description += f"- **Deployment script**: {script}\n"
            
            # Add script arguments
            args = deployment.get('arguments', [])
            if args:
                description += "- **Script arguments**:\n"
                for arg in args:
                    description += f"  - {arg}\n"
            else:
                description += "- **Script arguments**: None\n"
                
        # Add dependencies
        dependencies = template.get('dependencies', [])
        if dependencies:
            description += "\n## Dependencies\n\n"
            description += f"This template depends on {len(dependencies)} other service{'s' if len(dependencies) > 1 else ''}:\n\n"
            for dep in dependencies:
                description += f"- {dep}\n"
        else:
            description += "\n## Dependencies\n\n"
            description += "This template does not depend on any other services.\n"
            
        # Add usage instructions
        description += "\n## Usage Instructions\n\n"
        
        if method == 'docker':
            description += "To deploy this template:\n\n"
            description += "1. Ensure Docker is installed on the target system\n"
            description += "2. Pull the Docker image if needed\n"
            description += f"3. Deploy the service using this template ID: `{template_id}`\n"
            
            # Add specific configuration notes
            if deployment.get('environment', {}):
                description += "4. Make sure to configure the required environment variables\n"
            if deployment.get('volumes', []):
                description += "5. Ensure the volume mount points exist on the host system\n"
                
        elif method == 'script':
            description += "To deploy this template:\n\n"
            description += "1. Ensure the target system meets all prerequisites\n"
            description += "2. Make sure the deployment script is executable\n"
            description += f"3. Deploy the service using this template ID: `{template_id}`\n"
            
        # Add customization notes
        description += "\n## Customization\n\n"
        description += "This template can be customized by modifying the following:\n\n"
        
        if method == 'docker':
            description += "- Environment variables to configure the application\n"
            description += "- Port mappings to change how the service is accessed\n"
            description += "- Volume mounts to persist data or provide configuration files\n"
        elif method == 'script':
            description += "- Script arguments to modify deployment behavior\n"
            description += "- Dependencies to ensure required services are available\n"
            
        return {
            "success": True,
            "template_id": template_id,
            "template_name": template_name,
            "description": description
        }