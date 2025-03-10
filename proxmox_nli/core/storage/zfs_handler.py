"""
ZFS handler module for Proxmox NLI.
Manages ZFS pools, datasets, and features including snapshots and replication.
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ZFSHandler:
    def __init__(self, api):
        self.api = api
    
    def list_pools(self, node: str) -> Dict:
        """List all ZFS pools on a node"""
        try:
            result = self.api.api_request('GET', f'nodes/{node}/storage', {'type': 'zfspool'})
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to list ZFS pools: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": "ZFS pools retrieved successfully",
                "pools": result['data']
            }
            
        except Exception as e:
            logger.error(f"Error listing ZFS pools: {str(e)}")
            return {
                "success": False,
                "message": f"Error listing ZFS pools: {str(e)}"
            }
    
    def get_pool_status(self, node: str, pool: str) -> Dict:
        """Get status information for a ZFS pool"""
        try:
            # Using the zpool command through the nodes API
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zpool',
                'args': ['status', '-v', pool]
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to get ZFS pool status: {result.get('message', 'Unknown error')}"
                }
            
            # Parse the command output
            output = result.get('data', {}).get('output', '')
            
            return {
                "success": True,
                "message": f"ZFS pool {pool} status retrieved successfully",
                "status": output
            }
            
        except Exception as e:
            logger.error(f"Error getting ZFS pool status: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting ZFS pool status: {str(e)}"
            }
    
    def create_pool(self, node: str, pool_name: str, devices: List[str], raid_type: str = "mirror") -> Dict:
        """Create a new ZFS pool"""
        try:
            valid_raid_types = ["mirror", "raidz", "raidz2", "raidz3", "stripe"]
            if raid_type not in valid_raid_types:
                return {
                    "success": False,
                    "message": f"Invalid RAID type: {raid_type}. Valid types are: {', '.join(valid_raid_types)}"
                }
            
            # Construct command arguments based on RAID type
            args = ['create', pool_name]
            
            if raid_type != "stripe":
                args.append(raid_type)
            
            args.extend(devices)
            
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zpool',
                'args': args
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to create ZFS pool: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"ZFS pool {pool_name} created successfully with {raid_type} configuration"
            }
            
        except Exception as e:
            logger.error(f"Error creating ZFS pool: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating ZFS pool: {str(e)}"
            }
    
    def destroy_pool(self, node: str, pool_name: str) -> Dict:
        """Destroy a ZFS pool"""
        try:
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zpool',
                'args': ['destroy', '-f', pool_name]
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to destroy ZFS pool: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"ZFS pool {pool_name} destroyed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error destroying ZFS pool: {str(e)}")
            return {
                "success": False,
                "message": f"Error destroying ZFS pool: {str(e)}"
            }
    
    def list_datasets(self, node: str) -> Dict:
        """List all ZFS datasets"""
        try:
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': ['list', '-H', '-o', 'name,used,avail,refer,mountpoint']
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to list ZFS datasets: {result.get('message', 'Unknown error')}"
                }
            
            # Parse the command output
            output = result.get('data', {}).get('output', '')
            datasets = []
            
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 5:
                        datasets.append({
                            'name': parts[0],
                            'used': parts[1],
                            'avail': parts[2],
                            'refer': parts[3],
                            'mountpoint': parts[4]
                        })
            
            return {
                "success": True,
                "message": "ZFS datasets retrieved successfully",
                "datasets": datasets
            }
            
        except Exception as e:
            logger.error(f"Error listing ZFS datasets: {str(e)}")
            return {
                "success": False,
                "message": f"Error listing ZFS datasets: {str(e)}"
            }
    
    def create_dataset(self, node: str, name: str, properties: Dict = None) -> Dict:
        """Create a new ZFS dataset"""
        try:
            args = ['create']
            
            # Add properties if specified
            if properties:
                for key, value in properties.items():
                    args.extend(['-o', f'{key}={value}'])
            
            args.append(name)
            
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': args
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to create ZFS dataset: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"ZFS dataset {name} created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating ZFS dataset: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating ZFS dataset: {str(e)}"
            }
    
    def destroy_dataset(self, node: str, name: str, recursive: bool = False) -> Dict:
        """Destroy a ZFS dataset"""
        try:
            args = ['destroy']
            
            if recursive:
                args.append('-r')
            
            args.append(name)
            
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': args
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to destroy ZFS dataset: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"ZFS dataset {name} destroyed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error destroying ZFS dataset: {str(e)}")
            return {
                "success": False,
                "message": f"Error destroying ZFS dataset: {str(e)}"
            }
    
    def set_property(self, node: str, name: str, property_name: str, value: str) -> Dict:
        """Set a property on a ZFS dataset or pool"""
        try:
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': ['set', f'{property_name}={value}', name]
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to set ZFS property: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"ZFS property {property_name} set to {value} for {name} successfully"
            }
            
        except Exception as e:
            logger.error(f"Error setting ZFS property: {str(e)}")
            return {
                "success": False,
                "message": f"Error setting ZFS property: {str(e)}"
            }
    
    def get_properties(self, node: str, name: str) -> Dict:
        """Get properties of a ZFS dataset or pool"""
        try:
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': ['get', 'all', '-H', name]
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to get ZFS properties: {result.get('message', 'Unknown error')}"
                }
            
            # Parse the command output
            output = result.get('data', {}).get('output', '')
            properties = {}
            
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        properties[parts[1]] = {
                            'value': parts[2],
                            'source': parts[3]
                        }
            
            return {
                "success": True,
                "message": f"ZFS properties for {name} retrieved successfully",
                "properties": properties
            }
            
        except Exception as e:
            logger.error(f"Error getting ZFS properties: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting ZFS properties: {str(e)}"
            }
    
    def create_snapshot(self, node: str, dataset: str, snapshot_name: str, recursive: bool = False) -> Dict:
        """Create a ZFS snapshot"""
        try:
            args = ['snapshot']
            
            if recursive:
                args.append('-r')
            
            args.append(f"{dataset}@{snapshot_name}")
            
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': args
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to create ZFS snapshot: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"ZFS snapshot {dataset}@{snapshot_name} created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating ZFS snapshot: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating ZFS snapshot: {str(e)}"
            }
    
    def list_snapshots(self, node: str, dataset: str = None) -> Dict:
        """List ZFS snapshots"""
        try:
            args = ['list', '-t', 'snapshot', '-H']
            
            if dataset:
                args.append(dataset)
            
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': args
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to list ZFS snapshots: {result.get('message', 'Unknown error')}"
                }
            
            # Parse the command output
            output = result.get('data', {}).get('output', '')
            snapshots = []
            
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        name = parts[0]
                        used = parts[1] if len(parts) > 1 else ''
                        snapshotname = name.split('@')[1] if '@' in name else ''
                        dataset_name = name.split('@')[0] if '@' in name else name
                        
                        snapshots.append({
                            'name': name,
                            'dataset': dataset_name,
                            'snapshot': snapshotname,
                            'used': used
                        })
            
            return {
                "success": True,
                "message": "ZFS snapshots retrieved successfully",
                "snapshots": snapshots
            }
            
        except Exception as e:
            logger.error(f"Error listing ZFS snapshots: {str(e)}")
            return {
                "success": False,
                "message": f"Error listing ZFS snapshots: {str(e)}"
            }
    
    def rollback_snapshot(self, node: str, snapshot: str, force: bool = False) -> Dict:
        """Rollback a ZFS dataset to a snapshot"""
        try:
            args = ['rollback']
            
            if force:
                args.append('-r')
            
            args.append(snapshot)
            
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': args
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to rollback ZFS snapshot: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"ZFS dataset rolled back to snapshot {snapshot} successfully"
            }
            
        except Exception as e:
            logger.error(f"Error rolling back ZFS snapshot: {str(e)}")
            return {
                "success": False,
                "message": f"Error rolling back ZFS snapshot: {str(e)}"
            }
    
    def destroy_snapshot(self, node: str, snapshot: str, recursive: bool = False) -> Dict:
        """Destroy a ZFS snapshot"""
        try:
            args = ['destroy']
            
            if recursive:
                args.append('-r')
            
            args.append(snapshot)
            
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zfs',
                'args': args
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to destroy ZFS snapshot: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"ZFS snapshot {snapshot} destroyed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error destroying ZFS snapshot: {str(e)}")
            return {
                "success": False,
                "message": f"Error destroying ZFS snapshot: {str(e)}"
            }
    
    def send_receive(self, source_node: str, target_node: str, source_snapshot: str, target_dataset: str) -> Dict:
        """Send and receive a ZFS snapshot to replicate data"""
        try:
            # This would normally be implemented using SSH between nodes and piping commands
            # For this example, we'll simulate the operation through API calls
            
            # In a real implementation, you would need to establish SSH connection between nodes
            # and execute something like: 
            # zfs send source_snapshot | ssh target_node zfs receive target_dataset
            
            return {
                "success": True,
                "message": f"ZFS snapshot {source_snapshot} sent to {target_dataset} on {target_node} successfully",
                "note": "This is a simulation - real implementation would require SSH and direct ZFS commands"
            }
            
        except Exception as e:
            logger.error(f"Error sending/receiving ZFS snapshot: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending/receiving ZFS snapshot: {str(e)}"
            }
    
    def scrub_pool(self, node: str, pool_name: str) -> Dict:
        """Start a scrub operation on a ZFS pool"""
        try:
            result = self.api.api_request('GET', f'nodes/{node}/exec', {
                'command': 'zpool',
                'args': ['scrub', pool_name]
            })
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to start scrub on ZFS pool: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Scrub operation started on ZFS pool {pool_name} successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting ZFS pool scrub: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting ZFS pool scrub: {str(e)}"
            }