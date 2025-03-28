"""
Cluster management for Proxmox NLI.
Provides functionality to manage multiple Proxmox nodes in a cluster.
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any
import time
import threading
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class ClusterManager:
    """Manager for Proxmox cluster operations."""
    
    def __init__(self, proxmox_api):
        """Initialize the cluster manager.
        
        Args:
            proxmox_api: ProxmoxAPI instance for API interactions
        """
        self.proxmox_api = proxmox_api
        self.cluster_status = {}
        self.nodes = []
        self.quorum_status = {}
        self.last_refresh = None
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'cluster')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing cluster data if available
        self._load_cluster_data()
        
    def _load_cluster_data(self):
        """Load cluster data from disk."""
        try:
            cluster_file = os.path.join(self.data_dir, 'cluster_data.json')
            if os.path.exists(cluster_file):
                with open(cluster_file, 'r') as f:
                    data = json.load(f)
                    self.cluster_status = data.get('status', {})
                    self.nodes = data.get('nodes', [])
                    self.quorum_status = data.get('quorum', {})
                    self.last_refresh = data.get('last_refresh')
                logger.info(f"Loaded cluster data with {len(self.nodes)} nodes")
        except Exception as e:
            logger.error(f"Error loading cluster data: {str(e)}")
            
    def _save_cluster_data(self):
        """Save cluster data to disk."""
        try:
            cluster_file = os.path.join(self.data_dir, 'cluster_data.json')
            data = {
                'status': self.cluster_status,
                'nodes': self.nodes,
                'quorum': self.quorum_status,
                'last_refresh': self.last_refresh
            }
            with open(cluster_file, 'w') as f:
                json.dump(data, f)
            logger.debug("Cluster data saved to disk")
        except Exception as e:
            logger.error(f"Error saving cluster data: {str(e)}")
    
    def refresh_cluster_status(self) -> Dict:
        """Refresh cluster status information.
        
        Returns:
            Dictionary with cluster status information
        """
        try:
            # Get cluster status
            status_result = self.proxmox_api.get('/cluster/status')
            if not status_result.get('success', False):
                return {'success': False, 'message': 'Failed to get cluster status'}
                
            self.cluster_status = status_result.get('data', [])
            
            # Get node list
            nodes_result = self.proxmox_api.get('/nodes')
            if nodes_result.get('success', False):
                self.nodes = nodes_result.get('data', [])
            
            # Get quorum status
            quorum_result = self.proxmox_api.get('/cluster/config/quorum')
            if quorum_result.get('success', False):
                self.quorum_status = quorum_result.get('data', {})
                
            self.last_refresh = datetime.now().isoformat()
            self._save_cluster_data()
            
            return {
                'success': True,
                'message': 'Cluster status refreshed',
                'status': self.cluster_status,
                'nodes': self.nodes,
                'quorum': self.quorum_status
            }
        except Exception as e:
            logger.error(f"Error refreshing cluster status: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_cluster_status(self, refresh: bool = False) -> Dict:
        """Get cluster status information.
        
        Args:
            refresh: Whether to refresh the status before returning
            
        Returns:
            Dictionary with cluster status information
        """
        if refresh or not self.last_refresh:
            return self.refresh_cluster_status()
            
        return {
            'success': True,
            'message': 'Cluster status retrieved',
            'status': self.cluster_status,
            'nodes': self.nodes,
            'quorum': self.quorum_status,
            'last_refresh': self.last_refresh
        }
    
    def execute_cluster_command(self, command: str, nodes: List[str] = None) -> Dict:
        """Execute a command on all or selected cluster nodes.
        
        Args:
            command: Command to execute
            nodes: List of node IDs to execute on (None for all nodes)
            
        Returns:
            Dictionary with command execution results
        """
        if not nodes:
            # Get all online nodes
            if not self.nodes:
                self.refresh_cluster_status()
            nodes = [node['node'] for node in self.nodes if node.get('status') == 'online']
            
        results = {}
        success_count = 0
        
        for node in nodes:
            try:
                # Execute command on the node
                cmd_result = self.proxmox_api.post(f'/nodes/{node}/exec', {
                    'command': command
                })
                
                results[node] = cmd_result
                if cmd_result.get('success', False):
                    success_count += 1
            except Exception as e:
                logger.error(f"Error executing command on node {node}: {str(e)}")
                results[node] = {'success': False, 'message': f'Error: {str(e)}'}
                
        return {
            'success': success_count == len(nodes),
            'message': f'Command executed on {success_count}/{len(nodes)} nodes',
            'results': results
        }
    
    def get_node_resources(self, node_id: str) -> Dict:
        """Get resource usage for a specific node.
        
        Args:
            node_id: ID of the node to get resources for
            
        Returns:
            Dictionary with node resource information
        """
        try:
            result = self.proxmox_api.get(f'/nodes/{node_id}/status')
            if not result.get('success', False):
                return {'success': False, 'message': f'Failed to get node status: {result.get("message")}'}
                
            return {
                'success': True,
                'message': 'Node resources retrieved',
                'data': result.get('data', {})
            }
        except Exception as e:
            logger.error(f"Error getting node resources: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def migrate_vm(self, vm_id: str, source_node: str, target_node: str, 
                  live_migration: bool = True, with_local_disks: bool = True) -> Dict:
        """Migrate a VM from one node to another.
        
        Args:
            vm_id: ID of the VM to migrate
            source_node: Source node ID
            target_node: Target node ID
            live_migration: Whether to use live migration
            with_local_disks: Whether to migrate local disks
            
        Returns:
            Dictionary with migration result
        """
        try:
            # Check if target node is available
            node_status = self.proxmox_api.get(f'/nodes/{target_node}/status')
            if not node_status.get('success', False) or node_status.get('data', {}).get('status') != 'online':
                return {'success': False, 'message': f'Target node {target_node} is not available'}
                
            # Start migration
            migration_options = {
                'target': target_node,
                'online': live_migration,
                'with-local-disks': with_local_disks
            }
            
            result = self.proxmox_api.post(f'/nodes/{source_node}/qemu/{vm_id}/migrate', migration_options)
            
            if not result.get('success', False):
                return {'success': False, 'message': f'Failed to start migration: {result.get("message")}'}
                
            return {
                'success': True,
                'message': f'Migration of VM {vm_id} to node {target_node} started',
                'data': result.get('data', {})
            }
        except Exception as e:
            logger.error(f"Error migrating VM: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_migration_status(self, vm_id: str, node: str) -> Dict:
        """Get the status of an ongoing migration.
        
        Args:
            vm_id: ID of the VM being migrated
            node: Source node ID
            
        Returns:
            Dictionary with migration status
        """
        try:
            result = self.proxmox_api.get(f'/nodes/{node}/qemu/{vm_id}/migration')
            
            if not result.get('success', False):
                return {'success': False, 'message': f'Failed to get migration status: {result.get("message")}'}
                
            return {
                'success': True,
                'message': 'Migration status retrieved',
                'data': result.get('data', {})
            }
        except Exception as e:
            logger.error(f"Error getting migration status: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_cluster_resources(self) -> Dict:
        """Get resource usage across all cluster nodes.
        
        Returns:
            Dictionary with cluster resource information
        """
        try:
            result = self.proxmox_api.get('/cluster/resources')
            
            if not result.get('success', False):
                return {'success': False, 'message': f'Failed to get cluster resources: {result.get("message")}'}
                
            return {
                'success': True,
                'message': 'Cluster resources retrieved',
                'data': result.get('data', [])
            }
        except Exception as e:
            logger.error(f"Error getting cluster resources: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
