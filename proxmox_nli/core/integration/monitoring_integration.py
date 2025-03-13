"""
Monitoring Integration module for connecting TESSA with monitoring platforms.
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import time

logger = logging.getLogger(__name__)

class MonitoringBackendBase(ABC):
    """Abstract base class for monitoring backend implementations"""
    
    @abstractmethod
    def configure(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the monitoring backend"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the monitoring backend"""
        pass
    
    @abstractmethod
    def register_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Register new metrics with the backend"""
        pass
    
    @abstractmethod
    def send_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send metrics to the backend"""
        pass
    
    @abstractmethod
    def query_metrics(self, query: str, start_time: int = None, end_time: int = None) -> Dict[str, Any]:
        """Query metrics from the backend"""
        pass

class MonitoringIntegration:
    """Main class for managing monitoring platform integrations"""
    
    def __init__(self, config_dir: str = None):
        """Initialize with optional config directory path"""
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, 'monitoring.json')
        self.backends: Dict[str, MonitoringBackendBase] = {}
        self.config = self._load_config()
        
        # Load default metric definitions
        self.default_metrics = {
            "cpu_usage": {
                "type": "gauge",
                "help": "CPU usage percentage",
                "labels": ["node", "vm_id"]
            },
            "memory_usage": {
                "type": "gauge",
                "help": "Memory usage in bytes",
                "labels": ["node", "vm_id"]
            },
            "disk_usage": {
                "type": "gauge",
                "help": "Disk usage in bytes",
                "labels": ["node", "vm_id", "disk"]
            },
            "network_traffic": {
                "type": "counter",
                "help": "Network traffic in bytes",
                "labels": ["node", "vm_id", "interface", "direction"]
            }
        }
    
    def _load_config(self) -> Dict:
        """Load monitoring configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading monitoring config: {str(e)}")
        
        return {
            "backends": {
                "prometheus": {
                    "enabled": False,
                    "settings": {
                        "url": "http://localhost:9090",
                        "scrape_interval": 15,
                        "push_gateway": None
                    }
                },
                "grafana": {
                    "enabled": False,
                    "settings": {
                        "url": "http://localhost:3000",
                        "api_key": None,
                        "org_id": 1
                    }
                },
                "influxdb": {
                    "enabled": False,
                    "settings": {
                        "url": "http://localhost:8086",
                        "token": None,
                        "org": "tessa",
                        "bucket": "metrics"
                    }
                }
            },
            "metric_retention": {
                "default": 30,  # days
                "high_resolution": 7,
                "low_resolution": 90
            },
            "custom_metrics": {},
            "dashboards": {},
            "alerts": {}
        }
    
    def _save_config(self) -> None:
        """Save monitoring configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving monitoring config: {str(e)}")
    
    def configure_backend(self, backend: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Configure a monitoring backend with settings"""
        try:
            if backend not in self.config["backends"]:
                return {
                    "success": False,
                    "message": f"Unsupported backend: {backend}"
                }
            
            # Update settings
            self.config["backends"][backend]["settings"].update(settings)
            self.config["backends"][backend]["enabled"] = True
            self._save_config()
            
            # Initialize backend if available
            if backend in self.backends:
                return self.backends[backend].configure(settings)
            
            return {
                "success": True,
                "message": f"Successfully configured {backend} backend"
            }
        except Exception as e:
            logger.error(f"Error configuring backend {backend}: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring backend: {str(e)}"
            }
    
    def register_custom_metric(self, name: str, metric_type: str, help_text: str, labels: List[str] = None) -> Dict[str, Any]:
        """Register a custom metric"""
        try:
            if name in self.default_metrics:
                return {
                    "success": False,
                    "message": f"Cannot override default metric: {name}"
                }
            
            self.config["custom_metrics"][name] = {
                "type": metric_type,
                "help": help_text,
                "labels": labels or []
            }
            self._save_config()
            
            # Register with enabled backends
            results = {
                "success": True,
                "registered": [],
                "failed": []
            }
            
            for backend_name, backend in self.backends.items():
                if self.config["backends"][backend_name]["enabled"]:
                    try:
                        result = backend.register_metrics([{
                            "name": name,
                            "type": metric_type,
                            "help": help_text,
                            "labels": labels
                        }])
                        if result["success"]:
                            results["registered"].append(backend_name)
                        else:
                            results["failed"].append({
                                "backend": backend_name,
                                "error": result["message"]
                            })
                    except Exception as e:
                        results["failed"].append({
                            "backend": backend_name,
                            "error": str(e)
                        })
            
            if results["failed"]:
                results["success"] = False
            
            return results
        
        except Exception as e:
            logger.error(f"Error registering custom metric: {str(e)}")
            return {
                "success": False,
                "message": f"Error registering custom metric: {str(e)}"
            }
    
    def send_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send metrics to all enabled backends"""
        try:
            results = {
                "success": True,
                "sent": [],
                "failed": []
            }
            
            for backend_name, backend in self.backends.items():
                if self.config["backends"][backend_name]["enabled"]:
                    try:
                        result = backend.send_metrics(metrics)
                        if result["success"]:
                            results["sent"].append(backend_name)
                        else:
                            results["failed"].append({
                                "backend": backend_name,
                                "error": result["message"]
                            })
                    except Exception as e:
                        results["failed"].append({
                            "backend": backend_name,
                            "error": str(e)
                        })
            
            if results["failed"]:
                results["success"] = False
            
            return results
        
        except Exception as e:
            logger.error(f"Error sending metrics: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending metrics: {str(e)}"
            }
    
    def query_metrics(self, query: str, backend: str = None, start_time: int = None, 
                     end_time: int = None) -> Dict[str, Any]:
        """Query metrics from a specific backend or try all enabled backends"""
        try:
            if backend:
                if backend not in self.backends or not self.config["backends"][backend]["enabled"]:
                    return {
                        "success": False,
                        "message": f"Backend {backend} not available"
                    }
                return self.backends[backend].query_metrics(query, start_time, end_time)
            
            # Try each enabled backend until we get results
            for backend_name, backend_obj in self.backends.items():
                if self.config["backends"][backend_name]["enabled"]:
                    try:
                        result = backend_obj.query_metrics(query, start_time, end_time)
                        if result["success"]:
                            result["backend"] = backend_name
                            return result
                    except Exception as e:
                        logger.debug(f"Error querying {backend_name}: {str(e)}")
            
            return {
                "success": False,
                "message": "No backend returned results for the query"
            }
        
        except Exception as e:
            logger.error(f"Error querying metrics: {str(e)}")
            return {
                "success": False,
                "message": f"Error querying metrics: {str(e)}"
            }
    
    def configure_dashboard(self, name: str, backend: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure a monitoring dashboard"""
        try:
            if backend not in self.backends or not self.config["backends"][backend]["enabled"]:
                return {
                    "success": False,
                    "message": f"Backend {backend} not available"
                }
            
            self.config["dashboards"][name] = {
                "backend": backend,
                "config": config,
                "created_at": int(time.time())
            }
            self._save_config()
            
            # Try to create dashboard in the backend
            try:
                if hasattr(self.backends[backend], 'create_dashboard'):
                    result = self.backends[backend].create_dashboard(name, config)
                    if not result["success"]:
                        logger.warning(f"Failed to create dashboard in backend: {result['message']}")
            except Exception as e:
                logger.warning(f"Error creating dashboard in backend: {str(e)}")
            
            return {
                "success": True,
                "message": f"Successfully configured dashboard {name}"
            }
        
        except Exception as e:
            logger.error(f"Error configuring dashboard: {str(e)}")
            return {
                "success": False,
                "message": f"Error configuring dashboard: {str(e)}"
            }
    
    def test_backend(self, backend: str) -> Dict[str, Any]:
        """Test connection to a monitoring backend"""
        try:
            if backend not in self.backends or not self.config["backends"][backend]["enabled"]:
                return {
                    "success": False,
                    "message": f"Backend {backend} not available"
                }
            
            return self.backends[backend].test_connection()
        except Exception as e:
            logger.error(f"Error testing backend {backend}: {str(e)}")
            return {
                "success": False,
                "message": f"Error testing backend: {str(e)}"
            }