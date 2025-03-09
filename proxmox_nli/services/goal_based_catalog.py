#!/usr/bin/env python3
"""
Goal-Based Service Catalog for TESSA
Organizes services by user goals rather than technical categories
"""

import os
import logging
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class GoalBasedCatalog:
    """
    Organizes services by user goals instead of technical categories.
    Provides interfaces for browsing and discovering services based on what
    the user wants to accomplish rather than technical implementation details.
    """
    
    def __init__(self, service_catalog=None, goal_mapper=None):
        """
        Initialize the goal-based catalog with a service catalog and goal mapper
        
        Args:
            service_catalog: The technical service catalog instance
            goal_mapper: The goal mapper instance that defines user goals
        """
        self.service_catalog = service_catalog
        self.goal_mapper = goal_mapper
        self.goal_index = defaultdict(list)
        self.cloud_replacement_index = defaultdict(list)
        
        if service_catalog:
            self.build_indexes()
    
    def build_indexes(self):
        """Build indexes for quick goal-based and replacement-based lookups"""
        if not self.service_catalog:
            logger.error("No service catalog provided to goal-based catalog")
            return
            
        self.goal_index.clear()
        self.cloud_replacement_index.clear()
        
        # Get all services
        services = self.service_catalog.get_all_services()
        
        # Index by goals
        for service in services:
            service_id = service['id']
            
            # Add to goal index
            if 'user_goals' in service:
                for goal in service.get('user_goals', []):
                    goal_id = goal['id']
                    self.goal_index[goal_id].append({
                        'id': service_id,
                        'service': service,
                        'relevance': goal.get('relevance', 'medium'),
                        'reason': goal.get('reason', '')
                    })
            
            # Add to cloud replacement index
            if 'replaces_services' in service:
                for replacement in service.get('replaces_services', []):
                    cloud_id = replacement['id']
                    self.cloud_replacement_index[cloud_id].append({
                        'id': service_id,
                        'service': service,
                        'quality': replacement.get('quality', 'good'),
                        'reason': replacement.get('reason', '')
                    })
        
        # Sort the indexes by relevance and quality
        for goal_id, services in self.goal_index.items():
            relevance_order = {'high': 0, 'medium': 1, 'low': 2}
            self.goal_index[goal_id] = sorted(
                services, 
                key=lambda s: relevance_order.get(s.get('relevance', 'medium'), 3)
            )
            
        for cloud_id, services in self.cloud_replacement_index.items():
            quality_order = {'excellent': 0, 'good': 1, 'fair': 2, 'poor': 3}
            self.cloud_replacement_index[cloud_id] = sorted(
                services, 
                key=lambda s: quality_order.get(s.get('quality', 'good'), 4)
            )
            
        logger.info(f"Built goal indexes for {len(self.goal_index)} goals and {len(self.cloud_replacement_index)} cloud services")
    
    def get_goals_with_services(self) -> List[Dict]:
        """
        Get all defined user goals with available services
        
        Returns:
            List of goal dictionaries with their services
        """
        if not self.goal_mapper:
            logger.error("No goal mapper provided to goal-based catalog")
            return []
            
        goals = []
        
        # Get all defined goals from the goal mapper
        all_goals = self.goal_mapper.get_all_goals()
        
        # For each goal, find the available services
        for goal_id, goal_info in all_goals.items():
            services = self.get_services_for_goal(goal_id)
            
            goals.append({
                'id': goal_id,
                'name': goal_info.get('name', goal_id),
                'description': goal_info.get('description', ''),
                'persona_description': goal_info.get('persona_description', ''),
                'services': services,
                'service_count': len(services)
            })
        
        # Sort by service count (most services first)
        return sorted(goals, key=lambda g: g['service_count'], reverse=True)
    
    def get_services_for_goal(self, goal_id: str) -> List[Dict]:
        """
        Get services that help achieve a specific user goal
        
        Args:
            goal_id: The ID of the user goal
            
        Returns:
            List of service dictionaries
        """
        if goal_id not in self.goal_index:
            return []
            
        return [item['service'] for item in self.goal_index[goal_id]]
    
    def get_services_for_cloud_replacement(self, cloud_id: str) -> List[Dict]:
        """
        Get services that can replace a specific cloud service
        
        Args:
            cloud_id: The ID of the cloud service to replace
            
        Returns:
            List of service dictionaries
        """
        if cloud_id not in self.cloud_replacement_index:
            return []
            
        return [item['service'] for item in self.cloud_replacement_index[cloud_id]]
    
    def get_cloud_replacements_with_services(self) -> List[Dict]:
        """
        Get all defined cloud services with available replacements
        
        Returns:
            List of cloud service dictionaries with their replacement services
        """
        if not self.goal_mapper:
            logger.error("No goal mapper provided to goal-based catalog")
            return []
            
        replacements = []
        
        # Get all defined cloud services from the goal mapper
        all_cloud_services = self.goal_mapper.get_all_cloud_services()
        
        # For each cloud service, find the available replacements
        for cloud_id, cloud_info in all_cloud_services.items():
            services = self.get_services_for_cloud_replacement(cloud_id)
            
            replacements.append({
                'id': cloud_id,
                'name': cloud_info.get('name', cloud_id),
                'description': cloud_info.get('description', ''),
                'persona_description': cloud_info.get('persona_description', ''),
                'services': services,
                'service_count': len(services)
            })
        
        # Sort by service count (most services first)
        return sorted(replacements, key=lambda r: r['service_count'], reverse=True)
    
    def find_services_by_goal_keywords(self, query: str) -> List[Dict]:
        """
        Find services and goals matching the given keywords in the query
        
        Args:
            query: The search query containing keywords
            
        Returns:
            List of dictionaries with goal and matching services
        """
        if not self.goal_mapper:
            logger.error("No goal mapper provided to goal-based catalog")
            return []
            
        query_terms = query.lower().split()
        matches = []
        
        # Get all defined goals
        all_goals = self.goal_mapper.get_all_goals()
        
        for goal_id, goal_info in all_goals.items():
            # Check if any goal keywords match
            goal_name = goal_info.get('name', '').lower()
            goal_desc = goal_info.get('description', '').lower()
            
            if any(term in goal_name or term in goal_desc for term in query_terms):
                services = self.get_services_for_goal(goal_id)
                
                if services:  # Only include goals with available services
                    matches.append({
                        'goal': goal_info,
                        'services': services,
                        'match_type': 'goal'
                    })
        
        # Also check cloud service replacements
        all_cloud_services = self.goal_mapper.get_all_cloud_services()
        
        for cloud_id, cloud_info in all_cloud_services.items():
            # Check if any cloud service keywords match
            cloud_name = cloud_info.get('name', '').lower()
            cloud_desc = cloud_info.get('description', '').lower()
            
            if any(term in cloud_name or term in cloud_desc for term in query_terms):
                services = self.get_services_for_cloud_replacement(cloud_id)
                
                if services:  # Only include cloud services with available replacements
                    matches.append({
                        'cloud_service': cloud_info,
                        'services': services,
                        'match_type': 'cloud_replacement'
                    })
                    
        return matches
    
    def get_service_info_with_goals(self, service_id: str) -> Dict:
        """
        Get service information including associated goals
        
        Args:
            service_id: The ID of the service
            
        Returns:
            Service dictionary with goal information
        """
        if not self.service_catalog:
            logger.error("No service catalog provided to goal-based catalog")
            return {}
            
        service = self.service_catalog.get_service(service_id)
        if not service:
            return {}
            
        # Enhance with goal information
        service_info = service.copy()
        service_info['goals'] = []
        
        # Add goals information
        for goal_id, services in self.goal_index.items():
            for service_item in services:
                if service_item['id'] == service_id:
                    if self.goal_mapper:
                        goal = self.goal_mapper.goal_mappings.get(goal_id, {})
                        service_info['goals'].append({
                            'id': goal_id,
                            'name': goal.get('name', goal_id),
                            'description': goal.get('description', ''),
                            'relevance': service_item.get('relevance', 'medium'),
                            'reason': service_item.get('reason', '')
                        })
                    else:
                        service_info['goals'].append({
                            'id': goal_id,
                            'name': goal_id,
                            'relevance': service_item.get('relevance', 'medium'),
                            'reason': service_item.get('reason', '')
                        })
                    break
        
        # Add cloud replacement information
        service_info['replaces'] = []
        
        for cloud_id, services in self.cloud_replacement_index.items():
            for service_item in services:
                if service_item['id'] == service_id:
                    if self.goal_mapper:
                        cloud = self.goal_mapper.cloud_replacements.get(cloud_id, {})
                        service_info['replaces'].append({
                            'id': cloud_id,
                            'name': cloud.get('name', cloud_id),
                            'description': cloud.get('description', ''),
                            'quality': service_item.get('quality', 'good'),
                            'reason': service_item.get('reason', '')
                        })
                    else:
                        service_info['replaces'].append({
                            'id': cloud_id,
                            'name': cloud_id,
                            'quality': service_item.get('quality', 'good'),
                            'reason': service_item.get('reason', '')
                        })
                    break
        
        return service_info
    
    def get_service_recommendations_by_goal(self, goal_ids: List[str], include_personality: bool = True) -> Dict[str, Dict]:
        """
        Get service recommendations for multiple goals
        
        Args:
            goal_ids: List of goal IDs to get recommendations for
            include_personality: Whether to include personality-driven recommendations
            
        Returns:
            Dictionary mapping service IDs to recommendation information
        """
        if not self.goal_mapper:
            logger.error("No goal mapper provided to goal-based catalog")
            return {}
            
        return self.goal_mapper.get_recommended_services(goal_ids, include_personality)
    
    def categorize_service_catalog(self) -> Dict[str, List[Dict]]:
        """
        Categorize the entire service catalog by primary user goals
        Instead of technical categories, group by what users want to accomplish
        
        Returns:
            Dictionary mapping goal categories to lists of services
        """
        goal_categories = {}
        
        # Get all defined goals with their services
        goals_with_services = self.get_goals_with_services()
        
        # Create category structure
        for goal in goals_with_services:
            goal_id = goal['id']
            goal_categories[goal_id] = {
                'name': goal['name'],
                'description': goal['description'],
                'persona_description': goal['persona_description'],
                'services': []
            }
            
            # Add services to this goal category
            for service in goal['services']:
                # Find the relevance of this service to this goal
                relevance = 'medium'
                reason = ''
                if 'user_goals' in service:
                    for service_goal in service['user_goals']:
                        if service_goal['id'] == goal_id:
                            relevance = service_goal.get('relevance', 'medium')
                            reason = service_goal.get('reason', '')
                            break
                
                goal_categories[goal_id]['services'].append({
                    'id': service['id'],
                    'name': service['name'],
                    'description': service['description'],
                    'relevance': relevance,
                    'reason': reason
                })
                
        # Sort services within each category by relevance
        relevance_order = {'high': 0, 'medium': 1, 'low': 2}
        for goal_id, category in goal_categories.items():
            category['services'] = sorted(
                category['services'],
                key=lambda s: relevance_order.get(s.get('relevance', 'medium'), 3)
            )
        
        return goal_categories