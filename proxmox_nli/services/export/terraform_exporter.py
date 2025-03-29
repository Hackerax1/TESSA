"""
Terraform Export/Import Module for TESSA.

This module provides functionality to export Proxmox configurations to Terraform format
and import Terraform configurations into Proxmox.
"""
import logging
import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ...api.proxmox_api import ProxmoxAPI

logger = logging.getLogger(__name__)

class TerraformExporter:
    """Exporter for Terraform configurations."""
    
    def __init__(self, api: ProxmoxAPI):
        """Initialize with Proxmox API connection."""
        self.api = api
        
    def export(self, output_dir: str, resource_types: List[str], include_sensitive: bool = False) -> Dict:
        """
        Export Proxmox configuration to Terraform format.
        
        Args:
            output_dir: Directory to write Terraform files to
            resource_types: List of resource types to export (e.g., ['vm', 'lxc', 'storage'])
            include_sensitive: Whether to include sensitive information (default: False)
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            exported_resources = []
            
            # Create provider configuration
            provider_content = self._generate_provider()
            with open(os.path.join(output_dir, 'provider.tf'), 'w') as f:
                f.write(provider_content)
            
            # Create variables file
            variables_content = self._generate_variables(include_sensitive)
            with open(os.path.join(output_dir, 'variables.tf'), 'w') as f:
                f.write(variables_content)
                
            # Generate outputs file
            outputs_content = self._generate_outputs()
            with open(os.path.join(output_dir, 'outputs.tf'), 'w') as f:
                f.write(outputs_content)
                
            # Generate terraform.tfvars file (with placeholder sensitive values)
            tfvars_content = self._generate_tfvars(include_sensitive)
            with open(os.path.join(output_dir, 'terraform.tfvars'), 'w') as f:
                f.write(tfvars_content)
            
            # Export VMs
            if "vm" in resource_types:
                vm_result = self._export_vms(output_dir)
                exported_resources.extend(vm_result.get("resources", []))
                
            # Export Containers (LXC)
            if "lxc" in resource_types:
                lxc_result = self._export_containers(output_dir)
                exported_resources.extend(lxc_result.get("resources", []))
                
            # Export Storage
            if "storage" in resource_types:
                storage_result = self._export_storage(output_dir)
                exported_resources.extend(storage_result.get("resources", []))
                
            # Export Network
            if "network" in resource_types:
                network_result = self._export_network(output_dir)
                exported_resources.extend(network_result.get("resources", []))
                
            # Create README
            readme_content = self._generate_readme()
            with open(os.path.join(output_dir, 'README.md'), 'w') as f:
                f.write(readme_content)
            
            return {
                "success": True,
                "message": f"Successfully exported {len(exported_resources)} resources to Terraform format",
                "resources": exported_resources,
                "output_dir": output_dir
            }
        except Exception as e:
            logger.error(f"Error exporting to Terraform: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export to Terraform: {str(e)}"
            }
            
    def import_config(self, input_path: str) -> Dict:
        """
        Import Terraform configuration into Proxmox.
        
        Args:
            input_path: Path to Terraform configuration directory or file
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            # Validate Terraform configuration
            validation_result = self._validate_terraform_config(input_path)
            if not validation_result["success"]:
                return validation_result
                
            # Plan the import
            plan_result = self._plan_terraform_import(input_path)
            if not plan_result["success"]:
                return plan_result
                
            # Execute the import
            import_result = self._execute_terraform_import(input_path, plan_result["plan"])
            
            return import_result
        except Exception as e:
            logger.error(f"Error importing Terraform configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to import Terraform configuration: {str(e)}"
            }
    
    def _generate_provider(self) -> str:
        """Generate Terraform provider configuration."""
        return """# Proxmox Provider Configuration
# Generated by TESSA Infrastructure as Code Exporter

terraform {
  required_providers {
    proxmox = {
      source  = "telmate/proxmox"
      version = ">= 2.9.10"
    }
  }
}

provider "proxmox" {
  pm_api_url      = var.proxmox_api_url
  pm_user         = var.proxmox_user
  pm_password     = var.proxmox_password
  pm_tls_insecure = var.proxmox_tls_insecure
  pm_debug        = var.proxmox_debug
}
"""

    def _generate_variables(self, include_sensitive: bool) -> str:
        """Generate Terraform variables configuration."""
        sensitive_str = "sensitive = true" if not include_sensitive else ""
        
        return f"""# Variables for Proxmox Terraform Configuration
# Generated by TESSA Infrastructure as Code Exporter

variable "proxmox_api_url" {{
  description = "The Proxmox API URL"
  type        = string
}}

variable "proxmox_user" {{
  description = "The Proxmox user with API access"
  type        = string
}}

variable "proxmox_password" {{
  description = "The Proxmox user password"
  type        = string
  {sensitive_str}
}}

variable "proxmox_tls_insecure" {{
  description = "Allow insecure TLS connections"
  type        = bool
  default     = false
}}

variable "proxmox_debug" {{
  description = "Enable debug logging"
  type        = bool
  default     = false
}}
"""

    def _generate_outputs(self) -> str:
        """Generate Terraform outputs configuration."""
        return """# Outputs for Proxmox Terraform Configuration
# Generated by TESSA Infrastructure as Code Exporter

output "vm_ips" {
  description = "IP addresses of all VMs"
  value = {
    for name, vm in proxmox_vm_qemu.vms : name => vm.default_ipv4_address
  }
}

output "container_ips" {
  description = "IP addresses of all containers"
  value = {
    for name, ct in proxmox_lxc.containers : name => ct.network[0].ip
  }
}
"""

    def _generate_tfvars(self, include_sensitive: bool) -> str:
        """Generate terraform.tfvars file."""
        # Get the API URL from the current connection
        api_url = "https://your-proxmox-host:8006/api2/json"
        if hasattr(self.api, 'base_url'):
            api_url = self.api.base_url
        
        password_placeholder = "change-me-to-secure-password"
        
        return f"""# Terraform variables values
# Generated by TESSA Infrastructure as Code Exporter
# IMPORTANT: Update sensitive values before applying!

proxmox_api_url      = "{api_url}"
proxmox_user         = "root@pam"
proxmox_password     = "{password_placeholder}"
proxmox_tls_insecure = true
proxmox_debug        = false
"""

    def _export_vms(self, output_dir: str) -> Dict:
        """Export VMs to Terraform configuration."""
        try:
            vm_resources = []
            
            # Get all VMs from API
            result = self.api.api_request('GET', 'cluster/resources', {'type': 'vm'})
            
            if not result["success"]:
                logger.error(f"Failed to retrieve VMs: {result.get('message', 'Unknown error')}")
                return {
                    "success": False,
                    "message": f"Failed to retrieve VMs: {result.get('message', 'Unknown error')}"
                }
                
            vms = result["data"]
            if not vms:
                return {
                    "success": True,
                    "message": "No VMs found to export",
                    "resources": []
                }
                
            # Create VM configuration
            vm_configs = []
            
            for vm in vms:
                vmid = vm.get('vmid')
                node = vm.get('node')
                name = vm.get('name', f"vm-{vmid}")
                
                # Get detailed VM config
                config_result = self.api.api_request('GET', f'nodes/{node}/qemu/{vmid}/config')
                
                if not config_result["success"]:
                    logger.warning(f"Failed to retrieve config for VM {vmid}: {config_result.get('message', 'Unknown error')}")
                    continue
                    
                vm_config = config_result["data"]
                
                # Convert VM config to Terraform format
                vm_tf_config = self._convert_vm_to_terraform(name, node, vmid, vm_config)
                vm_configs.append(vm_tf_config)
                
                # Add to resources list
                vm_resources.append({
                    "type": "vm",
                    "id": str(vmid),
                    "name": name,
                    "node": node
                })
            
            # Write VM configurations to file
            if vm_configs:
                combined_config = "\n\n".join(vm_configs)
                vm_file_path = os.path.join(output_dir, 'vms.tf')
                with open(vm_file_path, 'w') as f:
                    f.write(combined_config)
            
            return {
                "success": True,
                "message": f"Exported {len(vm_resources)} VMs to Terraform configuration",
                "resources": vm_resources
            }
                
        except Exception as e:
            logger.error(f"Error exporting VMs: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export VMs: {str(e)}"
            }
    
    def _export_containers(self, output_dir: str) -> Dict:
        """Export LXC containers to Terraform configuration."""
        try:
            container_resources = []
            
            # Get all containers from API
            result = self.api.api_request('GET', 'cluster/resources', {'type': 'lxc'})
            
            if not result["success"]:
                logger.error(f"Failed to retrieve containers: {result.get('message', 'Unknown error')}")
                return {
                    "success": False,
                    "message": f"Failed to retrieve containers: {result.get('message', 'Unknown error')}"
                }
                
            containers = result["data"]
            if not containers:
                return {
                    "success": True,
                    "message": "No containers found to export",
                    "resources": []
                }
                
            # Create container configuration
            container_configs = []
            
            for container in containers:
                ctid = container.get('vmid')
                node = container.get('node')
                name = container.get('name', f"ct-{ctid}")
                
                # Get detailed container config
                config_result = self.api.api_request('GET', f'nodes/{node}/lxc/{ctid}/config')
                
                if not config_result["success"]:
                    logger.warning(f"Failed to retrieve config for container {ctid}: {config_result.get('message', 'Unknown error')}")
                    continue
                    
                ct_config = config_result["data"]
                
                # Convert container config to Terraform format
                ct_tf_config = self._convert_container_to_terraform(name, node, ctid, ct_config)
                container_configs.append(ct_tf_config)
                
                # Add to resources list
                container_resources.append({
                    "type": "lxc",
                    "id": str(ctid),
                    "name": name,
                    "node": node
                })
            
            # Write container configurations to file
            if container_configs:
                combined_config = "\n\n".join(container_configs)
                ct_file_path = os.path.join(output_dir, 'containers.tf')
                with open(ct_file_path, 'w') as f:
                    f.write(combined_config)
            
            return {
                "success": True,
                "message": f"Exported {len(container_resources)} containers to Terraform configuration",
                "resources": container_resources
            }
                
        except Exception as e:
            logger.error(f"Error exporting containers: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export containers: {str(e)}"
            }
    
    def _export_storage(self, output_dir: str) -> Dict:
        """Export storage configurations to Terraform format."""
        try:
            storage_resources = []
            
            # Get all storage from API
            result = self.api.api_request('GET', 'storage')
            
            if not result["success"]:
                logger.error(f"Failed to retrieve storage: {result.get('message', 'Unknown error')}")
                return {
                    "success": False,
                    "message": f"Failed to retrieve storage: {result.get('message', 'Unknown error')}"
                }
                
            storages = result["data"]
            if not storages:
                return {
                    "success": True,
                    "message": "No storage found to export",
                    "resources": []
                }
                
            # Create storage configuration
            storage_configs = []
            
            for storage in storages:
                storage_id = storage.get('storage')
                storage_type = storage.get('type')
                
                # Convert storage config to Terraform format
                storage_tf_config = self._convert_storage_to_terraform(storage_id, storage)
                if storage_tf_config:  # Some storage types may not be supported
                    storage_configs.append(storage_tf_config)
                
                    # Add to resources list
                    storage_resources.append({
                        "type": "storage",
                        "id": storage_id,
                        "storage_type": storage_type
                    })
            
            # Write storage configurations to file
            if storage_configs:
                combined_config = "\n\n".join(storage_configs)
                storage_file_path = os.path.join(output_dir, 'storage.tf')
                with open(storage_file_path, 'w') as f:
                    f.write(combined_config)
            
            return {
                "success": True,
                "message": f"Exported {len(storage_resources)} storage resources to Terraform configuration",
                "resources": storage_resources
            }
                
        except Exception as e:
            logger.error(f"Error exporting storage: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export storage: {str(e)}"
            }
    
    def _export_network(self, output_dir: str) -> Dict:
        """Export network configurations to Terraform format."""
        try:
            network_resources = []
            node_networks = {}
            
            # Get list of nodes
            nodes_result = self.api.api_request('GET', 'nodes')
            if not nodes_result["success"]:
                logger.error(f"Failed to retrieve nodes: {nodes_result.get('message', 'Unknown error')}")
                return {
                    "success": False,
                    "message": f"Failed to retrieve nodes: {nodes_result.get('message', 'Unknown error')}"
                }
            
            # For each node, get network configuration
            for node in nodes_result["data"]:
                node_name = node.get('node')
                
                # Get network configuration for this node
                net_result = self.api.api_request('GET', f'nodes/{node_name}/network')
                
                if not net_result["success"]:
                    logger.warning(f"Failed to retrieve network for node {node_name}: {net_result.get('message', 'Unknown error')}")
                    continue
                    
                networks = net_result["data"]
                node_networks[node_name] = networks
                
                # Process each network interface
                for iface in networks:
                    iface_name = iface.get('iface')
                    iface_type = iface.get('type')
                    
                    # Add to resources list
                    network_resources.append({
                        "type": "network",
                        "id": iface_name,
                        "node": node_name,
                        "network_type": iface_type
                    })
            
            # Create network configurations
            network_configs = []
            
            for node_name, networks in node_networks.items():
                # Convert network configs to Terraform format
                node_net_config = self._convert_network_to_terraform(node_name, networks)
                network_configs.append(node_net_config)
            
            # Write network configurations to file
            if network_configs:
                combined_config = "\n\n".join(network_configs)
                network_file_path = os.path.join(output_dir, 'network.tf')
                with open(network_file_path, 'w') as f:
                    f.write(combined_config)
            
            return {
                "success": True,
                "message": f"Exported {len(network_resources)} network resources to Terraform configuration",
                "resources": network_resources
            }
                
        except Exception as e:
            logger.error(f"Error exporting network: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to export network: {str(e)}"
            }
    
    def _convert_vm_to_terraform(self, name: str, node: str, vmid: int, config: Dict) -> str:
        """Convert VM configuration to Terraform format."""
        # Normalize VM name for Terraform
        tf_name = re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
        
        # Extract key VM properties
        memory = config.get('memory', 512)
        cores = config.get('cores', 1)
        sockets = config.get('sockets', 1)
        disk_size = None
        
        # Find primary disk size
        for key, value in config.items():
            if key.startswith('scsi') and 'size' in value:
                # Extract size (e.g., "32G" -> 32)
                size_match = re.match(r'(\d+)G', value)
                if size_match:
                    disk_size = size_match.group(1)
                    break
        
        # Network configuration
        network = []
        for key, value in config.items():
            if key.startswith('net'):
                # Parse network string (e.g., "virtio=XX:XX:XX:XX:XX:XX,bridge=vmbr0")
                net_parts = value.split(',')
                net_config = {}
                for part in net_parts:
                    if '=' in part:
                        k, v = part.split('=', 1)
                        net_config[k] = v
                
                if 'bridge' in net_config:
                    network.append({
                        "bridge": net_config['bridge'],
                        "model": net_config.get('virtio', 'virtio')
                    })
        
        # Build Terraform configuration
        tf_config = f'''# VM: {name} (ID: {vmid})
resource "proxmox_vm_qemu" "vm_{tf_name}" {{
  name        = "{name}"
  target_node = "{node}"
  vmid        = {vmid}
  
  # Hardware
  memory      = {memory}
  cores       = {cores}
  sockets     = {sockets}
'''

        # Add OS/template info if available
        if 'ostype' in config:
            tf_config += f'  os_type     = "{config["ostype"]}"\n'
            
        # Add disk configuration
        if disk_size:
            tf_config += f'''
  disk {{
    type    = "scsi"
    storage = "local-lvm"
    size    = "{disk_size}G"
  }}
'''
        
        # Add network configuration
        for i, net in enumerate(network):
            tf_config += f'''
  network {{
    bridge   = "{net['bridge']}"
    model    = "{net['model']}"
  }}
'''
        
        # Close the resource block
        tf_config += '}\n'
        
        return tf_config
    
    def _convert_container_to_terraform(self, name: str, node: str, ctid: int, config: Dict) -> str:
        """Convert LXC container configuration to Terraform format."""
        # Normalize container name for Terraform
        tf_name = re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
        
        # Extract key container properties
        memory = config.get('memory', 512)
        cores = config.get('cores', 1)
        swap = config.get('swap', 0)
        
        # Get rootfs info
        rootfs_str = config.get('rootfs', '')
        rootfs_parts = rootfs_str.split(',') if rootfs_str else []
        storage = None
        size = None
        
        for part in rootfs_parts:
            if part.startswith('volume='):
                volume = part[7:]
                if ':' in volume:
                    storage, _ = volume.split(':', 1)
            elif part.startswith('size='):
                size_match = re.match(r'size=(\d+)G', part)
                if size_match:
                    size = size_match.group(1)
        
        # Network configuration
        networks = []
        net_config = {}
        
        # Parse network configuration
        if 'net0' in config:
            net_parts = config['net0'].split(',')
            for part in net_parts:
                if '=' in part:
                    k, v = part.split('=', 1)
                    net_config[k] = v
            
            if 'name' in net_config and 'ip' in net_config:
                networks.append({
                    "name": net_config['name'],
                    "ip": net_config['ip'],
                    "bridge": net_config.get('bridge', 'vmbr0'),
                    "gw": config.get('gw', '')
                })
        
        # Build Terraform configuration
        tf_config = f'''# Container: {name} (ID: {ctid})
resource "proxmox_lxc" "container_{tf_name}" {{
  hostname    = "{name}"
  target_node = "{node}"
  vmid        = {ctid}
  
  # Resources
  memory      = {memory}
  cores       = {cores}
  swap        = {swap}
'''

        # Add OS template if available
        if 'ostemplate' in config:
            tf_config += f'  ostemplate  = "{config["ostemplate"]}"\n'
            
        # Add rootfs configuration
        if storage and size:
            tf_config += f'''
  rootfs {{
    storage = "{storage}"
    size    = "{size}G"
  }}
'''
        
        # Add network configuration
        for net in networks:
            tf_config += f'''
  network {{
    name   = "{net['name']}"
    ip     = "{net['ip']}"
    bridge = "{net['bridge']}"
'''
            if net['gw']:
                tf_config += f'    gw     = "{net["gw"]}"\n'
            
            tf_config += '  }\n'
        
        # Close the resource block
        tf_config += '}\n'
        
        return tf_config
    
    def _convert_storage_to_terraform(self, storage_id: str, config: Dict) -> Optional[str]:
        """Convert storage configuration to Terraform format."""
        storage_type = config.get('type')
        # Currently supports only these storage types
        if storage_type not in ['dir', 'nfs', 'lvm', 'lvmthin', 'zfspool']:
            return None
            
        # Normalize storage name for Terraform
        tf_name = re.sub(r'[^a-zA-Z0-9_]', '_', storage_id).lower()
        
        # Build Terraform configuration
        tf_config = f'''# Storage: {storage_id} (Type: {storage_type})
resource "proxmox_storage_{storage_type}" "storage_{tf_name}" {{
  storage     = "{storage_id}"
'''

        # Add type-specific configuration
        if storage_type == 'dir':
            path = config.get('path', '')
            tf_config += f'  path        = "{path}"\n'
            
        elif storage_type == 'nfs':
            server = config.get('server', '')
            export = config.get('export', '')
            tf_config += f'  server      = "{server}"\n'
            tf_config += f'  export      = "{export}"\n'
            
        elif storage_type in ['lvm', 'lvmthin']:
            vg = config.get('vgname', '')
            tf_config += f'  vgname      = "{vg}"\n'
            
        elif storage_type == 'zfspool':
            pool = config.get('pool', '')
            tf_config += f'  pool        = "{pool}"\n'
            
        # Add common properties
        content = config.get('content', '')
        if content:
            tf_config += f'  content     = "{content}"\n'
            
        shared = config.get('shared', 0)
        if shared:
            tf_config += f'  shared      = {shared}\n'
            
        # Close the resource block
        tf_config += '}\n'
        
        return tf_config
    
    def _convert_network_to_terraform(self, node: str, networks: List[Dict]) -> str:
        """Convert network configuration to Terraform format."""
        # Normalize node name for Terraform
        tf_node_name = re.sub(r'[^a-zA-Z0-9_]', '_', node).lower()
        
        # Start with node-specific locals block
        tf_config = f'''# Network configuration for node: {node}
locals {{
  node_{tf_node_name}_network = {{
'''

        # Process each interface
        for network in networks:
            iface = network.get('iface', '')
            # Skip if no interface name
            if not iface:
                continue
                
            # Normalize interface name
            tf_iface = re.sub(r'[^a-zA-Z0-9_]', '_', iface).lower()
            
            tf_config += f'    {tf_iface} = {{\n'
            
            # Add interface properties
            for key, value in network.items():
                if key == 'iface':
                    continue
                    
                # Format value based on type
                if isinstance(value, str):
                    tf_config += f'      {key} = "{value}"\n'
                elif isinstance(value, bool):
                    tf_config += f'      {key} = {str(value).lower()}\n'
                else:
                    tf_config += f'      {key} = {value}\n'
                    
            tf_config += '    }\n'
        
        # Close the locals block
        tf_config += '  }\n}\n'
        
        return tf_config
    
    def _generate_readme(self) -> str:
        """Generate a README file for the Terraform configuration."""
        return """# Proxmox Terraform Configuration

This Terraform configuration was automatically generated by TESSA (Technical Environment Self-Service Assistant).

## Prerequisites

- Terraform v1.0.0+
- Proxmox VE 7.0+
- Proxmox Terraform Provider

## Getting Started

1. Update the `terraform.tfvars` file with your Proxmox credentials:

```hcl
proxmox_api_url      = "https://your-proxmox-host:8006/api2/json"
proxmox_user         = "your-api-user@pam"
proxmox_password     = "your-password"
proxmox_tls_insecure = true  # Set to false in production
```

2. Initialize Terraform:

```bash
terraform init
```

3. Review the execution plan:

```bash
terraform plan
```

4. Apply the configuration:

```bash
terraform apply
```

## Structure

- `provider.tf` - Proxmox provider configuration
- `variables.tf` - Input variables definition
- `terraform.tfvars` - Variable values (edit this file)
- `outputs.tf` - Output definitions
- `vms.tf` - Virtual machines configuration
- `containers.tf` - LXC containers configuration
- `storage.tf` - Storage configuration
- `network.tf` - Network configuration

## Important Notes

- Review all configurations before applying
- Sensitive values in `terraform.tfvars` should be updated
- Consider using Terraform Cloud or another secure storage for sensitive values

Generated by TESSA on """ + f"{self._get_current_date()}"
    
    def _validate_terraform_config(self, input_path: str) -> Dict:
        """Validate Terraform configuration."""
        # This would be implemented with terraform CLI commands
        # For now, just check if path exists and has terraform files
        if not os.path.exists(input_path):
            return {
                "success": False,
                "message": f"Path does not exist: {input_path}"
            }
            
        if os.path.isdir(input_path):
            tf_files = [f for f in os.listdir(input_path) if f.endswith('.tf')]
            if not tf_files:
                return {
                    "success": False,
                    "message": f"No Terraform files found in directory: {input_path}"
                }
                
            return {
                "success": True,
                "message": f"Found {len(tf_files)} Terraform files"
            }
        elif input_path.endswith('.tf'):
            return {
                "success": True,
                "message": "Terraform file found"
            }
        else:
            return {
                "success": False,
                "message": f"Not a Terraform file or directory: {input_path}"
            }
    
    def _plan_terraform_import(self, input_path: str) -> Dict:
        """Plan Terraform import operations."""
        # This would involve terraform plan in import mode
        # For now, just return a simple plan that would need implementation
        return {
            "success": True,
            "message": "Import plan created (implementation needed)",
            "plan": {
                "vms": [],
                "containers": [],
                "storage": [],
                "networks": []
            }
        }
    
    def _execute_terraform_import(self, input_path: str, plan: Dict) -> Dict:
        """Execute Terraform import operations."""
        # This would implement the actual import with terraform CLI
        # For now, just return placeholder result
        return {
            "success": True,
            "message": "Import plan execution not yet implemented",
            "resources_imported": 0
        }
    
    def _get_current_date(self) -> str:
        """Get current date formatted string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")