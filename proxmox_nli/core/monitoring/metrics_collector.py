"""
Metrics collection module for gathering system and application metrics.
"""
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and aggregates metrics from various sources"""
    
    def __init__(self, api, monitoring_integration=None):
        """Initialize with API connection and optional monitoring integration"""
        self.api = api
        self.monitoring = monitoring_integration
        self.collection_active = False
        self.collection_thread = None
        self.metrics_buffer = []
        self.buffer_lock = threading.Lock()
        self.default_collection_interval = 60  # seconds
        
        # Define metric types and their collection methods
        self.metric_collectors = {
            'vm_stats': self._collect_vm_metrics,
            'node_stats': self._collect_node_metrics,
            'storage_stats': self._collect_storage_metrics,
            'network_stats': self._collect_network_metrics
        }
    
    def start_collection(self, interval: int = None) -> Dict[str, Any]:
        """Start metrics collection in background thread"""
        try:
            if self.collection_active:
                return {
                    "success": False,
                    "message": "Metrics collection already running"
                }
            
            self.collection_active = True
            self.collection_thread = threading.Thread(
                target=self._collection_loop,
                args=(interval or self.default_collection_interval,),
                daemon=True
            )
            self.collection_thread.start()
            
            return {
                "success": True,
                "message": "Metrics collection started"
            }
        except Exception as e:
            logger.error(f"Error starting metrics collection: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting metrics collection: {str(e)}"
            }
    
    def stop_collection(self) -> Dict[str, Any]:
        """Stop metrics collection"""
        try:
            if not self.collection_active:
                return {
                    "success": False,
                    "message": "Metrics collection not running"
                }
            
            self.collection_active = False
            if self.collection_thread:
                self.collection_thread.join(timeout=5)
            
            return {
                "success": True,
                "message": "Metrics collection stopped"
            }
        except Exception as e:
            logger.error(f"Error stopping metrics collection: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping metrics collection: {str(e)}"
            }
    
    def _collection_loop(self, interval: int):
        """Main collection loop running in background thread"""
        while self.collection_active:
            try:
                metrics = self.collect_all_metrics()
                if metrics["success"]:
                    self._buffer_metrics(metrics["metrics"])
                    if self.monitoring:
                        self.monitoring.send_metrics(metrics["metrics"])
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {str(e)}")
            
            time.sleep(interval)
    
    def _buffer_metrics(self, metrics: List[Dict]):
        """Buffer metrics in memory"""
        with self.buffer_lock:
            self.metrics_buffer.extend(metrics)
            # Trim buffer if it gets too large
            if len(self.metrics_buffer) > 1000:
                self.metrics_buffer = self.metrics_buffer[-1000:]
    
    def get_buffered_metrics(self, count: int = None) -> List[Dict]:
        """Get metrics from buffer"""
        with self.buffer_lock:
            if count:
                return self.metrics_buffer[-count:]
            return self.metrics_buffer.copy()
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all configured metrics"""
        try:
            results = []
            timestamp = int(time.time())
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    collector_name: executor.submit(collector_func)
                    for collector_name, collector_func in self.metric_collectors.items()
                }
                
                for name, future in futures.items():
                    try:
                        metrics = future.result()
                        if metrics:
                            for metric in metrics:
                                metric.update({
                                    'collector': name,
                                    'timestamp': timestamp
                                })
                            results.extend(metrics)
                    except Exception as e:
                        logger.error(f"Error collecting {name} metrics: {str(e)}")
            
            return {
                "success": True,
                "metrics": results
            }
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            return {
                "success": False,
                "message": f"Error collecting metrics: {str(e)}"
            }
    
    def _collect_vm_metrics(self) -> List[Dict]:
        """Collect VM-level metrics"""
        metrics = []
        try:
            vms = self.api.api_request('GET', 'cluster/resources', {'type': 'vm'})
            if vms['success']:
                for vm in vms['data']:
                    vm_id = vm.get('vmid')
                    if vm_id:
                        status = self.api.api_request('GET', f'nodes/{vm["node"]}/qemu/{vm_id}/status/current')
                        if status['success']:
                            data = status['data']
                            metrics.append({
                                'type': 'vm_cpu',
                                'vm_id': vm_id,
                                'node': vm['node'],
                                'value': data.get('cpu', 0)
                            })
                            metrics.append({
                                'type': 'vm_memory',
                                'vm_id': vm_id,
                                'node': vm['node'],
                                'value': data.get('mem', 0)
                            })
        except Exception as e:
            logger.error(f"Error collecting VM metrics: {str(e)}")
        return metrics
    
    def _collect_node_metrics(self) -> List[Dict]:
        """Collect node-level metrics"""
        metrics = []
        try:
            nodes = self.api.api_request('GET', 'nodes')
            if nodes['success']:
                for node in nodes['data']:
                    status = self.api.api_request('GET', f'nodes/{node["node"]}/status')
                    if status['success']:
                        data = status['data']
                        metrics.append({
                            'type': 'node_cpu',
                            'node': node['node'],
                            'value': data.get('cpu', 0)
                        })
                        metrics.append({
                            'type': 'node_memory',
                            'node': node['node'],
                            'value': data.get('memory', {}).get('used', 0),
                            'total': data.get('memory', {}).get('total', 0)
                        })
        except Exception as e:
            logger.error(f"Error collecting node metrics: {str(e)}")
        return metrics
    
    def _collect_storage_metrics(self) -> List[Dict]:
        """Collect storage-related metrics"""
        metrics = []
        try:
            storages = self.api.api_request('GET', 'storage')
            if storages['success']:
                for storage in storages['data']:
                    metrics.append({
                        'type': 'storage',
                        'storage': storage['storage'],
                        'used': storage.get('used', 0),
                        'total': storage.get('total', 0)
                    })
        except Exception as e:
            logger.error(f"Error collecting storage metrics: {str(e)}")
        return metrics
    
    def _collect_network_metrics(self) -> List[Dict]:
        """Collect network-related metrics"""
        metrics = []
        try:
            nodes = self.api.api_request('GET', 'nodes')
            if nodes['success']:
                for node in nodes['data']:
                    netdata = self.api.api_request('GET', f'nodes/{node["node"]}/netstat')
                    if netdata['success']:
                        for interface in netdata.get('data', []):
                            metrics.append({
                                'type': 'network',
                                'node': node['node'],
                                'interface': interface['iface'],
                                'in': interface.get('in', 0),
                                'out': interface.get('out', 0)
                            })
        except Exception as e:
            logger.error(f"Error collecting network metrics: {str(e)}")
        return metrics