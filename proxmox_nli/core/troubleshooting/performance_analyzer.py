"""
Performance Analyzer for Proxmox NLI.
Provides tools for analyzing system performance and detecting bottlenecks.
"""
import logging
import subprocess
import re
import json
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """Analyzes system performance and detects bottlenecks."""
    
    def __init__(self, api):
        """Initialize the performance analyzer.
        
        Args:
            api: Proxmox API client
        """
        self.api = api
        
        # Performance monitoring commands
        self.monitoring_commands = {
            "cpu": {
                "usage": "mpstat -P ALL 1 5",
                "load": "uptime",
                "top_processes": "ps aux --sort=-%cpu | head -10"
            },
            "memory": {
                "usage": "free -m",
                "detailed": "vmstat -s",
                "top_processes": "ps aux --sort=-%mem | head -10"
            },
            "disk": {
                "usage": "df -h",
                "io": "iostat -x 1 5",
                "top_processes": "iotop -b -n 2 -o"
            },
            "network": {
                "interfaces": "ifstat -a 1 5",
                "connections": "netstat -tunapl | grep ESTABLISHED | wc -l",
                "top_processes": "nethogs -t -c 5"
            }
        }
    
    def analyze_performance(self, resource_type: str = None, context: Dict = None) -> Dict:
        """Analyze system performance.
        
        Args:
            resource_type: Type of resource to analyze (cpu, memory, disk, network, all)
            context: Additional context for performance analysis
            
        Returns:
            Dict with performance analysis results
        """
        context = context or {}
        
        if resource_type == "cpu":
            return self.analyze_cpu_performance(context.get("node", "pve"))
        elif resource_type == "memory":
            return self.analyze_memory_performance(context.get("node", "pve"))
        elif resource_type == "disk":
            return self.analyze_disk_performance(context.get("node", "pve"), context.get("storage_id"))
        elif resource_type == "network":
            return self.analyze_network_performance(context.get("node", "pve"), context.get("interface"))
        else:
            # Analyze all resources
            return self.analyze_all_performance(context.get("node", "pve"))
    
    def analyze_all_performance(self, node: str = "pve") -> Dict:
        """Analyze performance of all resources.
        
        Args:
            node: Node to analyze performance on
            
        Returns:
            Dict with comprehensive performance analysis results
        """
        results = {
            "success": True,
            "message": f"Analyzed performance of all resources on node {node}",
            "bottlenecks": [],
            "recommendations": []
        }
        
        # Analyze CPU performance
        cpu_results = self.analyze_cpu_performance(node)
        results["cpu"] = cpu_results
        
        if cpu_results.get("bottleneck", False):
            results["bottlenecks"].append("CPU")
            results["recommendations"].extend(cpu_results.get("recommendations", []))
        
        # Analyze memory performance
        memory_results = self.analyze_memory_performance(node)
        results["memory"] = memory_results
        
        if memory_results.get("bottleneck", False):
            results["bottlenecks"].append("Memory")
            results["recommendations"].extend(memory_results.get("recommendations", []))
        
        # Analyze disk performance
        disk_results = self.analyze_disk_performance(node)
        results["disk"] = disk_results
        
        if disk_results.get("bottleneck", False):
            results["bottlenecks"].append("Disk")
            results["recommendations"].extend(disk_results.get("recommendations", []))
        
        # Analyze network performance
        network_results = self.analyze_network_performance(node)
        results["network"] = network_results
        
        if network_results.get("bottleneck", False):
            results["bottlenecks"].append("Network")
            results["recommendations"].extend(network_results.get("recommendations", []))
        
        # Generate overall summary
        if results["bottlenecks"]:
            results["message"] = f"Detected bottlenecks in: {', '.join(results['bottlenecks'])}"
        else:
            results["message"] = "No performance bottlenecks detected"
        
        return results
    
    def analyze_cpu_performance(self, node: str = "pve") -> Dict:
        """Analyze CPU performance.
        
        Args:
            node: Node to analyze CPU performance on
            
        Returns:
            Dict with CPU performance analysis results
        """
        results = {
            "success": True,
            "message": f"Analyzed CPU performance on node {node}",
            "bottleneck": False,
            "metrics": {},
            "recommendations": []
        }
        
        try:
            # Get node CPU information from Proxmox API
            node_status = self.api.nodes(node).status.get()
            
            if "cpu" in node_status:
                cpu_usage = node_status["cpu"] * 100  # Convert to percentage
                results["metrics"]["usage_percent"] = cpu_usage
                
                if cpu_usage > 80:
                    results["bottleneck"] = True
                    results["message"] = f"High CPU usage detected: {cpu_usage:.1f}%"
                    results["recommendations"].append("Consider reducing CPU allocation to VMs/containers")
                    results["recommendations"].append("Check for CPU-intensive processes")
            
            # Get CPU load average
            if "loadavg" in node_status:
                load_avg = node_status["loadavg"]
                results["metrics"]["load_average"] = load_avg
                
                # Get CPU count
                cpu_count = node_status.get("cpuinfo", {}).get("cpus", 1)
                results["metrics"]["cpu_count"] = cpu_count
                
                # Calculate load per CPU
                load_per_cpu = [load / cpu_count for load in load_avg]
                results["metrics"]["load_per_cpu"] = load_per_cpu
                
                if load_per_cpu[0] > 1.0:  # 1-minute load average per CPU
                    results["bottleneck"] = True
                    results["message"] = f"High CPU load detected: {load_per_cpu[0]:.2f} per CPU"
                    results["recommendations"].append("Check for processes causing high CPU load")
                    results["recommendations"].append("Consider adding more CPU resources")
            
            # Run mpstat command to get detailed CPU usage
            cpu_usage_cmd = self.monitoring_commands["cpu"]["usage"]
            cpu_usage_output = self._run_command(cpu_usage_cmd)
            
            # Parse CPU usage output
            results["metrics"]["detailed_usage"] = self._parse_mpstat_output(cpu_usage_output)
            
            # Check for high system time
            for cpu_id, cpu_data in results["metrics"]["detailed_usage"].items():
                if cpu_data.get("system", 0) > 20:  # More than 20% system time
                    results["bottleneck"] = True
                    results["message"] = f"High system CPU time detected on CPU {cpu_id}: {cpu_data.get('system')}%"
                    results["recommendations"].append("Check for kernel or driver issues causing high system CPU time")
                
                if cpu_data.get("iowait", 0) > 10:  # More than 10% I/O wait time
                    results["bottleneck"] = True
                    results["message"] = f"High I/O wait time detected on CPU {cpu_id}: {cpu_data.get('iowait')}%"
                    results["recommendations"].append("Check for disk I/O bottlenecks")
                    results["recommendations"].append("Consider upgrading storage devices")
            
            # Get top CPU-consuming processes
            top_processes_cmd = self.monitoring_commands["cpu"]["top_processes"]
            top_processes_output = self._run_command(top_processes_cmd)
            
            # Parse top processes output
            results["metrics"]["top_processes"] = top_processes_output
            
            # Look for processes consuming excessive CPU
            for line in top_processes_output.splitlines():
                if line.startswith("USER"):
                    continue
                    
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        cpu_percent = float(parts[2])
                        if cpu_percent > 50:  # Process using more than 50% CPU
                            process_name = parts[10] if len(parts) > 10 else "unknown"
                            results["recommendations"].append(f"Check process '{process_name}' consuming {cpu_percent}% CPU")
                    except (ValueError, IndexError):
                        pass
        
        except Exception as e:
            logger.error(f"Error analyzing CPU performance: {str(e)}")
            results["success"] = False
            results["message"] = f"Error analyzing CPU performance: {str(e)}"
        
        return results
    
    def analyze_memory_performance(self, node: str = "pve") -> Dict:
        """Analyze memory performance.
        
        Args:
            node: Node to analyze memory performance on
            
        Returns:
            Dict with memory performance analysis results
        """
        results = {
            "success": True,
            "message": f"Analyzed memory performance on node {node}",
            "bottleneck": False,
            "metrics": {},
            "recommendations": []
        }
        
        try:
            # Get node memory information from Proxmox API
            node_status = self.api.nodes(node).status.get()
            
            if "memory" in node_status:
                memory_info = node_status["memory"]
                
                # Calculate memory usage
                if "used" in memory_info and "total" in memory_info:
                    memory_used = memory_info["used"]
                    memory_total = memory_info["total"]
                    memory_percent = (memory_used / memory_total) * 100
                    
                    results["metrics"]["total_bytes"] = memory_total
                    results["metrics"]["used_bytes"] = memory_used
                    results["metrics"]["usage_percent"] = memory_percent
                    
                    if memory_percent > 90:
                        results["bottleneck"] = True
                        results["message"] = f"High memory usage detected: {memory_percent:.1f}%"
                        results["recommendations"].append("Consider reducing memory allocation to VMs/containers")
                        results["recommendations"].append("Check for memory leaks in applications")
            
            # Run free command to get detailed memory usage
            memory_usage_cmd = self.monitoring_commands["memory"]["usage"]
            memory_usage_output = self._run_command(memory_usage_cmd)
            
            # Parse memory usage output
            results["metrics"]["detailed_usage"] = self._parse_free_output(memory_usage_output)
            
            # Check for low available memory
            if "available" in results["metrics"]["detailed_usage"]:
                available_mb = results["metrics"]["detailed_usage"]["available"]
                if available_mb < 512:  # Less than 512 MB available
                    results["bottleneck"] = True
                    results["message"] = f"Low available memory: {available_mb} MB"
                    results["recommendations"].append("Free up memory by stopping unnecessary services")
                    results["recommendations"].append("Add more physical memory to the system")
            
            # Check for high swap usage
            if "swap_used" in results["metrics"]["detailed_usage"] and "swap_total" in results["metrics"]["detailed_usage"]:
                swap_used = results["metrics"]["detailed_usage"]["swap_used"]
                swap_total = results["metrics"]["detailed_usage"]["swap_total"]
                
                if swap_total > 0:
                    swap_percent = (swap_used / swap_total) * 100
                    results["metrics"]["swap_percent"] = swap_percent
                    
                    if swap_percent > 50:
                        results["bottleneck"] = True
                        results["message"] = f"High swap usage detected: {swap_percent:.1f}%"
                        results["recommendations"].append("System is using swap memory, which can severely impact performance")
                        results["recommendations"].append("Add more physical memory to the system")
                        results["recommendations"].append("Reduce memory allocation to VMs/containers")
            
            # Get top memory-consuming processes
            top_processes_cmd = self.monitoring_commands["memory"]["top_processes"]
            top_processes_output = self._run_command(top_processes_cmd)
            
            # Parse top processes output
            results["metrics"]["top_processes"] = top_processes_output
            
            # Look for processes consuming excessive memory
            for line in top_processes_output.splitlines():
                if line.startswith("USER"):
                    continue
                    
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        mem_percent = float(parts[3])
                        if mem_percent > 20:  # Process using more than 20% memory
                            process_name = parts[10] if len(parts) > 10 else "unknown"
                            results["recommendations"].append(f"Check process '{process_name}' consuming {mem_percent}% memory")
                    except (ValueError, IndexError):
                        pass
        
        except Exception as e:
            logger.error(f"Error analyzing memory performance: {str(e)}")
            results["success"] = False
            results["message"] = f"Error analyzing memory performance: {str(e)}"
        
        return results
    
    def analyze_disk_performance(self, node: str = "pve", storage_id: str = None) -> Dict:
        """Analyze disk performance.
        
        Args:
            node: Node to analyze disk performance on
            storage_id: Specific storage ID to analyze
            
        Returns:
            Dict with disk performance analysis results
        """
        results = {
            "success": True,
            "message": f"Analyzed disk performance on node {node}",
            "bottleneck": False,
            "metrics": {},
            "recommendations": []
        }
        
        try:
            # Get storage information from Proxmox API
            if storage_id:
                storage_info = self.api.nodes(node).storage(storage_id).status.get()
                results["metrics"]["storage_info"] = storage_info
                
                # Check storage usage
                if "used" in storage_info and "total" in storage_info:
                    used_bytes = storage_info["used"]
                    total_bytes = storage_info["total"]
                    used_percent = (used_bytes / total_bytes) * 100
                    
                    results["metrics"]["usage_percent"] = used_percent
                    
                    if used_percent > 90:
                        results["bottleneck"] = True
                        results["message"] = f"Storage {storage_id} is nearly full: {used_percent:.1f}%"
                        results["recommendations"].append(f"Free up space on storage {storage_id}")
                        results["recommendations"].append("Consider adding more storage capacity")
            else:
                # Get all storage information
                storage_list = self.api.nodes(node).storage.get()
                results["metrics"]["storage_list"] = storage_list
                
                # Check each storage
                for storage in storage_list:
                    if "used" in storage and "total" in storage:
                        used_bytes = storage["used"]
                        total_bytes = storage["total"]
                        used_percent = (used_bytes / total_bytes) * 100
                        
                        if used_percent > 90:
                            results["bottleneck"] = True
                            results["message"] = f"Storage {storage.get('storage')} is nearly full: {used_percent:.1f}%"
                            results["recommendations"].append(f"Free up space on storage {storage.get('storage')}")
                            results["recommendations"].append("Consider adding more storage capacity")
            
            # Run df command to get filesystem usage
            disk_usage_cmd = self.monitoring_commands["disk"]["usage"]
            disk_usage_output = self._run_command(disk_usage_cmd)
            
            # Parse disk usage output
            results["metrics"]["filesystem_usage"] = disk_usage_output
            
            # Check for filesystems with high usage
            for line in disk_usage_output.splitlines():
                if line.startswith("/"):
                    parts = line.split()
                    if len(parts) >= 5:
                        usage = parts[4].rstrip("%")
                        try:
                            usage_percent = int(usage)
                            if usage_percent > 90:
                                results["bottleneck"] = True
                                results["message"] = f"Filesystem {parts[0]} is nearly full: {usage_percent}%"
                                results["recommendations"].append(f"Free up space on filesystem {parts[0]}")
                        except ValueError:
                            pass
            
            # Run iostat command to get disk I/O statistics
            disk_io_cmd = self.monitoring_commands["disk"]["io"]
            disk_io_output = self._run_command(disk_io_cmd)
            
            # Parse disk I/O output
            results["metrics"]["disk_io"] = disk_io_output
            
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
                        if await_percent > 100:  # More than 100ms average wait time
                            high_io_wait = True
                            device = parts[0]
                            results["bottleneck"] = True
                            results["message"] = f"High disk I/O wait time detected on device {device}: {await_percent} ms"
                            results["recommendations"].append(f"Check for disk I/O bottlenecks on device {device}")
                            results["recommendations"].append("Consider upgrading to faster storage devices")
                            results["recommendations"].append("Check for applications with excessive disk I/O")
                    except (ValueError, IndexError):
                        pass
            
            # Get top disk I/O processes if iotop is available
            try:
                top_processes_cmd = self.monitoring_commands["disk"]["top_processes"]
                top_processes_output = self._run_command(top_processes_cmd)
                
                # Parse top processes output
                results["metrics"]["top_io_processes"] = top_processes_output
                
                # Look for processes with excessive I/O
                for line in top_processes_output.splitlines():
                    if "DISK READ" in line:
                        continue
                        
                    parts = line.split()
                    if len(parts) >= 10:
                        try:
                            io_percent = float(parts[8])
                            if io_percent > 50:  # Process using more than 50% I/O
                                process_name = " ".join(parts[9:])
                                results["recommendations"].append(f"Check process '{process_name}' consuming {io_percent}% disk I/O")
                        except (ValueError, IndexError):
                            pass
            except Exception:
                # iotop might not be available
                pass
        
        except Exception as e:
            logger.error(f"Error analyzing disk performance: {str(e)}")
            results["success"] = False
            results["message"] = f"Error analyzing disk performance: {str(e)}"
        
        return results
    
    def analyze_network_performance(self, node: str = "pve", interface: str = None) -> Dict:
        """Analyze network performance.
        
        Args:
            node: Node to analyze network performance on
            interface: Specific network interface to analyze
            
        Returns:
            Dict with network performance analysis results
        """
        results = {
            "success": True,
            "message": f"Analyzed network performance on node {node}",
            "bottleneck": False,
            "metrics": {},
            "recommendations": []
        }
        
        try:
            # Get network interfaces information
            interfaces_cmd = "ip -j addr"
            interfaces_output = self._run_command(interfaces_cmd)
            
            try:
                interfaces_data = json.loads(interfaces_output)
                results["metrics"]["interfaces"] = interfaces_data
                
                # Check for interfaces with issues
                for iface in interfaces_data:
                    iface_name = iface.get("ifname")
                    
                    # Skip if we're only interested in a specific interface
                    if interface and iface_name != interface:
                        continue
                    
                    # Check interface state
                    if iface.get("operstate") != "UP":
                        results["bottleneck"] = True
                        results["message"] = f"Network interface {iface_name} is down"
                        results["recommendations"].append(f"Check network interface {iface_name} configuration")
                        results["recommendations"].append(f"Try bringing up interface: ip link set {iface_name} up")
                    
                    # Check for interfaces without IP addresses
                    if iface_name != "lo" and not any(addr.get("family") == "inet" for addr in iface.get("addr_info", [])):
                        results["bottleneck"] = True
                        results["message"] = f"Network interface {iface_name} has no IPv4 address"
                        results["recommendations"].append(f"Configure IPv4 address for interface {iface_name}")
            except json.JSONDecodeError:
                # Fallback to non-JSON output
                interfaces_cmd = "ip addr"
                interfaces_output = self._run_command(interfaces_cmd)
                results["metrics"]["interfaces"] = interfaces_output
            
            # Run ifstat command to get network throughput if available
            try:
                network_throughput_cmd = self.monitoring_commands["network"]["interfaces"]
                network_throughput_output = self._run_command(network_throughput_cmd)
                
                # Parse network throughput output
                results["metrics"]["network_throughput"] = network_throughput_output
                
                # Check for high network utilization
                # This is a simplified check and would need to be adapted to the actual output format
                for line in network_throughput_output.splitlines():
                    if interface and interface in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                kb_in = float(parts[1])
                                kb_out = float(parts[2])
                                
                                # Assuming 1Gbps link (125000 KB/s)
                                if kb_in > 100000 or kb_out > 100000:  # More than 80% of 1Gbps
                                    results["bottleneck"] = True
                                    results["message"] = f"High network utilization on interface {interface}"
                                    results["recommendations"].append("Check for network-intensive applications")
                                    results["recommendations"].append("Consider upgrading network infrastructure")
                            except (ValueError, IndexError):
                                pass
            except Exception:
                # ifstat might not be available
                pass
            
            # Get number of established connections
            connections_cmd = self.monitoring_commands["network"]["connections"]
            connections_output = self._run_command(connections_cmd)
            
            try:
                num_connections = int(connections_output.strip())
                results["metrics"]["established_connections"] = num_connections
                
                if num_connections > 1000:  # Arbitrary threshold
                    results["bottleneck"] = True
                    results["message"] = f"High number of network connections: {num_connections}"
                    results["recommendations"].append("Check for applications creating excessive network connections")
                    results["recommendations"].append("Consider connection pooling or optimizing network usage")
            except ValueError:
                pass
            
            # Get top network-using processes if nethogs is available
            try:
                top_processes_cmd = self.monitoring_commands["network"]["top_processes"]
                top_processes_output = self._run_command(top_processes_cmd)
                
                # Parse top processes output
                results["metrics"]["top_network_processes"] = top_processes_output
                
                # Look for processes with excessive network usage
                for line in top_processes_output.splitlines():
                    if "PID" in line or "Refreshing" in line:
                        continue
                        
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            sent_kb = float(parts[1])
                            recv_kb = float(parts[2])
                            
                            if sent_kb > 1000 or recv_kb > 1000:  # More than 1 MB/s
                                process_name = parts[0]
                                results["recommendations"].append(f"Check process '{process_name}' with high network usage")
                        except (ValueError, IndexError):
                            pass
            except Exception:
                # nethogs might not be available
                pass
        
        except Exception as e:
            logger.error(f"Error analyzing network performance: {str(e)}")
            results["success"] = False
            results["message"] = f"Error analyzing network performance: {str(e)}"
        
        return results
    
    def detect_bottlenecks(self, node: str = "pve") -> Dict:
        """Detect performance bottlenecks.
        
        Args:
            node: Node to detect bottlenecks on
            
        Returns:
            Dict with bottleneck detection results
        """
        # This is a wrapper around analyze_all_performance
        return self.analyze_all_performance(node)
    
    def _parse_mpstat_output(self, output: str) -> Dict:
        """Parse mpstat output to extract CPU usage statistics."""
        result = {}
        
        for line in output.splitlines():
            if "CPU" in line and "%usr" in line:
                # Header line, skip
                continue
                
            if "Average" in line:
                # Parse average CPU usage
                parts = line.split()
                if len(parts) >= 12:
                    try:
                        cpu_id = parts[2]
                        if cpu_id == "all":
                            cpu_id = "average"
                        
                        result[cpu_id] = {
                            "user": float(parts[3]),
                            "nice": float(parts[4]),
                            "system": float(parts[5]),
                            "iowait": float(parts[6]),
                            "irq": float(parts[7]),
                            "soft": float(parts[8]),
                            "steal": float(parts[9]),
                            "guest": float(parts[10]),
                            "idle": float(parts[11])
                        }
                    except (ValueError, IndexError):
                        pass
        
        return result
    
    def _parse_free_output(self, output: str) -> Dict:
        """Parse free command output to extract memory usage statistics."""
        result = {}
        
        for line in output.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                if len(parts) >= 7:
                    try:
                        result["total"] = int(parts[1])
                        result["used"] = int(parts[2])
                        result["free"] = int(parts[3])
                        result["shared"] = int(parts[4])
                        result["buffers"] = int(parts[5])
                        result["available"] = int(parts[6])
                    except (ValueError, IndexError):
                        pass
            elif line.startswith("Swap:"):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        result["swap_total"] = int(parts[1])
                        result["swap_used"] = int(parts[2])
                        result["swap_free"] = int(parts[3])
                    except (ValueError, IndexError):
                        pass
        
        return result
    
    def _run_command(self, command: str) -> str:
        """Run a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command execution failed: {str(e)}")
            return e.stdout if e.stdout else ""
