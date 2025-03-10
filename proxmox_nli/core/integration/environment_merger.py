"""
Environment Merger module for integrating existing Proxmox environments into TESSA.
Handles discovery, analysis, and merging of existing Proxmox configurations.
"""
import logging
import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
import ipaddress

from ...api.proxmox_api import ProxmoxAPI
from ..automation.auto_configurator import ProxmoxAutoConfigurator

logger = logging.getLogger(__name__)

class EnvironmentMerger:
    """Class for detecting and merging existing Proxmox environments into TESSA"""
    
    def __init__(self, api: ProxmoxAPI, base_dir: str = None):
        """Initialize with Proxmox API connection"""
        self.api = api
        self.auto_configurator = ProxmoxAutoConfigurator(api)
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_dir = os.path.join(self.base_dir, 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.merger_config_path = os.path.join(self.config_dir, 'environment_merger.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load merger configuration or create default"""
        if os.path.exists(self.merger_config_path):
            try:
                with open(self.merger_config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading environment merger config: {str(e)}")
        
        # Default configuration
        return {
            "merge_options": {
                "storage_pools": True,
                "network_config": True,
                "virtual_machines": True,
                "containers": True,
                "users_and_permissions": False,  # More sensitive, off by default
                "backups": True,
                "firewall_rules": False,  # More sensitive, off by default
                "ha_settings": True
            },
            "conflict_resolution": "ask",  # Options: "ask", "tessa_priority", "existing_priority", "merge"
            "merged_environments": []
        }
    
    def _save_config(self) -> None:
        """Save configuration to file"""
        with open(self.merger_config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def discover_environment(self) -> Dict:
        """Discover details about the existing Proxmox environment"""
        try:
            result = {
                "success": True,
                "timestamp": None,
                "cluster": {
                    "name": None,
                    "quorum_status": None,
                    "ha_enabled": False,
                    "nodes": []
                },
                "resources": {
                    "vms": [],
                    "containers": [],
                    "storage": [],
                    "networks": []
                },
                "messages": []
            }
            
            # Get cluster status
            cluster_status = self.api.api_request('GET', 'cluster/status')
            if cluster_status['success']:
                for item in cluster_status['data']:
                    if item['type'] == 'cluster':
                        result['cluster']['name'] = item.get('name', 'unknown')
                        result['cluster']['quorum_status'] = item.get('quorate', 0)
                        result['timestamp'] = item.get('date')
                
                # Add nodes
                for item in cluster_status['data']:
                    if item['type'] == 'node':
                        result['cluster']['nodes'].append({
                            'name': item.get('name'),
                            'status': item.get('status'),
                            'ip': item.get('ip', 'unknown')
                        })
            else:
                result['messages'].append("Failed to get cluster status")
            
            # Get HA status
            ha_status = self.api.api_request('GET', 'cluster/ha/status')
            if ha_status['success']:
                result['cluster']['ha_enabled'] = len(ha_status['data']) > 0
            
            # Get VMs
            vms = self.api.api_request('GET', 'cluster/resources', {'type': 'vm'})
            if vms['success']:
                result['resources']['vms'] = vms['data']
            else:
                result['messages'].append("Failed to get VM list")
            
            # Get containers
            containers = self.api.api_request('GET', 'cluster/resources', {'type': 'lxc'})
            if containers['success']:
                result['resources']['containers'] = containers['data']
            else:
                result['messages'].append("Failed to get container list")
            
            # Get storage
            storage = self.api.api_request('GET', 'storage')
            if storage['success']:
                result['resources']['storage'] = storage['data']
            else:
                result['messages'].append("Failed to get storage list")
            
            # Get network for each node
            for node in result['cluster']['nodes']:
                node_name = node['name']
                networks = self.api.api_request('GET', f'nodes/{node_name}/network')
                if networks['success']:
                    for net in networks['data']:
                        if 'iface' in net:
                            net['node'] = node_name
                            result['resources']['networks'].append(net)
                else:
                    result['messages'].append(f"Failed to get network for node {node_name}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error discovering environment: {str(e)}")
            return {"success": False, "message": f"Error discovering environment: {str(e)}"}
    
    def analyze_environment(self, environment: Dict) -> Dict:
        """Analyze the discovered environment and identify merge points"""
        try:
            analysis = {
                "success": True,
                "cluster_info": {
                    "name": environment['cluster']['name'],
                    "nodes": len(environment['cluster']['nodes']),
                    "ha_status": "Enabled" if environment['cluster']['ha_enabled'] else "Disabled"
                },
                "resources": {
                    "vms": len(environment['resources']['vms']),
                    "containers": len(environment['resources']['containers']),
                    "storage_pools": len(environment['resources']['storage']),
                    "networks": len(environment['resources']['networks'])
                },
                "network": {
                    "subnets": {},
                    "vlans": []
                },
                "storage": {
                    "types": {},
                    "total_space_gb": 0
                },
                "recommendations": []
            }
            
            # Analyze networks
            vlan_patterns = []
            subnets = set()
            
            for network in environment['resources']['networks']:
                # Detect VLANs
                if 'iface' in network and '.' in network['iface']:
                    base, vlan = network['iface'].split('.')
                    try:
                        vlan_id = int(vlan)
                        if vlan_id not in analysis['network']['vlans']:
                            analysis['network']['vlans'].append(vlan_id)
                    except ValueError:
                        pass
                
                # Detect subnets
                if 'cidr' in network:
                    try:
                        subnet = ipaddress.ip_network(network['cidr'], strict=False)
                        subnet_key = str(subnet)
                        if subnet_key not in subnets:
                            subnets.add(subnet_key)
                            analysis['network']['subnets'][subnet_key] = {
                                'interfaces': [],
                                'gateway': None
                            }
                        
                        analysis['network']['subnets'][subnet_key]['interfaces'].append(
                            network['iface']
                        )
                        
                        # Try to identify gateway
                        if 'gateway' in network:
                            analysis['network']['subnets'][subnet_key]['gateway'] = network['gateway']
                    except (ValueError, ipaddress.AddressValueError):
                        pass
            
            # Analyze storage
            for storage in environment['resources']['storage']:
                storage_type = storage.get('type', 'unknown')
                if storage_type in analysis['storage']['types']:
                    analysis['storage']['types'][storage_type] += 1
                else:
                    analysis['storage']['types'][storage_type] = 1
                
                # Try to get storage size
                if 'total' in storage:
                    try:
                        size_gb = int(storage['total']) / (1024 * 1024 * 1024)
                        analysis['storage']['total_space_gb'] += size_gb
                    except (ValueError, TypeError):
                        pass
            
            # Generate recommendations
            if len(analysis['network']['vlans']) > 0:
                analysis['recommendations'].append(
                    "VLAN configurations detected. Consider reviewing network segmentation settings."
                )
            
            if 'zfs' in analysis['storage']['types']:
                analysis['recommendations'].append(
                    "ZFS storage pools found. TESSA can manage and optimize these pools."
                )
            
            if analysis['resources']['vms'] > 0:
                analysis['recommendations'].append(
                    f"Found {analysis['resources']['vms']} VMs that will be imported into TESSA."
                )
            
            if analysis['resources']['containers'] > 0:
                analysis['recommendations'].append(
                    f"Found {analysis['resources']['containers']} containers that will be imported into TESSA."
                )
            
            # Check if network overlaps with TESSA's default networks
            auto_config = self.auto_configurator._load_config()
            for profile_name, profile in auto_config['network']['network_profiles'].items():
                tessa_subnet = ipaddress.ip_network(profile['subnet'])
                for subnet in subnets:
                    existing_subnet = ipaddress.ip_network(subnet)
                    if tessa_subnet.overlaps(existing_subnet):
                        analysis['recommendations'].append(
                            f"Network conflict detected: Existing subnet {subnet} overlaps with TESSA's {profile_name} profile subnet {profile['subnet']}."
                        )
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing environment: {str(e)}")
            return {"success": False, "message": f"Error analyzing environment: {str(e)}"}
    
    def generate_merge_plan(self, environment: Dict, analysis: Dict) -> Dict:
        """Generate a plan for merging the environment"""
        try:
            merge_options = self.config['merge_options']
            conflict_resolution = self.config['conflict_resolution']
            
            plan = {
                "success": True,
                "actions": [],
                "conflicts": [],
                "config_updates": {
                    "network": {},
                    "storage": {},
                    "vms": [],
                    "containers": []
                }
            }
            
            # Plan network configuration imports
            if merge_options['network_config']:
                # Import existing subnets as network profiles
                for subnet, subnet_info in analysis['network']['subnets'].items():
                    profile_name = f"imported_{subnet.replace('.', '_').replace('/', '_')}"
                    plan['config_updates']['network'][profile_name] = {
                        "subnet": subnet,
                        "gateway": subnet_info['gateway'],
                        "dns_servers": ["1.1.1.1", "8.8.8.8"]  # Default DNS servers
                    }
                    
                    plan['actions'].append(
                        f"Create network profile '{profile_name}' with subnet {subnet} and gateway {subnet_info['gateway']}"
                    )
            
            # Plan storage imports
            if merge_options['storage_pools']:
                # Get all ZFS pools from environment
                zfs_pools = []
                for storage in environment['resources']['storage']:
                    if storage.get('type') == 'zfspool':
                        pool_name = storage.get('pool', '')
                        if pool_name and pool_name not in [p['name'] for p in zfs_pools]:
                            zfs_pools.append({
                                "name": pool_name,
                                "storage_name": storage.get('storage', '')
                            })
                
                # Add ZFS pools to TESSA's configuration
                for pool in zfs_pools:
                    plan['config_updates']['storage'][pool['name']] = {
                        "type": "zfspool",
                        "name": pool['name'],
                        "imported": True,
                        "storage_name": pool['storage_name']
                    }
                    
                    plan['actions'].append(
                        f"Import ZFS pool '{pool['name']}' into TESSA's storage configuration"
                    )
            
            # Plan VM imports
            if merge_options['virtual_machines']:
                for vm in environment['resources']['vms']:
                    vm_id = vm.get('vmid')
                    vm_name = vm.get('name')
                    if vm_id is not None and vm_name:
                        plan['config_updates']['vms'].append({
                            "vmid": vm_id,
                            "name": vm_name,
                            "status": vm.get('status', 'unknown'),
                            "node": vm.get('node', 'unknown')
                        })
                        
                        plan['actions'].append(
                            f"Import VM '{vm_name}' (ID: {vm_id}) into TESSA's VM inventory"
                        )
            
            # Plan container imports
            if merge_options['containers']:
                for ct in environment['resources']['containers']:
                    ct_id = ct.get('vmid')
                    ct_name = ct.get('name')
                    if ct_id is not None and ct_name:
                        plan['config_updates']['containers'].append({
                            "vmid": ct_id,
                            "name": ct_name,
                            "status": ct.get('status', 'unknown'),
                            "node": ct.get('node', 'unknown')
                        })
                        
                        plan['actions'].append(
                            f"Import container '{ct_name}' (ID: {ct_id}) into TESSA's container inventory"
                        )
            
            # Identify conflicts
            auto_config = self.auto_configurator._load_config()
            
            # Network conflicts
            for profile_name, profile in auto_config['network']['network_profiles'].items():
                tessa_subnet = ipaddress.ip_network(profile['subnet'])
                for subnet in analysis['network']['subnets']:
                    try:
                        existing_subnet = ipaddress.ip_network(subnet)
                        if tessa_subnet.overlaps(existing_subnet):
                            plan['conflicts'].append({
                                "type": "network_overlap",
                                "tessa": {
                                    "profile": profile_name,
                                    "subnet": profile['subnet']
                                },
                                "existing": {
                                    "subnet": subnet,
                                    "interfaces": analysis['network']['subnets'][subnet]['interfaces']
                                },
                                "resolution": conflict_resolution
                            })
                    except ValueError:
                        pass
            
            return plan
        
        except Exception as e:
            logger.error(f"Error generating merge plan: {str(e)}")
            return {"success": False, "message": f"Error generating merge plan: {str(e)}"}
    
    def execute_merge(self, plan: Dict) -> Dict:
        """Execute the merge plan to integrate an existing environment"""
        try:
            result = {
                "success": True,
                "merged_items": {
                    "networks": 0,
                    "storage": 0,
                    "vms": 0,
                    "containers": 0
                },
                "skipped_items": [],
                "errors": []
            }
            
            # Load current configurations
            auto_config = self.auto_configurator._load_config()
            
            # Update network configurations
            if self.config['merge_options']['network_config']:
                for profile_name, profile in plan['config_updates']['network'].items():
                    # Check for conflicts and handle according to resolution strategy
                    conflict = False
                    for conf in plan['conflicts']:
                        if conf['type'] == 'network_overlap' and conf['existing']['subnet'] == profile['subnet']:
                            conflict = True
                            if conf['resolution'] == 'existing_priority' or conf['resolution'] == 'merge':
                                # Allow the import even with conflict
                                pass
                            elif conf['resolution'] == 'tessa_priority':
                                # Skip this network
                                result['skipped_items'].append(f"Network profile '{profile_name}' due to conflict resolution")
                                continue
                            elif conf['resolution'] == 'ask':
                                # In a real implementation, we would prompt the user here
                                # For now, default to skipping
                                result['skipped_items'].append(f"Network profile '{profile_name}' due to unresolved conflict")
                                continue
                    
                    # Add the network profile
                    auto_config['network']['network_profiles'][profile_name] = {
                        "subnet": profile['subnet'],
                        "gateway": profile['gateway'],
                        "dns_servers": profile['dns_servers']
                    }
                    result['merged_items']['networks'] += 1
            
            # Update storage configurations
            if self.config['merge_options']['storage_pools']:
                # Update ZFS pool configurations for auto detection
                auto_config['storage']['detect_disks'] = True
                
                # Mark existing pools as imported so they're not recreated
                for pool_name, pool_info in plan['config_updates']['storage'].items():
                    # Find if this pool name already exists in the config
                    existing_pool = None
                    for pool in auto_config['storage']['zfs_pools']:
                        if pool['name'] == pool_name:
                            existing_pool = pool
                            break
                    
                    if existing_pool:
                        existing_pool['imported'] = True
                    else:
                        # Add as a new pool
                        new_pool = {
                            "name": pool_name,
                            "raid_level": "imported",  # Special flag for imported pools
                            "auto_detect": False,
                            "imported": True,  # Mark as imported
                            "disks": [],  # We don't know the underlying disks
                            "datasets": []  # We'll discover datasets later
                        }
                        auto_config['storage']['zfs_pools'].append(new_pool)
                    
                    result['merged_items']['storage'] += 1
            
            # Save the updated configuration
            self.auto_configurator.update_config(auto_config)
            
            # Record this environment as merged
            environment_id = f"env_{len(self.config['merged_environments']) + 1}"
            self.config['merged_environments'].append({
                "id": environment_id,
                "timestamp": plan.get('timestamp', None),
                "vm_count": len(plan['config_updates']['vms']),
                "container_count": len(plan['config_updates']['containers']),
                "network_count": len(plan['config_updates']['network']),
                "storage_count": len(plan['config_updates']['storage'])
            })
            self._save_config()
            
            # Report on the results
            result['message'] = (
                f"Successfully merged environment. "
                f"Added {result['merged_items']['networks']} network profiles, "
                f"{result['merged_items']['storage']} storage pools, "
                f"and prepared for {len(plan['config_updates']['vms'])} VMs "
                f"and {len(plan['config_updates']['containers'])} containers."
            )
            
            if result['skipped_items']:
                result['message'] += f" Skipped {len(result['skipped_items'])} items due to conflicts."
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing merge: {str(e)}")
            return {"success": False, "message": f"Error executing merge: {str(e)}"}
    
    def merge_existing_environment(self, conflict_resolution: str = None) -> Dict:
        """Main function to discover, analyze, plan, and execute a merge"""
        try:
            # Update conflict resolution if provided
            if conflict_resolution is not None:
                valid_resolutions = ["ask", "tessa_priority", "existing_priority", "merge"]
                if conflict_resolution in valid_resolutions:
                    self.config['conflict_resolution'] = conflict_resolution
                    self._save_config()
                else:
                    return {
                        "success": False,
                        "message": f"Invalid conflict resolution strategy. Valid options are: {', '.join(valid_resolutions)}"
                    }
            
            # Discover environment
            discovery_result = self.discover_environment()
            if not discovery_result['success']:
                return discovery_result
            
            # Analyze environment
            analysis_result = self.analyze_environment(discovery_result)
            if not analysis_result['success']:
                return analysis_result
            
            # Generate merge plan
            plan_result = self.generate_merge_plan(discovery_result, analysis_result)
            if not plan_result['success']:
                return plan_result
            
            # Execute merge
            merge_result = self.execute_merge(plan_result)
            
            # Add analysis and discovery data to the result
            merge_result['analysis'] = analysis_result
            merge_result['environment_summary'] = {
                "cluster_name": discovery_result['cluster']['name'],
                "nodes": len(discovery_result['cluster']['nodes']),
                "vms": len(discovery_result['resources']['vms']),
                "containers": len(discovery_result['resources']['containers'])
            }
            
            return merge_result
        
        except Exception as e:
            logger.error(f"Error in merge process: {str(e)}")
            return {"success": False, "message": f"Error in merge process: {str(e)}"}
    
    def set_merge_options(self, options: Dict) -> Dict:
        """Update the merge options"""
        try:
            for key, value in options.items():
                if key in self.config['merge_options']:
                    self.config['merge_options'][key] = bool(value)
            
            self._save_config()
            
            return {
                "success": True,
                "message": "Merge options updated successfully",
                "options": self.config['merge_options']
            }
        except Exception as e:
            logger.error(f"Error updating merge options: {str(e)}")
            return {"success": False, "message": f"Error updating merge options: {str(e)}"}
    
    def get_merge_history(self) -> Dict:
        """Get history of merged environments"""
        try:
            return {
                "success": True,
                "merged_environments": self.config['merged_environments']
            }
        except Exception as e:
            logger.error(f"Error getting merge history: {str(e)}")
            return {"success": False, "message": f"Error getting merge history: {str(e)}"}