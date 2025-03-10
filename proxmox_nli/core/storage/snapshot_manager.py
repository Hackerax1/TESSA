"""
Snapshot manager module for Proxmox NLI.
Handles VM snapshots for quick point-in-time recovery.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SnapshotManager:
    def __init__(self, api):
        self.api = api
    
    def list_snapshots(self, vm_id: str, node: str = None) -> Dict:
        """List all snapshots for a VM"""
        try:
            # If node is not provided, try to find it
            if not node:
                result = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
                if not result['success'] or not result['data']:
                    return {
                        "success": False,
                        "message": f"VM {vm_id} not found"
                    }
                node = result['data'][0]['node']
                
            # Get snapshots for the VM
            result = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/snapshot')
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to list snapshots: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Snapshots for VM {vm_id} retrieved successfully",
                "snapshots": result['data']
            }
            
        except Exception as e:
            logger.error(f"Error listing snapshots: {str(e)}")
            return {
                "success": False,
                "message": f"Error listing snapshots: {str(e)}"
            }
    
    def create_snapshot(self, vm_id: str, name: str, description: str = None, include_ram: bool = False, node: str = None) -> Dict:
        """Create a snapshot of a VM"""
        try:
            # If node is not provided, try to find it
            if not node:
                result = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
                if not result['success'] or not result['data']:
                    return {
                        "success": False,
                        "message": f"VM {vm_id} not found"
                    }
                node = result['data'][0]['node']
            
            # Create parameters for snapshot
            params = {
                'snapname': name,
                'vmstate': 1 if include_ram else 0
            }
            
            if description:
                params['description'] = description
            
            # Create snapshot
            result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/snapshot', params)
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to create snapshot: {result.get('message', 'Unknown error')}"
                }
                
            # Wait for operation to complete (UPID task)
            task_id = result.get('data')
            if task_id:
                task_status = self.api.wait_for_task(node, task_id)
                if not task_status['success']:
                    return {
                        "success": False,
                        "message": f"Snapshot creation failed: {task_status.get('message', 'Task failed')}"
                    }
            
            return {
                "success": True,
                "message": f"Snapshot '{name}' created successfully for VM {vm_id}",
                "task_id": task_id
            }
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating snapshot: {str(e)}"
            }
    
    def delete_snapshot(self, vm_id: str, snapshot_name: str, node: str = None) -> Dict:
        """Delete a snapshot"""
        try:
            # If node is not provided, try to find it
            if not node:
                result = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
                if not result['success'] or not result['data']:
                    return {
                        "success": False,
                        "message": f"VM {vm_id} not found"
                    }
                node = result['data'][0]['node']
            
            # Delete the snapshot
            result = self.api.api_request('DELETE', f'nodes/{node}/qemu/{vm_id}/snapshot/{snapshot_name}')
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to delete snapshot: {result.get('message', 'Unknown error')}"
                }
                
            # Wait for operation to complete (UPID task)
            task_id = result.get('data')
            if task_id:
                task_status = self.api.wait_for_task(node, task_id)
                if not task_status['success']:
                    return {
                        "success": False,
                        "message": f"Snapshot deletion failed: {task_status.get('message', 'Task failed')}"
                    }
            
            return {
                "success": True,
                "message": f"Snapshot '{snapshot_name}' deleted successfully from VM {vm_id}",
                "task_id": task_id
            }
            
        except Exception as e:
            logger.error(f"Error deleting snapshot: {str(e)}")
            return {
                "success": False,
                "message": f"Error deleting snapshot: {str(e)}"
            }
    
    def rollback_snapshot(self, vm_id: str, snapshot_name: str, node: str = None) -> Dict:
        """Rollback a VM to a snapshot"""
        try:
            # If node is not provided, try to find it
            if not node:
                result = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
                if not result['success'] or not result['data']:
                    return {
                        "success": False,
                        "message": f"VM {vm_id} not found"
                    }
                node = result['data'][0]['node']
            
            # Check VM status
            vm_status = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/status/current')
            if vm_status['success'] and vm_status['data']['status'] == 'running':
                return {
                    "success": False,
                    "message": "Cannot rollback while VM is running. Please stop the VM first."
                }
            
            # Rollback to the snapshot
            result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/snapshot/{snapshot_name}/rollback')
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to rollback snapshot: {result.get('message', 'Unknown error')}"
                }
                
            # Wait for operation to complete (UPID task)
            task_id = result.get('data')
            if task_id:
                task_status = self.api.wait_for_task(node, task_id)
                if not task_status['success']:
                    return {
                        "success": False,
                        "message": f"Snapshot rollback failed: {task_status.get('message', 'Task failed')}"
                    }
            
            return {
                "success": True,
                "message": f"VM {vm_id} rolled back to snapshot '{snapshot_name}' successfully",
                "task_id": task_id
            }
            
        except Exception as e:
            logger.error(f"Error rolling back snapshot: {str(e)}")
            return {
                "success": False,
                "message": f"Error rolling back snapshot: {str(e)}"
            }
    
    def get_snapshot_details(self, vm_id: str, snapshot_name: str, node: str = None) -> Dict:
        """Get details of a specific snapshot"""
        try:
            # If node is not provided, try to find it
            if not node:
                result = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
                if not result['success'] or not result['data']:
                    return {
                        "success": False,
                        "message": f"VM {vm_id} not found"
                    }
                node = result['data'][0]['node']
            
            # Get snapshot details
            result = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/snapshot/{snapshot_name}/config')
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to get snapshot details: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Snapshot '{snapshot_name}' details retrieved successfully",
                "snapshot": result['data']
            }
            
        except Exception as e:
            logger.error(f"Error getting snapshot details: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting snapshot details: {str(e)}"
            }
    
    def create_scheduled_snapshots(self, vm_id: str, schedule: Dict, node: str = None) -> Dict:
        """Configure scheduled snapshots for a VM"""
        try:
            # If node is not provided, try to find it
            if not node:
                result = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
                if not result['success'] or not result['data']:
                    return {
                        "success": False,
                        "message": f"VM {vm_id} not found"
                    }
                node = result['data'][0]['node']
            
            # Format schedule according to Proxmox cron format
            # schedule should contain: minute, hour, day, month, dayofweek
            cron_format = f"{schedule.get('minute', '*')} {schedule.get('hour', '*')} {schedule.get('day', '*')} "
            cron_format += f"{schedule.get('month', '*')} {schedule.get('dayofweek', '*')}"
            
            # Setup snapshot job
            snapshot_name = schedule.get('name', 'auto-snap-')
            if snapshot_name == 'auto-snap-':
                snapshot_name += "%Y%m%d-%H%M%S"
            
            params = {
                'snapname': snapshot_name,
                'schedule': cron_format,
                'enabled': 1,
                'vmid': vm_id
            }
            
            if 'description' in schedule:
                params['description'] = schedule['description']
            
            if 'retention' in schedule:
                params['maxfiles'] = schedule['retention']
                
            if 'include_ram' in schedule:
                params['vmstate'] = 1 if schedule['include_ram'] else 0
            
            # Use vzdump API for scheduled snapshots
            result = self.api.api_request('POST', f'nodes/{node}/vzdump', params)
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to configure scheduled snapshots: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Scheduled snapshots configured successfully for VM {vm_id}",
                "schedule": cron_format,
                "snapshot_name": snapshot_name
            }
            
        except Exception as e:
            logger.error(f"Error configuring scheduled snapshots: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring scheduled snapshots: {str(e)}"
            }
    
    def create_bulk_snapshots(self, vm_ids: List[str], name_prefix: str = None, description: str = None, include_ram: bool = False) -> Dict:
        """Create snapshots for multiple VMs at once"""
        try:
            results = {}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name_prefix = name_prefix or f"bulk-snap-{timestamp}"
            
            for vm_id in vm_ids:
                snapshot_name = f"{name_prefix}-{vm_id}"
                result = self.create_snapshot(
                    vm_id=vm_id,
                    name=snapshot_name, 
                    description=description,
                    include_ram=include_ram
                )
                results[vm_id] = result
            
            # Check if all snapshots were successful
            all_success = all(result['success'] for result in results.values())
            
            return {
                "success": all_success,
                "message": f"Created snapshots for {len(vm_ids)} VMs" if all_success else "Some snapshots failed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error creating bulk snapshots: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating bulk snapshots: {str(e)}"
            }
    
    def restore_from_snapshot(self, vm_id: str, snapshot_name: str, target_vm_id: str = None, target_node: str = None, node: str = None) -> Dict:
        """Restore a VM from a snapshot to a new VM"""
        try:
            # If node is not provided, try to find it
            if not node:
                result = self.api.api_request('GET', f'cluster/resources?type=vm&vmid={vm_id}')
                if not result['success'] or not result['data']:
                    return {
                        "success": False,
                        "message": f"VM {vm_id} not found"
                    }
                node = result['data'][0]['node']
            
            if target_vm_id is None:
                # Rollback the existing VM to the snapshot
                return self.rollback_snapshot(vm_id, snapshot_name, node)
            else:
                # Clone to a new VM from the snapshot
                target_node = target_node or node
                
                # First get the snapshot config
                result = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/snapshot/{snapshot_name}/config')
                if not result['success']:
                    return {
                        "success": False,
                        "message": f"Failed to get snapshot config: {result.get('message', 'Unknown error')}"
                    }
                
                # Create a new VM with the snapshot
                clone_params = {
                    'newid': target_vm_id,
                    'name': f"clone-{vm_id}-{snapshot_name}",
                    'target': target_node,
                    'full': 1,
                    'snapshot': snapshot_name
                }
                
                result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/clone', clone_params)
                
                if not result['success']:
                    return {
                        "success": False,
                        "message": f"Failed to clone VM from snapshot: {result.get('message', 'Unknown error')}"
                    }
                    
                # Wait for clone operation to complete
                task_id = result.get('data')
                if task_id:
                    task_status = self.api.wait_for_task(node, task_id)
                    if not task_status['success']:
                        return {
                            "success": False,
                            "message": f"VM clone from snapshot failed: {task_status.get('message', 'Task failed')}"
                        }
                
                return {
                    "success": True,
                    "message": f"VM {vm_id} restored from snapshot '{snapshot_name}' to new VM {target_vm_id}",
                    "task_id": task_id
                }
            
        except Exception as e:
            logger.error(f"Error restoring from snapshot: {str(e)}")
            return {
                "success": False,
                "message": f"Error restoring from snapshot: {str(e)}"
            }
    
    def create_snapshot_policy(self, vm_ids: List[str], policy: Dict) -> Dict:
        """Create a snapshot policy for multiple VMs"""
        try:
            policy_results = {}
            
            # Process each schedule in the policy
            for schedule_type, schedule in policy.get('schedules', {}).items():
                # Set default schedule values
                schedule_config = {
                    'name': f"auto-{schedule_type}-%Y%m%d-%H%M%S",
                    'description': f"Automated {schedule_type} snapshot",
                    'retention': policy.get('retention', {}).get(schedule_type, 7),
                    'include_ram': policy.get('include_ram', False)
                }
                
                # Add time parameters based on schedule type
                if schedule_type == 'hourly':
                    schedule_config.update({
                        'minute': '0',
                        'hour': '*',
                        'day': '*',
                        'month': '*',
                        'dayofweek': '*'
                    })
                elif schedule_type == 'daily':
                    schedule_config.update({
                        'minute': '0',
                        'hour': '0',
                        'day': '*',
                        'month': '*',
                        'dayofweek': '*'
                    })
                elif schedule_type == 'weekly':
                    schedule_config.update({
                        'minute': '0',
                        'hour': '0',
                        'day': '*',
                        'month': '*',
                        'dayofweek': '0'  # Sunday
                    })
                elif schedule_type == 'monthly':
                    schedule_config.update({
                        'minute': '0',
                        'hour': '0',
                        'day': '1',
                        'month': '*',
                        'dayofweek': '*'
                    })
                
                # Override with custom schedule values if provided
                schedule_config.update(schedule)
                
                # Apply the schedule to each VM
                for vm_id in vm_ids:
                    result = self.create_scheduled_snapshots(vm_id, schedule_config)
                    
                    if vm_id not in policy_results:
                        policy_results[vm_id] = {}
                    
                    policy_results[vm_id][schedule_type] = result
            
            # Check if all schedules were successful
            all_success = all(
                all(sched['success'] for sched in vm_results.values())
                for vm_results in policy_results.values()
            )
            
            return {
                "success": all_success,
                "message": f"Snapshot policy applied to {len(vm_ids)} VMs" if all_success else "Some policies failed",
                "results": policy_results
            }
            
        except Exception as e:
            logger.error(f"Error creating snapshot policy: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating snapshot policy: {str(e)}"
            }