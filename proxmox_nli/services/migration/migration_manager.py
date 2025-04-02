"""
Migration Manager Module

This module provides a central manager for all migration services, handling
platform detection, service instantiation, and migration coordination.
"""

import os
import json
import logging
import importlib
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Type

from proxmox_nli.services.proxmox_api import ProxmoxAPI
from proxmox_nli.services.migration.migration_base import MigrationBase

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manager for cross-platform migration services"""
    
    def __init__(self, proxmox_api: ProxmoxAPI, config: Optional[Dict] = None):
        """
        Initialize migration manager
        
        Args:
            proxmox_api: Instance of ProxmoxAPI for interacting with Proxmox
            config: Optional configuration dictionary
        """
        self.proxmox_api = proxmox_api
        self.config = config or {}
        self.migration_services = {}
        self.active_migrations = {}
        
        # Register available migration services
        self._register_migration_services()
    
    def _register_migration_services(self):
        """Register available migration services"""
        try:
            # Import migration service classes
            # This allows for dynamic loading of migration services
            from proxmox_nli.services.migration.unraid_migration import UnraidMigrationService
            self.migration_services["unraid"] = UnraidMigrationService
        except ImportError:
            logger.warning("Unraid migration service not available")
        
        try:
            from proxmox_nli.services.migration.truenas_migration import TrueNASMigrationService
            self.migration_services["truenas"] = TrueNASMigrationService
        except ImportError:
            logger.warning("TrueNAS migration service not available")
        
        try:
            from proxmox_nli.services.migration.esxi_migration import ESXiMigrationService
            self.migration_services["esxi"] = ESXiMigrationService
        except ImportError:
            logger.warning("ESXi migration service not available")
    
    def get_available_platforms(self) -> List[Dict]:
        """
        Get list of available migration platforms
        
        Returns:
            List of platform information dictionaries
        """
        platforms = []
        
        if "unraid" in self.migration_services:
            platforms.append({
                "id": "unraid",
                "name": "Unraid",
                "description": "Migrate from Unraid Server",
                "icon": "fa-server",
                "available": True
            })
        else:
            platforms.append({
                "id": "unraid",
                "name": "Unraid",
                "description": "Migrate from Unraid Server",
                "icon": "fa-server",
                "available": False,
                "message": "Unraid migration service not installed"
            })
        
        if "truenas" in self.migration_services:
            platforms.append({
                "id": "truenas",
                "name": "TrueNAS",
                "description": "Migrate from TrueNAS Core/Scale",
                "icon": "fa-database",
                "available": True
            })
        else:
            platforms.append({
                "id": "truenas",
                "name": "TrueNAS",
                "description": "Migrate from TrueNAS Core/Scale",
                "icon": "fa-database",
                "available": False,
                "message": "TrueNAS migration service not installed"
            })
        
        if "esxi" in self.migration_services:
            platforms.append({
                "id": "esxi",
                "name": "ESXi/vSphere",
                "description": "Migrate from VMware ESXi/vSphere",
                "icon": "fa-cloud",
                "available": True
            })
        else:
            platforms.append({
                "id": "esxi",
                "name": "ESXi/vSphere",
                "description": "Migrate from VMware ESXi/vSphere",
                "icon": "fa-cloud",
                "available": False,
                "message": "ESXi migration service not installed"
            })
        
        return platforms
    
    def get_migration_service(self, platform: str) -> Optional[MigrationBase]:
        """
        Get migration service for a platform
        
        Args:
            platform: Platform identifier (unraid, truenas, esxi)
            
        Returns:
            Migration service instance or None if not available
        """
        if platform not in self.migration_services:
            logger.error(f"Migration service for platform {platform} not available")
            return None
        
        try:
            # Instantiate migration service
            service_class = self.migration_services[platform]
            service = service_class(self.proxmox_api, self.config.get(platform, {}))
            return service
        except Exception as e:
            logger.error(f"Error instantiating migration service for {platform}: {str(e)}")
            return None
    
    def validate_source_credentials(self, platform: str, credentials: Dict) -> Dict:
        """
        Validate credentials for a source platform
        
        Args:
            platform: Platform identifier
            credentials: Credentials dictionary
            
        Returns:
            Validation results
        """
        service = self.get_migration_service(platform)
        
        if not service:
            return {
                "success": False,
                "message": f"Migration service for platform {platform} not available"
            }
        
        try:
            result = service.validate_source_credentials(credentials)
            return result
        except Exception as e:
            logger.error(f"Error validating credentials for {platform}: {str(e)}")
            return {
                "success": False,
                "message": f"Error validating credentials: {str(e)}"
            }
    
    def analyze_source_environment(self, platform: str, credentials: Dict) -> Dict:
        """
        Analyze source environment
        
        Args:
            platform: Platform identifier
            credentials: Credentials dictionary
            
        Returns:
            Analysis results
        """
        service = self.get_migration_service(platform)
        
        if not service:
            return {
                "success": False,
                "message": f"Migration service for platform {platform} not available"
            }
        
        try:
            result = service.analyze_source_environment(credentials)
            
            # Store migration data for later use
            migration_id = service.migration_id
            if migration_id:
                self.active_migrations[migration_id] = {
                    "platform": platform,
                    "service": service,
                    "status": "analyzed",
                    "timestamp": datetime.now().isoformat()
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing source environment for {platform}: {str(e)}")
            return {
                "success": False,
                "message": f"Error analyzing source environment: {str(e)}"
            }
    
    def create_migration_plan(self, migration_id: str, source_resources: Dict, target_node: str) -> Dict:
        """
        Create migration plan
        
        Args:
            migration_id: Migration ID
            source_resources: Source resources dictionary
            target_node: Target Proxmox node
            
        Returns:
            Migration plan
        """
        if migration_id not in self.active_migrations:
            return {
                "success": False,
                "message": f"Migration {migration_id} not found"
            }
        
        migration = self.active_migrations[migration_id]
        service = migration["service"]
        
        try:
            result = service.create_migration_plan(source_resources, target_node)
            
            # Update migration status
            migration["status"] = "planned"
            migration["timestamp"] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"Error creating migration plan: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating migration plan: {str(e)}"
            }
    
    def execute_migration(self, migration_id: str, migration_plan: Dict) -> Dict:
        """
        Execute migration
        
        Args:
            migration_id: Migration ID
            migration_plan: Migration plan dictionary
            
        Returns:
            Migration results
        """
        if migration_id not in self.active_migrations:
            return {
                "success": False,
                "message": f"Migration {migration_id} not found"
            }
        
        migration = self.active_migrations[migration_id]
        service = migration["service"]
        
        try:
            # Define progress callback
            def progress_callback(progress: Dict):
                # Update migration status
                migration["progress"] = progress
                migration["timestamp"] = datetime.now().isoformat()
            
            # Execute migration
            result = service.execute_migration(migration_plan, progress_callback)
            
            # Update migration status
            migration["status"] = "completed" if result.get("success", False) else "failed"
            migration["timestamp"] = datetime.now().isoformat()
            migration["result"] = result
            
            return result
        except Exception as e:
            logger.error(f"Error executing migration: {str(e)}")
            
            # Update migration status
            migration["status"] = "failed"
            migration["timestamp"] = datetime.now().isoformat()
            migration["error"] = str(e)
            
            return {
                "success": False,
                "message": f"Error executing migration: {str(e)}"
            }
    
    def get_migration_status(self, migration_id: str) -> Dict:
        """
        Get migration status
        
        Args:
            migration_id: Migration ID
            
        Returns:
            Migration status
        """
        if migration_id not in self.active_migrations:
            # Try to load from saved state
            try:
                for platform in self.migration_services:
                    service = self.get_migration_service(platform)
                    if service:
                        try:
                            state = service.load_migration_state(migration_id)
                            self.active_migrations[migration_id] = {
                                "platform": platform,
                                "service": service,
                                "status": state.get("status", "unknown"),
                                "timestamp": datetime.now().isoformat()
                            }
                            break
                        except:
                            continue
            except Exception as e:
                logger.error(f"Error loading migration state: {str(e)}")
            
            if migration_id not in self.active_migrations:
                return {
                    "success": False,
                    "message": f"Migration {migration_id} not found"
                }
        
        migration = self.active_migrations[migration_id]
        
        return {
            "success": True,
            "migration_id": migration_id,
            "platform": migration["platform"],
            "status": migration["status"],
            "timestamp": migration["timestamp"],
            "progress": migration.get("progress"),
            "result": migration.get("result"),
            "error": migration.get("error")
        }
    
    def list_migrations(self) -> List[Dict]:
        """
        List all migrations
        
        Returns:
            List of migration status dictionaries
        """
        migrations = []
        
        # Add active migrations
        for migration_id, migration in self.active_migrations.items():
            migrations.append({
                "migration_id": migration_id,
                "platform": migration["platform"],
                "status": migration["status"],
                "timestamp": migration["timestamp"]
            })
        
        # Add saved migrations from all services
        for platform in self.migration_services:
            service = self.get_migration_service(platform)
            if service:
                try:
                    saved_migrations = service.list_migrations()
                    
                    for saved in saved_migrations:
                        # Check if already in list
                        if any(m["migration_id"] == saved["migration_id"] for m in migrations):
                            continue
                        
                        migrations.append({
                            "migration_id": saved["migration_id"],
                            "platform": saved["source_platform"],
                            "status": saved["status"],
                            "timestamp": saved.get("created_at") or saved.get("updated_at")
                        })
                except Exception as e:
                    logger.error(f"Error listing migrations for {platform}: {str(e)}")
        
        return migrations
    
    def get_migration_report(self, migration_id: str) -> Dict:
        """
        Get migration report
        
        Args:
            migration_id: Migration ID
            
        Returns:
            Migration report
        """
        if migration_id not in self.active_migrations:
            # Try to load from saved state
            try:
                for platform in self.migration_services:
                    service = self.get_migration_service(platform)
                    if service:
                        try:
                            state = service.load_migration_state(migration_id)
                            self.active_migrations[migration_id] = {
                                "platform": platform,
                                "service": service,
                                "status": state.get("status", "unknown"),
                                "timestamp": datetime.now().isoformat()
                            }
                            break
                        except:
                            continue
            except Exception as e:
                logger.error(f"Error loading migration state: {str(e)}")
            
            if migration_id not in self.active_migrations:
                return {
                    "success": False,
                    "message": f"Migration {migration_id} not found"
                }
        
        migration = self.active_migrations[migration_id]
        service = migration["service"]
        
        try:
            report = service.generate_migration_report()
            return report
        except Exception as e:
            logger.error(f"Error generating migration report: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating migration report: {str(e)}"
            }
    
    def cancel_migration(self, migration_id: str) -> Dict:
        """
        Cancel migration
        
        Args:
            migration_id: Migration ID
            
        Returns:
            Cancellation result
        """
        if migration_id not in self.active_migrations:
            return {
                "success": False,
                "message": f"Migration {migration_id} not found"
            }
        
        migration = self.active_migrations[migration_id]
        
        # Update migration status
        migration["status"] = "cancelled"
        migration["timestamp"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": f"Migration {migration_id} cancelled"
        }
