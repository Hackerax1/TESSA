#!/usr/bin/env python3
"""
Goal Mapper Service for TESSA
Maps user goals to recommended services and provides explanations
"""

import os
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class GoalMapper:
    """Maps user goals to recommended services"""
    
    def __init__(self, catalog_dir=None):
        """Initialize the goal mapper with the service catalog directory"""
        if catalog_dir is None:
            # Default to the catalog directory in the same package
            catalog_dir = os.path.join(os.path.dirname(__file__), 'catalog')
        
        self.catalog_dir = catalog_dir
        self.services = {}
        self.load_services()
        
        # Define services to exclude from recommendations
        self.excluded_services = ['portainer']
        
        # Define goal to service mappings with more detailed descriptions
        self.goal_mappings = {
            'media': {
                'name': 'Media Server',
                'description': 'A media server lets you store and stream your movies, TV shows, and music.',
                'persona_description': 'Enjoy your media collection from anywhere, on any device. No more subscriptions!'
            },
            'files': {
                'name': 'File Storage & Sync',
                'description': 'File storage solutions let you back up, sync, and access your files from anywhere.',
                'persona_description': 'Keep your important files safe, accessible, and under your control.'
            },
            'photos': {
                'name': 'Photo Management',
                'description': 'Photo management tools help you organize, back up, and enjoy your photo collection.',
                'persona_description': 'Preserve your memories in a beautiful, searchable library you control completely.'
            },
            'documents': {
                'name': 'Document Management',
                'description': 'Document management systems help you organize and search your important papers.',
                'persona_description': 'Say goodbye to paper clutter and never lose an important document again!'
            },
            'webhosting': {
                'name': 'Web Hosting',
                'description': 'Web hosting tools let you run your own websites and web applications.',
                'persona_description': 'Host your own websites and web apps with complete creative freedom.'
            },
            'homeauto': {
                'name': 'Home Automation',
                'description': 'Home automation tools let you control and automate your smart home devices.',
                'persona_description': 'Make your home smarter and more responsive to your needs and preferences.'
            },
            'productivity': {
                'name': 'Productivity Tools',
                'description': 'Productivity tools help you organize your work, collaborate, and manage passwords.',
                'persona_description': 'Boost your efficiency with tools designed to help you get more done.'
            },
            'gaming': {
                'name': 'Gaming',
                'description': 'Gaming servers let you host multiplayer games for you and your friends.',
                'persona_description': 'Create your own gaming community with servers you control completely.'
            },
            'privacy': {
                'name': 'Privacy & Security',
                'description': 'Privacy tools help protect your data and block unwanted tracking and ads.',
                'persona_description': 'Take back control of your digital privacy and secure your online presence.'
            },
            'networking': {
                'name': 'Networking',
                'description': 'Networking tools give you control over your home network and internet connection.',
                'persona_description': 'Optimize your home network for better performance, security, and control.'
            },
            'cooking': {
                'name': 'Cooking & Recipes',
                'description': 'Recipe management tools help you organize recipes and plan meals.',
                'persona_description': 'Keep your favorite recipes organized and make meal planning a breeze!'
            }
        }
        
        # Define cloud service replacements with more detailed descriptions
        self.cloud_replacements = {
            'google_photos': {
                'name': 'Google Photos',
                'description': 'Replace Google Photos with your own photo storage and sharing solution.',
                'persona_description': 'Keep your precious memories private and under your control, not Google\'s.'
            },
            'google_drive': {
                'name': 'Google Drive',
                'description': 'Replace Google Drive with your own file storage and sharing solution.',
                'persona_description': 'Access your files from anywhere without giving Google access to your data.'
            },
            'dropbox': {
                'name': 'Dropbox',
                'description': 'Replace Dropbox with your own file storage and sharing solution.',
                'persona_description': 'All the convenience of Dropbox without the subscription fees or privacy concerns.'
            },
            'netflix': {
                'name': 'Netflix',
                'description': 'Replace Netflix with your own media server for movies and TV shows.',
                'persona_description': 'Build your own streaming service with content you choose, no subscriptions needed.'
            },
            'spotify': {
                'name': 'Spotify',
                'description': 'Replace Spotify with your own music streaming server.',
                'persona_description': 'Stream your music collection from anywhere without monthly fees.'
            },
            'lastpass': {
                'name': 'LastPass',
                'description': 'Replace LastPass with your own password manager.',
                'persona_description': 'Keep your passwords secure and accessible without trusting a third-party service.'
            },
            'github': {
                'name': 'GitHub',
                'description': 'Replace GitHub with your own Git repository hosting.',
                'persona_description': 'Host your code repositories with complete control over access and features.'
            },
            'google_calendar': {
                'name': 'Google Calendar',
                'description': 'Replace Google Calendar with your own calendar server.',
                'persona_description': 'Manage your schedule privately without sharing your appointments with Google.'
            },
            'google_docs': {
                'name': 'Google Docs',
                'description': 'Replace Google Docs with your own document collaboration tools.',
                'persona_description': 'Collaborate on documents without giving Google access to your content.'
            },
            'evernote': {
                'name': 'Evernote',
                'description': 'Replace Evernote with your own note-taking and document management system.',
                'persona_description': 'Keep your notes organized and searchable without subscription fees.'
            },
            'recipe_apps': {
                'name': 'Recipe Apps',
                'description': 'Replace commercial recipe apps with your own recipe management system.',
                'persona_description': 'Organize your recipes your way without ads or subscription fees.'
            }
        }
    
    def load_services(self):
        """Load all services from the catalog directory"""
        try:
            catalog_path = Path(self.catalog_dir)
            for file_path in catalog_path.glob('*.yml'):
                try:
                    with open(file_path, 'r') as f:
                        service_data = yaml.safe_load(f)
                        service_id = service_data.get('id', os.path.splitext(os.path.basename(file_path))[0])
                        self.services[service_id] = service_data
                except Exception as e:
                    logger.error(f"Error loading service {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error accessing catalog directory: {str(e)}")
    
    def get_service_by_id(self, service_id):
        """Get service details by ID"""
        return self.services.get(service_id)
        
    def is_foss_service(self, service):
        """
        Determine if a service is FOSS (Free and Open Source Software)
        
        Args:
            service (dict): Service definition dictionary
            
        Returns:
            bool: True if service is FOSS, False otherwise
        """
        # Check if service has an explicit license_type field
        if 'license_type' in service:
            license_type = service['license_type'].lower()
            return 'foss' in license_type or 'open source' in license_type or 'free' in license_type
        
        # Check keywords for indicators of FOSS
        if 'keywords' in service:
            keywords = [k.lower() for k in service.get('keywords', [])]
            if any(k in keywords for k in ['open source', 'foss', 'free software']):
                return True
                
        # Default most services in our catalog to be FOSS unless explicitly marked
        return service.get('is_foss', True)
    
    def is_excluded_service(self, service_id):
        """
        Check if a service should be excluded from recommendations
        
        Args:
            service_id (str): Service ID to check
            
        Returns:
            bool: True if service should be excluded, False otherwise
        """
        return service_id.lower() in self.excluded_services
    
    def get_recommended_services(self, goals, include_personality=True):
        """
        Get recommended services based on user goals
        
        Args:
            goals (list): List of goal IDs selected by the user
            include_personality (bool): Whether to include personality-driven recommendations
            
        Returns:
            dict: Dictionary with recommended services and explanations
        """
        recommended = {}
        
        # First, get services directly from the service catalog by goal
        for goal in goals:
            if goal in self.goal_mappings:
                goal_info = self.goal_mappings[goal]
                
                # Collect all matching services for this goal to prioritize FOSS options
                matching_services = []
                
                # Get services that match this goal from their user_goals attribute
                for service_id, service in self.services.items():
                    # Skip excluded services
                    if self.is_excluded_service(service_id):
                        continue
                        
                    if 'user_goals' in service:
                        for service_goal in service.get('user_goals', []):
                            if service_goal['id'] == goal and service_id not in recommended:
                                # Add service to matching services with its information
                                matching_services.append({
                                    'id': service_id,
                                    'service': service,
                                    'relevance': service_goal.get('relevance', 'medium'),
                                    'reason': service_goal.get('reason', ''),
                                    'is_foss': self.is_foss_service(service)
                                })
                                break
                
                # Sort by FOSS status first (FOSS first), then by relevance
                sorted_services = sorted(
                    matching_services,
                    key=lambda s: (not s['is_foss'], self._get_relevance_order(s['relevance']))
                )
                
                # Add sorted services to recommendations
                for match in sorted_services:
                    service_id = match['id']
                    if service_id not in recommended:
                        recommended[service_id] = self._create_recommendation(
                            match['service'], 
                            goal, 
                            goal_info,
                            match['relevance'],
                            match['reason'],
                            include_personality
                        )
                        # Add FOSS status to the recommendation
                        recommended[service_id]['is_foss'] = match['is_foss']
        
        # Sort recommendations by FOSS status first, then by relevance
        sorted_recommendations = {}
        for service_id, rec in sorted(
            recommended.items(), 
            key=lambda item: (not item[1].get('is_foss', True), self._get_relevance_order(item[1].get('relevance', 'medium')))
        ):
            sorted_recommendations[service_id] = rec
            
        return sorted_recommendations
    
    def _get_relevance_order(self, relevance):
        """Helper method to get numeric order for relevance values"""
        relevance_order = {'high': 0, 'medium': 1, 'low': 2}
        return relevance_order.get(relevance, 3)
        
    def _get_quality_order(self, quality):
        """Helper method to get numeric order for quality values"""
        quality_order = {'excellent': 0, 'good': 1, 'fair': 2, 'poor': 3}
        return quality_order.get(quality, 4)
    
    def _create_recommendation(self, service, goal_id, goal_info, relevance, reason, include_personality):
        """Create a recommendation object with personality if available"""
        recommendation = {
            'id': service.get('id'),
            'name': service.get('name', service.get('id')),
            'description': service.get('description', ''),
            'goal': goal_id,
            'goal_name': goal_info.get('name', goal_id),
            'goal_description': goal_info.get('description', ''),
            'relevance': relevance,
            'reason': reason,
            'vm_requirements': service.get('vm_requirements', {}),
            'is_foss': self.is_foss_service(service)
        }
        
        # Add personality-driven recommendation if available and requested
        if include_personality and 'personality_recommendation' in service:
            recommendation['personality_recommendation'] = service.get('personality_recommendation')
        elif include_personality:
            # Generate a generic personality recommendation based on goal
            foss_note = " It's completely open-source too!" if recommendation['is_foss'] else ""
            recommendation['personality_recommendation'] = (
                f"I think you'd really enjoy {service.get('name')} for your "
                f"{goal_info.get('name', goal_id).lower()} needs! "
                f"{reason if reason else goal_info.get('persona_description', '')}"
                f"{foss_note}"
            )
            
        # Add dependency information
        if 'dependencies' in service:
            recommendation['dependencies'] = service.get('dependencies', [])
            
        return recommendation
    
    def get_cloud_replacement_services(self, service_names, include_personality=True):
        """
        Get recommended services to replace specific cloud services
        
        Args:
            service_names (list): List of cloud service IDs to replace
            include_personality (bool): Whether to include personality-driven recommendations
            
        Returns:
            dict: Dictionary with recommended services and explanations
        """
        recommended = {}
        
        # Get services that can replace the requested cloud services
        for cloud_service_id in service_names:
            if cloud_service_id in self.cloud_replacements:
                cloud_info = self.cloud_replacements[cloud_service_id]
                
                # Collect all matching services for this cloud service to prioritize FOSS options
                matching_services = []
                
                # Find services that list this cloud service in their replaces_services
                for service_id, service in self.services.items():
                    # Skip excluded services
                    if self.is_excluded_service(service_id):
                        continue
                        
                    if 'replaces_services' in service:
                        for replacement in service.get('replaces_services', []):
                            if replacement['id'] == cloud_service_id and service_id not in recommended:
                                # Add service to matching services with its information
                                matching_services.append({
                                    'id': service_id,
                                    'service': service,
                                    'quality': replacement.get('quality', 'good'),
                                    'reason': replacement.get('reason', ''),
                                    'is_foss': self.is_foss_service(service)
                                })
                                break
                
                # Sort by FOSS status first (FOSS first), then by quality
                sorted_services = sorted(
                    matching_services,
                    key=lambda s: (not s['is_foss'], self._get_quality_order(s['quality']))
                )
                
                # Add sorted services to recommendations
                for match in sorted_services:
                    service_id = match['id']
                    if service_id not in recommended:
                        recommended[service_id] = self._create_replacement_recommendation(
                            match['service'],
                            cloud_service_id,
                            cloud_info,
                            match['quality'],
                            match['reason'],
                            include_personality
                        )
                        # Add FOSS status to the recommendation
                        recommended[service_id]['is_foss'] = match['is_foss']
        
        # Sort recommendations by FOSS status first, then by quality
        sorted_recommendations = {}
        for service_id, rec in sorted(
            recommended.items(), 
            key=lambda item: (not item[1].get('is_foss', True), self._get_quality_order(item[1].get('quality', 'good')))
        ):
            sorted_recommendations[service_id] = rec
            
        return sorted_recommendations
    
    def _create_replacement_recommendation(self, service, cloud_id, cloud_info, quality, reason, include_personality):
        """Create a replacement recommendation object with personality if available"""
        recommendation = {
            'id': service.get('id'),
            'name': service.get('name', service.get('id')),
            'description': service.get('description', ''),
            'replaces': cloud_id,
            'replaces_name': cloud_info.get('name', cloud_id),
            'replacement_description': cloud_info.get('description', ''),
            'quality': quality,
            'reason': reason,
            'vm_requirements': service.get('vm_requirements', {}),
            'is_foss': self.is_foss_service(service)
        }
        
        # Add personality-driven recommendation if available and requested
        if include_personality and 'personality_recommendation' in service:
            recommendation['personality_recommendation'] = service.get('personality_recommendation')
        elif include_personality:
            # Generate a generic personality recommendation based on cloud service
            foss_note = " As a bonus, it's completely open-source!" if recommendation['is_foss'] else ""
            recommendation['personality_recommendation'] = (
                f"I think you'd really love {service.get('name')} as a replacement for "
                f"{cloud_info.get('name', cloud_id)}! "
                f"{reason if reason else cloud_info.get('persona_description', '')}"
                f"{foss_note}"
            )
            
        # Add dependency information
        if 'dependencies' in service:
            recommendation['dependencies'] = service.get('dependencies', [])
            
        return recommendation
    
    def estimate_resource_requirements(self, service_ids):
        """
        Estimate total resource requirements for a set of services
        
        Args:
            service_ids (list): List of service IDs
            
        Returns:
            dict: Dictionary with total resource requirements
        """
        total_resources = {
            'cores': 0,
            'memory': 0,
            'disk': 0
        }
        
        for service_id in service_ids:
            service = self.get_service_by_id(service_id)
            if service and 'vm_requirements' in service:
                requirements = service['vm_requirements']
                total_resources['cores'] += requirements.get('cores', 0)
                total_resources['memory'] += requirements.get('memory', 0)
                total_resources['disk'] += requirements.get('disk', 0)
        
        return total_resources
    
    def get_service_dependencies(self, service_id):
        """
        Get all dependencies for a specific service
        
        Args:
            service_id (str): Service ID to get dependencies for
            
        Returns:
            list: List of dependency dictionaries
        """
        service = self.get_service_by_id(service_id)
        if not service or 'dependencies' not in service:
            return []
            
        dependencies = []
        for dep in service.get('dependencies', []):
            dep_service = self.get_service_by_id(dep['id'])
            if dep_service:
                dependencies.append({
                    'id': dep['id'],
                    'name': dep_service.get('name', dep['id']),
                    'required': dep['required'],
                    'description': dep.get('description', ''),
                    'service': dep_service
                })
            else:
                # Dependency service not found in catalog
                dependencies.append({
                    'id': dep['id'],
                    'name': dep['id'],
                    'required': dep['required'],
                    'description': dep.get('description', ''),
                    'service': None
                })
                
        return dependencies
    
    def get_all_required_dependencies(self, service_id, processed_services=None):
        """
        Get all required dependencies for a service, including transitive dependencies
        
        Args:
            service_id (str): Service ID to get dependencies for
            processed_services (list): List of already processed service IDs (to prevent cycles)
            
        Returns:
            list: List of dependency dictionaries
        """
        if processed_services is None:
            processed_services = []
            
        if service_id in processed_services:
            return []  # Prevent circular dependencies
            
        processed_services.append(service_id)
        
        direct_deps = self.get_service_dependencies(service_id)
        all_deps = []
        
        for dep in direct_deps:
            if dep['required'] and dep['id'] not in [d['id'] for d in all_deps]:
                all_deps.append(dep)
                
                # Get transitive dependencies
                if dep['service']:
                    transitive_deps = self.get_all_required_dependencies(
                        dep['id'], processed_services.copy()
                    )
                    
                    # Add only new dependencies
                    for trans_dep in transitive_deps:
                        if trans_dep['id'] not in [d['id'] for d in all_deps]:
                            all_deps.append(trans_dep)
                            
        return all_deps
    
    def get_all_goals(self):
        """
        Get all defined user goals
        
        Returns:
            dict: Dictionary of all goals with their descriptions
        """
        return {goal_id: {
            'id': goal_id,
            'name': info.get('name', goal_id),
            'description': info.get('description', ''),
            'persona_description': info.get('persona_description', '')
        } for goal_id, info in self.goal_mappings.items()}
    
    def get_all_cloud_services(self):
        """
        Get all defined cloud services that can be replaced
        
        Returns:
            dict: Dictionary of all cloud services with their descriptions
        """
        return {service_id: {
            'id': service_id,
            'name': info.get('name', service_id),
            'description': info.get('description', ''),
            'persona_description': info.get('persona_description', '')
        } for service_id, info in self.cloud_replacements.items()}
