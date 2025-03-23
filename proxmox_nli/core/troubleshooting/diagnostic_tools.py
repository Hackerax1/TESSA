"""
Diagnostic Tools for Proxmox NLI.
Provides tools for diagnosing common issues in Proxmox environments.
"""
import logging
import subprocess
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DiagnosticTools:
    """Collection of diagnostic tools for troubleshooting Proxmox environments."""
    
    def __init__(self, api):
        """Initialize the diagnostic tools.
        
        Args:
            api: Proxmox API client
        """
        self.api = api
        
        # Common diagnostic commands
        self.diagnostic_commands = {
            "network": {
                "connectivity": "ping -c 4 {target}",
                "dns": "nslookup {domain}",
                "routes": "ip route",
                "interfaces": "ip addr",
                "open_ports": "ss -tuln",
                "connections": "ss -tan state established",
                "firewall": "iptables -L -n"
            },
            "storage": {
                "disk_usage": "df -h",
                "disk_io": "iostat -x 1 5",
                "disk_health": "smartctl -a {device}",
                "zfs_status": "zpool status",
                "zfs_list": "zfs list",
                "lvm_status": "lvs"
            },
            "system": {
                "cpu_usage": "mpstat 1 5",
                "memory_usage": "free -h",
                "process_list": "ps aux --sort=-%cpu | head -20",
                "load_average": "uptime",
                "kernel_messages": "dmesg | tail -50",
                "service_status": "systemctl status {service}"
            },
            "proxmox": {
                "cluster_status": "pvecm status",
                "node_status": "pvenode status",
                "vm_list": "qm list",
                "container_list": "pct list",
                "storage_status": "pvesm status"
            }
        }
    
    def run_diagnostics(self, diagnostic_type: str, context: Dict = None) -> Dict:
        """Run diagnostics for a specific type.
        
        Args:
            diagnostic_type: Type of diagnostics to run (network, storage, system, proxmox)
            context: Additional context for the diagnostics
            
        Returns:
            Dict with diagnostic results
        """
        context = context or {}
        
        if diagnostic_type == "network":
            return self.check_network(context)
        elif diagnostic_type == "storage":
            return self.check_storage(context.get("node", "pve"), context.get("storage_id"))
        elif diagnostic_type == "system":
            return self.check_system(context.get("node", "pve"))
        elif diagnostic_type == "proxmox":
            return self.check_proxmox(context.get("node", "pve"))
        else:
            return {
                "success": False,
                "message": f"Unknown diagnostic type: {diagnostic_type}",
                "recommendations": ["Please specify a valid diagnostic type: network, storage, system, proxmox"]
            }
    
    def check_network(self, context: Dict = None) -> Dict:
        """Check network connectivity and configuration.
        
        Args:
            context: Additional context for network diagnostics
            
        Returns:
            Dict with network diagnostic results
        """
        context = context or {}
        results = {
            "success": True,
            "message": "Completed network diagnostics",
            "diagnostics": {},
            "issues": []
        }
        
        try:
            # Check internet connectivity
            target = context.get("target", "8.8.8.8")  # Default to Google DNS
            ping_cmd = self.diagnostic_commands["network"]["connectivity"].format(target=target)
            ping_output = self._run_command(ping_cmd)
            
            # Parse ping results
            if "100% packet loss" in ping_output:
                results["diagnostics"]["connectivity"] = {
                    "success": False,
                    "output": ping_output,
                    "summary": f"No connectivity to {target}"
                }
                results["issues"].append(f"No network connectivity to {target}")
            else:
                results["diagnostics"]["connectivity"] = {
                    "success": True,
                    "output": ping_output,
                    "summary": f"Connectivity to {target} confirmed"
                }
            
            # Check DNS resolution
            domain = context.get("domain", "google.com")
            dns_cmd = self.diagnostic_commands["network"]["dns"].format(domain=domain)
            dns_output = self._run_command(dns_cmd)
            
            # Parse DNS results
            if "server can't find" in dns_output or "SERVFAIL" in dns_output:
                results["diagnostics"]["dns"] = {
                    "success": False,
                    "output": dns_output,
                    "summary": f"DNS resolution failed for {domain}"
                }
                results["issues"].append(f"DNS resolution failed for {domain}")
            else:
                results["diagnostics"]["dns"] = {
                    "success": True,
                    "output": dns_output,
                    "summary": f"DNS resolution successful for {domain}"
                }
            
            # Check network interfaces
            interfaces_cmd = self.diagnostic_commands["network"]["interfaces"]
            interfaces_output = self._run_command(interfaces_cmd)
            
            # Parse interfaces results
            results["diagnostics"]["interfaces"] = {
                "success": True,
                "output": interfaces_output,
                "summary": "Network interfaces information"
            }
            
            # Check for interfaces without IP addresses
            if "inet" not in interfaces_output:
                results["issues"].append("No IP addresses configured on network interfaces")
            
            # Check routing table
            routes_cmd = self.diagnostic_commands["network"]["routes"]
            routes_output = self._run_command(routes_cmd)
            
            # Parse routes results
            results["diagnostics"]["routes"] = {
                "success": True,
                "output": routes_output,
                "summary": "Routing table information"
            }
            
            # Check for default route
            if "default" not in routes_output:
                results["issues"].append("No default route configured")
            
            # Check open ports
            ports_cmd = self.diagnostic_commands["network"]["open_ports"]
            ports_output = self._run_command(ports_cmd)
            
            # Parse open ports results
            results["diagnostics"]["open_ports"] = {
                "success": True,
                "output": ports_output,
                "summary": "Open ports information"
            }
            
            # Check firewall rules
            firewall_cmd = self.diagnostic_commands["network"]["firewall"]
            firewall_output = self._run_command(firewall_cmd)
            
            # Parse firewall results
            results["diagnostics"]["firewall"] = {
                "success": True,
                "output": firewall_output,
                "summary": "Firewall rules information"
            }
            
        except Exception as e:
            logger.error(f"Error running network diagnostics: {str(e)}")
            results["success"] = False
            results["message"] = f"Error running network diagnostics: {str(e)}"
        
        return results
    
    def check_storage(self, node: str = "pve", storage_id: str = None) -> Dict:
        """Check storage health and configuration.
        
        Args:
            node: Node to check storage on
            storage_id: Specific storage ID to check
            
        Returns:
            Dict with storage diagnostic results
        """
        results = {
            "success": True,
            "message": f"Completed storage diagnostics for node {node}",
            "diagnostics": {},
            "issues": []
        }
        
        try:
            # Get storage information from Proxmox API
            if storage_id:
                storage_info = self.api.nodes(node).storage(storage_id).status.get()
                results["storage_info"] = storage_info
                
                # Check storage status
                if storage_info.get("status") != "available":
                    results["issues"].append(f"Storage {storage_id} is not available (status: {storage_info.get('status')})")
                
                # Check disk usage
                if "used" in storage_info and "total" in storage_info:
                    used_percent = (storage_info["used"] / storage_info["total"]) * 100
                    if used_percent > 90:
                        results["issues"].append(f"Storage {storage_id} is nearly full ({used_percent:.1f}% used)")
            else:
                # Get all storage information
                storage_list = self.api.nodes(node).storage.get()
                results["storage_list"] = storage_list
                
                # Check each storage
                for storage in storage_list:
                    if storage.get("status") != "available":
                        results["issues"].append(f"Storage {storage.get('storage')} is not available (status: {storage.get('status')})")
                    
                    # Check disk usage
                    if "used" in storage and "total" in storage:
                        used_percent = (storage["used"] / storage["total"]) * 100
                        if used_percent > 90:
                            results["issues"].append(f"Storage {storage.get('storage')} is nearly full ({used_percent:.1f}% used)")
            
            # Check disk usage with df command
            disk_usage_cmd = self.diagnostic_commands["storage"]["disk_usage"]
            disk_usage_output = self._run_command(disk_usage_cmd)
            
            # Parse disk usage results
            results["diagnostics"]["disk_usage"] = {
                "success": True,
                "output": disk_usage_output,
                "summary": "Disk usage information"
            }
            
            # Check for filesystems with high usage
            for line in disk_usage_output.splitlines():
                if line.startswith("/"):
                    parts = line.split()
                    if len(parts) >= 5:
                        usage = parts[4].rstrip("%")
                        try:
                            usage_percent = int(usage)
                            if usage_percent > 90:
                                results["issues"].append(f"Filesystem {parts[0]} is nearly full ({usage_percent}% used)")
                        except ValueError:
                            pass
            
            # Check disk I/O
            disk_io_cmd = self.diagnostic_commands["storage"]["disk_io"]
            disk_io_output = self._run_command(disk_io_cmd)
            
            # Parse disk I/O results
            results["diagnostics"]["disk_io"] = {
                "success": True,
                "output": disk_io_output,
                "summary": "Disk I/O information"
            }
            
            # Check for high disk I/O wait time
            high_io_wait = False
            for line in disk_io_output.splitlines():
                if "avg-cpu" in line:
                    continue
                if "Device" in line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 10:
                    try:
                        await_percent = float(parts[9])
                        if await_percent > 100:
                            high_io_wait = True
                            break
                    except (ValueError, IndexError):
                        pass
            
            if high_io_wait:
                results["issues"].append("High disk I/O wait time detected, possible disk bottleneck")
            
            # Check ZFS status if available
            zfs_status_cmd = self.diagnostic_commands["storage"]["zfs_status"]
            zfs_status_output = self._run_command(zfs_status_cmd)
            
            # Parse ZFS status results
            if "no pools available" not in zfs_status_output:
                results["diagnostics"]["zfs_status"] = {
                    "success": True,
                    "output": zfs_status_output,
                    "summary": "ZFS pool status information"
                }
                
                # Check for ZFS pool issues
                if "state: DEGRADED" in zfs_status_output or "state: FAULTED" in zfs_status_output:
                    results["issues"].append("ZFS pool is in degraded or faulted state")
                
                if "errors:" in zfs_status_output and "No known data errors" not in zfs_status_output:
                    results["issues"].append("ZFS pool has data errors")
            
        except Exception as e:
            logger.error(f"Error running storage diagnostics: {str(e)}")
            results["success"] = False
            results["message"] = f"Error running storage diagnostics: {str(e)}"
        
        return results
    
    def check_system(self, node: str = "pve") -> Dict:
        """Check system health and configuration.
        
        Args:
            node: Node to check system on
            
        Returns:
            Dict with system diagnostic results
        """
        results = {
            "success": True,
            "message": f"Completed system diagnostics for node {node}",
            "diagnostics": {},
            "issues": []
        }
        
        try:
            # Get node status from Proxmox API
            node_status = self.api.nodes(node).status.get()
            results["node_status"] = node_status
            
            # Check CPU usage
            if "cpu" in node_status:
                cpu_usage = node_status["cpu"] * 100  # Convert to percentage
                if cpu_usage > 90:
                    results["issues"].append(f"High CPU usage: {cpu_usage:.1f}%")
            
            # Check memory usage
            if "memory" in node_status and "total" in node_status["memory"]:
                memory_used = node_status["memory"]["used"]
                memory_total = node_status["memory"]["total"]
                memory_percent = (memory_used / memory_total) * 100
                if memory_percent > 90:
                    results["issues"].append(f"High memory usage: {memory_percent:.1f}%")
            
            # Check load average
            if "loadavg" in node_status:
                load_avg = node_status["loadavg"][0]  # 1-minute load average
                cpu_count = node_status.get("cpuinfo", {}).get("cpus", 1)
                load_per_cpu = load_avg / cpu_count
                if load_per_cpu > 1.5:
                    results["issues"].append(f"High system load: {load_avg:.2f} (load per CPU: {load_per_cpu:.2f})")
            
            # Check CPU usage with mpstat command
            cpu_usage_cmd = self.diagnostic_commands["system"]["cpu_usage"]
            cpu_usage_output = self._run_command(cpu_usage_cmd)
            
            # Parse CPU usage results
            results["diagnostics"]["cpu_usage"] = {
                "success": True,
                "output": cpu_usage_output,
                "summary": "CPU usage information"
            }
            
            # Check memory usage with free command
            memory_usage_cmd = self.diagnostic_commands["system"]["memory_usage"]
            memory_usage_output = self._run_command(memory_usage_cmd)
            
            # Parse memory usage results
            results["diagnostics"]["memory_usage"] = {
                "success": True,
                "output": memory_usage_output,
                "summary": "Memory usage information"
            }
            
            # Check process list
            process_list_cmd = self.diagnostic_commands["system"]["process_list"]
            process_list_output = self._run_command(process_list_cmd)
            
            # Parse process list results
            results["diagnostics"]["process_list"] = {
                "success": True,
                "output": process_list_output,
                "summary": "Top CPU-consuming processes"
            }
            
            # Check kernel messages
            kernel_messages_cmd = self.diagnostic_commands["system"]["kernel_messages"]
            kernel_messages_output = self._run_command(kernel_messages_cmd)
            
            # Parse kernel messages results
            results["diagnostics"]["kernel_messages"] = {
                "success": True,
                "output": kernel_messages_output,
                "summary": "Recent kernel messages"
            }
            
            # Check for kernel errors
            if "error" in kernel_messages_output.lower() or "fail" in kernel_messages_output.lower():
                results["issues"].append("Kernel errors detected in dmesg output")
            
        except Exception as e:
            logger.error(f"Error running system diagnostics: {str(e)}")
            results["success"] = False
            results["message"] = f"Error running system diagnostics: {str(e)}"
        
        return results
    
    def check_proxmox(self, node: str = "pve") -> Dict:
        """Check Proxmox-specific configuration and status.
        
        Args:
            node: Node to check Proxmox on
            
        Returns:
            Dict with Proxmox diagnostic results
        """
        results = {
            "success": True,
            "message": f"Completed Proxmox diagnostics for node {node}",
            "diagnostics": {},
            "issues": []
        }
        
        try:
            # Check cluster status
            cluster_status_cmd = self.diagnostic_commands["proxmox"]["cluster_status"]
            cluster_status_output = self._run_command(cluster_status_cmd)
            
            # Parse cluster status results
            results["diagnostics"]["cluster_status"] = {
                "success": True,
                "output": cluster_status_output,
                "summary": "Cluster status information"
            }
            
            # Check for cluster issues
            if "not running" in cluster_status_output or "no quorum" in cluster_status_output:
                results["issues"].append("Cluster is not running or has no quorum")
            
            # Check node status
            node_status_cmd = self.diagnostic_commands["proxmox"]["node_status"]
            node_status_output = self._run_command(node_status_cmd)
            
            # Parse node status results
            results["diagnostics"]["node_status"] = {
                "success": True,
                "output": node_status_output,
                "summary": "Node status information"
            }
            
            # Check VM list
            vm_list_cmd = self.diagnostic_commands["proxmox"]["vm_list"]
            vm_list_output = self._run_command(vm_list_cmd)
            
            # Parse VM list results
            results["diagnostics"]["vm_list"] = {
                "success": True,
                "output": vm_list_output,
                "summary": "VM list information"
            }
            
            # Check container list
            container_list_cmd = self.diagnostic_commands["proxmox"]["container_list"]
            container_list_output = self._run_command(container_list_cmd)
            
            # Parse container list results
            results["diagnostics"]["container_list"] = {
                "success": True,
                "output": container_list_output,
                "summary": "Container list information"
            }
            
            # Check storage status
            storage_status_cmd = self.diagnostic_commands["proxmox"]["storage_status"]
            storage_status_output = self._run_command(storage_status_cmd)
            
            # Parse storage status results
            results["diagnostics"]["storage_status"] = {
                "success": True,
                "output": storage_status_output,
                "summary": "Storage status information"
            }
            
            # Check for storage issues
            if "inactive" in storage_status_output or "error" in storage_status_output:
                results["issues"].append("One or more storage resources are inactive or have errors")
            
            # Get version information
            version_info = self.api.version.get()
            results["version_info"] = version_info
            
            # Check subscription status
            try:
                subscription_info = self.api.nodes(node).subscription.get()
                results["subscription_info"] = subscription_info
                
                # Check subscription status
                if subscription_info.get("status") != "Active":
                    results["issues"].append(f"Proxmox subscription is not active (status: {subscription_info.get('status')})")
            except Exception:
                # Subscription API might not be available in free version
                pass
            
        except Exception as e:
            logger.error(f"Error running Proxmox diagnostics: {str(e)}")
            results["success"] = False
            results["message"] = f"Error running Proxmox diagnostics: {str(e)}"
        
        return results
    
    def _run_command(self, command: str) -> str:
        """Run a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command execution failed: {str(e)}")
            return e.stdout if e.stdout else ""
