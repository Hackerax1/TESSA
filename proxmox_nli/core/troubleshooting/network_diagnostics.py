"""
Network Diagnostics for Proxmox NLI.
Provides tools for diagnosing network issues and visualizing network topology.
"""
import logging
import subprocess
import re
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class NetworkDiagnostics:
    """Provides network diagnostics and visualization tools."""
    
    def __init__(self, api):
        """Initialize the network diagnostics.
        
        Args:
            api: Proxmox API client
        """
        self.api = api
        
        # Network diagnostic commands
        self.diagnostic_commands = {
            "ping": "ping -c 4 {target}",
            "traceroute": "traceroute {target}",
            "dns_lookup": "nslookup {domain}",
            "port_check": "nc -zv {host} {port}",
            "route_check": "ip route get {target}",
            "interfaces": "ip -j addr",
            "connections": "ss -tan state established",
            "listening": "ss -tuln",
            "firewall": "iptables-save"
        }
    
    def run_diagnostics(self, context: Dict = None) -> Dict:
        """Run network diagnostics.
        
        Args:
            context: Additional context for network diagnostics
            
        Returns:
            Dict with network diagnostic results
        """
        context = context or {}
        
        # Determine what to diagnose based on context
        if "connectivity" in context:
            return self.check_connectivity(context.get("target", "8.8.8.8"))
        elif "dns" in context:
            return self.check_dns(context.get("domain", "google.com"))
        elif "port" in context:
            return self.check_port(context.get("host", "localhost"), context.get("port", 22))
        elif "route" in context:
            return self.check_route(context.get("target", "8.8.8.8"))
        else:
            # Run comprehensive network diagnostics
            return self.comprehensive_diagnostics(context)
    
    def comprehensive_diagnostics(self, context: Dict = None) -> Dict:
        """Run comprehensive network diagnostics.
        
        Args:
            context: Additional context for network diagnostics
            
        Returns:
            Dict with comprehensive network diagnostic results
        """
        context = context or {}
        results = {
            "success": True,
            "message": "Completed comprehensive network diagnostics",
            "diagnostics": {},
            "issues": []
        }
        
        # Check internet connectivity
        connectivity = self.check_connectivity(context.get("target", "8.8.8.8"))
        results["diagnostics"]["connectivity"] = connectivity
        if not connectivity.get("success", False):
            results["issues"].append("Internet connectivity issue detected")
        
        # Check DNS resolution
        dns = self.check_dns(context.get("domain", "google.com"))
        results["diagnostics"]["dns"] = dns
        if not dns.get("success", False):
            results["issues"].append("DNS resolution issue detected")
        
        # Check network interfaces
        interfaces = self.get_network_interfaces()
        results["diagnostics"]["interfaces"] = interfaces
        
        # Check for interfaces without IP addresses
        for interface in interfaces.get("interfaces", []):
            if interface.get("name") != "lo" and not interface.get("ipv4", []) and not interface.get("ipv6", []):
                results["issues"].append(f"Interface {interface.get('name')} has no IP addresses")
        
        # Check routing
        route = self.check_route(context.get("target", "8.8.8.8"))
        results["diagnostics"]["route"] = route
        if not route.get("success", False):
            results["issues"].append("Routing issue detected")
        
        # Check open ports
        listening = self.get_listening_ports()
        results["diagnostics"]["listening"] = listening
        
        # Check active connections
        connections = self.get_active_connections()
        results["diagnostics"]["connections"] = connections
        
        # Check firewall rules
        firewall = self.get_firewall_rules()
        results["diagnostics"]["firewall"] = firewall
        
        return results
    
    def check_connectivity(self, target: str = "8.8.8.8") -> Dict:
        """Check network connectivity to a target.
        
        Args:
            target: Target to ping
            
        Returns:
            Dict with connectivity check results
        """
        results = {
            "success": True,
            "message": f"Checked connectivity to {target}",
            "target": target
        }
        
        try:
            # Run ping command
            ping_cmd = self.diagnostic_commands["ping"].format(target=target)
            ping_output = self._run_command(ping_cmd)
            
            # Parse ping results
            results["output"] = ping_output
            
            # Check for packet loss
            packet_loss_match = re.search(r"(\d+)% packet loss", ping_output)
            if packet_loss_match:
                packet_loss = int(packet_loss_match.group(1))
                results["packet_loss"] = packet_loss
                
                if packet_loss == 100:
                    results["success"] = False
                    results["message"] = f"No connectivity to {target} (100% packet loss)"
                elif packet_loss > 20:
                    results["message"] = f"Poor connectivity to {target} ({packet_loss}% packet loss)"
            
            # Extract round-trip times
            rtt_match = re.search(r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", ping_output)
            if rtt_match:
                results["rtt"] = {
                    "min": float(rtt_match.group(1)),
                    "avg": float(rtt_match.group(2)),
                    "max": float(rtt_match.group(3)),
                    "mdev": float(rtt_match.group(4))
                }
                
                # Check for high latency
                if results["rtt"]["avg"] > 200:
                    results["message"] = f"High latency to {target} (avg: {results['rtt']['avg']}ms)"
            
        except Exception as e:
            logger.error(f"Error checking connectivity to {target}: {str(e)}")
            results["success"] = False
            results["message"] = f"Error checking connectivity: {str(e)}"
        
        return results
    
    def check_dns(self, domain: str = "google.com") -> Dict:
        """Check DNS resolution for a domain.
        
        Args:
            domain: Domain to resolve
            
        Returns:
            Dict with DNS check results
        """
        results = {
            "success": True,
            "message": f"Checked DNS resolution for {domain}",
            "domain": domain
        }
        
        try:
            # Run nslookup command
            dns_cmd = self.diagnostic_commands["dns_lookup"].format(domain=domain)
            dns_output = self._run_command(dns_cmd)
            
            # Parse DNS results
            results["output"] = dns_output
            
            # Check for DNS errors
            if "server can't find" in dns_output or "SERVFAIL" in dns_output:
                results["success"] = False
                results["message"] = f"DNS resolution failed for {domain}"
            else:
                # Extract IP addresses
                ip_matches = re.findall(r"Address: ([\d.]+)", dns_output)
                if ip_matches:
                    results["ip_addresses"] = ip_matches
                    results["message"] = f"DNS resolution successful for {domain}: {', '.join(ip_matches)}"
                else:
                    results["success"] = False
                    results["message"] = f"No IP addresses found for {domain}"
            
        except Exception as e:
            logger.error(f"Error checking DNS for {domain}: {str(e)}")
            results["success"] = False
            results["message"] = f"Error checking DNS: {str(e)}"
        
        return results
    
    def check_port(self, host: str = "localhost", port: int = 22) -> Dict:
        """Check if a port is open on a host.
        
        Args:
            host: Host to check
            port: Port to check
            
        Returns:
            Dict with port check results
        """
        results = {
            "success": True,
            "message": f"Checked port {port} on {host}",
            "host": host,
            "port": port
        }
        
        try:
            # Run netcat command
            port_cmd = self.diagnostic_commands["port_check"].format(host=host, port=port)
            port_output = self._run_command(port_cmd)
            
            # Parse port check results
            results["output"] = port_output
            
            # Check if port is open
            if "open" in port_output or "succeeded" in port_output:
                results["port_open"] = True
                results["message"] = f"Port {port} is open on {host}"
            else:
                results["port_open"] = False
                results["success"] = False
                results["message"] = f"Port {port} is closed on {host}"
            
        except Exception as e:
            logger.error(f"Error checking port {port} on {host}: {str(e)}")
            results["success"] = False
            results["message"] = f"Error checking port: {str(e)}"
        
        return results
    
    def check_route(self, target: str = "8.8.8.8") -> Dict:
        """Check routing to a target.
        
        Args:
            target: Target to check routing for
            
        Returns:
            Dict with route check results
        """
        results = {
            "success": True,
            "message": f"Checked routing to {target}",
            "target": target
        }
        
        try:
            # Run ip route command
            route_cmd = self.diagnostic_commands["route_check"].format(target=target)
            route_output = self._run_command(route_cmd)
            
            # Parse route check results
            results["output"] = route_output
            
            # Check if route exists
            if target in route_output:
                # Extract interface
                interface_match = re.search(r"dev (\w+)", route_output)
                if interface_match:
                    results["interface"] = interface_match.group(1)
                
                # Extract source IP
                src_match = re.search(r"src ([\d.]+)", route_output)
                if src_match:
                    results["source_ip"] = src_match.group(1)
                
                results["message"] = f"Route to {target} exists via {results.get('interface', 'unknown')}"
            else:
                results["success"] = False
                results["message"] = f"No route to {target}"
            
        except Exception as e:
            logger.error(f"Error checking route to {target}: {str(e)}")
            results["success"] = False
            results["message"] = f"Error checking route: {str(e)}"
        
        return results
    
    def get_network_interfaces(self) -> Dict:
        """Get network interfaces information.
        
        Returns:
            Dict with network interfaces information
        """
        results = {
            "success": True,
            "message": "Retrieved network interfaces information",
            "interfaces": []
        }
        
        try:
            # Run ip addr command in JSON format
            interfaces_cmd = self.diagnostic_commands["interfaces"]
            interfaces_output = self._run_command(interfaces_cmd)
            
            # Parse interfaces output
            try:
                interfaces_data = json.loads(interfaces_output)
                
                # Process each interface
                for interface in interfaces_data:
                    interface_info = {
                        "name": interface.get("ifname"),
                        "state": interface.get("operstate"),
                        "mac": interface.get("address"),
                        "ipv4": [],
                        "ipv6": []
                    }
                    
                    # Extract IP addresses
                    for addr_info in interface.get("addr_info", []):
                        if addr_info.get("family") == "inet":
                            interface_info["ipv4"].append({
                                "address": addr_info.get("local"),
                                "prefix": addr_info.get("prefixlen")
                            })
                        elif addr_info.get("family") == "inet6":
                            interface_info["ipv6"].append({
                                "address": addr_info.get("local"),
                                "prefix": addr_info.get("prefixlen")
                            })
                    
                    results["interfaces"].append(interface_info)
                
            except json.JSONDecodeError:
                # Fallback to non-JSON output parsing
                interfaces_cmd = "ip addr"
                interfaces_output = self._run_command(interfaces_cmd)
                
                # Simple parsing of ip addr output
                current_interface = None
                for line in interfaces_output.splitlines():
                    if line.startswith(" "):
                        if current_interface and "inet " in line:
                            # IPv4 address
                            ipv4_match = re.search(r"inet ([\d.]+)/(\d+)", line)
                            if ipv4_match:
                                current_interface["ipv4"].append({
                                    "address": ipv4_match.group(1),
                                    "prefix": int(ipv4_match.group(2))
                                })
                        elif current_interface and "inet6 " in line:
                            # IPv6 address
                            ipv6_match = re.search(r"inet6 ([0-9a-f:]+)/(\d+)", line)
                            if ipv6_match:
                                current_interface["ipv6"].append({
                                    "address": ipv6_match.group(1),
                                    "prefix": int(ipv6_match.group(2))
                                })
                    else:
                        # New interface
                        interface_match = re.search(r"^\d+: (\w+): <([^>]+)>", line)
                        if interface_match:
                            current_interface = {
                                "name": interface_match.group(1),
                                "state": "UP" if "UP" in interface_match.group(2) else "DOWN",
                                "mac": "",
                                "ipv4": [],
                                "ipv6": []
                            }
                            
                            # Extract MAC address
                            mac_match = re.search(r"link/ether ([0-9a-f:]+)", line)
                            if mac_match:
                                current_interface["mac"] = mac_match.group(1)
                                
                            results["interfaces"].append(current_interface)
        
        except Exception as e:
            logger.error(f"Error getting network interfaces: {str(e)}")
            results["success"] = False
            results["message"] = f"Error getting network interfaces: {str(e)}"
        
        return results
    
    def get_listening_ports(self) -> Dict:
        """Get listening ports information.
        
        Returns:
            Dict with listening ports information
        """
        results = {
            "success": True,
            "message": "Retrieved listening ports information",
            "ports": []
        }
        
        try:
            # Run ss command
            listening_cmd = self.diagnostic_commands["listening"]
            listening_output = self._run_command(listening_cmd)
            
            # Parse listening ports output
            for line in listening_output.splitlines():
                if "LISTEN" in line:
                    # Extract port information
                    parts = line.split()
                    if len(parts) >= 5:
                        proto = parts[0]
                        local_address = parts[4]
                        
                        # Extract port from address
                        port_match = re.search(r":(\d+)$", local_address)
                        if port_match:
                            port = int(port_match.group(1))
                            
                            # Extract IP from address
                            ip_match = re.search(r"^([\d.]+):", local_address)
                            ip = ip_match.group(1) if ip_match else "*"
                            
                            results["ports"].append({
                                "protocol": proto,
                                "ip": ip,
                                "port": port
                            })
        
        except Exception as e:
            logger.error(f"Error getting listening ports: {str(e)}")
            results["success"] = False
            results["message"] = f"Error getting listening ports: {str(e)}"
        
        return results
    
    def get_active_connections(self) -> Dict:
        """Get active network connections.
        
        Returns:
            Dict with active connections information
        """
        results = {
            "success": True,
            "message": "Retrieved active connections information",
            "connections": []
        }
        
        try:
            # Run ss command
            connections_cmd = self.diagnostic_commands["connections"]
            connections_output = self._run_command(connections_cmd)
            
            # Parse connections output
            for line in connections_output.splitlines():
                if "ESTAB" in line:
                    # Extract connection information
                    parts = line.split()
                    if len(parts) >= 5:
                        proto = parts[0]
                        local_address = parts[3]
                        remote_address = parts[4]
                        
                        # Extract local IP and port
                        local_match = re.search(r"^([\d.]+):(\d+)$", local_address)
                        if local_match:
                            local_ip = local_match.group(1)
                            local_port = int(local_match.group(2))
                        else:
                            local_ip = local_address
                            local_port = 0
                        
                        # Extract remote IP and port
                        remote_match = re.search(r"^([\d.]+):(\d+)$", remote_address)
                        if remote_match:
                            remote_ip = remote_match.group(1)
                            remote_port = int(remote_match.group(2))
                        else:
                            remote_ip = remote_address
                            remote_port = 0
                        
                        results["connections"].append({
                            "protocol": proto,
                            "local_ip": local_ip,
                            "local_port": local_port,
                            "remote_ip": remote_ip,
                            "remote_port": remote_port
                        })
        
        except Exception as e:
            logger.error(f"Error getting active connections: {str(e)}")
            results["success"] = False
            results["message"] = f"Error getting active connections: {str(e)}"
        
        return results
    
    def get_firewall_rules(self) -> Dict:
        """Get firewall rules.
        
        Returns:
            Dict with firewall rules information
        """
        results = {
            "success": True,
            "message": "Retrieved firewall rules information",
            "rules": []
        }
        
        try:
            # Run iptables command
            firewall_cmd = self.diagnostic_commands["firewall"]
            firewall_output = self._run_command(firewall_cmd)
            
            # Parse firewall rules output
            current_chain = None
            for line in firewall_output.splitlines():
                if line.startswith("*"):
                    # Table
                    results["table"] = line[1:]
                elif line.startswith(":"):
                    # Chain
                    chain_match = re.search(r":(\w+) (\w+) \[(\d+):(\d+)\]", line)
                    if chain_match:
                        chain_name = chain_match.group(1)
                        chain_policy = chain_match.group(2)
                        current_chain = chain_name
                        
                        results["rules"].append({
                            "chain": chain_name,
                            "policy": chain_policy,
                            "rules": []
                        })
                elif line.startswith("-A"):
                    # Rule
                    rule_match = re.search(r"-A (\w+) (.+)", line)
                    if rule_match:
                        chain_name = rule_match.group(1)
                        rule_spec = rule_match.group(2)
                        
                        # Find the chain in results
                        for chain in results["rules"]:
                            if chain["chain"] == chain_name:
                                chain["rules"].append(rule_spec)
                                break
        
        except Exception as e:
            logger.error(f"Error getting firewall rules: {str(e)}")
            results["success"] = False
            results["message"] = f"Error getting firewall rules: {str(e)}"
        
        return results
    
    def visualize_network(self, scope: str = "cluster", context: Dict = None) -> Dict:
        """Generate network visualization data.
        
        Args:
            scope: Scope of the visualization (cluster, node, vm, container)
            context: Additional context for network visualization
            
        Returns:
            Dict with network visualization data
        """
        context = context or {}
        results = {
            "success": True,
            "message": f"Generated network visualization for {scope}",
            "scope": scope,
            "nodes": [],
            "links": []
        }
        
        try:
            if scope == "cluster":
                # Visualize cluster network
                self._visualize_cluster_network(results)
            elif scope == "node":
                # Visualize node network
                node = context.get("node", "pve")
                self._visualize_node_network(results, node)
            elif scope == "vm":
                # Visualize VM network
                vm_id = context.get("vm_id")
                node = context.get("node", "pve")
                self._visualize_vm_network(results, node, vm_id)
            elif scope == "container":
                # Visualize container network
                container_id = context.get("container_id")
                node = context.get("node", "pve")
                self._visualize_container_network(results, node, container_id)
            else:
                results["success"] = False
                results["message"] = f"Unknown visualization scope: {scope}"
        
        except Exception as e:
            logger.error(f"Error generating network visualization: {str(e)}")
            results["success"] = False
            results["message"] = f"Error generating network visualization: {str(e)}"
        
        return results
    
    def _visualize_cluster_network(self, results: Dict):
        """Visualize cluster network."""
        # Get cluster nodes
        try:
            nodes = self.api.nodes.get()
            
            # Add nodes to visualization
            for node in nodes:
                node_id = node["node"]
                results["nodes"].append({
                    "id": node_id,
                    "type": "node",
                    "name": node_id,
                    "status": node.get("status", "unknown")
                })
            
            # Add links between nodes
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if i < j:  # Avoid duplicate links
                        results["links"].append({
                            "source": node1["node"],
                            "target": node2["node"],
                            "type": "cluster"
                        })
        
        except Exception as e:
            logger.error(f"Error visualizing cluster network: {str(e)}")
    
    def _visualize_node_network(self, results: Dict, node: str):
        """Visualize node network."""
        # Get node information
        try:
            node_info = self.api.nodes(node).get()
            
            # Add node to visualization
            results["nodes"].append({
                "id": node,
                "type": "node",
                "name": node,
                "status": node_info.get("status", "unknown")
            })
            
            # Get VMs on the node
            vms = self.api.nodes(node).qemu.get()
            
            # Add VMs to visualization
            for vm in vms:
                vm_id = vm["vmid"]
                results["nodes"].append({
                    "id": f"vm-{vm_id}",
                    "type": "vm",
                    "name": vm.get("name", f"VM {vm_id}"),
                    "status": vm.get("status", "unknown")
                })
                
                # Add link between node and VM
                results["links"].append({
                    "source": node,
                    "target": f"vm-{vm_id}",
                    "type": "vm"
                })
            
            # Get containers on the node
            containers = self.api.nodes(node).lxc.get()
            
            # Add containers to visualization
            for container in containers:
                container_id = container["vmid"]
                results["nodes"].append({
                    "id": f"ct-{container_id}",
                    "type": "container",
                    "name": container.get("name", f"Container {container_id}"),
                    "status": container.get("status", "unknown")
                })
                
                # Add link between node and container
                results["links"].append({
                    "source": node,
                    "target": f"ct-{container_id}",
                    "type": "container"
                })
        
        except Exception as e:
            logger.error(f"Error visualizing node network: {str(e)}")
    
    def _visualize_vm_network(self, results: Dict, node: str, vm_id: str):
        """Visualize VM network."""
        # Get VM information
        try:
            vm_info = self.api.nodes(node).qemu(vm_id).get()
            
            # Add VM to visualization
            results["nodes"].append({
                "id": f"vm-{vm_id}",
                "type": "vm",
                "name": vm_info.get("name", f"VM {vm_id}"),
                "status": vm_info.get("status", "unknown")
            })
            
            # Get VM network interfaces
            vm_config = self.api.nodes(node).qemu(vm_id).config.get()
            
            # Extract network interfaces from config
            for key, value in vm_config.items():
                if key.startswith("net") and isinstance(value, str):
                    # Parse network interface config
                    parts = value.split(",")
                    model = next((part.split("=")[1] for part in parts if part.startswith("model=")), "unknown")
                    bridge = next((part.split("=")[1] for part in parts if part.startswith("bridge=")), "unknown")
                    
                    # Add network interface to visualization
                    nic_id = f"vm-{vm_id}-{key}"
                    results["nodes"].append({
                        "id": nic_id,
                        "type": "nic",
                        "name": f"{key} ({model})",
                        "bridge": bridge
                    })
                    
                    # Add link between VM and network interface
                    results["links"].append({
                        "source": f"vm-{vm_id}",
                        "target": nic_id,
                        "type": "nic"
                    })
                    
                    # Add link between network interface and bridge
                    results["links"].append({
                        "source": nic_id,
                        "target": bridge,
                        "type": "bridge"
                    })
        
        except Exception as e:
            logger.error(f"Error visualizing VM network: {str(e)}")
    
    def _visualize_container_network(self, results: Dict, node: str, container_id: str):
        """Visualize container network."""
        # Get container information
        try:
            container_info = self.api.nodes(node).lxc(container_id).get()
            
            # Add container to visualization
            results["nodes"].append({
                "id": f"ct-{container_id}",
                "type": "container",
                "name": container_info.get("name", f"Container {container_id}"),
                "status": container_info.get("status", "unknown")
            })
            
            # Get container network interfaces
            container_config = self.api.nodes(node).lxc(container_id).config.get()
            
            # Extract network interfaces from config
            for key, value in container_config.items():
                if key.startswith("net") and isinstance(value, str):
                    # Parse network interface config
                    parts = value.split(",")
                    name = next((part.split("=")[1] for part in parts if part.startswith("name=")), key)
                    bridge = next((part.split("=")[1] for part in parts if part.startswith("bridge=")), "unknown")
                    
                    # Add network interface to visualization
                    nic_id = f"ct-{container_id}-{key}"
                    results["nodes"].append({
                        "id": nic_id,
                        "type": "nic",
                        "name": name,
                        "bridge": bridge
                    })
                    
                    # Add link between container and network interface
                    results["links"].append({
                        "source": f"ct-{container_id}",
                        "target": nic_id,
                        "type": "nic"
                    })
                    
                    # Add link between network interface and bridge
                    results["links"].append({
                        "source": nic_id,
                        "target": bridge,
                        "type": "bridge"
                    })
        
        except Exception as e:
            logger.error(f"Error visualizing container network: {str(e)}")
    
    def _run_command(self, command: str) -> str:
        """Run a shell command and return the output."""
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command execution failed: {str(e)}")
            return e.stdout if e.stdout else ""
