"""
Storage management operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional

class StorageManager:
    def __init__(self, api):
        self.api = api

    def create_storage(self, node: str, name: str, storage_type: str, 
                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new storage
        
        Args:
            node: Node name
            name: Storage name
            storage_type: Storage type (dir, nfs, zfs, lvm, etc)
            config: Storage configuration
            
        Returns:
            Dict with operation result
        """
        # Prepare storage config
        storage_config = {
            'storage': name,
            'type': storage_type
        }
        storage_config.update(config)
        
        result = self.api.api_request('POST', f'nodes/{node}/storage', storage_config)
        
        if result['success']:
            return {
                "success": True,
                "message": f"Created {storage_type} storage {name}"
            }
        return result

    def create_zfs_pool(self, node: str, name: str, devices: List[str], 
                       raid_level: str = 'mirror') -> Dict[str, Any]:
        """Create ZFS storage pool
        
        Args:
            node: Node name
            name: Pool name
            devices: List of devices
            raid_level: RAID level (mirror, raidz, raidz2, etc)
            
        Returns:
            Dict with operation result
        """
        # Create ZFS pool command
        devices_str = ' '.join(devices)
        command = f'zpool create {name} {raid_level} {devices_str}'
        
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': command
        })
        
        if result['success']:
            # Create storage configuration
            storage_config = {
                'pool': name,
                'sparse': 1,
                'content': 'images,rootdir'
            }
            return self.create_storage(node, name, 'zfspool', storage_config)
        return result

    def create_lvm_group(self, node: str, name: str, devices: List[str]) -> Dict[str, Any]:
        """Create LVM volume group
        
        Args:
            node: Node name
            name: Volume group name
            devices: List of devices
            
        Returns:
            Dict with operation result
        """
        # Create physical volumes
        for device in devices:
            pv_result = self.api.api_request('POST', f'nodes/{node}/execute', {
                'command': f'pvcreate {device}'
            })
            if not pv_result['success']:
                return pv_result
                
        # Create volume group
        devices_str = ' '.join(devices)
        vg_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'vgcreate {name} {devices_str}'
        })
        
        if vg_result['success']:
            # Create storage configuration
            storage_config = {
                'vgname': name,
                'content': 'images,rootdir'
            }
            return self.create_storage(node, name, 'lvmthin', storage_config)
        return vg_result

    def create_nfs_storage(self, node: str, name: str, server: str, 
                          export: str, options: Optional[str] = None) -> Dict[str, Any]:
        """Create NFS storage
        
        Args:
            node: Node name
            name: Storage name
            server: NFS server address
            export: NFS export path
            options: Optional mount options
            
        Returns:
            Dict with operation result
        """
        storage_config = {
            'server': server,
            'export': export,
            'content': 'images,iso,vztmpl',
            'options': options if options else 'soft,tcp'
        }
        
        return self.create_storage(node, name, 'nfs', storage_config)

    def create_cifs_storage(self, node: str, name: str, server: str, 
                           share: str, username: str = None, 
                           password: str = None) -> Dict[str, Any]:
        """Create CIFS/SMB storage
        
        Args:
            node: Node name
            name: Storage name
            server: CIFS server address
            share: Share name
            username: Optional username
            password: Optional password
            
        Returns:
            Dict with operation result
        """
        storage_config = {
            'server': server,
            'share': share,
            'content': 'images,iso'
        }
        
        if username:
            storage_config['username'] = username
        if password:
            storage_config['password'] = password
            
        return self.create_storage(node, name, 'cifs', storage_config)

    def get_storage_info(self, node: str, storage: Optional[str] = None) -> Dict[str, Any]:
        """Get storage information
        
        Args:
            node: Node name
            storage: Optional specific storage name
            
        Returns:
            Dict with storage information
        """
        if storage:
            result = self.api.api_request('GET', f'nodes/{node}/storage/{storage}/status')
        else:
            result = self.api.api_request('GET', f'nodes/{node}/storage')
            
        if result['success']:
            return {
                "success": True,
                "storage": result['data']
            }
        return result

    def get_zfs_info(self, node: str, pool: Optional[str] = None) -> Dict[str, Any]:
        """Get ZFS information
        
        Args:
            node: Node name
            pool: Optional specific pool name
            
        Returns:
            Dict with ZFS information
        """
        command = 'zpool list -H -o name,size,alloc,free,frag,health'
        if pool:
            command += f' {pool}'
            
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': command
        })
        
        if result['success']:
            pools = []
            for line in result['data'].splitlines():
                if line.strip():
                    name, size, alloc, free, frag, health = line.split()
                    pools.append({
                        'name': name,
                        'size': size,
                        'allocated': alloc,
                        'free': free,
                        'fragmentation': frag,
                        'health': health
                    })
                    
            return {
                "success": True,
                "pools": pools
            }
        return result

    def get_lvm_info(self, node: str, vg: Optional[str] = None) -> Dict[str, Any]:
        """Get LVM information
        
        Args:
            node: Node name
            vg: Optional specific volume group name
            
        Returns:
            Dict with LVM information
        """
        command = 'vgs --noheadings -o vg_name,vg_size,vg_free'
        if vg:
            command += f' {vg}'
            
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': command
        })
        
        if result['success']:
            vgs = []
            for line in result['data'].splitlines():
                if line.strip():
                    name, size, free = line.split()
                    vgs.append({
                        'name': name,
                        'size': size,
                        'free': free
                    })
                    
            return {
                "success": True,
                "volume_groups": vgs
            }
        return result

    def delete_storage(self, node: str, storage: str) -> Dict[str, Any]:
        """Delete storage configuration
        
        Args:
            node: Node name
            storage: Storage name
            
        Returns:
            Dict with operation result
        """
        result = self.api.api_request('DELETE', f'nodes/{node}/storage/{storage}')
        
        if result['success']:
            return {
                "success": True,
                "message": f"Deleted storage {storage}"
            }
        return result

    def resize_storage(self, node: str, storage: str, size: str) -> Dict[str, Any]:
        """Resize storage
        
        Args:
            node: Node name
            storage: Storage name
            size: New size (e.g., '500G')
            
        Returns:
            Dict with operation result
        """
        # Get storage type
        info = self.get_storage_info(node, storage)
        if not info['success']:
            return info
            
        storage_type = info['storage'].get('type')
        
        if storage_type == 'zfspool':
            # ZFS online resize not supported, need to add devices
            return {
                "success": False,
                "message": "ZFS pool resize requires adding devices"
            }
        elif storage_type == 'lvmthin':
            # Resize LVM volume group
            result = self.api.api_request('POST', f'nodes/{node}/execute', {
                'command': f'lvextend -L {size} /dev/{storage}'
            })
            
            if result['success']:
                return {
                    "success": True,
                    "message": f"Resized LVM storage {storage} to {size}"
                }
            return result
        else:
            return {
                "success": False,
                "message": f"Resize not supported for storage type {storage_type}"
            }

    def check_storage_health(self, node: str, storage: str) -> Dict[str, Any]:
        """Check storage health
        
        Args:
            node: Node name
            storage: Storage name
            
        Returns:
            Dict with health status
        """
        # Get storage info
        info = self.get_storage_info(node, storage)
        if not info['success']:
            return info
            
        storage_type = info['storage'].get('type')
        health_checks = []
        
        if storage_type == 'zfspool':
            # Check ZFS pool health
            zfs_result = self.get_zfs_info(node, storage)
            if zfs_result['success'] and zfs_result['pools']:
                pool = zfs_result['pools'][0]
                health_checks.append({
                    'component': 'zfs_pool',
                    'status': pool['health'],
                    'fragmentation': pool['fragmentation']
                })
                
        elif storage_type in ['lvmthin', 'lvm']:
            # Check LVM health
            lvm_result = self.get_lvm_info(node, storage)
            if lvm_result['success'] and lvm_result['volume_groups']:
                vg = lvm_result['volume_groups'][0]
                health_checks.append({
                    'component': 'lvm_vg',
                    'status': 'OK' if float(vg['free'].rstrip('g')) > 0 else 'WARNING',
                    'free_space': vg['free']
                })
                
        # Check general storage status
        status = info['storage'].get('status', 'unknown')
        health_checks.append({
            'component': 'storage',
            'status': 'OK' if status == 'available' else 'ERROR',
            'state': status
        })
        
        return {
            "success": True,
            "health_checks": health_checks
        }