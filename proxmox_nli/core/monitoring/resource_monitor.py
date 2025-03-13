"""
Resource monitoring module for active tracking of system resources.
"""
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
from .metrics_collector import MetricsCollector
from .resource_analyzer import ResourceAnalyzer

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Actively monitors system resources and provides alerts"""
    
    def __init__(self, api, monitoring_integration=None):
        """Initialize with API connection and optional monitoring integration"""
        self.api = api
        self.monitoring = monitoring_integration
        self.metrics_collector = MetricsCollector(api, monitoring_integration)
        self.resource_analyzer = ResourceAnalyzer(api)
        self.alert_callbacks = []
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Default thresholds
        self.thresholds = {
            'cpu': {
                'warning': 80,  # percentage
                'critical': 90
            },
            'memory': {
                'warning': 85,  # percentage
                'critical': 95
            },
            'storage': {
                'warning': 85,  # percentage
                'critical': 95
            },
            'network': {
                'warning': 80,  # percentage of max bandwidth
                'critical': 90
            }
        }
    
    def start_monitoring(self, interval: int = 300) -> Dict[str, Any]:
        """Start resource monitoring"""
        try:
            if self.monitoring_active:
                return {
                    "success": False,
                    "message": "Resource monitoring already running"
                }
            
            # Start metrics collection first
            collection_result = self.metrics_collector.start_collection()
            if not collection_result["success"]:
                return collection_result
            
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(interval,),
                daemon=True
            )
            self.monitor_thread.start()
            
            return {
                "success": True,
                "message": "Resource monitoring started"
            }
        except Exception as e:
            logger.error(f"Error starting resource monitoring: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting resource monitoring: {str(e)}"
            }
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop resource monitoring"""
        try:
            if not self.monitoring_active:
                return {
                    "success": False,
                    "message": "Resource monitoring not running"
                }
            
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            # Stop metrics collection
            self.metrics_collector.stop_collection()
            
            return {
                "success": True,
                "message": "Resource monitoring stopped"
            }
        except Exception as e:
            logger.error(f"Error stopping resource monitoring: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping resource monitoring: {str(e)}"
            }
    
    def register_alert_callback(self, callback: callable) -> None:
        """Register a callback for resource alerts"""
        self.alert_callbacks.append(callback)
    
    def update_thresholds(self, thresholds: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Update monitoring thresholds"""
        try:
            for resource, levels in thresholds.items():
                if resource in self.thresholds:
                    self.thresholds[resource].update(levels)
            
            return {
                "success": True,
                "message": "Thresholds updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating thresholds: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating thresholds: {str(e)}"
            }
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self.metrics_collector.collect_all_metrics()
                if metrics["success"]:
                    self._analyze_current_state(metrics["metrics"])
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
            
            time.sleep(interval)
    
    def _analyze_current_state(self, metrics: List[Dict]):
        """Analyze current system state and generate alerts if needed"""
        try:
            # Group metrics by type
            grouped_metrics = {}
            for metric in metrics:
                metric_type = metric['type']
                if metric_type not in grouped_metrics:
                    grouped_metrics[metric_type] = []
                grouped_metrics[metric_type].append(metric)
            
            # Check nodes
            if 'node_cpu' in grouped_metrics:
                for metric in grouped_metrics['node_cpu']:
                    self._check_threshold('cpu', metric['value'], {
                        'node': metric['node']
                    })
            
            if 'node_memory' in grouped_metrics:
                for metric in grouped_metrics['node_memory']:
                    if metric['total'] > 0:
                        usage_percent = (metric['value'] / metric['total']) * 100
                        self._check_threshold('memory', usage_percent, {
                            'node': metric['node']
                        })
            
            # Check storage
            if 'storage' in grouped_metrics:
                for metric in grouped_metrics['storage']:
                    if metric['total'] > 0:
                        usage_percent = (metric['used'] / metric['total']) * 100
                        self._check_threshold('storage', usage_percent, {
                            'storage': metric['storage']
                        })
            
            # Check network
            if 'network' in grouped_metrics:
                for metric in grouped_metrics['network']:
                    total_traffic = metric['in'] + metric['out']
                    # Assume 1Gbps max bandwidth for now, should be configurable
                    max_bandwidth = 1000000000  # 1 Gbps in bytes
                    usage_percent = (total_traffic / max_bandwidth) * 100
                    self._check_threshold('network', usage_percent, {
                        'node': metric['node'],
                        'interface': metric['interface']
                    })
            
            # Get additional insights from resource analyzer
            efficiency = self.resource_analyzer.get_cluster_efficiency()
            if efficiency["success"]:
                metrics = efficiency["metrics"]
                if metrics["cpu_efficiency"] > self.thresholds["cpu"]["warning"]:
                    self._trigger_alert("warning", "High cluster CPU utilization", {
                        "type": "cluster_cpu",
                        "value": metrics["cpu_efficiency"]
                    })
                if metrics["memory_efficiency"] > self.thresholds["memory"]["warning"]:
                    self._trigger_alert("warning", "High cluster memory utilization", {
                        "type": "cluster_memory",
                        "value": metrics["memory_efficiency"]
                    })
        
        except Exception as e:
            logger.error(f"Error analyzing current state: {str(e)}")
    
    def _check_threshold(self, resource: str, value: float, context: Dict):
        """Check if a value exceeds thresholds and trigger alerts"""
        thresholds = self.thresholds.get(resource)
        if not thresholds:
            return
        
        if value >= thresholds['critical']:
            self._trigger_alert('critical', f'Critical {resource} usage', {
                'type': resource,
                'value': value,
                **context
            })
        elif value >= thresholds['warning']:
            self._trigger_alert('warning', f'High {resource} usage', {
                'type': resource,
                'value': value,
                **context
            })
    
    def _trigger_alert(self, level: str, message: str, context: Dict):
        """Trigger alert through registered callbacks"""
        alert = {
            'level': level,
            'message': message,
            'timestamp': int(time.time()),
            'context': context
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {str(e)}")
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get a summary of current resource usage"""
        try:
            metrics = self.metrics_collector.get_buffered_metrics(1)
            if not metrics:
                return {
                    "success": False,
                    "message": "No metrics available"
                }
            
            # Process latest metrics
            summary = {
                "nodes": {},
                "storage": {},
                "network": {},
                "timestamp": metrics[-1]['timestamp']
            }
            
            for metric in metrics:
                if metric['type'] == 'node_cpu':
                    if metric['node'] not in summary['nodes']:
                        summary['nodes'][metric['node']] = {}
                    summary['nodes'][metric['node']]['cpu'] = metric['value']
                
                elif metric['type'] == 'node_memory':
                    if metric['node'] not in summary['nodes']:
                        summary['nodes'][metric['node']] = {}
                    summary['nodes'][metric['node']]['memory'] = {
                        'used': metric['value'],
                        'total': metric['total']
                    }
                
                elif metric['type'] == 'storage':
                    summary['storage'][metric['storage']] = {
                        'used': metric['used'],
                        'total': metric['total']
                    }
                
                elif metric['type'] == 'network':
                    if metric['node'] not in summary['network']:
                        summary['network'][metric['node']] = {}
                    summary['network'][metric['node']][metric['interface']] = {
                        'in': metric['in'],
                        'out': metric['out']
                    }
            
            return {
                "success": True,
                "summary": summary
            }
        
        except Exception as e:
            logger.error(f"Error getting resource summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting resource summary: {str(e)}"
            }