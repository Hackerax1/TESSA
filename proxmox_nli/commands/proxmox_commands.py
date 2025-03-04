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