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
        
        # Define goal to service mappings
        self.goal_mappings = {
            'media': {
                'services': ['jellyfin', 'arr-stack'],
                'description': 'A media server lets you store and stream your movies, TV shows, and music.'
            },
            'files': {
                'services': ['nextcloud', 'syncthing', 'truenas'],
                'description': 'File storage solutions let you back up, sync, and access your files from anywhere.'
            },
            'webhosting': {
                'services': ['nginx', 'gitea', 'cloudflared'],
                'description': 'Web hosting tools let you run your own websites and web applications.'
            },
            'homeauto': {
                'services': ['home-assistant-docker', 'home-assistant-os'],
                'description': 'Home automation tools let you control and automate your smart home devices.'
            },
            'productivity': {
                'services': ['nextcloud', 'gitea', 'bitwarden'],
                'description': 'Productivity tools help you organize your work, collaborate, and manage passwords.'
            },
            'gaming': {
                'services': ['arr-stack'],
                'description': 'Gaming servers let you host multiplayer games for you and your friends.'
            },
            'privacy': {
                'services': ['pihole', 'vpn-service', 'bitwarden'],
                'description': 'Privacy tools help protect your data and block unwanted tracking and ads.'
            },
            'networking': {
                'services': ['pfsense', 'pihole', 'cloudflared'],
                'description': 'Networking tools give you control over your home network and internet connection.'
            }
        }
        
        # Define cloud service replacements
        self.cloud_replacements = {
            'google_photos': {
                'services': ['nextcloud', 'syncthing'],
                'description': 'Replace Google Photos with your own photo storage and sharing solution.'
            },
            'google_drive': {
                'services': ['nextcloud', 'syncthing'],
                'description': 'Replace Google Drive with your own file storage and sharing solution.'
            },
            'dropbox': {
                'services': ['nextcloud', 'syncthing'],
                'description': 'Replace Dropbox with your own file storage and sharing solution.'
            },
            'netflix': {
                'services': ['jellyfin', 'arr-stack'],
                'description': 'Replace Netflix with your own media server for movies and TV shows.'
            },
            'spotify': {
                'services': ['jellyfin'],
                'description': 'Replace Spotify with your own music streaming server.'
            },
            'lastpass': {
                'services': ['bitwarden'],
                'description': 'Replace LastPass with your own password manager.'
            },
            'github': {
                'services': ['gitea'],
                'description': 'Replace GitHub with your own Git repository hosting.'
            },
            'google_calendar': {
                'services': ['nextcloud'],
                'description': 'Replace Google Calendar with your own calendar server.'
            },
            'google_docs': {
                'services': ['nextcloud'],
                'description': 'Replace Google Docs with your own document collaboration tools.'
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
                        service_id = os.path.splitext(os.path.basename(file_path))[0]
                        self.services[service_id] = service_data
                except Exception as e:
                    logger.error(f"Error loading service {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error accessing catalog directory: {str(e)}")
    
    def get_service_by_id(self, service_id):
        """Get service details by ID"""
        return self.services.get(service_id)
    
    def get_recommended_services(self, goals):
        """
        Get recommended services based on user goals
        
        Args:
            goals (list): List of goal IDs selected by the user
            
        Returns:
            dict: Dictionary with recommended services and explanations
        """
        recommended = {}
        
        for goal in goals:
            if goal in self.goal_mappings:
                goal_info = self.goal_mappings[goal]
                for service_id in goal_info['services']:
                    service = self.get_service_by_id(service_id)
                    if service and service_id not in recommended:
                        recommended[service_id] = {
                            'name': service.get('name', service_id),
                            'description': service.get('description', ''),
                            'goal': goal,
                            'goal_description': goal_info['description'],
                            'resources': service.get('resources', {})
                        }
        
        return recommended
    
    def get_cloud_replacement_services(self, service_names):
        """
        Get recommended services to replace specific cloud services
        
        Args:
            service_names (list): List of cloud service IDs to replace
            
        Returns:
            dict: Dictionary with recommended services and explanations
        """
        recommended = {}
        
        for service_name in service_names:
            if service_name in self.cloud_replacements:
                replacement_info = self.cloud_replacements[service_name]
                for service_id in replacement_info['services']:
                    service = self.get_service_by_id(service_id)
                    if service and service_id not in recommended:
                        recommended[service_id] = {
                            'name': service.get('name', service_id),
                            'description': service.get('description', ''),
                            'replaces': service_name,
                            'replacement_description': replacement_info['description'],
                            'resources': service.get('resources', {})
                        }
        
        return recommended
    
    def estimate_resource_requirements(self, service_ids):
        """
        Estimate total resource requirements for a set of services
        
        Args:
            service_ids (list): List of service IDs
            
        Returns:
            dict: Dictionary with total resource requirements
        """
        total_resources = {
            'cpu_cores': 0,
            'memory_mb': 0,
            'storage_gb': 0
        }
        
        for service_id in service_ids:
            service = self.get_service_by_id(service_id)
            if service and 'resources' in service:
                resources = service['resources']
                total_resources['cpu_cores'] += resources.get('cpu_cores', 0)
                total_resources['memory_mb'] += resources.get('memory_mb', 0)
                total_resources['storage_gb'] += resources.get('storage_gb', 0)
        
        return total_resources
