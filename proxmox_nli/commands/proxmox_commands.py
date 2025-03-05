import os
import subprocess
from datetime import datetime

class ProxmoxCommands:
    def __init__(self, api):
        self.api = api

    def list_vms(self):
        """List all VMs"""
        result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if result['success']:
            vms = []
            for vm in result['data']:
                vms.append({
                    'id': vm['vmid'],
                    'name': vm.get('name', f"VM {vm['vmid']}"),
                    'status': vm['status'],
                    'node': vm['node'],
                    'cpu': int(vm.get('cpu', 0)),  # Convert to integer
                    'memory': vm.get('maxmem', 0) / (1024*1024),  # Convert to MB
                    'disk': vm.get('maxdisk', 0) / (1024*1024*1024)  # Convert to GB
                })
            return {"success": True, "message": "Found VMs", "vms": vms}
        else:
            return result
    
    def start_vm(self, vm_id):
        """Start a VM"""
        # First, we need to find which node the VM is on
        vm_info = self.get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
        
        node = vm_info['node']
        result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/status/start')
        if result['success']:
            return {"success": True, "message": f"VM {vm_id} started successfully"}
        else:
            return result
    
    def stop_vm(self, vm_id):
        """Stop a VM"""
        vm_info = self.get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
        
        node = vm_info['node']
        result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/status/stop')
        if result['success']:
            return {"success": True, "message": f"VM {vm_id} stopped successfully"}
        else:
            return result
    
    def restart_vm(self, vm_id):
        """Restart a VM"""
        vm_info = self.get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
        
        node = vm_info['node']
        result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/status/reset')
        if result['success']:
            return {"success": True, "message": f"VM {vm_id} restarted successfully"}
        else:
            return result
    
    def get_vm_status(self, vm_id):
        """Get the status of a VM"""
        vm_info = self.get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
        
        node = vm_info['node']
        result = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/status/current')
        if result['success']:
            status = result['data']
            return {
                "success": True,
                "message": f"VM {vm_id} status",
                "status": {
                    "status": status['status'],
                    "cpu": status.get('cpu', 0),
                    "memory": status.get('mem', 0) / (1024*1024),  # Convert to MB
                    "disk": sum(disk.get('size', 0) for disk in status.get('disks', {}).values()) / (1024*1024*1024)  # Convert to GB
                }
            }
        else:
            return result
    
    def create_vm(self, params):
        """Create a new VM with the given parameters"""
        # For simplicity, we'll create it on the first available node
        nodes_result = self.api.api_request('GET', 'nodes')
        if not nodes_result['success']:
            return nodes_result
        
        if not nodes_result['data']:
            return {"success": False, "message": "No nodes available"}
        
        node = nodes_result['data'][0]['node']
        
        # Get next available VM ID
        nextid_result = self.api.api_request('GET', 'cluster/nextid')
        if not nextid_result['success']:
            return nextid_result
        
        vm_id = nextid_result['data']
        
        # Default parameters
        create_params = {
            'vmid': vm_id,
            'cores': params.get('cores', 1),
            'memory': params.get('memory', 512),  # MB
            'ostype': 'l26',  # Linux 2.6/3.x/4.x Kernel
            'net0': 'virtio,bridge=vmbr0'
        }
        
        # Add storage if specified
        if 'disk' in params:
            create_params['scsihw'] = 'virtio-scsi-pci'
            create_params['scsi0'] = f'local-lvm:{params["disk"]}'
        
        # Create the VM
        result = self.api.api_request('POST', f'nodes/{node}/qemu', create_params)
        if result['success']:
            return {"success": True, "message": f"VM {vm_id} created successfully on node {node}"}
        else:
            return result
    
    def delete_vm(self, vm_id):
        """Delete a VM"""
        vm_info = self.get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
        
        node = vm_info['node']
        result = self.api.api_request('DELETE', f'nodes/{node}/qemu/{vm_id}')
        if result['success']:
            return {"success": True, "message": f"VM {vm_id} deleted successfully"}
        else:
            return result
    
    def list_containers(self):
        """List all containers"""
        result = self.api.api_request('GET', 'cluster/resources?type=lxc')
        if result['success']:
            containers = []
            for ct in result['data']:
                containers.append({
                    'id': ct['vmid'],
                    'name': ct.get('name', f"CT {ct['vmid']}"),
                    'status': ct['status'],
                    'node': ct['node']
                })
            return {"success": True, "message": "Found containers", "containers": containers}
        else:
            return result
    
    def get_cluster_status(self):
        """Get the status of the cluster"""
        result = self.api.api_request('GET', 'cluster/status')
        if result['success']:
            return {"success": True, "message": "Cluster status", "status": result['data']}
        else:
            return result
    
    def get_node_status(self, node):
        """Get the status of a node"""
        result = self.api.api_request('GET', f'nodes/{node}/status')
        if result['success']:
            return {"success": True, "message": f"Node {node} status", "status": result['data']}
        else:
            return result
    
    def get_storage_info(self):
        """Get storage information"""
        result = self.api.api_request('GET', 'cluster/resources?type=storage')
        if result['success']:
            storages = []
            for storage in result['data']:
                storages.append({
                    'name': storage['storage'],
                    'type': storage['type'],
                    'node': storage['node'],
                    'used': storage.get('used', 0) / (1024*1024*1024),  # Convert to GB
                    'total': storage.get('total', 0) / (1024*1024*1024),  # Convert to GB
                    'available': storage.get('avail', 0) / (1024*1024*1024)  # Convert to GB
                })
            return {"success": True, "message": "Storage information", "storages": storages}
        else:
            return result
    
    def get_vm_location(self, vm_id):
        """Get the node where a VM is located"""
        result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not result['success']:
            return result
        
        for vm in result['data']:
            if str(vm['vmid']) == str(vm_id):
                return {"success": True, "node": vm['node']}
        
        return {"success": False, "message": f"VM {vm_id} not found"}
    
    def get_help(self):
        """Get help information"""
        commands = [
            # Existing commands
            "list vms - Show all virtual machines",
            "start vm <id> - Start a virtual machine",
            "stop vm <id> - Stop a virtual machine",
            "restart vm <id> - Restart a virtual machine",
            "status of vm <id> - Get status of a virtual machine",
            "create a new vm with 2GB RAM, 2 CPUs and 20GB disk using ubuntu - Create a new VM",
            "delete vm <id> - Delete a virtual machine",
            "list containers - Show all LXC containers",
            "get cluster status - Show cluster status",
            "get status of node <n> - Show node status",
            "get storage info - Show storage information",
            
            # ZFS Storage Commands
            "create pool <name> with devices /dev/sda /dev/sdb using mirror - Create a new ZFS pool",
            "list pools on node <name> - Show all ZFS pools",
            "create dataset <name> - Create a new ZFS dataset",
            "list datasets - Show all ZFS datasets",
            "set compression=lz4 on dataset <name> - Set ZFS dataset properties",
            "create snapshot <name> of dataset <name> - Create a ZFS snapshot",
            "setup auto snapshots for dataset <name> - Configure automatic snapshots",
            
            # Cloudflare Domain Management
            "configure cloudflare domain <domain> with email <email> - Configure a domain with Cloudflare",
            "setup cloudflare tunnel for domain <domain> - Create a Cloudflare tunnel",
            "list cloudflare domains - Show all configured Cloudflare domains",
            "list cloudflare tunnels - Show all configured Cloudflare tunnels",
            "remove cloudflare domain <domain> - Remove a domain from Cloudflare configuration",
            
            # Resource Analysis Commands
            "analyze vm <id> resources - Show resource usage analysis and recommendations",
            "get cluster efficiency - Show cluster-wide resource efficiency metrics",
            
            # Backup Management Commands
            "configure backup for vm <id> - Set up automated backups for a VM",
            "create backup of vm <id> - Create an immediate backup of a VM",
            "verify backup of vm <id> - Verify a VM's backup integrity",
            "restore vm <id> from backup - Restore a VM from its backup",
            "configure remote storage s3 with key=KEY secret=SECRET bucket=BUCKET - Set up remote backup storage",
            "get backup status [vm <id>] - Show backup status for all VMs or specific VM",
            
            # Network Management Commands
            "setup network segmentation - Configure initial VLAN-based network segments",
            "create network segment NAME with vlan ID and subnet SUBNET - Create a new network segment",
            "get network recommendations for SERVICE_TYPE - Get network configuration recommendations",
            "configure network for service ID of type TYPE on vm ID - Configure service networking",
            "analyze network security - Get network security analysis and recommendations",
            
            "help - Show this help message"
        ]
        return {"success": True, "message": "Available commands", "commands": commands}

    def backup_vm(self, vm_id, backup_dir):
        """Backup a VM to the specified directory"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_file = os.path.join(backup_dir, f'vm_{vm_id}_backup_{timestamp}.tar.gz')
        command = [
            'vzdump',
            '--dumpdir', backup_dir,
            '--compress', 'gzip',
            '--mode', 'snapshot',
            str(vm_id)
        ]
        subprocess.run(command, check=True)
        return backup_file

    def restore_vm(self, backup_file, vm_id):
        """Restore a VM from the specified backup file"""
        command = [
            'qmrestore',
            backup_file,
            str(vm_id)
        ]
        subprocess.run(command, check=True)

    def create_zfs_pool(self, node: str, name: str, devices: list, raid_level: str = 'mirror') -> dict:
        """Create a ZFS storage pool on a node.
        
        Args:
            node: Node name
            name: Pool name
            devices: List of device paths
            raid_level: ZFS raid level (mirror, raidz, raidz2, etc.)
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

    def get_zfs_pools(self, node: str) -> dict:
        """Get ZFS pool information from a node."""
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
                
        return {"success": True, "message": "ZFS pools", "pools": pools}

    def get_zfs_datasets(self, node: str, pool: str = None) -> dict:
        """Get ZFS dataset information."""
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
                
        return {"success": True, "message": "ZFS datasets", "datasets": datasets}

    def create_zfs_dataset(self, node: str, name: str, options: dict = None) -> dict:
        """Create a ZFS dataset with options."""
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

    def set_zfs_properties(self, node: str, dataset: str, properties: dict) -> dict:
        """Set ZFS dataset properties."""
        for prop, value in properties.items():
            result = self.api.api_request('POST', f'nodes/{node}/execute', {
                'command': f"zfs set {prop}={value} {dataset}"
            })
            
            if not result['success']:
                return result
                
        return {"success": True, "message": f"Set properties on {dataset}"}

    def create_zfs_snapshot(self, node: str, dataset: str, snapshot_name: str, recursive: bool = False) -> dict:
        """Create a ZFS snapshot."""
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

    def setup_auto_snapshots(self, node: str, dataset: str, schedule: str = 'hourly') -> dict:
        """Configure automatic ZFS snapshots."""
        # Setup zfs-auto-snapshot or similar tool
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f"zfs set com.sun:auto-snapshot={schedule} {dataset}"
        })
        
        if result['success']:
            return {"success": True, "message": f"Configured auto-snapshots for {dataset}"}
        return result

    def configure_cloudflare_domain(self, domain_name, email, api_key=None):
        """Configure a domain with Cloudflare"""
        from ..core.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return cf_manager.configure_domain(domain_name, email, api_key)

    def setup_cloudflare_tunnel(self, domain_name, tunnel_name="homelab"):
        """Set up a Cloudflare tunnel for a domain"""
        from ..core.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return cf_manager.create_tunnel(domain_name, tunnel_name)

    def list_cloudflare_domains(self):
        """List all configured Cloudflare domains"""
        from ..core.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return {
            "success": True,
            "message": "Cloudflare domains",
            "domains": cf_manager.get_domains()
        }

    def list_cloudflare_tunnels(self):
        """List all configured Cloudflare tunnels"""
        from ..core.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return {
            "success": True,
            "message": "Cloudflare tunnels",
            "tunnels": cf_manager.get_tunnels()
        }

    def remove_cloudflare_domain(self, domain_name):
        """Remove a domain from Cloudflare configuration"""
        from ..core.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return cf_manager.remove_domain(domain_name)

    def analyze_vm_resources(self, vm_id: str, days: int = 7) -> dict:
        """Analyze VM resource usage and provide optimization recommendations"""
        from ..core.resource_analyzer import ResourceAnalyzer
        analyzer = ResourceAnalyzer(self.api)
        return analyzer.analyze_vm_resources(vm_id, days)

    def get_cluster_efficiency(self) -> dict:
        """Get cluster efficiency metrics and recommendations"""
        from ..core.resource_analyzer import ResourceAnalyzer
        analyzer = ResourceAnalyzer(self.api)
        return analyzer.get_cluster_efficiency()

    def configure_backup(self, vm_id: str, schedule: dict = None) -> dict:
        """Configure automated backups for a VM"""
        from ..core.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.configure_backup(vm_id, schedule)

    def create_backup(self, vm_id: str) -> dict:
        """Create a backup of a VM"""
        from ..core.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.create_backup(vm_id)

    def verify_backup(self, vm_id: str) -> dict:
        """Verify a VM's backup integrity"""
        from ..core.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.verify_backup(vm_id)

    def restore_backup(self, vm_id: str, backup_file: str = None) -> dict:
        """Restore a VM from backup"""
        from ..core.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.restore_backup(vm_id, backup_file)

    def configure_remote_storage(self, storage_type: str, config: dict) -> dict:
        """Configure remote backup storage"""
        from ..core.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.configure_remote_storage(storage_type, config)

    def get_backup_status(self, vm_id: str = None) -> dict:
        """Get backup status for VMs"""
        from ..core.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.get_backup_status(vm_id)

    def setup_network_segmentation(self) -> dict:
        """Set up initial network segmentation with VLANs"""
        from ..core.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.setup_network_segmentation()

    def create_network_segment(self, name: str, vlan_id: int, subnet: str, purpose: str) -> dict:
        """Create a new network segment"""
        from ..core.network_manager import NetworkManager, NetworkSegment
        network_mgr = NetworkManager(self.api)
        segment = NetworkSegment(
            name=name,
            vlan_id=vlan_id,
            subnet=subnet,
            purpose=purpose,
            security_level="medium",
            allowed_services=["http", "https"]
        )
        return network_mgr.create_network_segment(segment)

    def get_network_recommendations(self, service_type: str) -> dict:
        """Get network configuration recommendations for a service"""
        from ..core.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.get_network_recommendations(service_type)

    def configure_service_network(self, service_id: str, service_type: str, vm_id: str) -> dict:
        """Configure network for a service"""
        from ..core.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.configure_service_network(service_id, service_type, vm_id)

    def analyze_network_security(self) -> dict:
        """Analyze network security and provide recommendations"""
        from ..core.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.analyze_network_security()