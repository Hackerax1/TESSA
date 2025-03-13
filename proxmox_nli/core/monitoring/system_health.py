"""
System health monitoring module for overall system status and health checks.
"""
import logging
import time
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
from .metrics_collector import MetricsCollector
from .resource_monitor import ResourceMonitor
from ..events.alert_manager import AlertManager

logger = logging.getLogger(__name__)

class SystemHealth:
    """Manages overall system health monitoring and status"""
    
    def __init__(self, api, monitoring_integration=None):
        """Initialize with API connection and optional monitoring integration"""
        self.api = api
        self.monitoring = monitoring_integration
        self.metrics_collector = MetricsCollector(api, monitoring_integration)
        self.resource_monitor = ResourceMonitor(api, monitoring_integration)
        self.alert_manager = AlertManager()
        self.health_checks_active = False
        self.health_check_thread = None
        
        # Register for resource alerts
        self.resource_monitor.register_alert_callback(self._handle_resource_alert)
        
        # Health check definitions
        self.health_checks = {
            'node_status': self._check_node_status,
            'cluster_quorum': self._check_cluster_quorum,
            'storage_health': self._check_storage_health,
            'network_connectivity': self._check_network_connectivity,
            'service_status': self._check_service_status,
            'backup_status': self._check_backup_status,
            'ha_status': self._check_ha_status
        }
        
        # System status cache
        self.system_status = {
            'overall_health': 'unknown',
            'last_check': None,
            'components': {},
            'active_alerts': []
        }
    
    def start_health_checks(self, interval: int = 300) -> Dict[str, Any]:
        """Start system health monitoring"""
        try:
            if self.health_checks_active:
                return {
                    "success": False,
                    "message": "Health checks already running"
                }
            
            # Start resource monitoring first
            monitor_result = self.resource_monitor.start_monitoring()
            if not monitor_result["success"]:
                return monitor_result
            
            self.health_checks_active = True
            self.health_check_thread = threading.Thread(
                target=self._health_check_loop,
                args=(interval,),
                daemon=True
            )
            self.health_check_thread.start()
            
            return {
                "success": True,
                "message": "System health monitoring started"
            }
        except Exception as e:
            logger.error(f"Error starting health checks: {str(e)}")
            return {
                "success": False,
                "message": f"Error starting health checks: {str(e)}"
            }
    
    def stop_health_checks(self) -> Dict[str, Any]:
        """Stop system health monitoring"""
        try:
            if not self.health_checks_active:
                return {
                    "success": False,
                    "message": "Health checks not running"
                }
            
            self.health_checks_active = False
            if self.health_check_thread:
                self.health_check_thread.join(timeout=5)
            
            # Stop resource monitoring
            self.resource_monitor.stop_monitoring()
            
            return {
                "success": True,
                "message": "System health monitoring stopped"
            }
        except Exception as e:
            logger.error(f"Error stopping health checks: {str(e)}")
            return {
                "success": False,
                "message": f"Error stopping health checks: {str(e)}"
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            # Update status if it's stale (older than 5 minutes)
            if (not self.system_status['last_check'] or 
                time.time() - self.system_status['last_check'] > 300):
                self._run_health_checks()
            
            return {
                "success": True,
                "status": self.system_status
            }
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting system health: {str(e)}"
            }
    
    def _health_check_loop(self, interval: int):
        """Main health check loop"""
        while self.health_checks_active:
            try:
                self._run_health_checks()
            except Exception as e:
                logger.error(f"Error in health check loop: {str(e)}")
            
            time.sleep(interval)
    
    def _run_health_checks(self):
        """Run all configured health checks"""
        try:
            results = {}
            critical_issues = []
            warnings = []
            
            for check_name, check_func in self.health_checks.items():
                try:
                    result = check_func()
                    results[check_name] = result
                    
                    if result['status'] == 'critical':
                        critical_issues.append(result)
                    elif result['status'] == 'warning':
                        warnings.append(result)
                except Exception as e:
                    logger.error(f"Error in health check {check_name}: {str(e)}")
                    results[check_name] = {
                        'status': 'error',
                        'message': str(e)
                    }
                    critical_issues.append(results[check_name])
            
            # Determine overall health
            if critical_issues:
                overall_health = 'critical'
            elif warnings:
                overall_health = 'warning'
            else:
                overall_health = 'healthy'
            
            # Update system status
            self.system_status = {
                'overall_health': overall_health,
                'last_check': int(time.time()),
                'components': results,
                'active_alerts': self._get_active_alerts()
            }
            
        except Exception as e:
            logger.error(f"Error running health checks: {str(e)}")
    
    def _check_node_status(self) -> Dict[str, Any]:
        """Check status of all cluster nodes"""
        try:
            nodes = self.api.api_request('GET', 'nodes')
            if not nodes['success']:
                return {
                    'status': 'critical',
                    'message': 'Failed to get node status'
                }
            
            offline_nodes = []
            for node in nodes['data']:
                if node.get('status') != 'online':
                    offline_nodes.append(node['node'])
            
            if offline_nodes:
                return {
                    'status': 'critical',
                    'message': f'Nodes offline: {", ".join(offline_nodes)}',
                    'affected_nodes': offline_nodes
                }
            
            return {
                'status': 'healthy',
                'message': 'All nodes online'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking node status: {str(e)}'
            }
    
    def _check_cluster_quorum(self) -> Dict[str, Any]:
        """Check cluster quorum status"""
        try:
            status = self.api.api_request('GET', 'cluster/status')
            if not status['success']:
                return {
                    'status': 'critical',
                    'message': 'Failed to get cluster status'
                }
            
            quorate = None
            for item in status['data']:
                if item['type'] == 'cluster':
                    quorate = item.get('quorate')
                    break
            
            if quorate is None:
                return {
                    'status': 'warning',
                    'message': 'Unable to determine quorum status'
                }
            elif not quorate:
                return {
                    'status': 'critical',
                    'message': 'Cluster has lost quorum'
                }
            
            return {
                'status': 'healthy',
                'message': 'Cluster quorum established'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking cluster quorum: {str(e)}'
            }
    
    def _check_storage_health(self) -> Dict[str, Any]:
        """Check health of storage pools"""
        try:
            storage = self.api.api_request('GET', 'storage')
            if not storage['success']:
                return {
                    'status': 'critical',
                    'message': 'Failed to get storage status'
                }
            
            issues = []
            for pool in storage['data']:
                if not pool.get('active'):
                    issues.append(f"Storage {pool['storage']} is inactive")
                elif pool.get('used', 0) / pool.get('total', 1) > 0.95:
                    issues.append(f"Storage {pool['storage']} is over 95% full")
            
            if issues:
                return {
                    'status': 'warning' if len(issues) == 1 else 'critical',
                    'message': '; '.join(issues)
                }
            
            return {
                'status': 'healthy',
                'message': 'All storage pools healthy'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking storage health: {str(e)}'
            }
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity between nodes"""
        try:
            nodes = self.api.api_request('GET', 'nodes')
            if not nodes['success']:
                return {
                    'status': 'critical',
                    'message': 'Failed to get node list'
                }
            
            issues = []
            for node in nodes['data']:
                ping = self.api.api_request('GET', f'nodes/{node["node"]}/ping')
                if not ping['success'] or not ping.get('data', {}).get('status', '').startswith('OK'):
                    issues.append(f"Node {node['node']} unreachable")
            
            if issues:
                return {
                    'status': 'critical',
                    'message': '; '.join(issues)
                }
            
            return {
                'status': 'healthy',
                'message': 'All nodes reachable'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking network connectivity: {str(e)}'
            }
    
    def _check_service_status(self) -> Dict[str, Any]:
        """Check status of critical services"""
        try:
            nodes = self.api.api_request('GET', 'nodes')
            if not nodes['success']:
                return {
                    'status': 'critical',
                    'message': 'Failed to get node list'
                }
            
            critical_services = ['pvedaemon', 'pveproxy', 'pve-cluster']
            issues = []
            
            for node in nodes['data']:
                services = self.api.api_request('GET', f'nodes/{node["node"]}/services')
                if not services['success']:
                    issues.append(f"Failed to get services for node {node['node']}")
                    continue
                
                for service in services['data']:
                    if service['name'] in critical_services and not service.get('running'):
                        issues.append(f"Service {service['name']} not running on {node['node']}")
            
            if issues:
                return {
                    'status': 'critical',
                    'message': '; '.join(issues)
                }
            
            return {
                'status': 'healthy',
                'message': 'All critical services running'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking service status: {str(e)}'
            }
    
    def _check_backup_status(self) -> Dict[str, Any]:
        """Check status of backup jobs"""
        try:
            nodes = self.api.api_request('GET', 'nodes')
            if not nodes['success']:
                return {
                    'status': 'warning',
                    'message': 'Failed to get node list'
                }
            
            issues = []
            for node in nodes['data']:
                tasks = self.api.api_request('GET', f'nodes/{node["node"]}/tasks')
                if not tasks['success']:
                    continue
                
                for task in tasks['data']:
                    if task['type'] == 'vzdump' and task.get('status') == 'error':
                        issues.append(f"Backup failed on {node['node']}: {task.get('exitstatus')}")
            
            if issues:
                return {
                    'status': 'warning',
                    'message': '; '.join(issues)
                }
            
            return {
                'status': 'healthy',
                'message': 'No backup issues detected'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking backup status: {str(e)}'
            }
    
    def _check_ha_status(self) -> Dict[str, Any]:
        """Check high availability status"""
        try:
            ha_status = self.api.api_request('GET', 'cluster/ha/status')
            if not ha_status['success']:
                return {
                    'status': 'warning',
                    'message': 'Failed to get HA status'
                }
            
            issues = []
            for resource in ha_status['data']:
                if resource.get('status') not in ['started', 'running']:
                    issues.append(f"HA resource {resource.get('id')} is {resource.get('status')}")
            
            if issues:
                return {
                    'status': 'critical',
                    'message': '; '.join(issues)
                }
            
            return {
                'status': 'healthy',
                'message': 'All HA resources running'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking HA status: {str(e)}'
            }
    
    def _handle_resource_alert(self, alert: Dict):
        """Handle resource alerts from ResourceMonitor"""
        try:
            # Forward alert to alert manager
            self.alert_manager.add_alert(
                level=alert['level'],
                message=alert['message'],
                source='resource_monitor',
                context=alert['context']
            )
        except Exception as e:
            logger.error(f"Error handling resource alert: {str(e)}")
    
    def _get_active_alerts(self) -> List[Dict]:
        """Get list of active alerts"""
        try:
            return self.alert_manager.get_active_alerts()
        except Exception as e:
            logger.error(f"Error getting active alerts: {str(e)}")
            return []