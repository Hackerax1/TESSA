"""
Self-Healing Tools for Proxmox NLI.
Provides automated remediation capabilities for common issues in Proxmox environments.
"""
import logging
import subprocess
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SelfHealingTools:
    """Provides automated remediation capabilities for common Proxmox issues."""
    
    def __init__(self, api):
        """Initialize the self-healing tools.
        
        Args:
            api: Proxmox API client
        """
        self.api = api
        
        # Common remediation commands
        self.remediation_commands = {
            "service": {
                "restart": "systemctl restart {service}",
                "start": "systemctl start {service}",
                "stop": "systemctl stop {service}",
                "enable": "systemctl enable {service}",
                "disable": "systemctl disable {service}"
            },
            "network": {
                "restart_networking": "systemctl restart networking",
                "restart_interface": "ifdown {interface} && ifup {interface}",
                "flush_dns": "systemd-resolve --flush-caches",
                "clear_arp": "ip neigh flush all"
            },
            "storage": {
                "clear_cache": "echo 3 > /proc/sys/vm/drop_caches",
                "repair_zfs": "zpool scrub {pool}",
                "check_fs": "fsck -y {device}",
                "mount": "mount {device} {mountpoint}"
            },
            "proxmox": {
                "restart_pve": "systemctl restart pve-cluster",
                "restart_pveproxy": "systemctl restart pveproxy",
                "restart_corosync": "systemctl restart corosync",
                "restart_ceph": "systemctl restart ceph-mon@$(hostname -s)"
            }
        }
    
    def apply_remediation(self, issue_type: str, context: Dict = None) -> Dict:
        """Apply automated remediation for a specific issue type.
        
        Args:
            issue_type: Type of issue to remediate
            context: Additional context for remediation
            
        Returns:
            Dict with remediation results
        """
        context = context or {}
        
        if issue_type == "service_down":
            return self.fix_service_issue(context.get("service"), context.get("node", "pve"))
        elif issue_type == "network_connectivity":
            return self.fix_network_connectivity(context)
        elif issue_type == "storage_issue":
            return self.fix_storage_issue(context)
        elif issue_type == "high_load":
            return self.fix_high_load(context.get("node", "pve"))
        elif issue_type == "cluster_issue":
            return self.fix_cluster_issue(context.get("node", "pve"))
        else:
            return {
                "success": False,
                "message": f"Unknown issue type: {issue_type}",
                "recommendations": ["Please specify a valid issue type: service_down, network_connectivity, storage_issue, high_load, cluster_issue"]
            }
    
    def fix_service_issue(self, service: str, node: str = "pve") -> Dict:
        """Fix issues with a service.
        
        Args:
            service: Service to fix
            node: Node to fix service on
            
        Returns:
            Dict with service remediation results
        """
        if not service:
            return {
                "success": False,
                "message": "No service specified",
                "recommendations": ["Please specify a service to fix"]
            }
        
        results = {
            "success": True,
            "message": f"Attempted to fix service {service} on node {node}",
            "actions_taken": [],
            "recommendations": []
        }
        
        try:
            # Check service status
            status_cmd = f"systemctl is-active {service}"
            status_output = self._run_command(status_cmd)
            
            if "inactive" in status_output or "failed" in status_output:
                # Service is down, try to start it
                start_cmd = self.remediation_commands["service"]["start"].format(service=service)
                start_output = self._run_command(start_cmd)
                
                results["actions_taken"].append(f"Started service {service}")
                
                # Check if service started successfully
                status_output = self._run_command(status_cmd)
                if "active" in status_output:
                    results["message"] = f"Successfully started service {service}"
                else:
                    # Service failed to start, try restarting
                    restart_cmd = self.remediation_commands["service"]["restart"].format(service=service)
                    restart_output = self._run_command(restart_cmd)
                    
                    results["actions_taken"].append(f"Restarted service {service}")
                    
                    # Check if service restarted successfully
                    status_output = self._run_command(status_cmd)
                    if "active" in status_output:
                        results["message"] = f"Successfully restarted service {service}"
                    else:
                        results["success"] = False
                        results["message"] = f"Failed to start or restart service {service}"
                        results["recommendations"].append(f"Check service logs: journalctl -u {service}")
                        results["recommendations"].append(f"Check service configuration")
            else:
                # Service is running, try restarting it
                restart_cmd = self.remediation_commands["service"]["restart"].format(service=service)
                restart_output = self._run_command(restart_cmd)
                
                results["actions_taken"].append(f"Restarted service {service}")
                
                # Check if service restarted successfully
                status_output = self._run_command(status_cmd)
                if "active" in status_output:
                    results["message"] = f"Successfully restarted service {service}"
                else:
                    results["success"] = False
                    results["message"] = f"Service {service} failed to restart"
                    results["recommendations"].append(f"Check service logs: journalctl -u {service}")
                    results["recommendations"].append(f"Check service configuration")
            
            # Check if service is enabled
            enabled_cmd = f"systemctl is-enabled {service}"
            enabled_output = self._run_command(enabled_cmd)
            
            if "disabled" in enabled_output:
                # Service is disabled, recommend enabling it
                results["recommendations"].append(f"Consider enabling service {service} to start on boot")
        
        except Exception as e:
            logger.error(f"Error fixing service {service}: {str(e)}")
            results["success"] = False
            results["message"] = f"Error fixing service {service}: {str(e)}"
        
        return results
    
    def fix_network_connectivity(self, context: Dict = None) -> Dict:
        """Fix network connectivity issues.
        
        Args:
            context: Additional context for network remediation
            
        Returns:
            Dict with network remediation results
        """
        context = context or {}
        
        results = {
            "success": True,
            "message": "Attempted to fix network connectivity issues",
            "actions_taken": [],
            "recommendations": []
        }
        
        try:
            # Determine what to fix based on context
            if "interface" in context:
                # Fix specific interface
                interface = context["interface"]
                restart_cmd = self.remediation_commands["network"]["restart_interface"].format(interface=interface)
                restart_output = self._run_command(restart_cmd)
                
                results["actions_taken"].append(f"Restarted network interface {interface}")
                results["message"] = f"Restarted network interface {interface}"
                
                # Check if interface is up
                check_cmd = f"ip link show {interface}"
                check_output = self._run_command(check_cmd)
                
                if "UP" not in check_output:
                    # Interface is still down
                    up_cmd = f"ip link set {interface} up"
                    up_output = self._run_command(up_cmd)
                    
                    results["actions_taken"].append(f"Brought up network interface {interface}")
                    
                    # Check again
                    check_output = self._run_command(check_cmd)
                    if "UP" in check_output:
                        results["message"] = f"Successfully brought up network interface {interface}"
                    else:
                        results["success"] = False
                        results["message"] = f"Failed to bring up network interface {interface}"
                        results["recommendations"].append("Check network interface hardware")
                        results["recommendations"].append("Check network interface configuration")
            
            elif "dns" in context:
                # Fix DNS issues
                flush_cmd = self.remediation_commands["network"]["flush_dns"]
                flush_output = self._run_command(flush_cmd)
                
                results["actions_taken"].append("Flushed DNS cache")
                results["message"] = "Flushed DNS cache"
                
                # Check resolv.conf
                check_cmd = "cat /etc/resolv.conf"
                check_output = self._run_command(check_cmd)
                
                if "nameserver" not in check_output:
                    # No nameservers configured
                    results["success"] = False
                    results["message"] = "No DNS nameservers configured"
                    results["recommendations"].append("Configure DNS nameservers in /etc/resolv.conf")
                    results["recommendations"].append("Check network configuration for DHCP DNS settings")
            
            else:
                # General network fix
                restart_cmd = self.remediation_commands["network"]["restart_networking"]
                restart_output = self._run_command(restart_cmd)
                
                results["actions_taken"].append("Restarted networking service")
                
                # Clear ARP cache
                arp_cmd = self.remediation_commands["network"]["clear_arp"]
                arp_output = self._run_command(arp_cmd)
                
                results["actions_taken"].append("Cleared ARP cache")
                results["message"] = "Restarted networking service and cleared ARP cache"
                
                # Check connectivity
                ping_cmd = "ping -c 1 8.8.8.8"
                ping_output = self._run_command(ping_cmd)
                
                if "100% packet loss" in ping_output:
                    # Still no connectivity
                    results["success"] = False
                    results["message"] = "Network connectivity issues persist"
                    results["recommendations"].append("Check physical network connections")
                    results["recommendations"].append("Check router/gateway configuration")
                    results["recommendations"].append("Check firewall rules")
        
        except Exception as e:
            logger.error(f"Error fixing network connectivity: {str(e)}")
            results["success"] = False
            results["message"] = f"Error fixing network connectivity: {str(e)}"
        
        return results
    
    def fix_storage_issue(self, context: Dict = None) -> Dict:
        """Fix storage issues.
        
        Args:
            context: Additional context for storage remediation
            
        Returns:
            Dict with storage remediation results
        """
        context = context or {}
        
        results = {
            "success": True,
            "message": "Attempted to fix storage issues",
            "actions_taken": [],
            "recommendations": []
        }
        
        try:
            # Determine what to fix based on context
            if "pool" in context and "zfs" in context:
                # Fix ZFS pool
                pool = context["pool"]
                repair_cmd = self.remediation_commands["storage"]["repair_zfs"].format(pool=pool)
                repair_output = self._run_command(repair_cmd)
                
                results["actions_taken"].append(f"Started scrub on ZFS pool {pool}")
                results["message"] = f"Started scrub on ZFS pool {pool}"
                results["recommendations"].append(f"Check scrub progress: zpool status {pool}")
                
            elif "device" in context and "filesystem" in context:
                # Fix filesystem
                device = context["device"]
                check_cmd = self.remediation_commands["storage"]["check_fs"].format(device=device)
                
                # Only run fsck if device is not mounted
                mount_check_cmd = f"mount | grep {device}"
                mount_check_output = self._run_command(mount_check_cmd)
                
                if not mount_check_output:
                    # Device is not mounted, safe to run fsck
                    check_output = self._run_command(check_cmd)
                    
                    results["actions_taken"].append(f"Checked and repaired filesystem on {device}")
                    results["message"] = f"Checked and repaired filesystem on {device}"
                    
                    if "mountpoint" in context:
                        # Mount the device
                        mountpoint = context["mountpoint"]
                        mount_cmd = self.remediation_commands["storage"]["mount"].format(device=device, mountpoint=mountpoint)
                        mount_output = self._run_command(mount_cmd)
                        
                        results["actions_taken"].append(f"Mounted {device} to {mountpoint}")
                else:
                    results["success"] = False
                    results["message"] = f"Device {device} is currently mounted, cannot run filesystem check"
                    results["recommendations"].append(f"Unmount the device first: umount {device}")
                    results["recommendations"].append("Schedule a filesystem check on next reboot")
            
            else:
                # General storage fix
                clear_cmd = self.remediation_commands["storage"]["clear_cache"]
                clear_output = self._run_command(clear_cmd)
                
                results["actions_taken"].append("Cleared system caches")
                results["message"] = "Cleared system caches"
                
                # Check disk usage
                check_cmd = "df -h"
                check_output = self._run_command(check_cmd)
                
                # Look for filesystems with high usage
                for line in check_output.splitlines():
                    if line.startswith("/"):
                        parts = line.split()
                        if len(parts) >= 5 and parts[4].endswith("%"):
                            usage = int(parts[4].rstrip("%"))
                            if usage > 90:
                                results["recommendations"].append(f"Filesystem {parts[0]} is nearly full ({usage}%), consider freeing up space")
        
        except Exception as e:
            logger.error(f"Error fixing storage issues: {str(e)}")
            results["success"] = False
            results["message"] = f"Error fixing storage issues: {str(e)}"
        
        return results
    
    def fix_high_load(self, node: str = "pve") -> Dict:
        """Fix high system load issues.
        
        Args:
            node: Node to fix high load on
            
        Returns:
            Dict with high load remediation results
        """
        results = {
            "success": True,
            "message": f"Attempted to fix high load issues on node {node}",
            "actions_taken": [],
            "recommendations": []
        }
        
        try:
            # Check for resource-intensive processes
            check_cmd = "ps aux --sort=-%cpu | head -10"
            check_output = self._run_command(check_cmd)
            
            results["process_info"] = check_output
            
            # Clear system caches
            clear_cmd = self.remediation_commands["storage"]["clear_cache"]
            clear_output = self._run_command(clear_cmd)
            
            results["actions_taken"].append("Cleared system caches")
            
            # Check if any Proxmox services are consuming high resources
            pve_check_cmd = "ps aux | grep pve | grep -v grep"
            pve_check_output = self._run_command(pve_check_cmd)
            
            high_cpu_pve_services = []
            for line in pve_check_output.splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        cpu_usage = float(parts[2])
                        if cpu_usage > 50:  # More than 50% CPU usage
                            service_name = parts[10] if len(parts) > 10 else "unknown"
                            high_cpu_pve_services.append((service_name, cpu_usage))
                    except (ValueError, IndexError):
                        pass
            
            if high_cpu_pve_services:
                # Restart high CPU Proxmox services
                for service_name, cpu_usage in high_cpu_pve_services:
                    if "pveproxy" in service_name:
                        restart_cmd = self.remediation_commands["proxmox"]["restart_pveproxy"]
                        restart_output = self._run_command(restart_cmd)
                        
                        results["actions_taken"].append("Restarted pveproxy service")
                    elif "pve-cluster" in service_name:
                        restart_cmd = self.remediation_commands["proxmox"]["restart_pve"]
                        restart_output = self._run_command(restart_cmd)
                        
                        results["actions_taken"].append("Restarted pve-cluster service")
            
            # Check for high I/O wait
            io_check_cmd = "iostat -x 1 2 | tail -n +4"
            io_check_output = self._run_command(io_check_cmd)
            
            high_io_wait = False
            for line in io_check_output.splitlines():
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
                # Clear caches again
                self._run_command(clear_cmd)
                results["actions_taken"].append("Cleared system caches to reduce I/O pressure")
                results["recommendations"].append("Consider upgrading storage devices or reducing I/O load")
            
            # Provide recommendations based on load type
            load_cmd = "uptime"
            load_output = self._run_command(load_cmd)
            
            # Extract load averages
            load_match = re.search(r"load average: ([\d.]+), ([\d.]+), ([\d.]+)", load_output)
            if load_match:
                load_1m = float(load_match.group(1))
                load_5m = float(load_match.group(2))
                load_15m = float(load_match.group(3))
                
                # Get CPU count
                cpu_cmd = "nproc"
                cpu_output = self._run_command(cpu_cmd)
                cpu_count = int(cpu_output.strip())
                
                # Calculate load per CPU
                load_per_cpu_1m = load_1m / cpu_count
                load_per_cpu_5m = load_5m / cpu_count
                
                if load_per_cpu_1m > load_per_cpu_5m:
                    # Short-term spike
                    results["recommendations"].append("Current load is a short-term spike, consider waiting for it to subside")
                else:
                    # Sustained high load
                    results["recommendations"].append("System is experiencing sustained high load, consider resource allocation adjustments")
                    
                if load_per_cpu_1m > 1.5:
                    results["recommendations"].append("CPU resources are overcommitted, consider reducing VM/container CPU allocations")
        
        except Exception as e:
            logger.error(f"Error fixing high load issues: {str(e)}")
            results["success"] = False
            results["message"] = f"Error fixing high load issues: {str(e)}"
        
        return results
    
    def fix_cluster_issue(self, node: str = "pve") -> Dict:
        """Fix Proxmox cluster issues.
        
        Args:
            node: Node to fix cluster issues on
            
        Returns:
            Dict with cluster remediation results
        """
        results = {
            "success": True,
            "message": f"Attempted to fix cluster issues on node {node}",
            "actions_taken": [],
            "recommendations": []
        }
        
        try:
            # Check cluster status
            status_cmd = "pvecm status"
            status_output = self._run_command(status_cmd)
            
            results["cluster_status"] = status_output
            
            if "not initialized" in status_output:
                # Cluster not initialized
                results["success"] = False
                results["message"] = "Cluster is not initialized"
                results["recommendations"].append("Initialize cluster: pvecm create")
                return results
            
            if "no quorum" in status_output:
                # No quorum
                results["message"] = "Cluster has no quorum"
                
                # Check if this is the only node
                if "1 nodes" in status_output:
                    # Single node cluster, force quorum
                    force_cmd = "pvecm expected 1"
                    force_output = self._run_command(force_cmd)
                    
                    results["actions_taken"].append("Forced quorum on single-node cluster")
                    results["message"] = "Forced quorum on single-node cluster"
                else:
                    # Multi-node cluster
                    results["recommendations"].append("Check other cluster nodes")
                    results["recommendations"].append("Ensure majority of nodes are online")
                    results["recommendations"].append("If needed, force quorum: pvecm expected <n>")
            
            # Restart corosync
            restart_cmd = self.remediation_commands["proxmox"]["restart_corosync"]
            restart_output = self._run_command(restart_cmd)
            
            results["actions_taken"].append("Restarted corosync service")
            
            # Wait for corosync to start
            time.sleep(5)
            
            # Restart pve-cluster
            pve_restart_cmd = self.remediation_commands["proxmox"]["restart_pve"]
            pve_restart_output = self._run_command(pve_restart_cmd)
            
            results["actions_taken"].append("Restarted pve-cluster service")
            
            # Check cluster status again
            status_output = self._run_command(status_cmd)
            
            if "no quorum" in status_output:
                # Still no quorum
                results["success"] = False
                results["message"] = "Cluster still has no quorum after service restarts"
                results["recommendations"].append("Check network connectivity between cluster nodes")
                results["recommendations"].append("Check corosync configuration")
                results["recommendations"].append("Consider manual cluster repair")
            else:
                results["message"] = "Successfully restored cluster services"
        
        except Exception as e:
            logger.error(f"Error fixing cluster issues: {str(e)}")
            results["success"] = False
            results["message"] = f"Error fixing cluster issues: {str(e)}"
        
        return results
    
    def _run_command(self, command: str) -> str:
        """Run a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command execution failed: {str(e)}")
            return e.stdout if e.stdout else ""
