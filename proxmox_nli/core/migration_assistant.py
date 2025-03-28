"""
Migration assistant for Proxmox NLI.
Provides guided workflows for migrating VMs and services between nodes.
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any
import time
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class MigrationAssistant:
    """Assistant for guided migration workflows."""
    
    def __init__(self, cluster_manager, service_manager):
        """Initialize the migration assistant.
        
        Args:
            cluster_manager: ClusterManager instance for cluster operations
            service_manager: ServiceManager instance for service operations
        """
        self.cluster_manager = cluster_manager
        self.service_manager = service_manager
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'migrations')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Store ongoing migrations
        self.migrations = {}
        self._load_migrations()
        
        # Migration workflow templates
        self.workflow_templates = {
            'standard_vm': [
                {'step': 'check_resources', 'description': 'Check resource availability on target node'},
                {'step': 'pre_migration_snapshot', 'description': 'Create pre-migration snapshot'},
                {'step': 'migrate_vm', 'description': 'Migrate VM to target node'},
                {'step': 'verify_vm_status', 'description': 'Verify VM status after migration'},
                {'step': 'cleanup', 'description': 'Clean up temporary resources'}
            ],
            'service_migration': [
                {'step': 'check_resources', 'description': 'Check resource availability on target node'},
                {'step': 'backup_service_data', 'description': 'Backup service data'},
                {'step': 'stop_service', 'description': 'Stop service on source node'},
                {'step': 'migrate_vm', 'description': 'Migrate VM to target node'},
                {'step': 'start_service', 'description': 'Start service on target node'},
                {'step': 'verify_service', 'description': 'Verify service functionality'},
                {'step': 'update_service_records', 'description': 'Update service records with new location'}
            ],
            'storage_migration': [
                {'step': 'check_storage', 'description': 'Check storage availability on target'},
                {'step': 'estimate_transfer_time', 'description': 'Estimate data transfer time'},
                {'step': 'backup_data', 'description': 'Create backup of data'},
                {'step': 'transfer_data', 'description': 'Transfer data to new storage'},
                {'step': 'verify_data', 'description': 'Verify data integrity after transfer'},
                {'step': 'update_vm_config', 'description': 'Update VM configuration to use new storage'},
                {'step': 'cleanup', 'description': 'Clean up temporary resources'}
            ]
        }
        
    def _load_migrations(self):
        """Load ongoing migrations from disk."""
        try:
            migrations_file = os.path.join(self.data_dir, 'ongoing_migrations.json')
            if os.path.exists(migrations_file):
                with open(migrations_file, 'r') as f:
                    self.migrations = json.load(f)
                logger.info(f"Loaded {len(self.migrations)} ongoing migrations")
        except Exception as e:
            logger.error(f"Error loading migrations: {str(e)}")
            self.migrations = {}
            
    def _save_migrations(self):
        """Save ongoing migrations to disk."""
        try:
            migrations_file = os.path.join(self.data_dir, 'ongoing_migrations.json')
            with open(migrations_file, 'w') as f:
                json.dump(self.migrations, f)
            logger.debug("Migrations saved to disk")
        except Exception as e:
            logger.error(f"Error saving migrations: {str(e)}")
    
    def start_migration_workflow(self, migration_type: str, vm_id: str, source_node: str, 
                               target_node: str, options: Dict = None) -> Dict:
        """Start a guided migration workflow.
        
        Args:
            migration_type: Type of migration workflow to use
            vm_id: ID of the VM to migrate
            source_node: Source node ID
            target_node: Target node ID
            options: Additional migration options
            
        Returns:
            Dictionary with migration workflow information
        """
        if migration_type not in self.workflow_templates:
            return {
                'success': False,
                'message': f'Unknown migration type: {migration_type}'
            }
            
        # Create a unique migration ID
        migration_id = f"migration_{int(time.time())}_{vm_id}"
        
        # Initialize migration record
        migration = {
            'id': migration_id,
            'type': migration_type,
            'vm_id': vm_id,
            'source_node': source_node,
            'target_node': target_node,
            'options': options or {},
            'status': 'initializing',
            'current_step': 0,
            'steps': self.workflow_templates[migration_type],
            'logs': [],
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'success': None
        }
        
        # Add to migrations dictionary
        self.migrations[migration_id] = migration
        self._save_migrations()
        
        # Start the migration workflow in a separate thread
        threading.Thread(target=self._execute_workflow, args=(migration_id,), daemon=True).start()
        
        return {
            'success': True,
            'message': f'Migration workflow started',
            'migration_id': migration_id,
            'migration': migration
        }
    
    def _execute_workflow(self, migration_id: str):
        """Execute a migration workflow.
        
        Args:
            migration_id: ID of the migration to execute
        """
        if migration_id not in self.migrations:
            logger.error(f"Migration {migration_id} not found")
            return
            
        migration = self.migrations[migration_id]
        migration['status'] = 'in_progress'
        self._log_migration(migration_id, 'Starting migration workflow')
        
        try:
            # Execute each step in the workflow
            for i, step in enumerate(migration['steps']):
                migration['current_step'] = i
                step_name = step['step']
                self._log_migration(migration_id, f"Starting step {i+1}/{len(migration['steps'])}: {step['description']}")
                
                # Execute the appropriate method for this step
                step_method = getattr(self, f"_step_{step_name}", None)
                if step_method:
                    step_result = step_method(migration)
                    if not step_result.get('success', False):
                        self._log_migration(migration_id, f"Step failed: {step_result.get('message', 'Unknown error')}", level='error')
                        migration['status'] = 'failed'
                        migration['success'] = False
                        migration['completed_at'] = datetime.now().isoformat()
                        self._save_migrations()
                        return
                else:
                    self._log_migration(migration_id, f"Step handler not found for {step_name}", level='warning')
                
                self._log_migration(migration_id, f"Completed step {i+1}/{len(migration['steps'])}: {step['description']}")
                self._save_migrations()
            
            # All steps completed successfully
            migration['status'] = 'completed'
            migration['success'] = True
            migration['completed_at'] = datetime.now().isoformat()
            self._log_migration(migration_id, "Migration workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Error executing migration workflow: {str(e)}")
            self._log_migration(migration_id, f"Migration failed: {str(e)}", level='error')
            migration['status'] = 'failed'
            migration['success'] = False
            migration['completed_at'] = datetime.now().isoformat()
            
        self._save_migrations()
    
    def _log_migration(self, migration_id: str, message: str, level: str = 'info'):
        """Add a log entry to a migration.
        
        Args:
            migration_id: ID of the migration to log for
            message: Log message
            level: Log level (info, warning, error)
        """
        if migration_id not in self.migrations:
            return
            
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level
        }
        
        self.migrations[migration_id]['logs'].append(log_entry)
        
        # Log to system logger as well
        if level == 'info':
            logger.info(f"Migration {migration_id}: {message}")
        elif level == 'warning':
            logger.warning(f"Migration {migration_id}: {message}")
        elif level == 'error':
            logger.error(f"Migration {migration_id}: {message}")
    
    def get_migration_status(self, migration_id: str) -> Dict:
        """Get the status of a migration workflow.
        
        Args:
            migration_id: ID of the migration to get status for
            
        Returns:
            Dictionary with migration status
        """
        if migration_id not in self.migrations:
            return {
                'success': False,
                'message': f'Migration {migration_id} not found'
            }
            
        return {
            'success': True,
            'message': 'Migration status retrieved',
            'migration': self.migrations[migration_id]
        }
    
    def get_all_migrations(self) -> Dict:
        """Get all migration workflows.
        
        Returns:
            Dictionary with all migrations
        """
        return {
            'success': True,
            'message': 'All migrations retrieved',
            'migrations': self.migrations
        }
    
    def cancel_migration(self, migration_id: str) -> Dict:
        """Cancel an ongoing migration workflow.
        
        Args:
            migration_id: ID of the migration to cancel
            
        Returns:
            Dictionary with cancellation result
        """
        if migration_id not in self.migrations:
            return {
                'success': False,
                'message': f'Migration {migration_id} not found'
            }
            
        migration = self.migrations[migration_id]
        
        if migration['status'] in ['completed', 'failed', 'cancelled']:
            return {
                'success': False,
                'message': f'Migration {migration_id} is already {migration["status"]}'
            }
            
        migration['status'] = 'cancelled'
        migration['completed_at'] = datetime.now().isoformat()
        self._log_migration(migration_id, "Migration cancelled by user")
        self._save_migrations()
        
        return {
            'success': True,
            'message': f'Migration {migration_id} cancelled',
            'migration': migration
        }
    
    # Step implementation methods
    
    def _step_check_resources(self, migration: Dict) -> Dict:
        """Check resource availability on target node.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        vm_id = migration['vm_id']
        target_node = migration['target_node']
        
        # Get VM resource requirements
        vm_info = self.cluster_manager.proxmox_api.get(f'/nodes/{migration["source_node"]}/qemu/{vm_id}/config')
        if not vm_info.get('success', False):
            return {'success': False, 'message': f'Failed to get VM info: {vm_info.get("message")}'}
        
        vm_config = vm_info.get('data', {})
        required_memory = int(vm_config.get('memory', 0))
        required_cores = int(vm_config.get('cores', 0))
        
        # Get target node resources
        node_resources = self.cluster_manager.get_node_resources(target_node)
        if not node_resources.get('success', False):
            return {'success': False, 'message': f'Failed to get target node resources: {node_resources.get("message")}'}
        
        node_data = node_resources.get('data', {})
        available_memory = node_data.get('memory', {}).get('free', 0)
        available_cores = node_data.get('cpuinfo', {}).get('cpus', 0) - node_data.get('cpu', 0)
        
        # Check if target node has enough resources
        if available_memory < required_memory:
            return {
                'success': False, 
                'message': f'Target node does not have enough memory: {available_memory}MB available, {required_memory}MB required'
            }
            
        if available_cores < required_cores:
            return {
                'success': False, 
                'message': f'Target node does not have enough CPU cores: {available_cores} available, {required_cores} required'
            }
            
        return {'success': True, 'message': 'Resource check passed'}
    
    def _step_pre_migration_snapshot(self, migration: Dict) -> Dict:
        """Create pre-migration snapshot.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        vm_id = migration['vm_id']
        source_node = migration['source_node']
        
        # Create a snapshot
        snapshot_name = f"pre_migration_{int(time.time())}"
        snapshot_result = self.cluster_manager.proxmox_api.post(
            f'/nodes/{source_node}/qemu/{vm_id}/snapshot', 
            {'snapname': snapshot_name, 'description': 'Pre-migration snapshot'}
        )
        
        if not snapshot_result.get('success', False):
            return {'success': False, 'message': f'Failed to create snapshot: {snapshot_result.get("message")}'}
            
        # Store snapshot name in migration options for later use
        migration['options']['pre_migration_snapshot'] = snapshot_name
        
        return {'success': True, 'message': f'Created pre-migration snapshot: {snapshot_name}'}
    
    def _step_migrate_vm(self, migration: Dict) -> Dict:
        """Migrate VM to target node.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        vm_id = migration['vm_id']
        source_node = migration['source_node']
        target_node = migration['target_node']
        
        # Get migration options
        live_migration = migration['options'].get('live_migration', True)
        with_local_disks = migration['options'].get('with_local_disks', True)
        
        # Start migration
        migration_result = self.cluster_manager.migrate_vm(
            vm_id, source_node, target_node, 
            live_migration=live_migration, 
            with_local_disks=with_local_disks
        )
        
        if not migration_result.get('success', False):
            return {'success': False, 'message': f'Failed to start migration: {migration_result.get("message")}'}
            
        # Wait for migration to complete
        max_wait_time = 3600  # 1 hour
        wait_interval = 10  # 10 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            # Check migration status
            status_result = self.cluster_manager.get_migration_status(vm_id, source_node)
            
            if not status_result.get('success', False):
                # If we can't get status, check if VM exists on target node
                target_vm_check = self.cluster_manager.proxmox_api.get(f'/nodes/{target_node}/qemu/{vm_id}/status/current')
                if target_vm_check.get('success', False):
                    # VM exists on target node, migration completed
                    return {'success': True, 'message': 'VM migration completed'}
            else:
                status_data = status_result.get('data', {})
                if status_data.get('status') == 'completed':
                    return {'success': True, 'message': 'VM migration completed'}
                elif status_data.get('status') == 'failed':
                    return {'success': False, 'message': f'Migration failed: {status_data.get("error")}'}
            
            # Wait before checking again
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        return {'success': False, 'message': 'Migration timed out'}
    
    def _step_verify_vm_status(self, migration: Dict) -> Dict:
        """Verify VM status after migration.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        vm_id = migration['vm_id']
        target_node = migration['target_node']
        
        # Check VM status on target node
        status_result = self.cluster_manager.proxmox_api.get(f'/nodes/{target_node}/qemu/{vm_id}/status/current')
        
        if not status_result.get('success', False):
            return {'success': False, 'message': f'Failed to get VM status: {status_result.get("message")}'}
            
        status_data = status_result.get('data', {})
        vm_status = status_data.get('status', '')
        
        if vm_status not in ['running', 'stopped']:
            return {'success': False, 'message': f'VM is in unexpected state: {vm_status}'}
            
        return {'success': True, 'message': f'VM status verified: {vm_status}'}
    
    def _step_cleanup(self, migration: Dict) -> Dict:
        """Clean up temporary resources.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        # Check if we need to clean up a snapshot
        snapshot_name = migration['options'].get('pre_migration_snapshot')
        if not snapshot_name:
            return {'success': True, 'message': 'No cleanup needed'}
            
        vm_id = migration['vm_id']
        target_node = migration['target_node']
        
        # Delete the snapshot if it exists
        snapshot_result = self.cluster_manager.proxmox_api.delete(
            f'/nodes/{target_node}/qemu/{vm_id}/snapshot/{snapshot_name}'
        )
        
        if not snapshot_result.get('success', False):
            return {'success': False, 'message': f'Failed to delete snapshot: {snapshot_result.get("message")}'}
            
        return {'success': True, 'message': f'Cleaned up pre-migration snapshot: {snapshot_name}'}
    
    def _step_backup_service_data(self, migration: Dict) -> Dict:
        """Backup service data.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        vm_id = migration['vm_id']
        service_id = migration['options'].get('service_id')
        
        if not service_id:
            return {'success': False, 'message': 'Service ID not provided'}
            
        # Get service information
        service_info = self.service_manager.get_service_info(service_id)
        if not service_info.get('success', False):
            return {'success': False, 'message': f'Failed to get service info: {service_info.get("message")}'}
            
        # Create backup of service data
        backup_result = self.service_manager.backup_service(service_id)
        
        if not backup_result.get('success', False):
            return {'success': False, 'message': f'Failed to backup service data: {backup_result.get("message")}'}
            
        # Store backup ID in migration options
        migration['options']['backup_id'] = backup_result.get('backup_id')
            
        return {'success': True, 'message': 'Service data backed up successfully'}
    
    def _step_stop_service(self, migration: Dict) -> Dict:
        """Stop service on source node.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        service_id = migration['options'].get('service_id')
        
        if not service_id:
            return {'success': False, 'message': 'Service ID not provided'}
            
        # Stop the service
        stop_result = self.service_manager.stop_service(service_id)
        
        if not stop_result.get('success', False):
            return {'success': False, 'message': f'Failed to stop service: {stop_result.get("message")}'}
            
        return {'success': True, 'message': 'Service stopped successfully'}
    
    def _step_start_service(self, migration: Dict) -> Dict:
        """Start service on target node.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        service_id = migration['options'].get('service_id')
        
        if not service_id:
            return {'success': False, 'message': 'Service ID not provided'}
            
        # Start the service
        start_result = self.service_manager.start_service(service_id)
        
        if not start_result.get('success', False):
            return {'success': False, 'message': f'Failed to start service: {start_result.get("message")}'}
            
        return {'success': True, 'message': 'Service started successfully'}
    
    def _step_verify_service(self, migration: Dict) -> Dict:
        """Verify service functionality.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        service_id = migration['options'].get('service_id')
        
        if not service_id:
            return {'success': False, 'message': 'Service ID not provided'}
            
        # Check service health
        health_result = self.service_manager.check_service_health(service_id)
        
        if not health_result.get('success', False):
            return {'success': False, 'message': f'Service health check failed: {health_result.get("message")}'}
            
        return {'success': True, 'message': 'Service verified successfully'}
    
    def _step_update_service_records(self, migration: Dict) -> Dict:
        """Update service records with new location.
        
        Args:
            migration: Migration workflow dictionary
            
        Returns:
            Step result dictionary
        """
        service_id = migration['options'].get('service_id')
        target_node = migration['target_node']
        
        if not service_id:
            return {'success': False, 'message': 'Service ID not provided'}
            
        # Update service location
        update_result = self.service_manager.update_service_location(service_id, target_node)
        
        if not update_result.get('success', False):
            return {'success': False, 'message': f'Failed to update service records: {update_result.get("message")}'}
            
        return {'success': True, 'message': 'Service records updated successfully'}
