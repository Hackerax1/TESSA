"""
AI-driven VM/container migration manager based on server load.

This module provides functionality to automatically migrate VMs and containers
between nodes based on resource usage patterns, load balancing needs, and
predictive analytics.
"""
import logging
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

from proxmox_nli.services.migration.migration_manager import MigrationManager
from proxmox_nli.core.monitoring.resource_monitor import ResourceMonitor
from proxmox_nli.core.monitoring.predictive_analyzer import PredictiveAnalyzer
from proxmox_nli.core.monitoring.resource_analyzer import ResourceAnalyzer

logger = logging.getLogger(__name__)

class AIMigrationManager:
    """AI-driven manager for automatic VM/container migration based on server load."""
    
    def __init__(self, api, migration_manager: MigrationManager = None, 
                 resource_monitor: ResourceMonitor = None):
        """
        Initialize the AI migration manager.
        
        Args:
            api: Proxmox API instance
            migration_manager: Optional MigrationManager instance
            resource_monitor: Optional ResourceMonitor instance
        """
        self.api = api
        self.migration_manager = migration_manager or MigrationManager(api)
        self.resource_monitor = resource_monitor or ResourceMonitor(api)
        self.resource_analyzer = ResourceAnalyzer(api)
        self.predictive_analyzer = PredictiveAnalyzer(self.resource_analyzer)
        
        # Configuration parameters
        self.config = {
            'enabled': False,
            'check_interval': 900,  # 15 minutes
            'cpu_threshold_high': 80,  # percentage
            'memory_threshold_high': 80,  # percentage
            'cpu_threshold_low': 20,  # percentage
            'memory_threshold_low': 20,  # percentage
            'migration_cooldown': 3600,  # 1 hour
            'max_migrations_per_run': 2,
            'prediction_horizon': 2,  # hours
            'auto_approve': False,
            'preferred_migration_hours': [1, 2, 3, 4, 5],  # 1 AM to 5 AM
            'exclude_vms': [],
            'exclude_nodes': []
        }
        
        # Runtime state
        self.running = False
        self.monitor_thread = None
        self.last_migration_time = {}  # Track last migration time for each VM/CT
        self.pending_migrations = []  # Migrations waiting for approval
        self.migration_history = []  # Track migration history
    
    def update_config(self, new_config: Dict) -> Dict[str, Any]:
        """
        Update configuration parameters.
        
        Args:
            new_config: Dictionary with new configuration values
            
        Returns:
            Dict with operation result
        """
        try:
            for key, value in new_config.items():
                if key in self.config:
                    self.config[key] = value
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "config": self.config
            }
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating configuration: {str(e)}"
            }
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Dict with current configuration
        """
        return {
            "success": True,
            "config": self.config
        }
    
    def start(self) -> Dict[str, Any]:
        """
        Start the automatic migration service.
        
        Returns:
            Dict with operation result
        """
        try:
            if self.running:
                return {
                    "success": False,
                    "message": "AI migration manager is already running"
                }
            
            # Make sure resource monitoring is active
            if not self.resource_monitor.monitoring_active:
                monitor_result = self.resource_monitor.start_monitoring()
                if not monitor_result["success"]:
                    return {
                        "success": False,
                        "message": f"Failed to start resource monitoring: {monitor_result['message']}"
                    }
            
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("AI migration manager started")
            return {
                "success": True,
                "message": "AI migration manager started successfully"
            }
        except Exception as e:
            logger.error(f"Error starting AI migration manager: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting AI migration manager: {str(e)}"
            }
    
    def stop(self) -> Dict[str, Any]:
        """
        Stop the automatic migration service.
        
        Returns:
            Dict with operation result
        """
        try:
            if not self.running:
                return {
                    "success": False,
                    "message": "AI migration manager is not running"
                }
            
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            logger.info("AI migration manager stopped")
            return {
                "success": True,
                "message": "AI migration manager stopped successfully"
            }
        except Exception as e:
            logger.error(f"Error stopping AI migration manager: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping AI migration manager: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the AI migration manager.
        
        Returns:
            Dict with status information
        """
        return {
            "success": True,
            "status": {
                "running": self.running,
                "pending_migrations": self.pending_migrations,
                "recent_migrations": self.migration_history[-10:] if self.migration_history else [],
                "config": self.config
            }
        }
    
    def approve_migration(self, migration_id: str) -> Dict[str, Any]:
        """
        Approve a pending migration.
        
        Args:
            migration_id: ID of the pending migration
            
        Returns:
            Dict with operation result
        """
        try:
            for i, migration in enumerate(self.pending_migrations):
                if migration["id"] == migration_id:
                    # Execute the migration
                    result = self._execute_migration(migration)
                    
                    # Remove from pending list
                    self.pending_migrations.pop(i)
                    
                    return result
            
            return {
                "success": False,
                "message": f"Migration with ID {migration_id} not found"
            }
        except Exception as e:
            logger.error(f"Error approving migration: {str(e)}")
            return {
                "success": False,
                "message": f"Error approving migration: {str(e)}"
            }
    
    def reject_migration(self, migration_id: str) -> Dict[str, Any]:
        """
        Reject a pending migration.
        
        Args:
            migration_id: ID of the pending migration
            
        Returns:
            Dict with operation result
        """
        try:
            for i, migration in enumerate(self.pending_migrations):
                if migration["id"] == migration_id:
                    # Remove from pending list
                    rejected = self.pending_migrations.pop(i)
                    
                    # Add to history as rejected
                    rejected["status"] = "rejected"
                    rejected["completion_time"] = datetime.now().isoformat()
                    self.migration_history.append(rejected)
                    
                    return {
                        "success": True,
                        "message": f"Migration {migration_id} rejected"
                    }
            
            return {
                "success": False,
                "message": f"Migration with ID {migration_id} not found"
            }
        except Exception as e:
            logger.error(f"Error rejecting migration: {str(e)}")
            return {
                "success": False,
                "message": f"Error rejecting migration: {str(e)}"
            }
    
    def _monitoring_loop(self):
        """Main monitoring loop for automatic migrations."""
        while self.running:
            try:
                # Check if we're in the preferred migration hours
                current_hour = datetime.now().hour
                in_preferred_hours = current_hour in self.config['preferred_migration_hours']
                
                # Only perform migrations during preferred hours or if we have high load
                if in_preferred_hours or self._check_for_high_load():
                    self._analyze_and_migrate()
                
                # Sleep until next check
                time.sleep(self.config['check_interval'])
            except Exception as e:
                logger.error(f"Error in AI migration monitoring loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying
    
    def _check_for_high_load(self) -> bool:
        """Check if any node has high load that requires immediate attention."""
        try:
            # Get cluster status
            nodes_result = self.api.api_request('GET', 'nodes')
            if not nodes_result['success']:
                return False
            
            for node in nodes_result['data']:
                node_name = node['node']
                
                # Skip excluded nodes
                if node_name in self.config['exclude_nodes']:
                    continue
                
                # Get node status
                status_result = self.api.api_request('GET', f'nodes/{node_name}/status')
                if not status_result['success']:
                    continue
                
                status = status_result['data']
                
                # Check CPU load
                cpu_load = status.get('cpu', 0) * 100  # Convert to percentage
                if cpu_load > self.config['cpu_threshold_high']:
                    logger.info(f"Node {node_name} has high CPU load ({cpu_load:.1f}%)")
                    return True
                
                # Check memory usage
                memory_total = status.get('memory', {}).get('total', 0)
                memory_used = status.get('memory', {}).get('used', 0)
                if memory_total > 0:
                    memory_usage = (memory_used / memory_total) * 100
                    if memory_usage > self.config['memory_threshold_high']:
                        logger.info(f"Node {node_name} has high memory usage ({memory_usage:.1f}%)")
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for high load: {str(e)}")
            return False
    
    def _analyze_and_migrate(self):
        """Analyze cluster state and initiate migrations if needed."""
        try:
            # Get all nodes
            nodes_result = self.api.api_request('GET', 'nodes')
            if not nodes_result['success']:
                logger.error("Failed to get nodes")
                return
            
            nodes = [n for n in nodes_result['data'] if n['node'] not in self.config['exclude_nodes']]
            if len(nodes) < 2:
                logger.info("Not enough nodes for migration (minimum 2 required)")
                return
            
            # Collect node resource information
            node_resources = {}
            for node in nodes:
                node_name = node['node']
                status_result = self.api.api_request('GET', f'nodes/{node_name}/status')
                if not status_result['success']:
                    continue
                
                status = status_result['data']
                
                # Calculate current load
                cpu_load = status.get('cpu', 0) * 100  # Convert to percentage
                memory_total = status.get('memory', {}).get('total', 0)
                memory_used = status.get('memory', {}).get('used', 0)
                memory_usage = (memory_used / memory_total) * 100 if memory_total > 0 else 0
                
                # Get predictive load for next few hours
                prediction = self.predictive_analyzer.predict_node_load(node_name, 
                                                                       self.config['prediction_horizon'])
                
                node_resources[node_name] = {
                    "current": {
                        "cpu": cpu_load,
                        "memory": memory_usage
                    },
                    "predicted": prediction.get("predictions", {})
                }
            
            # Identify overloaded and underloaded nodes
            overloaded_nodes = []
            underloaded_nodes = []
            
            for node_name, resources in node_resources.items():
                current = resources["current"]
                predicted = resources.get("predicted", {})
                
                # Check if currently overloaded
                if (current["cpu"] > self.config['cpu_threshold_high'] or 
                    current["memory"] > self.config['memory_threshold_high']):
                    overloaded_nodes.append({
                        "node": node_name,
                        "resources": resources,
                        "reason": "current_high_load"
                    })
                
                # Check if predicted to be overloaded
                elif (predicted.get("cpu", {}).get("peak", 0) > self.config['cpu_threshold_high'] or 
                      predicted.get("memory", {}).get("peak", 0) > self.config['memory_threshold_high']):
                    overloaded_nodes.append({
                        "node": node_name,
                        "resources": resources,
                        "reason": "predicted_high_load"
                    })
                
                # Check if underloaded
                elif (current["cpu"] < self.config['cpu_threshold_low'] and 
                      current["memory"] < self.config['memory_threshold_low']):
                    underloaded_nodes.append({
                        "node": node_name,
                        "resources": resources,
                        "reason": "current_low_load"
                    })
            
            # Sort overloaded nodes by load (highest first)
            overloaded_nodes.sort(key=lambda n: max(n["resources"]["current"]["cpu"], 
                                                   n["resources"]["current"]["memory"]), 
                                  reverse=True)
            
            # Sort underloaded nodes by load (lowest first)
            underloaded_nodes.sort(key=lambda n: max(n["resources"]["current"]["cpu"], 
                                                    n["resources"]["current"]["memory"]))
            
            # Process migrations
            migrations_planned = 0
            
            # First, handle overloaded nodes
            for overloaded in overloaded_nodes:
                if migrations_planned >= self.config['max_migrations_per_run']:
                    break
                
                source_node = overloaded["node"]
                
                # Find VMs/containers to migrate
                vms_to_migrate = self._find_migration_candidates(source_node)
                
                for vm in vms_to_migrate:
                    if migrations_planned >= self.config['max_migrations_per_run']:
                        break
                    
                    # Find best target node
                    target_node = self._find_best_target_node(vm, underloaded_nodes, node_resources)
                    
                    if target_node:
                        # Plan migration
                        migration = self._plan_migration(vm, source_node, target_node, 
                                                        overloaded["reason"])
                        
                        if migration:
                            migrations_planned += 1
            
            # Then, consider consolidation if we have underloaded nodes and no overloaded ones
            if not overloaded_nodes and len(underloaded_nodes) > 1:
                # Find the most empty node to migrate VMs from
                source_node = underloaded_nodes[0]["node"]
                
                # Find VMs/containers to migrate
                vms_to_migrate = self._find_migration_candidates(source_node)
                
                # Skip the first node (source) when looking for targets
                potential_targets = [n for n in underloaded_nodes[1:]]
                
                for vm in vms_to_migrate:
                    if migrations_planned >= self.config['max_migrations_per_run']:
                        break
                    
                    # Find best target node
                    target_node = self._find_best_target_node(vm, potential_targets, node_resources)
                    
                    if target_node:
                        # Plan migration
                        migration = self._plan_migration(vm, source_node, target_node, "consolidation")
                        
                        if migration:
                            migrations_planned += 1
        
        except Exception as e:
            logger.error(f"Error in analyze_and_migrate: {str(e)}")
    
    def _find_migration_candidates(self, node_name: str) -> List[Dict]:
        """Find VMs/containers that are candidates for migration from a node."""
        candidates = []
        
        try:
            # Get VMs on the node
            vms_result = self.api.api_request('GET', f'nodes/{node_name}/qemu')
            if vms_result['success']:
                for vm in vms_result['data']:
                    vm_id = vm['vmid']
                    
                    # Skip excluded VMs
                    if str(vm_id) in self.config['exclude_vms']:
                        continue
                    
                    # Skip if recently migrated
                    if (vm_id in self.last_migration_time and 
                        (datetime.now() - self.last_migration_time[vm_id]).total_seconds() < 
                        self.config['migration_cooldown']):
                        continue
                    
                    # Get VM status and resource usage
                    status_result = self.api.api_request('GET', 
                                                        f'nodes/{node_name}/qemu/{vm_id}/status/current')
                    if not status_result['success']:
                        continue
                    
                    status = status_result['data']
                    
                    # Only consider running VMs
                    if status['status'] != 'running':
                        continue
                    
                    candidates.append({
                        "id": vm_id,
                        "name": vm.get('name', f"VM {vm_id}"),
                        "type": "vm",
                        "cpu": status.get('cpu', 0) * 100,  # Convert to percentage
                        "memory": status.get('mem', 0),
                        "disk": sum(disk.get('size', 0) for disk in status.get('disks', {}).values())
                    })
            
            # Get containers on the node
            ct_result = self.api.api_request('GET', f'nodes/{node_name}/lxc')
            if ct_result['success']:
                for ct in ct_result['data']:
                    ct_id = ct['vmid']
                    
                    # Skip excluded containers
                    if str(ct_id) in self.config['exclude_vms']:
                        continue
                    
                    # Skip if recently migrated
                    if (ct_id in self.last_migration_time and 
                        (datetime.now() - self.last_migration_time[ct_id]).total_seconds() < 
                        self.config['migration_cooldown']):
                        continue
                    
                    # Get container status and resource usage
                    status_result = self.api.api_request('GET', 
                                                        f'nodes/{node_name}/lxc/{ct_id}/status/current')
                    if not status_result['success']:
                        continue
                    
                    status = status_result['data']
                    
                    # Only consider running containers
                    if status['status'] != 'running':
                        continue
                    
                    candidates.append({
                        "id": ct_id,
                        "name": ct.get('name', f"CT {ct_id}"),
                        "type": "ct",
                        "cpu": status.get('cpu', 0) * 100,  # Convert to percentage
                        "memory": status.get('mem', 0),
                        "disk": status.get('disk', 0)
                    })
            
            # Sort by resource usage (highest first)
            candidates.sort(key=lambda c: c["cpu"] + (c["memory"] / (1024*1024*10)), reverse=True)
            
            return candidates
        
        except Exception as e:
            logger.error(f"Error finding migration candidates: {str(e)}")
            return []
    
    def _find_best_target_node(self, vm: Dict, potential_targets: List[Dict], 
                              node_resources: Dict) -> Optional[str]:
        """Find the best target node for a VM migration."""
        if not potential_targets:
            return None
        
        best_node = None
        best_score = float('-inf')
        
        for target in potential_targets:
            node_name = target["node"]
            resources = node_resources[node_name]
            
            # Calculate how well this VM would fit on the target node
            current_cpu = resources["current"]["cpu"]
            current_memory = resources["current"]["memory"]
            
            # Estimate new load after migration
            new_cpu = current_cpu + vm["cpu"] * 0.01  # Adjust for percentage
            new_memory = current_memory + (vm["memory"] / (1024*1024)) * 0.01  # Adjust for percentage
            
            # Skip if this would overload the target
            if (new_cpu > self.config['cpu_threshold_high'] or 
                new_memory > self.config['memory_threshold_high']):
                continue
            
            # Calculate score (lower is better)
            # We want to balance load while keeping it under thresholds
            cpu_headroom = self.config['cpu_threshold_high'] - new_cpu
            memory_headroom = self.config['memory_threshold_high'] - new_memory
            
            # Score based on available headroom and balance
            score = min(cpu_headroom, memory_headroom) * 0.7 + (100 - abs(new_cpu - new_memory)) * 0.3
            
            if score > best_score:
                best_score = score
                best_node = node_name
        
        return best_node
    
    def _plan_migration(self, vm: Dict, source_node: str, target_node: str, 
                       reason: str) -> Optional[Dict]:
        """Plan a migration and add it to pending migrations."""
        try:
            migration_id = f"{int(time.time())}-{vm['id']}"
            
            migration = {
                "id": migration_id,
                "vm_id": vm["id"],
                "vm_name": vm["name"],
                "vm_type": vm["type"],
                "source_node": source_node,
                "target_node": target_node,
                "reason": reason,
                "creation_time": datetime.now().isoformat(),
                "status": "pending",
                "resources": {
                    "cpu": vm["cpu"],
                    "memory": vm["memory"],
                    "disk": vm["disk"]
                }
            }
            
            # If auto-approve is enabled, execute immediately
            if self.config['auto_approve']:
                return self._execute_migration(migration)
            
            # Otherwise, add to pending migrations
            self.pending_migrations.append(migration)
            logger.info(f"Planned migration: {vm['name']} from {source_node} to {target_node}")
            
            return migration
        
        except Exception as e:
            logger.error(f"Error planning migration: {str(e)}")
            return None
    
    def _execute_migration(self, migration: Dict) -> Dict[str, Any]:
        """Execute a planned migration."""
        try:
            vm_id = migration["vm_id"]
            source_node = migration["source_node"]
            target_node = migration["target_node"]
            vm_type = migration["vm_type"]
            
            logger.info(f"Executing migration: {migration['vm_name']} from {source_node} to {target_node}")
            
            # Execute migration based on VM type
            if vm_type == "vm":
                result = self.api.api_request('POST', 
                                             f'nodes/{source_node}/qemu/{vm_id}/migrate', 
                                             {'target': target_node, 'online': 1})
            else:  # Container
                result = self.api.api_request('POST', 
                                             f'nodes/{source_node}/lxc/{vm_id}/migrate', 
                                             {'target': target_node, 'restart': 1})
            
            # Update migration status
            migration["status"] = "success" if result["success"] else "failed"
            migration["completion_time"] = datetime.now().isoformat()
            migration["result"] = result
            
            # Add to history
            self.migration_history.append(migration)
            
            # Update last migration time
            if result["success"]:
                self.last_migration_time[vm_id] = datetime.now()
            
            return {
                "success": result["success"],
                "message": f"Migration of {migration['vm_name']} to {target_node} " + 
                          ("successful" if result["success"] else "failed"),
                "migration": migration
            }
        
        except Exception as e:
            logger.error(f"Error executing migration: {str(e)}")
            
            # Update migration status
            migration["status"] = "failed"
            migration["completion_time"] = datetime.now().isoformat()
            migration["error"] = str(e)
            
            # Add to history
            self.migration_history.append(migration)
            
            return {
                "success": False,
                "message": f"Error executing migration: {str(e)}",
                "migration": migration
            }
