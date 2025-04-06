"""
Predictive maintenance module for hardware performance monitoring and alerts.

This module analyzes hardware performance data to predict potential failures
and generate maintenance alerts before issues occur.
"""
import logging
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from proxmox_nli.core.monitoring.resource_analyzer import ResourceAnalyzer
from proxmox_nli.core.monitoring.system_health import SystemHealth

logger = logging.getLogger(__name__)

class PredictiveMaintenance:
    """Analyzes hardware performance data to predict potential failures."""
    
    def __init__(self, api, resource_analyzer: ResourceAnalyzer = None):
        """
        Initialize the predictive maintenance system.
        
        Args:
            api: Proxmox API instance
            resource_analyzer: Optional ResourceAnalyzer instance
        """
        self.api = api
        self.resource_analyzer = resource_analyzer or ResourceAnalyzer(api)
        self.system_health = SystemHealth(api)
        self.scaler = StandardScaler()
        self.models = {}
        
        # Configuration parameters
        self.config = {
            'enabled': False,
            'check_interval': 3600,  # 1 hour
            'training_period_days': 30,  # Days of data to use for training
            'prediction_threshold': 0.9,  # Anomaly threshold (0-1)
            'disk_smart_threshold': 0.7,  # SMART health threshold
            'cpu_temp_threshold': 80,  # CPU temperature threshold (°C)
            'gpu_temp_threshold': 85,  # GPU temperature threshold (°C)
            'memory_error_threshold': 10,  # Memory errors per day
            'notification_cooldown': 86400,  # 24 hours between repeat notifications
        }
        
        # Runtime state
        self.running = False
        self.monitor_thread = None
        self.last_notification = {}  # Track last notification time for each issue
        self.alert_history = []  # Track alert history
    
    def update_config(self, new_config: Dict) -> Dict[str, Any]:
        """Update configuration parameters."""
        try:
            for key, value in new_config.items():
                if key in self.config:
                    self.config[key] = value
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "config": self.config
            }
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating configuration: {str(e)}"
            }
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "success": True,
            "config": self.config
        }
    
    def start(self) -> Dict[str, Any]:
        """Start the predictive maintenance service."""
        try:
            if self.running:
                return {
                    "success": False,
                    "message": "Predictive maintenance is already running"
                }
            
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("Predictive maintenance started")
            return {
                "success": True,
                "message": "Predictive maintenance started successfully"
            }
        except Exception as e:
            logger.error(f"Error starting predictive maintenance: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting predictive maintenance: {str(e)}"
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop the predictive maintenance service."""
        try:
            if not self.running:
                return {
                    "success": False,
                    "message": "Predictive maintenance is not running"
                }
            
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            logger.info("Predictive maintenance stopped")
            return {
                "success": True,
                "message": "Predictive maintenance stopped successfully"
            }
        except Exception as e:
            logger.error(f"Error stopping predictive maintenance: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping predictive maintenance: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the predictive maintenance service."""
        return {
            "success": True,
            "status": {
                "running": self.running,
                "recent_alerts": self.alert_history[-10:] if self.alert_history else [],
                "config": self.config
            }
        }
    
    def analyze_hardware(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze hardware health and predict potential issues.
        
        Args:
            node_id: Optional node ID to analyze. If None, analyzes all nodes.
            
        Returns:
            Dict with analysis results
        """
        try:
            if node_id:
                nodes = [node_id]
            else:
                # Get all nodes
                nodes_result = self.api.api_request('GET', 'nodes')
                if not nodes_result['success']:
                    return {
                        "success": False,
                        "message": "Failed to get nodes"
                    }
                nodes = [node['node'] for node in nodes_result['data']]
            
            results = {}
            alerts = []
            
            for node in nodes:
                node_result = self._analyze_node_hardware(node)
                results[node] = node_result
                
                # Collect alerts
                if node_result.get('alerts'):
                    for alert in node_result['alerts']:
                        alerts.append({
                            "node": node,
                            **alert
                        })
            
            return {
                "success": True,
                "results": results,
                "alerts": alerts
            }
        except Exception as e:
            logger.error(f"Error analyzing hardware: {str(e)}")
            return {
                "success": False,
                "message": f"Error analyzing hardware: {str(e)}"
            }
    
    def _monitoring_loop(self):
        """Main monitoring loop for predictive maintenance."""
        while self.running:
            try:
                # Analyze hardware and generate alerts
                analysis = self.analyze_hardware()
                
                if analysis['success'] and analysis.get('alerts'):
                    for alert in analysis['alerts']:
                        self._process_alert(alert)
                
                # Sleep until next check
                time.sleep(self.config['check_interval'])
            except Exception as e:
                logger.error(f"Error in predictive maintenance loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying
    
    def _process_alert(self, alert: Dict):
        """Process and notify about a maintenance alert."""
        try:
            alert_id = f"{alert['node']}_{alert['component']}_{alert['type']}"
            
            # Check if we've recently notified about this issue
            if alert_id in self.last_notification:
                time_since_last = (datetime.now() - self.last_notification[alert_id]).total_seconds()
                if time_since_last < self.config['notification_cooldown']:
                    return  # Skip notification due to cooldown
            
            # Add timestamp and ID to alert
            alert['timestamp'] = datetime.now().isoformat()
            alert['id'] = f"{alert_id}_{int(time.time())}"
            
            # Add to history
            self.alert_history.append(alert)
            
            # Update last notification time
            self.last_notification[alert_id] = datetime.now()
            
            # Log the alert
            logger.warning(f"Predictive maintenance alert: {alert['message']} (Node: {alert['node']})")
            
            # TODO: Send notification through the notification system
            # This would integrate with the existing notification system
        except Exception as e:
            logger.error(f"Error processing alert: {str(e)}")
    
    def _analyze_node_hardware(self, node: str) -> Dict[str, Any]:
        """
        Analyze hardware health for a specific node.
        
        Args:
            node: Node ID to analyze
            
        Returns:
            Dict with analysis results and alerts
        """
        try:
            alerts = []
            predictions = {}
            
            # Get node health data
            health_result = self.system_health.get_node_health(node)
            if not health_result['success']:
                return {
                    "success": False,
                    "message": f"Failed to get health data for node {node}"
                }
            
            health_data = health_result['health']
            
            # Analyze disks
            if 'disks' in health_data:
                for disk in health_data['disks']:
                    disk_id = disk['device']
                    smart_data = disk.get('smart', {})
                    
                    # Get historical SMART data
                    historical_data = self._get_historical_smart_data(node, disk_id)
                    
                    # Predict disk failure
                    disk_prediction = self._predict_disk_failure(smart_data, historical_data)
                    predictions[f"disk_{disk_id}"] = disk_prediction
                    
                    if disk_prediction['failure_probability'] > self.config['disk_smart_threshold']:
                        alerts.append({
                            "component": "disk",
                            "type": "predicted_failure",
                            "severity": "high" if disk_prediction['failure_probability'] > 0.9 else "medium",
                            "message": f"Disk {disk_id} predicted to fail within {disk_prediction['estimated_days']} days",
                            "details": {
                                "device": disk_id,
                                "probability": disk_prediction['failure_probability'],
                                "estimated_days": disk_prediction['estimated_days'],
                                "indicators": disk_prediction['indicators']
                            },
                            "recommendations": [
                                "Backup data immediately",
                                "Plan for disk replacement",
                                "Check for disk errors in system logs"
                            ]
                        })
            
            # Analyze CPU
            if 'cpu' in health_data:
                cpu_data = health_data['cpu']
                
                # Check temperature
                if 'temperature' in cpu_data and cpu_data['temperature'] > self.config['cpu_temp_threshold']:
                    alerts.append({
                        "component": "cpu",
                        "type": "high_temperature",
                        "severity": "medium",
                        "message": f"CPU temperature is high ({cpu_data['temperature']}°C)",
                        "details": {
                            "temperature": cpu_data['temperature'],
                            "threshold": self.config['cpu_temp_threshold']
                        },
                        "recommendations": [
                            "Check cooling system",
                            "Clean dust from CPU cooler",
                            "Verify case airflow"
                        ]
                    })
                
                # Predict CPU issues
                historical_data = self._get_historical_cpu_data(node)
                cpu_prediction = self._predict_cpu_issues(cpu_data, historical_data)
                predictions["cpu"] = cpu_prediction
                
                if cpu_prediction.get('anomaly_score', 0) > self.config['prediction_threshold']:
                    alerts.append({
                        "component": "cpu",
                        "type": "predicted_issue",
                        "severity": "medium",
                        "message": "CPU performance degradation predicted",
                        "details": {
                            "anomaly_score": cpu_prediction['anomaly_score'],
                            "indicators": cpu_prediction['indicators']
                        },
                        "recommendations": [
                            "Monitor CPU performance",
                            "Check for thermal throttling",
                            "Consider running CPU diagnostics"
                        ]
                    })
            
            # Analyze memory
            if 'memory' in health_data:
                memory_data = health_data['memory']
                
                # Check for memory errors
                if memory_data.get('errors', 0) > self.config['memory_error_threshold']:
                    alerts.append({
                        "component": "memory",
                        "type": "memory_errors",
                        "severity": "high",
                        "message": f"Memory reporting {memory_data['errors']} errors",
                        "details": {
                            "errors": memory_data['errors'],
                            "threshold": self.config['memory_error_threshold']
                        },
                        "recommendations": [
                            "Run memory diagnostics",
                            "Check for faulty memory modules",
                            "Consider memory replacement"
                        ]
                    })
                
                # Predict memory issues
                historical_data = self._get_historical_memory_data(node)
                memory_prediction = self._predict_memory_issues(memory_data, historical_data)
                predictions["memory"] = memory_prediction
                
                if memory_prediction.get('anomaly_score', 0) > self.config['prediction_threshold']:
                    alerts.append({
                        "component": "memory",
                        "type": "predicted_issue",
                        "severity": "medium",
                        "message": "Memory performance degradation predicted",
                        "details": {
                            "anomaly_score": memory_prediction['anomaly_score'],
                            "indicators": memory_prediction['indicators']
                        },
                        "recommendations": [
                            "Monitor memory performance",
                            "Run memory diagnostics",
                            "Check for memory leaks in VMs"
                        ]
                    })
            
            return {
                "success": True,
                "predictions": predictions,
                "alerts": alerts
            }
        except Exception as e:
            logger.error(f"Error analyzing node hardware: {str(e)}")
            return {
                "success": False,
                "message": f"Error analyzing node hardware: {str(e)}"
            }
    
    def _get_historical_smart_data(self, node: str, disk_id: str) -> List[Dict]:
        """Get historical SMART data for a disk."""
        # This would normally query a time-series database or logs
        # For now, we'll return a placeholder
        return []
    
    def _get_historical_cpu_data(self, node: str) -> List[Dict]:
        """Get historical CPU performance data."""
        # This would normally query a time-series database or logs
        # For now, we'll return a placeholder
        return []
    
    def _get_historical_memory_data(self, node: str) -> List[Dict]:
        """Get historical memory performance data."""
        # This would normally query a time-series database or logs
        # For now, we'll return a placeholder
        return []
    
    def _predict_disk_failure(self, smart_data: Dict, historical_data: List[Dict]) -> Dict:
        """
        Predict disk failure based on SMART data.
        
        Args:
            smart_data: Current SMART attributes
            historical_data: Historical SMART data
            
        Returns:
            Dict with prediction results
        """
        # Extract key SMART indicators
        indicators = []
        failure_probability = 0.0
        estimated_days = 365  # Default to 1 year
        
        # Check for critical SMART attributes
        if 'attributes' in smart_data:
            attrs = smart_data['attributes']
            
            # Reallocated sectors (ID 5)
            if '5' in attrs and attrs['5']['raw'] > 0:
                indicators.append({
                    "attribute": "Reallocated Sectors",
                    "value": attrs['5']['raw'],
                    "impact": "high"
                })
                failure_probability += 0.2
                estimated_days = min(estimated_days, 90)
            
            # Pending sectors (ID 197)
            if '197' in attrs and attrs['197']['raw'] > 0:
                indicators.append({
                    "attribute": "Pending Sectors",
                    "value": attrs['197']['raw'],
                    "impact": "high"
                })
                failure_probability += 0.2
                estimated_days = min(estimated_days, 60)
            
            # Uncorrectable errors (ID 198)
            if '198' in attrs and attrs['198']['raw'] > 0:
                indicators.append({
                    "attribute": "Uncorrectable Errors",
                    "value": attrs['198']['raw'],
                    "impact": "critical"
                })
                failure_probability += 0.3
                estimated_days = min(estimated_days, 30)
            
            # SMART health status
            if smart_data.get('health', '') == 'FAILING_NOW':
                indicators.append({
                    "attribute": "SMART Health",
                    "value": "FAILING_NOW",
                    "impact": "critical"
                })
                failure_probability += 0.5
                estimated_days = min(estimated_days, 7)
        
        # Cap probability at 0.99
        failure_probability = min(failure_probability, 0.99)
        
        return {
            "failure_probability": failure_probability,
            "estimated_days": estimated_days,
            "indicators": indicators
        }
    
    def _predict_cpu_issues(self, cpu_data: Dict, historical_data: List[Dict]) -> Dict:
        """
        Predict CPU issues based on performance data.
        
        Args:
            cpu_data: Current CPU data
            historical_data: Historical CPU data
            
        Returns:
            Dict with prediction results
        """
        anomaly_score = 0.0
        indicators = []
        
        # Check for thermal issues
        if 'temperature' in cpu_data:
            temp = cpu_data['temperature']
            if temp > self.config['cpu_temp_threshold'] - 10:
                indicators.append({
                    "attribute": "Temperature",
                    "value": temp,
                    "impact": "medium" if temp < self.config['cpu_temp_threshold'] else "high"
                })
                anomaly_score += 0.1 * (temp / self.config['cpu_temp_threshold'])
        
        # Check for throttling
        if cpu_data.get('throttling', False):
            indicators.append({
                "attribute": "Throttling",
                "value": "Active",
                "impact": "high"
            })
            anomaly_score += 0.3
        
        # Check for high error rates
        if cpu_data.get('mce_errors', 0) > 0:
            indicators.append({
                "attribute": "MCE Errors",
                "value": cpu_data['mce_errors'],
                "impact": "critical"
            })
            anomaly_score += 0.5
        
        return {
            "anomaly_score": anomaly_score,
            "indicators": indicators
        }
    
    def _predict_memory_issues(self, memory_data: Dict, historical_data: List[Dict]) -> Dict:
        """
        Predict memory issues based on performance data.
        
        Args:
            memory_data: Current memory data
            historical_data: Historical memory data
            
        Returns:
            Dict with prediction results
        """
        anomaly_score = 0.0
        indicators = []
        
        # Check for memory errors
        if 'errors' in memory_data:
            errors = memory_data['errors']
            if errors > 0:
                indicators.append({
                    "attribute": "Memory Errors",
                    "value": errors,
                    "impact": "high"
                })
                anomaly_score += min(0.5, errors / 20)  # Cap at 0.5
        
        # Check for ECC corrections
        if memory_data.get('ecc_corrections', 0) > 10:
            indicators.append({
                "attribute": "ECC Corrections",
                "value": memory_data['ecc_corrections'],
                "impact": "medium"
            })
            anomaly_score += 0.2
        
        return {
            "anomaly_score": anomaly_score,
            "indicators": indicators
        }
