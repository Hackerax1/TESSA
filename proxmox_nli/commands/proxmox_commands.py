import os
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

from .backup_scheduler_commands import BackupSchedulerCommands
from datetime import datetime
from typing import List, Dict, Any, Optional

class ProxmoxCommands:
    def __init__(self, api):
        self.api = api
        # Initialize backup scheduler commands
        self.backup_scheduler = BackupSchedulerCommands(api)

    def list_vms(self):
        """Get a list of all VMs with their status"""
        result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not result['success']:
            return result
        
        vms = []
        for vm in result['data']:
            vm_status = self.get_vm_status(vm['vmid'])
            if vm_status['success']:
                vms.append({
                    'id': vm['vmid'],
                    'name': vm['name'],
                    'status': vm_status['status']['status'],
                    'cpu': vm_status['status']['cpu'],
                    'memory': vm_status['status']['memory'],
                    'disk': vm_status['status']['disk']
                })
        
        return {"success": True, "vms": vms}

    def get_cluster_status(self):
        """Get status of all nodes in the cluster"""
        result = self.api.api_request('GET', 'cluster/status')
        if not result['success']:
            return result
        
        nodes = []
        for node in result['data']:
            if node['type'] == 'node':
                nodes.append({
                    'name': node['name'],
                    'status': 'online' if node['online'] == 1 else 'offline',
                    'id': node['id']
                })
        
        return {"success": True, "status": nodes}

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
            
            # SSH Device Management Commands
            "scan network for SSH devices - Scan your network for SSH-accessible devices",
            "discover SSH devices on network - Discover and add SSH devices with basic authentication",
            "list SSH devices - Show all discovered SSH devices",
            "add SSH device HOSTNAME with username USER - Add a device manually for SSH access", 
            "execute command 'COMMAND' on device HOSTNAME - Run a command on an SSH device",
            "run command 'COMMAND' on all raspberry_pi devices - Run a command on a group of devices",
            "setup SSH keys for device HOSTNAME - Configure passwordless SSH access",
            "setup SSH keys for all linux_server devices - Configure SSH keys for a device group",
            
            # Environment Merger Commands
            "merge existing proxmox environment - Detect, analyze, and import an existing Proxmox setup",
            "discover proxmox environment - Discover details about the existing Proxmox configuration",
            "analyze proxmox environment - Analyze the existing environment for merge points",
            "set environment merge options - Configure which elements to include in merger",
            "get merge history - View history of previously merged environments",
            
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
        from ..core.network.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return cf_manager.configure_domain(domain_name, email, api_key)

    def setup_cloudflare_tunnel(self, domain_name, tunnel_name="homelab"):
        """Set up a Cloudflare tunnel for a domain"""
        from ..core.network.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return cf_manager.create_tunnel(domain_name, tunnel_name)

    def list_cloudflare_domains(self):
        """List all configured Cloudflare domains"""
        from ..core.network.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return {
            "success": True,
            "message": "Cloudflare domains",
            "domains": cf_manager.get_domains()
        }

    def list_cloudflare_tunnels(self):
        """List all configured Cloudflare tunnels"""
        from ..core.network.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return {
            "success": True,
            "message": "Cloudflare tunnels",
            "tunnels": cf_manager.get_tunnels()
        }

    def remove_cloudflare_domain(self, domain_name):
        """Remove a domain from Cloudflare configuration"""
        from ..core.network.cloudflare_manager import CloudflareManager
        cf_manager = CloudflareManager()
        return cf_manager.remove_domain(domain_name)

    def analyze_vm_resources(self, vm_id: str, days: int = 7) -> dict:
        """Analyze VM resource usage and provide optimization recommendations"""
        from ..core.monitoring.resource_analyzer import ResourceAnalyzer
        analyzer = ResourceAnalyzer(self.api)
        return analyzer.analyze_vm_resources(vm_id, days)

    def get_cluster_efficiency(self) -> dict:
        """Get cluster efficiency metrics and recommendations"""
        from ..core.monitoring.resource_analyzer import ResourceAnalyzer
        analyzer = ResourceAnalyzer(self.api)
        return analyzer.get_cluster_efficiency()

    def configure_backup(self, vm_id: str, schedule: dict = None) -> dict:
        """Configure automated backups for a VM"""
        from ..core.storage.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.configure_backup(vm_id, schedule)

    def create_backup(self, vm_id: str) -> dict:
        """Create a backup of a VM"""
        from ..core.storage.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.create_backup(vm_id)

    def verify_backup(self, vm_id: str) -> dict:
        """Verify a VM's backup integrity"""
        from ..core.storage.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.verify_backup(vm_id)

    def restore_backup(self, vm_id: str, backup_file: str = None) -> dict:
        """Restore a VM from backup"""
        from ..core.storage.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.restore_backup(vm_id, backup_file)

    def configure_remote_storage(self, storage_type: str, config: dict) -> dict:
        """Configure remote backup storage"""
        from ..core.storage.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.configure_remote_storage(storage_type, config)

    def get_backup_status(self, vm_id: str = None) -> dict:
        """Get backup status for VMs"""
        from ..core.storage.backup_manager import BackupManager
        backup_mgr = BackupManager(self.api)
        return backup_mgr.get_backup_status(vm_id)

    def setup_network_segmentation(self) -> dict:
        """Set up initial network segmentation with VLANs"""
        from ..core.network.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.setup_network_segmentation()

    def create_network_segment(self, name: str, vlan_id: int, subnet: str, purpose: str) -> dict:
        """Create a new network segment"""
        from ..core.network.network_manager import NetworkManager, NetworkSegment
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
        from ..core.network.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.get_network_recommendations(service_type)

    def configure_service_network(self, service_id: str, service_type: str, vm_id: str) -> dict:
        """Configure network for a service"""
        from ..core.network.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.configure_service_network(service_id, service_type, vm_id)

    def analyze_network_security(self) -> dict:
        """Analyze network security and provide recommendations"""
        from ..core.network.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.analyze_network_security()

    def auto_configure_node(self, node: str = None) -> dict:
        """Automatically configure initial Proxmox network and storage settings"""
        from ..core.automation.auto_configurator import ProxmoxAutoConfigurator
        configurator = ProxmoxAutoConfigurator(self.api)
        return configurator.auto_configure(node)
        
    def configure_network(self, node: str, use_dhcp: bool = None) -> dict:
        """Configure network settings for a node using auto-detection"""
        from ..core.automation.auto_configurator import ProxmoxAutoConfigurator
        configurator = ProxmoxAutoConfigurator(self.api)
        
        # Update DHCP setting if provided
        if use_dhcp is not None:
            configurator.toggle_dhcp(use_dhcp)
            
        return configurator.configure_networking(node)
        
    def set_network_profile(self, profile_name: str) -> dict:
        """Set the default network profile for auto-configuration"""
        from ..core.automation.auto_configurator import ProxmoxAutoConfigurator
        configurator = ProxmoxAutoConfigurator(self.api)
        return configurator.set_network_profile(profile_name)
        
    def create_network_profile(self, name: str, subnet: str, gateway: str, dns_servers: list) -> dict:
        """Create a new network profile for auto-configuration"""
        from ..core.automation.auto_configurator import ProxmoxAutoConfigurator
        configurator = ProxmoxAutoConfigurator(self.api)
        return configurator.create_network_profile(name, subnet, gateway, dns_servers)
        
    def detect_network_interfaces(self, node: str) -> dict:
        """Detect available network interfaces on a node"""
        from ..core.automation.auto_configurator import ProxmoxAutoConfigurator
        configurator = ProxmoxAutoConfigurator(self.api)
        interfaces = configurator._detect_network_interfaces(node)
        return {
            "success": True,
            "message": f"Detected {len(interfaces)} network interfaces on node {node}",
            "interfaces": interfaces
        }

    # SSH Device Management Commands
    def scan_network_for_devices(self, subnet: str = None) -> dict:
        """Scan network for SSH-accessible devices
        
        Args:
            subnet (str, optional): Subnet to scan in CIDR notation. Defaults to local subnet.
        
        Returns:
            dict: Scan results
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.scan_network(subnet)
        
    def discover_ssh_devices(self, subnet: str = None, username: str = "root", password: str = None) -> dict:
        """Discover and add SSH devices on the network
        
        Args:
            subnet (str, optional): Subnet to scan in CIDR notation. Defaults to local subnet.
            username (str, optional): Default username for connections. Defaults to "root".
            password (str, optional): Default password for connections. Defaults to None.
        
        Returns:
            dict: Discovery results
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.discover_devices(subnet, username, password)
        
    def list_ssh_devices(self, device_type: str = None) -> dict:
        """List all SSH devices or devices of a specific type
        
        Args:
            device_type (str, optional): Filter by device type. Defaults to None.
        
        Returns:
            dict: List of devices
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.list_devices(device_type)
    
    def get_ssh_device_groups(self) -> dict:
        """Get devices grouped by their type
        
        Returns:
            dict: Device groups
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.get_device_groups()
    
    def add_ssh_device(self, hostname: str, name: str = None, username: str = "root",
                       password: str = None, port: int = 22,
                       description: str = "", tags: List[str] = None) -> dict:
        """Add an SSH device manually
        
        Args:
            hostname (str): IP or hostname of the device
            name (str, optional): User-friendly name. Defaults to hostname.
            username (str, optional): Username for SSH. Defaults to "root".
            password (str, optional): Password for SSH. Defaults to None.
            port (int, optional): SSH port. Defaults to 22.
            description (str, optional): Description of the device. Defaults to "".
            tags (List[str], optional): Tags for the device. Defaults to None.
        
        Returns:
            dict: Result of operation
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.add_device(hostname, name, username, password, port, description, tags)
    
    def remove_ssh_device(self, hostname: str) -> dict:
        """Remove an SSH device
        
        Args:
            hostname (str): IP or hostname of the device
        
        Returns:
            dict: Result of operation
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.remove_device(hostname)
    
    def execute_ssh_command(self, hostname: str, command: str) -> dict:
        """Execute a command on an SSH device
        
        Args:
            hostname (str): IP or hostname of the device
            command (str): Command to execute
        
        Returns:
            dict: Command execution results
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.execute_command(hostname, command)
    
    def execute_ssh_command_on_multiple(self, hostnames: List[str], command: str) -> dict:
        """Execute a command on multiple SSH devices
        
        Args:
            hostnames (List[str]): List of IPs or hostnames
            command (str): Command to execute
        
        Returns:
            dict: Command execution results for each device
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.execute_command_on_multiple(hostnames, command)
    
    def execute_ssh_command_on_group(self, group_name: str, command: str) -> dict:
        """Execute a command on a group of SSH devices
        
        Args:
            group_name (str): Group name (device type)
            command (str): Command to execute
        
        Returns:
            dict: Command execution results for each device
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.execute_command_on_group(group_name, command)
    
    def setup_ssh_keys(self, hostnames: List[str], key_path: str = None) -> dict:
        """Set up SSH key authentication for multiple devices
        
        Args:
            hostnames (List[str]): List of IPs or hostnames
            key_path (str, optional): Path to existing SSH key. Defaults to None.
        
        Returns:
            dict: Results of key setup
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.setup_ssh_keys(hostnames, key_path)
    
    def setup_ssh_keys_for_group(self, group_name: str, key_path: str = None) -> dict:
        """Set up SSH key authentication for a group of devices
        
        Args:
            group_name (str): Group name (device type)
            key_path (str, optional): Path to existing SSH key. Defaults to None.
        
        Returns:
            dict: Results of key setup
        """
        from .ssh_commands import SSHCommands
        ssh_commands = SSHCommands(self.api)
        return ssh_commands.setup_ssh_keys_for_group(group_name, key_path)

    def create_vlan(self, name: str, vlan_id: int, subnet: str, purpose: str) -> dict:
        """Create a new VLAN"""
        from ..core.network.network_manager import NetworkManager, NetworkSegment
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

    def configure_firewall_rule(self, rule: dict) -> dict:
        """Configure a firewall rule"""
        from ..core.network.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.api.api_request('POST', 'nodes/localhost/firewall/rules', rule)

    def ssh_into_device(self, hostname: str, username: str = "root", port: int = 22) -> dict:
        """SSH into a device on the network"""
        from ..core.network.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.api.api_request('POST', f'nodes/localhost/ssh', {
            'hostname': hostname,
            'username': username,
            'port': port
        })

    def setup_pxe_service(self) -> dict:
        """Set up PXE service for network booting"""
        from ..core.network.network_manager import NetworkManager
        network_mgr = NetworkManager(self.api)
        return network_mgr.api.api_request('POST', 'nodes/localhost/pxe', {
            'enable': True
        })

    # Enhanced Network Management Commands
    def create_vlan(self, name: str, vlan_id: int, subnet: str, purpose: str = "general") -> dict:
        """Create a new VLAN
        
        Args:
            name: Name of the VLAN
            vlan_id: VLAN ID (1-4094)
            subnet: Subnet in CIDR notation (e.g., 192.168.10.0/24)
            purpose: Purpose of the VLAN
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.vlan_handler import VLANHandler
        vlan_handler = VLANHandler(self.api)
        return vlan_handler.create_vlan(vlan_id, name, subnet)

    def list_vlans(self) -> dict:
        """List all configured VLANs
        
        Returns:
            dict: List of VLANs
        """
        from ..core.network.vlan_handler import VLANHandler
        vlan_handler = VLANHandler(self.api)
        return vlan_handler.list_vlans()

    def delete_vlan(self, vlan_id: int, bridge: str = "vmbr0") -> dict:
        """Delete a VLAN
        
        Args:
            vlan_id: VLAN ID to delete
            bridge: Bridge interface (default: vmbr0)
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.vlan_handler import VLANHandler
        vlan_handler = VLANHandler(self.api)
        return vlan_handler.delete_vlan(vlan_id, bridge)

    def assign_vm_to_vlan(self, vm_id: int, vlan_id: int) -> dict:
        """Assign a VM to a VLAN
        
        Args:
            vm_id: ID of the VM
            vlan_id: ID of the VLAN
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.vlan_handler import VLANHandler
        vlan_handler = VLANHandler(self.api)
        return vlan_handler.assign_vm_to_vlan(vm_id, vlan_id)

    # Enhanced Firewall Management
    def add_firewall_rule(self, rule: dict) -> dict:
        """Add a firewall rule
        
        Args:
            rule: Firewall rule definition including:
                - action: ACCEPT, DROP, REJECT
                - type: in, out
                - proto: Protocol (tcp, udp, etc.)
                - dport: Destination port(s)
                - source: Source address (optional)
                - dest: Destination address (optional)
                - comment: Rule description
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.firewall_manager import FirewallManager
        fw_manager = FirewallManager(self.api)
        return fw_manager.add_rule(rule)

    def list_firewall_rules(self) -> dict:
        """List all firewall rules
        
        Returns:
            dict: List of firewall rules
        """
        from ..core.network.firewall_manager import FirewallManager
        fw_manager = FirewallManager(self.api)
        return fw_manager.list_rules()

    def delete_firewall_rule(self, rule_id: int) -> dict:
        """Delete a firewall rule
        
        Args:
            rule_id: ID of the rule to delete
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.firewall_manager import FirewallManager
        fw_manager = FirewallManager(self.api)
        return fw_manager.delete_rule(rule_id)

    def add_service_firewall_rules(self, service_name: str, ports: List[int], sources: List[str] = None) -> dict:
        """Add firewall rules for a service
        
        Args:
            service_name: Name of the service (for comments)
            ports: List of ports to allow
            sources: List of source IPs/networks (None for any)
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.firewall_manager import FirewallManager
        fw_manager = FirewallManager(self.api)
        return fw_manager.add_service_rules(service_name, ports, sources)

    def get_firewall_status(self) -> dict:
        """Get firewall status
        
        Returns:
            dict: Firewall status information
        """
        from ..core.network.firewall_manager import FirewallManager
        fw_manager = FirewallManager(self.api)
        return fw_manager.get_firewall_status()

    # Enhanced SSH Management
    def ssh_into_device(self, hostname: str, username: str = "root", port: int = 22) -> dict:
        """SSH into a network device
        
        Args:
            hostname: Hostname or IP address
            username: SSH username
            port: SSH port
        
        Returns:
            dict: SSH connection information
        """
        try:
            # Check if the host is reachable first
            ping_cmd = f"ping -c 1 -W 2 {hostname}"
            ping_result = self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': ping_cmd
            })
            
            if not ping_result.get('success', False) or "0 received" in ping_result.get('data', ''):
                return {
                    'success': False,
                    'message': f"Host {hostname} is not reachable"
                }
            
            # Attempt SSH connection
            ssh_cmd = f"ssh -o ConnectTimeout=5 -o BatchMode=yes -p {port} {username}@{hostname} echo 'Connection successful'"
            result = self.api.api_request('POST', 'nodes/localhost/execute', {
                'command': ssh_cmd
            })
            
            if result.get('success', False) and "Connection successful" in result.get('data', ''):
                return {
                    'success': True,
                    'message': f"Successfully connected to {hostname}",
                    'connection': {
                        'hostname': hostname,
                        'username': username,
                        'port': port
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to connect to {hostname}. Check credentials or SSH configuration."
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error connecting to {hostname}: {str(e)}"
            }

    # PXE Boot Service Management
    def setup_pxe_service(self, network_interface: str = "vmbr0", subnet: str = None) -> dict:
        """Set up PXE service for network booting
        
        Args:
            network_interface: Network interface to serve PXE on
            subnet: Subnet for DHCP (optional)
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.pxe_manager import PXEManager
        pxe_manager = PXEManager(self.api)
        return pxe_manager.enable_pxe_service(network_interface, subnet)

    def disable_pxe_service(self) -> dict:
        """Disable PXE boot service
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.pxe_manager import PXEManager
        pxe_manager = PXEManager(self.api)
        return pxe_manager.disable_pxe_service()

    def get_pxe_status(self) -> dict:
        """Get PXE service status
        
        Returns:
            dict: Status of PXE services
        """
        from ..core.network.pxe_manager import PXEManager
        pxe_manager = PXEManager(self.api)
        return pxe_manager.get_pxe_status()

    def upload_pxe_boot_image(self, image_type: str, image_path: str) -> dict:
        """Upload a boot image for PXE
        
        Args:
            image_type: Type of image (e.g., 'ubuntu', 'centos')
            image_path: Local path to boot image
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.pxe_manager import PXEManager
        pxe_manager = PXEManager(self.api)
        return pxe_manager.upload_boot_image(image_type, image_path)

    def list_pxe_boot_images(self) -> dict:
        """List available PXE boot images
        
        Returns:
            dict: List of boot images
        """
        from ..core.network.pxe_manager import PXEManager
        pxe_manager = PXEManager(self.api)
        return pxe_manager.list_boot_images()

    # DNS Management
    def add_dns_record(self, hostname: str, ip_address: str, comment: str = None) -> dict:
        """Add a DNS record
        
        Args:
            hostname: Hostname to add
            ip_address: IP address for hostname
            comment: Optional comment
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.dns_manager import DNSManager
        dns_manager = DNSManager(self.api)
        return dns_manager.add_dns_record(hostname, ip_address, comment)

    def list_dns_records(self) -> dict:
        """List all DNS records
        
        Returns:
            dict: List of DNS records
        """
        from ..core.network.dns_manager import DNSManager
        dns_manager = DNSManager(self.api)
        return dns_manager.list_dns_records()

    def update_dns_servers(self, servers: List[str]) -> dict:
        """Update DNS servers
        
        Args:
            servers: List of DNS server IP addresses
        
        Returns:
            dict: Result of the operation
        """
        from ..core.network.dns_manager import DNSManager
        dns_manager = DNSManager(self.api)
        return dns_manager.update_dns_servers(servers)

    # Environment Merger Commands
    def merge_existing_proxmox(self, conflict_resolution: str = None) -> dict:
        """Merge an existing Proxmox environment into TESSA
        
        This detects, analyzes and imports configurations from an existing Proxmox environment.
        
        Args:
            conflict_resolution: How to resolve conflicts - "ask", "tessa_priority", "existing_priority", "merge"
            
        Returns:
            dict: Results of the merge operation
        """
        from ..core.integration.environment_merger import EnvironmentMerger
        merger = EnvironmentMerger(self.api)
        return merger.merge_existing_environment(conflict_resolution)
    
    def discover_proxmox_environment(self) -> dict:
        """Discover details about the existing Proxmox environment
        
        Returns:
            dict: Discovered environment details
        """
        from ..core.integration.environment_merger import EnvironmentMerger
        merger = EnvironmentMerger(self.api)
        return merger.discover_environment()
    
    def analyze_proxmox_environment(self) -> dict:
        """Analyze the existing Proxmox environment for potential merge points
        
        Returns:
            dict: Analysis results with recommendations
        """
        from ..core.integration.environment_merger import EnvironmentMerger
        merger = EnvironmentMerger(self.api)
        discovery = merger.discover_environment()
        if not discovery['success']:
            return discovery
        return merger.analyze_environment(discovery)
    
    def set_environment_merge_options(self, options: dict) -> dict:
        """Set options for merging environments
        
        Args:
            options: Dictionary with option flags:
                - storage_pools: Whether to merge storage pools
                - network_config: Whether to merge network configurations
                - virtual_machines: Whether to merge VM inventory
                - containers: Whether to merge container inventory
                - users_and_permissions: Whether to merge users and permissions
                - backups: Whether to merge backup configurations
                - firewall_rules: Whether to merge firewall rules
                - ha_settings: Whether to merge HA settings
                
        Returns:
            dict: Updated merge options
        """
        from ..core.integration.environment_merger import EnvironmentMerger
        merger = EnvironmentMerger(self.api)
        return merger.set_merge_options(options)
    
    def get_merge_history(self) -> dict:
        """Get history of previously merged environments
        
        Returns:
            dict: History of merged environments
        """
        from ..core.integration.environment_merger import EnvironmentMerger
        merger = EnvironmentMerger(self.api)
        return merger.get_merge_history()

    # Backup Scheduler Methods
    def start_backup_scheduler(self) -> Dict:
        """Start the backup scheduler service.
        
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.start_scheduler()
    
    def stop_backup_scheduler(self) -> Dict:
        """Stop the backup scheduler service.
        
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.stop_scheduler()
    
    def get_scheduler_status(self) -> Dict:
        """Get the status of the backup scheduler.
        
        Returns:
            Dict: Scheduler status information
        """
        return self.backup_scheduler.get_scheduler_status()
    
    def schedule_backup(self, vm_id: str, schedule: Dict) -> Dict:
        """Configure backup schedule for a VM.
        
        Args:
            vm_id: VM ID
            schedule: Schedule configuration with frequency, time, etc.
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.configure_backup_schedule(vm_id, schedule)
    
    def configure_recovery_testing(self, config: Dict) -> Dict:
        """Configure automated recovery testing.
        
        Args:
            config: Recovery testing configuration
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.configure_recovery_testing(config)
    
    def configure_retention_policy(self, vm_id: str, policy: Dict) -> Dict:
        """Configure backup retention policy for a VM.
        
        Args:
            vm_id: VM ID
            policy: Retention policy configuration
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.configure_retention_policy(vm_id, policy)
    
    def run_backup_now(self, vm_id: str) -> Dict:
        """Run a backup immediately.
        
        Args:
            vm_id: VM ID
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.run_backup_now(vm_id)
    
    def run_recovery_test_now(self, vm_ids: Optional[List[str]] = None) -> Dict:
        """Run a recovery test immediately.
        
        Args:
            vm_ids: Optional list of VM IDs to test
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.run_recovery_testing_now(vm_ids)
    
    def run_retention_enforcement_now(self) -> Dict:
        """Run retention policy enforcement immediately.
        
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.run_retention_enforcement_now()
    
    def run_deduplication_now(self) -> Dict:
        """Run data deduplication immediately.
        
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.run_deduplication_now()
    
    def configure_notifications(self, config: Dict) -> Dict:
        """Configure backup notifications.
        
        Args:
            config: Notification configuration
            
        Returns:
            Dict: Result of the operation
        """
        return self.backup_scheduler.configure_notifications(config)