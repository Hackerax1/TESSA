"""
ZFS storage management operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional

class ZFSManager:
    def __init__(self, api):
        self.api = api

    def create_pool(self, node: str, name: str, devices: List[str], 
                   raid_level: str = 'mirror') -> Dict[str, Any]:
        """Create a ZFS storage pool
        
        Args:
            node: Node name
            name: Pool name
            devices: List of device paths
            raid_level: ZFS raid level (mirror, raidz, raidz2, etc.)
        
        Returns:
            Dict with operation result
        """
        # First check if devices exist
        devices_str = ' '.join(devices)
        create_cmd = f"zpool create {name} {raid_level} {devices_str}"
        
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': create_cmd
        })
        
        if result['success']:
            return {"success": True, "message": f"Created ZFS pool {name} on node {node}"}
        return result

    def list_pools(self, node: str) -> Dict[str, Any]:
        """List ZFS pools
        
        Args:
            node: Node name
        
        Returns:
            Dict with pool information
        """
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': 'zpool list -H -o name,size,alloc,free,capacity,health'
        })
        
        if not result['success']:
            return result
            
        pools = []
        for line in result['data'].splitlines():
            if line.strip():
                name, size, alloc, free, cap, health = line.split()
                pools.append({
                    'name': name,
                    'size': size,
                    'allocated': alloc,
                    'free': free,
                    'capacity': cap,
                    'health': health
                })
                
        return {
            "success": True, 
            "message": "ZFS pools", 
            "pools": pools
        }

    def list_datasets(self, node: str, pool: Optional[str] = None) -> Dict[str, Any]:
        """List ZFS datasets
        
        Args:
            node: Node name
            pool: Optional pool name to filter
        
        Returns:
            Dict with dataset information
        """
        cmd = 'zfs list -H -o name,used,avail,refer,mountpoint'
        if pool:
            cmd += f' {pool}'
            
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': cmd
        })
        
        if not result['success']:
            return result
            
        datasets = []
        for line in result['data'].splitlines():
            if line.strip():
                name, used, avail, refer, mount = line.split()
                datasets.append({
                    'name': name,
                    'used': used,
                    'available': avail,
                    'referenced': refer,
                    'mountpoint': mount
                })
                
        return {
            "success": True,
            "message": "ZFS datasets",
            "datasets": datasets
        }

    def create_dataset(self, node: str, name: str, options: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a ZFS dataset
        
        Args:
            node: Node name
            name: Dataset name
            options: Optional dataset properties
        
        Returns:
            Dict with operation result
        """
        create_cmd = f"zfs create"
        
        if options:
            for key, value in options.items():
                create_cmd += f" -o {key}={value}"
                
        create_cmd += f" {name}"
        
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': create_cmd
        })
        
        if result['success']:
            return {"success": True, "message": f"Created ZFS dataset {name}"}
        return result

    def set_properties(self, node: str, dataset: str, properties: Dict[str, str]) -> Dict[str, Any]:
        """Set ZFS dataset properties
        
        Args:
            node: Node name
            dataset: Dataset name
            properties: Properties to set
        
        Returns:
            Dict with operation result
        """
        results = []
        failed = []
        
        for prop, value in properties.items():
            result = self.api.api_request('POST', f'nodes/{node}/execute', {
                'command': f"zfs set {prop}={value} {dataset}"
            })
            
            if result['success']:
                results.append(f"{prop}={value}")
            else:
                failed.append({
                    'property': prop,
                    'value': value,
                    'error': result.get('message', 'Unknown error')
                })
                
        if failed:
            return {
                "success": False,
                "message": f"Failed to set {len(failed)} properties",
                "set": results,
                "failed": failed
            }
                
        return {
            "success": True, 
            "message": f"Set properties on {dataset}",
            "properties": results
        }

    def create_snapshot(self, node: str, dataset: str, snapshot_name: str, recursive: bool = False) -> Dict[str, Any]:
        """Create a ZFS snapshot
        
        Args:
            node: Node name
            dataset: Dataset name
            snapshot_name: Snapshot name
            recursive: Whether to create recursive snapshot
        
        Returns:
            Dict with operation result
        """
        cmd = "zfs snapshot"
        if recursive:
            cmd += " -r"
        cmd += f" {dataset}@{snapshot_name}"
        
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': cmd
        })
        
        if result['success']:
            return {"success": True, "message": f"Created snapshot {dataset}@{snapshot_name}"}
        return result

    def list_snapshots(self, node: str, dataset: Optional[str] = None) -> Dict[str, Any]:
        """List ZFS snapshots
        
        Args:
            node: Node name
            dataset: Optional dataset name to filter
        
        Returns:
            Dict with snapshot information
        """
        cmd = 'zfs list -t snapshot -H -o name,used,refer,creation'
        if dataset:
            cmd += f' {dataset}'
            
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': cmd
        })
        
        if not result['success']:
            return result
            
        snapshots = []
        for line in result['data'].splitlines():
            if line.strip():
                name, used, refer, creation = line.split()
                snapshots.append({
                    'name': name,
                    'used': used,
                    'referenced': refer,
                    'creation': creation
                })
                
        return {
            "success": True,
            "message": "ZFS snapshots",
            "snapshots": snapshots
        }

    def delete_snapshot(self, node: str, snapshot: str, recursive: bool = False) -> Dict[str, Any]:
        """Delete a ZFS snapshot
        
        Args:
            node: Node name
            snapshot: Snapshot name (dataset@snapshot)
            recursive: Whether to delete recursively
        
        Returns:
            Dict with operation result
        """
        cmd = "zfs destroy"
        if recursive:
            cmd += " -r"
        cmd += f" {snapshot}"
        
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': cmd
        })
        
        if result['success']:
            return {"success": True, "message": f"Deleted snapshot {snapshot}"}
        return result

    def rollback_snapshot(self, node: str, snapshot: str, force: bool = False) -> Dict[str, Any]:
        """Rollback to a ZFS snapshot
        
        Args:
            node: Node name
            snapshot: Snapshot name (dataset@snapshot)
            force: Whether to force rollback, destroying later snapshots
        
        Returns:
            Dict with operation result
        """
        cmd = "zfs rollback"
        if force:
            cmd += " -r"
        cmd += f" {snapshot}"
        
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': cmd
        })
        
        if result['success']:
            return {"success": True, "message": f"Rolled back to snapshot {snapshot}"}
        return result

    def setup_auto_snapshots(self, node: str, dataset: str, schedule: str = 'hourly') -> Dict[str, Any]:
        """Configure automatic snapshots
        
        Args:
            node: Node name
            dataset: Dataset name
            schedule: Schedule type (hourly, daily, weekly, monthly)
        
        Returns:
            Dict with operation result
        """
        # Setup zfs-auto-snapshot
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f"zfs set com.sun:auto-snapshot={schedule} {dataset}"
        })
        
        if result['success']:
            return {"success": True, "message": f"Configured auto-snapshots for {dataset}"}
        return result

    def get_pool_status(self, node: str, pool: str) -> Dict[str, Any]:
        """Get detailed pool status
        
        Args:
            node: Node name
            pool: Pool name
        
        Returns:
            Dict with pool status
        """
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f"zpool status {pool}"
        })
        
        if not result['success']:
            return result
            
        return {
            "success": True,
            "message": f"Status for pool {pool}",
            "status": result['data']
        }

    def scrub_pool(self, node: str, pool: str) -> Dict[str, Any]:
        """Start pool scrub
        
        Args:
            node: Node name
            pool: Pool name
        
        Returns:
            Dict with operation result
        """
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f"zpool scrub {pool}"
        })
        
        if result['success']:
            return {"success": True, "message": f"Started scrub on pool {pool}"}
        return result

    def get_scrub_status(self, node: str, pool: str) -> Dict[str, Any]:
        """Get pool scrub status
        
        Args:
            node: Node name
            pool: Pool name
        
        Returns:
            Dict with scrub status
        """
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f"zpool status {pool}"
        })
        
        if not result['success']:
            return result
            
        # Parse scrub status from pool status output
        status = result['data']
        scrub_info = {}
        
        for line in status.splitlines():
            if 'scan:' in line:
                scrub_info['status'] = line.strip()
            elif 'scrub in progress' in line:
                # Parse progress information
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'done,':
                        scrub_info['progress'] = parts[i-1]
                    elif part == 'remaining,':
                        scrub_info['remaining'] = f"{parts[i-2]} {parts[i-1]}"
                        
        return {
            "success": True,
            "message": f"Scrub status for pool {pool}",
            "scrub": scrub_info
        }

    def create_mirror(self, node: str, pool: str, devices: List[str]) -> Dict[str, Any]:
        """Create a mirror in an existing pool
        
        Args:
            node: Node name
            pool: Pool name
            devices: List of device paths
        
        Returns:
            Dict with operation result
        """
        devices_str = ' '.join(devices)
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f"zpool add {pool} mirror {devices_str}"
        })
        
        if result['success']:
            return {"success": True, "message": f"Added mirror to pool {pool}"}
        return result

    def replace_device(self, node: str, pool: str, old_device: str, new_device: str) -> Dict[str, Any]:
        """Replace a device in a pool
        
        Args:
            node: Node name
            pool: Pool name
            old_device: Path to old device
            new_device: Path to new device
        
        Returns:
            Dict with operation result
        """
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f"zpool replace {pool} {old_device} {new_device}"
        })
        
        if result['success']:
            return {"success": True, "message": f"Replacing device in pool {pool}"}
        return result

    def get_device_health(self, node: str, device: str) -> Dict[str, Any]:
        """Get SMART health information for a device
        
        Args:
            node: Node name
            device: Device path
        
        Returns:
            Dict with device health information
        """
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f"smartctl -H {device}"
        })
        
        if not result['success']:
            return result
            
        return {
            "success": True,
            "message": f"Health status for device {device}",
            "health": result['data']
        }