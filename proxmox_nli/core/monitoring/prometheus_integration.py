"""Prometheus integration for metrics collection and monitoring."""

import logging
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PrometheusClient:
    """Client for interacting with Prometheus API"""
    
    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url.rstrip('/')
        
    def query(self, query: str, time: Optional[datetime] = None) -> Dict:
        """Execute a PromQL query."""
        try:
            params = {'query': query}
            if time:
                params['time'] = time.isoformat()
            
            response = requests.get(f"{self.base_url}/api/v1/query", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error querying Prometheus: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def query_range(self, query: str, start: datetime, end: datetime, step: str = "1h") -> Dict:
        """Execute a PromQL query over a time range."""
        try:
            params = {
                'query': query,
                'start': start.isoformat(),
                'end': end.isoformat(),
                'step': step
            }
            
            response = requests.get(f"{self.base_url}/api/v1/query_range", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error querying Prometheus range: {str(e)}")
            return {"status": "error", "error": str(e)}

class PrometheusMetricsCollector:
    """Collector for Prometheus metrics specific to Proxmox monitoring."""
    
    def __init__(self, client: PrometheusClient):
        self.client = client
    
    def get_node_metrics(self, node: str, duration: timedelta = timedelta(hours=24)) -> Dict:
        """Get metrics for a specific node."""
        end_time = datetime.now()
        start_time = end_time - duration
        
        metrics = {}
        
        # CPU Usage
        cpu_query = f'100 - (avg by (instance) (irate(node_cpu_seconds_total{{mode="idle",instance="{node}"}}[5m])) * 100)'
        cpu_result = self.client.query_range(cpu_query, start_time, end_time)
        if cpu_result.get("status") == "success":
            metrics["cpu"] = self._process_metric_values(cpu_result)
        
        # Memory Usage
        mem_query = f'100 * (1 - ((node_memory_MemAvailable_bytes{{instance="{node}"}}) / (node_memory_MemTotal_bytes{{instance="{node}"}})))'
        mem_result = self.client.query_range(mem_query, start_time, end_time)
        if mem_result.get("status") == "success":
            metrics["memory"] = self._process_metric_values(mem_result)
        
        # Disk Usage
        disk_query = f'100 - ((node_filesystem_avail_bytes{{instance="{node}",mountpoint="/"}} * 100) / node_filesystem_size_bytes{{instance="{node}",mountpoint="/"}})'
        disk_result = self.client.query_range(disk_query, start_time, end_time)
        if disk_result.get("status") == "success":
            metrics["disk"] = self._process_metric_values(disk_result)
        
        # Network Usage
        net_query = f'rate(node_network_receive_bytes_total{{instance="{node}",device!~"lo|veth.*|docker.*|br.*|vmbr.*"}}[5m])'
        net_result = self.client.query_range(net_query, start_time, end_time)
        if net_result.get("status") == "success":
            metrics["network"] = self._process_metric_values(net_result)
        
        return metrics
    
    def _process_metric_values(self, result: Dict) -> Dict:
        """Process metric values from Prometheus result."""
        if "data" not in result or "result" not in result["data"]:
            return {"error": "No data in response"}
            
        values = []
        for series in result["data"]["result"]:
            for timestamp, value in series.get("values", []):
                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    continue
        
        if not values:
            return {"error": "No valid values found"}
            
        return {
            "current": values[-1],
            "avg": sum(values) / len(values),
            "max": max(values),
            "min": min(values)
        }