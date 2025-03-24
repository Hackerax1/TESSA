"""
System diagnostics and troubleshooting operations for Proxmox NLI.
"""
from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timedelta

class DiagnosticsManager:
    def __init__(self, api):
        self.api = api

    def run_system_diagnostics(self, node: str) -> Dict[str, Any]:
        """Run comprehensive system diagnostics
        
        Args:
            node: Node name
            
        Returns:
            Dict with diagnostic results
        """
        diagnostics = []
        
        # Check system resources
        resources = self._check_system_resources(node)
        if resources['success']:
            diagnostics.extend(resources['checks'])
            
        # Check system logs
        logs = self._analyze_system_logs(node)
        if logs['success']:
            diagnostics.extend(logs['issues'])
            
        # Check storage health
        storage = self._check_storage_health(node)
        if storage['success']:
            diagnostics.extend(storage['status'])
            
        # Check network connectivity
        network = self._check_network_connectivity(node)
        if network['success']:
            diagnostics.extend(network['checks'])
            
        return {
            "success": True,
            "message": f"Completed system diagnostics for node {node}",
            "diagnostics": diagnostics
        }

    def analyze_performance_issues(self, node: str, timeframe: str = '1h') -> Dict[str, Any]:
        """Analyze system performance issues
        
        Args:
            node: Node name
            timeframe: Time period to analyze (e.g., 1h, 24h)
            
        Returns:
            Dict with performance analysis
        """
        # Get RRD data for performance metrics
        rrd_result = self.api.api_request('GET', f'nodes/{node}/rrddata', {
            'timeframe': timeframe
        })
        
        if not rrd_result['success']:
            return rrd_result
            
        analysis = []
        thresholds = {
            'cpu': 80,  # CPU usage threshold (%)
            'memory': 90,  # Memory usage threshold (%)
            'iowait': 10,  # IO wait threshold (%)
            'load': 0.7  # Load average per CPU threshold
        }
        
        # Analyze CPU usage
        cpu_high = False
        for data in rrd_result['data']:
            if data.get('cpu') and float(data['cpu']) > thresholds['cpu']:
                cpu_high = True
                analysis.append({
                    'component': 'cpu',
                    'status': 'high_usage',
                    'value': f"{data['cpu']}%",
                    'threshold': f"{thresholds['cpu']}%",
                    'timestamp': data.get('time')
                })
                
        # Analyze memory usage
        memory_high = False
        for data in rrd_result['data']:
            if data.get('memory') and float(data['memory']) > thresholds['memory']:
                memory_high = True
                analysis.append({
                    'component': 'memory',
                    'status': 'high_usage',
                    'value': f"{data['memory']}%",
                    'threshold': f"{thresholds['memory']}%",
                    'timestamp': data.get('time')
                })
                
        # Get running processes if high resource usage detected
        if cpu_high or memory_high:
            top_result = self.api.api_request('POST', f'nodes/{node}/execute', {
                'command': 'ps aux --sort=-%cpu,%mem | head -10'
            })
            
            if top_result['success']:
                analysis.append({
                    'component': 'processes',
                    'status': 'top_processes',
                    'data': top_result['data']
                })
                
        return {
            "success": True,
            "message": f"Completed performance analysis for node {node}",
            "analysis": analysis
        }

    def get_error_report(self, node: str, timeframe: str = '24h') -> Dict[str, Any]:
        """Generate error report from logs
        
        Args:
            node: Node name
            timeframe: Time period to analyze
            
        Returns:
            Dict with error report
        """
        # Calculate timestamp for timeframe
        hours = int(timeframe.replace('h', ''))
        since = datetime.now() - timedelta(hours=hours)
        since_str = since.strftime('%Y-%m-%d %H:%M:%S')
        
        # Get system logs
        logs_result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': f'journalctl --since "{since_str}" -p err,crit,alert,emerg'
        })
        
        if not logs_result['success']:
            return logs_result
            
        errors = []
        for line in logs_result['data'].splitlines():
            if line.strip():
                # Parse log line
                match = re.match(r'(\w+\s+\d+\s+\d+:\d+:\d+).*?(\w+)\[(\d+)\]:\s+(.+)', line)
                if match:
                    timestamp, service, pid, message = match.groups()
                    errors.append({
                        'timestamp': timestamp,
                        'service': service,
                        'pid': pid,
                        'message': message,
                        'severity': self._get_error_severity(message)
                    })
                
        return {
            "success": True,
            "message": f"Generated error report for node {node}",
            "errors": errors
        }

    def run_health_check(self, node: str) -> Dict[str, Any]:
        """Run comprehensive health check
        
        Args:
            node: Node name
            
        Returns:
            Dict with health check results
        """
        checks = []
        
        # Check node status
        node_result = self.api.api_request('GET', f'nodes/{node}/status')
        if node_result['success']:
            checks.append({
                'component': 'node',
                'status': node_result['data'].get('status', 'unknown'),
                'uptime': node_result['data'].get('uptime'),
                'health': 'good' if node_result['data'].get('status') == 'online' else 'bad'
            })
            
        # Check services status
        services_result = self.api.api_request('GET', f'nodes/{node}/services')
        if services_result['success']:
            for service in services_result['data']:
                checks.append({
                    'component': 'service',
                    'name': service.get('name'),
                    'status': service.get('state'),
                    'health': 'good' if service.get('state') == 'running' else 'bad'
                })
                
        # Check storage status
        storage_result = self.api.api_request('GET', f'nodes/{node}/storage')
        if storage_result['success']:
            for storage in storage_result['data']:
                checks.append({
                    'component': 'storage',
                    'name': storage.get('storage'),
                    'type': storage.get('type'),
                    'status': storage.get('active'),
                    'health': 'good' if storage.get('active') else 'bad'
                })
                
        # Check network status
        network_result = self.api.api_request('GET', f'nodes/{node}/network')
        if network_result['success']:
            for interface in network_result['data']:
                checks.append({
                    'component': 'network',
                    'name': interface.get('iface'),
                    'status': 'up' if interface.get('active') else 'down',
                    'health': 'good' if interface.get('active') else 'bad'
                })
                
        return {
            "success": True,
            "message": f"Completed health check for node {node}",
            "checks": checks
        }

    def _check_system_resources(self, node: str) -> Dict[str, Any]:
        """Check system resource usage
        
        Args:
            node: Node name
            
        Returns:
            Dict with resource checks
        """
        result = self.api.api_request('GET', f'nodes/{node}/status')
        if not result['success']:
            return result
            
        checks = []
        data = result['data']
        
        # CPU check
        cpu_usage = data.get('cpu', 0)
        checks.append({
            'component': 'cpu',
            'status': 'warning' if cpu_usage > 80 else 'normal',
            'value': f"{cpu_usage}%",
            'message': f"CPU usage is {cpu_usage}%"
        })
        
        # Memory check
        memory_total = data.get('memory', {}).get('total', 0)
        memory_used = data.get('memory', {}).get('used', 0)
        if memory_total > 0:
            memory_percent = (memory_used / memory_total) * 100
            checks.append({
                'component': 'memory',
                'status': 'warning' if memory_percent > 90 else 'normal',
                'value': f"{memory_percent:.1f}%",
                'message': f"Memory usage is {memory_percent:.1f}%"
            })
            
        # Swap check
        swap_total = data.get('swap', {}).get('total', 0)
        swap_used = data.get('swap', {}).get('used', 0)
        if swap_total > 0:
            swap_percent = (swap_used / swap_total) * 100
            checks.append({
                'component': 'swap',
                'status': 'warning' if swap_percent > 50 else 'normal',
                'value': f"{swap_percent:.1f}%",
                'message': f"Swap usage is {swap_percent:.1f}%"
            })
            
        return {
            "success": True,
            "checks": checks
        }

    def _analyze_system_logs(self, node: str) -> Dict[str, Any]:
        """Analyze system logs for issues
        
        Args:
            node: Node name
            
        Returns:
            Dict with log analysis
        """
        # Get recent logs
        result = self.api.api_request('POST', f'nodes/{node}/execute', {
            'command': 'journalctl -n 1000 -p err,crit,alert,emerg'
        })
        
        if not result['success']:
            return result
            
        issues = []
        current_time = datetime.now()
        
        for line in result['data'].splitlines():
            if line.strip():
                # Look for common error patterns
                if 'error' in line.lower() or 'failed' in line.lower():
                    issues.append({
                        'type': 'error',
                        'message': line,
                        'timestamp': current_time.isoformat()
                    })
                elif 'warning' in line.lower():
                    issues.append({
                        'type': 'warning',
                        'message': line,
                        'timestamp': current_time.isoformat()
                    })
                    
        return {
            "success": True,
            "issues": issues
        }

    def _check_storage_health(self, node: str) -> Dict[str, Any]:
        """Check storage health
        
        Args:
            node: Node name
            
        Returns:
            Dict with storage status
        """
        result = self.api.api_request('GET', f'nodes/{node}/storage')
        if not result['success']:
            return result
            
        status = []
        for storage in result['data']:
            # Get storage details
            details = self.api.api_request('GET', f'nodes/{node}/storage/{storage["storage"]}/status')
            if details['success']:
                status.append({
                    'storage': storage['storage'],
                    'type': storage['type'],
                    'status': 'healthy' if details['data'].get('active') else 'issue',
                    'total': details['data'].get('total'),
                    'used': details['data'].get('used'),
                    'available': details['data'].get('avail')
                })
                
        return {
            "success": True,
            "status": status
        }

    def _check_network_connectivity(self, node: str) -> Dict[str, Any]:
        """Check network connectivity
        
        Args:
            node: Node name
            
        Returns:
            Dict with network checks
        """
        result = self.api.api_request('GET', f'nodes/{node}/network')
        if not result['success']:
            return result
            
        checks = []
        for interface in result['data']:
            if interface.get('iface'):
                # Test connectivity
                ping_result = self.api.api_request('POST', f'nodes/{node}/execute', {
                    'command': f'ping -c 1 -W 2 {interface.get("gateway", "8.8.8.8")}'
                })
                
                checks.append({
                    'interface': interface['iface'],
                    'status': 'up' if ping_result['success'] else 'down',
                    'speed': interface.get('speed'),
                    'duplex': interface.get('duplex'),
                    'message': 'Connected' if ping_result['success'] else 'No connectivity'
                })
                
        return {
            "success": True,
            "checks": checks
        }

    def _get_error_severity(self, message: str) -> str:
        """Determine error severity from message
        
        Args:
            message: Error message
            
        Returns:
            Severity level (critical, error, warning)
        """
        message = message.lower()
        if any(x in message for x in ['emergency', 'alert', 'critical', 'panic']):
            return 'critical'
        elif any(x in message for x in ['error', 'fail', 'failed']):
            return 'error'
        else:
            return 'warning'