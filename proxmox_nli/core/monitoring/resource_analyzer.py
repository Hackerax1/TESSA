"""
Resource analysis and optimization module for Proxmox NLI.
Provides insights and recommendations for resource usage optimization.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ResourceAnalyzer:
    def __init__(self, api):
        self.api = api
        self.metrics_cache = {}
        self.recommendations_cache = {}
        
    def analyze_vm_resources(self, vm_id: str, days: int = 7) -> Dict:
        """Analyze VM resource usage and provide optimization recommendations"""
        try:
            # Get historical resource usage
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            metrics = self._get_vm_metrics(vm_id, start_time, end_time)
            recommendations = self._generate_recommendations(vm_id, metrics)
            
            return {
                "success": True,
                "vm_id": vm_id,
                "metrics": metrics,
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"Error analyzing VM resources: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to analyze VM resources: {str(e)}"
            }
    
    def _get_vm_metrics(self, vm_id: str, start_time: datetime, end_time: datetime) -> Dict:
        """Get VM resource usage metrics"""
        try:
            # Get VM info first
            vm_info = self.api.api_request('GET', f'nodes/localhost/qemu/{vm_id}/status/current')
            if not vm_info['success']:
                return {}
                
            # Get RRD metrics
            rrd_data = self.api.api_request('GET', f'nodes/localhost/qemu/{vm_id}/rrddata')
            if not rrd_data['success']:
                return {}
                
            # Process metrics
            cpu_usage = []
            memory_usage = []
            disk_io = []
            network_io = []
            
            for point in rrd_data['data']:
                if 'time' not in point:
                    continue
                    
                timestamp = datetime.fromtimestamp(point['time'])
                if start_time <= timestamp <= end_time:
                    cpu_usage.append({
                        'timestamp': timestamp,
                        'value': point.get('cpu', 0)
                    })
                    memory_usage.append({
                        'timestamp': timestamp,
                        'value': point.get('mem', 0)
                    })
                    disk_io.append({
                        'timestamp': timestamp,
                        'read': point.get('diskread', 0),
                        'write': point.get('diskwrite', 0)
                    })
                    network_io.append({
                        'timestamp': timestamp,
                        'in': point.get('netin', 0),
                        'out': point.get('netout', 0)
                    })
            
            return {
                'cpu': self._analyze_metric(cpu_usage),
                'memory': self._analyze_metric(memory_usage),
                'disk': self._analyze_io_metric(disk_io),
                'network': self._analyze_io_metric(network_io)
            }
            
        except Exception as e:
            logger.error(f"Error getting VM metrics: {str(e)}")
            return {}
    
    def _analyze_metric(self, data: List[Dict]) -> Dict:
        """Analyze a single metric's data points"""
        if not data:
            return {
                'average': 0,
                'peak': 0,
                'min': 0,
                'trend': 'stable'
            }
            
        values = [point['value'] for point in data]
        return {
            'average': sum(values) / len(values),
            'peak': max(values),
            'min': min(values),
            'trend': self._calculate_trend(values)
        }
    
    def _analyze_io_metric(self, data: List[Dict]) -> Dict:
        """Analyze IO metrics (disk, network)"""
        if not data:
            return {
                'read': {'average': 0, 'peak': 0},
                'write': {'average': 0, 'peak': 0}
            }
            
        reads = [point['read'] for point in data]
        writes = [point['write'] for point in data]
        
        return {
            'read': {
                'average': sum(reads) / len(reads),
                'peak': max(reads)
            },
            'write': {
                'average': sum(writes) / len(writes),
                'peak': max(writes)
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values"""
        if len(values) < 2:
            return 'stable'
            
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = second_half - first_half
        if abs(diff) < (first_half * 0.1):  # Less than 10% change
            return 'stable'
        return 'increasing' if diff > 0 else 'decreasing'
    
    def _generate_recommendations(self, vm_id: str, metrics: Dict) -> List[Dict]:
        """Generate resource optimization recommendations"""
        recommendations = []
        
        # CPU recommendations
        if metrics.get('cpu'):
            cpu_avg = metrics['cpu']['average']
            cpu_peak = metrics['cpu']['peak']
            
            if cpu_avg < 20 and cpu_peak < 50:
                recommendations.append({
                    'type': 'cpu',
                    'severity': 'medium',
                    'message': 'CPU usage is consistently low. Consider reducing allocated CPUs.',
                    'action': f'Reduce CPU cores for VM {vm_id}',
                    'savings': 'Reduced host CPU contention'
                })
            elif cpu_peak > 90:
                recommendations.append({
                    'type': 'cpu',
                    'severity': 'high',
                    'message': 'CPU usage frequently peaks. Consider increasing CPU allocation.',
                    'action': f'Increase CPU cores for VM {vm_id}',
                    'impact': 'Improved performance during peak loads'
                })
        
        # Memory recommendations
        if metrics.get('memory'):
            mem_avg = metrics['memory']['average']
            mem_peak = metrics['memory']['peak']
            
            if mem_avg < 40 and mem_peak < 60:
                recommendations.append({
                    'type': 'memory',
                    'severity': 'medium',
                    'message': 'Memory usage is consistently low. Consider reducing allocated memory.',
                    'action': f'Reduce memory allocation for VM {vm_id}',
                    'savings': 'Free up memory for other VMs'
                })
            elif mem_peak > 90:
                recommendations.append({
                    'type': 'memory',
                    'severity': 'high',
                    'message': 'Memory usage frequently peaks. Consider increasing memory allocation.',
                    'action': f'Increase memory allocation for VM {vm_id}',
                    'impact': 'Prevent potential swapping and performance issues'
                })
        
        # Disk recommendations
        if metrics.get('disk'):
            disk_read = metrics['disk']['read']['average']
            disk_write = metrics['disk']['write']['average']
            
            if disk_read > 50_000_000 or disk_write > 50_000_000:  # 50MB/s
                recommendations.append({
                    'type': 'disk',
                    'severity': 'medium',
                    'message': 'High disk I/O detected. Consider using SSD storage.',
                    'action': f'Migrate VM {vm_id} to SSD storage',
                    'impact': 'Improved disk performance'
                })
        
        # Network recommendations
        if metrics.get('network'):
            net_in = metrics['network']['read']['average']
            net_out = metrics['network']['write']['average']
            
            if net_in > 100_000_000 or net_out > 100_000_000:  # 100MB/s
                recommendations.append({
                    'type': 'network',
                    'severity': 'medium',
                    'message': 'High network usage detected. Consider using 10GbE network.',
                    'action': f'Review network configuration for VM {vm_id}',
                    'impact': 'Improved network performance'
                })
        
        return recommendations
    
    def get_cluster_efficiency(self) -> Dict:
        """Analyze overall cluster efficiency"""
        try:
            # Get cluster resources
            nodes_result = self.api.api_request('GET', 'nodes')
            if not nodes_result['success']:
                return {
                    "success": False,
                    "message": "Failed to get cluster nodes"
                }
                
            total_cpu = 0
            total_memory = 0
            used_cpu = 0
            used_memory = 0
            
            for node in nodes_result['data']:
                node_status = self.api.api_request('GET', f"nodes/{node['node']}/status")
                if node_status['success']:
                    status = node_status['data']
                    total_cpu += status.get('cpuinfo', {}).get('cpus', 0)
                    total_memory += status.get('memory', {}).get('total', 0)
                    used_cpu += status.get('cpu', 0) * status.get('cpuinfo', {}).get('cpus', 0)
                    used_memory += status.get('memory', {}).get('used', 0)
            
            return {
                "success": True,
                "metrics": {
                    "cpu_efficiency": (used_cpu / total_cpu * 100) if total_cpu else 0,
                    "memory_efficiency": (used_memory / total_memory * 100) if total_memory else 0
                },
                "recommendations": self._get_cluster_recommendations(used_cpu/total_cpu if total_cpu else 0,
                                                                  used_memory/total_memory if total_memory else 0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing cluster efficiency: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to analyze cluster efficiency: {str(e)}"
            }
    
    def _get_cluster_recommendations(self, cpu_usage: float, memory_usage: float) -> List[Dict]:
        """Generate cluster-wide recommendations"""
        recommendations = []
        
        # CPU efficiency recommendations
        if cpu_usage < 0.3:  # Less than 30% CPU usage
            recommendations.append({
                'type': 'cluster_cpu',
                'severity': 'medium',
                'message': 'Cluster CPU usage is low. Consider consolidating VMs.',
                'action': 'Review VM placement and consider node consolidation',
                'savings': 'Reduced power consumption and better resource utilization'
            })
        elif cpu_usage > 0.8:  # More than 80% CPU usage
            recommendations.append({
                'type': 'cluster_cpu',
                'severity': 'high',
                'message': 'Cluster CPU usage is high. Consider adding more compute resources.',
                'action': 'Plan for additional compute capacity',
                'impact': 'Ensure performance during peak loads'
            })
        
        # Memory efficiency recommendations
        if memory_usage < 0.4:  # Less than 40% memory usage
            recommendations.append({
                'type': 'cluster_memory',
                'severity': 'medium',
                'message': 'Cluster memory usage is low. Consider optimizing memory allocations.',
                'action': 'Review VM memory allocations',
                'savings': 'Better memory utilization'
            })
        elif memory_usage > 0.85:  # More than 85% memory usage
            recommendations.append({
                'type': 'cluster_memory',
                'severity': 'high',
                'message': 'Cluster memory usage is high. Consider adding more memory.',
                'action': 'Plan for additional memory capacity',
                'impact': 'Prevent memory constraints'
            })
        
        return recommendations