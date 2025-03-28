"""
Service metrics dashboard for Proxmox NLI.
Provides plain language explanations of service performance metrics.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import json
import threading
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

class ServiceMetricsDashboard:
    """Provides a dashboard with plain language explanations of service metrics."""
    
    def __init__(self, service_manager, health_monitor=None):
        """Initialize the metrics dashboard.
        
        Args:
            service_manager: ServiceManager instance to interact with services
            health_monitor: Optional ServiceHealthMonitor instance for health data
        """
        self.service_manager = service_manager
        self.health_monitor = health_monitor
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data', 'metrics')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Store historical metrics
        self.metrics_history = {}
        self.load_metrics_history()
        
        # Configure metric thresholds (these can be customized per service)
        self.default_thresholds = {
            'cpu': {
                'high': 80,  # percentage
                'critical': 90
            },
            'memory': {
                'high': 80,  # percentage
                'critical': 90
            },
            'disk_space': {
                'high': 80,  # percentage
                'critical': 90
            },
            'response_time': {
                'high': 2.0,  # seconds
                'critical': 5.0
            }
        }
        
        # Define metric categories for organization
        self.metric_categories = {
            'utilization': ['cpu', 'memory', 'disk_space'],
            'performance': ['response_time', 'throughput', 'request_rate'],
            'reliability': ['uptime', 'error_rate', 'availability']
        }
        
        # Plain language explanations for metrics
        self.metric_explanations = {
            'cpu': {
                'name': 'CPU Usage',
                'description': 'The amount of CPU resources the service is using.',
                'low': 'Very little CPU is being used. The service is idle or not processing much data.',
                'normal': 'The service is using a healthy amount of CPU resources.',
                'high': 'The service is using a lot of CPU resources. It might be under heavy load.',
                'critical': 'The service is using almost all available CPU resources. This could cause slowdowns.',
                'unit': '%',
                'good_range': '10-70%'
            },
            'memory': {
                'name': 'Memory Usage',
                'description': 'The amount of RAM the service is using.',
                'low': 'The service is using very little memory. It might not be caching data efficiently.',
                'normal': 'The service is using a healthy amount of memory.',
                'high': 'The service is using a lot of memory. It might be handling large datasets.',
                'critical': 'The service is using almost all available memory. This could lead to crashes or slowdowns.',
                'unit': '%',
                'good_range': '20-70%'
            },
            'disk_space': {
                'name': 'Disk Space',
                'description': 'The amount of storage space the service is using.',
                'low': 'The service is using very little disk space.',
                'normal': 'The service is using a reasonable amount of disk space.',
                'high': 'The service is using a lot of disk space. Consider adding more storage soon.',
                'critical': 'The service is using almost all available disk space. This could cause failures.',
                'unit': '%',
                'good_range': '10-70%'
            },
            'response_time': {
                'name': 'Response Time',
                'description': 'How quickly the service responds to requests.',
                'low': 'The service is responding very quickly. This is excellent performance.',
                'normal': 'The service is responding in a reasonable time.',
                'high': 'The service is responding slowly. Users might notice delays.',
                'critical': 'The service is responding very slowly. Users will experience significant delays.',
                'unit': 'seconds',
                'good_range': '< 1 second'
            },
            'throughput': {
                'name': 'Throughput',
                'description': 'The amount of data or requests the service can handle per second.',
                'low': 'The service is handling very few requests or little data per second.',
                'normal': 'The service is handling a healthy amount of traffic.',
                'high': 'The service is handling a lot of traffic. It\'s working hard but keeping up.',
                'critical': 'The service is handling an extremely high volume of traffic. It might struggle to keep up.',
                'unit': 'requests/s',
                'good_range': 'Depends on service type'
            },
            'uptime': {
                'name': 'Uptime',
                'description': 'The percentage of time the service has been available and running.',
                'low': 'The service has significant downtime. This indicates reliability issues.',
                'normal': 'The service has good uptime with minimal interruptions.',
                'high': 'The service has excellent uptime with very rare interruptions.',
                'critical': 'N/A - High uptime is always good',
                'unit': '%',
                'good_range': '> 99.9%'
            },
            'error_rate': {
                'name': 'Error Rate',
                'description': 'The percentage of requests or operations that result in errors.',
                'low': 'The service has very few errors. This is excellent reliability.',
                'normal': 'The service has an acceptable number of errors.',
                'high': 'The service has many errors. This indicates potential issues.',
                'critical': 'The service has an extremely high error rate. This indicates serious problems.',
                'unit': '%',
                'good_range': '< 1%'
            }
        }
        
    def load_metrics_history(self):
        """Load metrics history from disk."""
        try:
            metrics_file = os.path.join(self.data_dir, 'metrics_history.json')
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    self.metrics_history = json.load(f)
                logger.info(f"Loaded metrics history for {len(self.metrics_history)} services")
        except Exception as e:
            logger.error(f"Error loading metrics history: {str(e)}")
            self.metrics_history = {}
            
    def save_metrics_history(self):
        """Save metrics history to disk."""
        try:
            metrics_file = os.path.join(self.data_dir, 'metrics_history.json')
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics_history, f)
            logger.debug("Metrics history saved to disk")
        except Exception as e:
            logger.error(f"Error saving metrics history: {str(e)}")
    
    def update_metrics(self, service_id: str, metrics: Dict):
        """Update metrics for a specific service.
        
        Args:
            service_id: ID of the service to update metrics for
            metrics: Dictionary of metrics to update
        """
        if service_id not in self.metrics_history:
            self.metrics_history[service_id] = {
                'recent_metrics': [],
                'daily_averages': {},
                'weekly_averages': {}
            }
            
        # Add timestamp to metrics
        metrics['timestamp'] = datetime.now().isoformat()
        
        # Add to recent metrics list
        self.metrics_history[service_id]['recent_metrics'].append(metrics)
        
        # Keep only the last 100 metrics points
        if len(self.metrics_history[service_id]['recent_metrics']) > 100:
            self.metrics_history[service_id]['recent_metrics'] = \
                self.metrics_history[service_id]['recent_metrics'][-100:]
        
        # Calculate and update daily average
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.metrics_history[service_id]['daily_averages']:
            self.metrics_history[service_id]['daily_averages'][today] = {
                'count': 0,
                'cpu': 0,
                'memory': 0
            }
            
        day_metrics = self.metrics_history[service_id]['daily_averages'][today]
        day_metrics['count'] += 1
        
        # Update averages for numerical metrics
        for key, value in metrics.items():
            if key in ['cpu_percent', 'memory_percent'] and isinstance(value, (int, float)):
                metric_key = key.split('_')[0]  # 'cpu' or 'memory'
                if metric_key not in day_metrics:
                    day_metrics[metric_key] = 0
                # Running average calculation
                day_metrics[metric_key] = ((day_metrics[metric_key] * (day_metrics['count'] - 1)) 
                                          + value) / day_metrics['count']
        
        # Save updated metrics
        self.save_metrics_history()
    
    def update_service_metrics_from_health(self):
        """Update metrics for all services using health monitor data."""
        if not self.health_monitor:
            logger.warning("Health monitor not available for metrics update")
            return
            
        for service_id, health_data in self.health_monitor.health_data.items():
            if not health_data.get('checks'):
                continue
                
            latest_check = health_data['checks'][-1]
            if not latest_check or 'metrics' not in latest_check:
                continue
                
            metrics = latest_check['metrics']
            
            # Extract numerical values for metrics dashboard
            dashboard_metrics = {}
            
            # Process CPU usage
            if 'cpu_usage' in metrics:
                cpu_value = metrics['cpu_usage'].strip('%')
                try:
                    dashboard_metrics['cpu_percent'] = float(cpu_value)
                except ValueError:
                    pass
            
            # Process memory usage
            if 'memory_usage' in metrics and ' / ' in metrics['memory_usage']:
                try:
                    used, total = metrics['memory_usage'].split(' / ')
                    used_value = used.rstrip("MiB").rstrip("GiB").strip()
                    total_value = total.rstrip("MiB").rstrip("GiB").strip()
                    used_unit = "GB" if "GiB" in used else "MB"
                    total_unit = "GB" if "GiB" in total else "MB"
                    
                    used_float = float(used_value)
                    total_float = float(total_value)
                    
                    # Convert to same unit if needed
                    if used_unit != total_unit:
                        if used_unit == "MB" and total_unit == "GB":
                            used_float = used_float / 1024
                        elif used_unit == "GB" and total_unit == "MB":
                            used_float = used_float * 1024
                            
                    # Calculate percentage
                    mem_percent = (used_float / total_float) * 100
                    dashboard_metrics['memory_percent'] = mem_percent
                    dashboard_metrics['memory_used'] = used_float
                    dashboard_metrics['memory_total'] = total_float
                    dashboard_metrics['memory_unit'] = total_unit
                except (ValueError, ZeroDivisionError):
                    pass
            
            # Process network I/O
            if 'network_io' in metrics:
                dashboard_metrics['network_io'] = metrics['network_io']
            
            # Process disk I/O
            if 'disk_io' in metrics:
                dashboard_metrics['disk_io'] = metrics['disk_io']
            
            # Update service metrics if we extracted any values
            if dashboard_metrics:
                self.update_metrics(service_id, dashboard_metrics)
    
    def get_service_dashboard(self, service_id: str) -> Dict:
        """Get a dashboard with plain language explanations for a specific service.
        
        Args:
            service_id: ID of the service to get dashboard for
            
        Returns:
            Dashboard dictionary with metrics and explanations
        """
        if service_id not in self.metrics_history:
            return {
                "success": False,
                "message": f"No metrics data available for service '{service_id}'",
                "dashboard": None
            }
        
        service_metrics = self.metrics_history[service_id]
        recent_metrics = service_metrics.get('recent_metrics', [])
        
        if not recent_metrics:
            return {
                "success": False,
                "message": f"No recent metrics available for service '{service_id}'",
                "dashboard": None
            }
            
        # Get service definition for context
        service_def = self.service_manager.catalog.get_service(service_id)
        service_name = service_def['name'] if service_def else service_id
        
        # Generate dashboard with current metrics and trends
        dashboard = {
            "service_id": service_id,
            "service_name": service_name,
            "last_updated": recent_metrics[-1].get('timestamp'),
            "metrics": self._get_latest_metrics(recent_metrics),
            "trends": self._analyze_trends(recent_metrics),
            "explanations": {},
            "recommendations": []
        }
        
        # Add plain language explanations
        dashboard["explanations"] = self._generate_explanations(dashboard["metrics"], dashboard["trends"])
        
        # Add recommendations based on metrics
        dashboard["recommendations"] = self._generate_recommendations(dashboard["metrics"], dashboard["trends"])
        
        return {
            "success": True,
            "dashboard": dashboard
        }
    
    def _get_latest_metrics(self, metrics: List[Dict]) -> Dict:
        """Extract the latest metrics from a list of metrics snapshots."""
        latest = metrics[-1]
        result = {}
        
        # Extract numerical metrics
        for key, value in latest.items():
            if key != 'timestamp' and isinstance(value, (int, float)):
                result[key] = value
                
        # Add derived metrics if possible
        if 'memory_used' in result and 'memory_total' in result:
            result['free_memory'] = result['memory_total'] - result['memory_used']
            
        return result
    
    def _analyze_trends(self, metrics: List[Dict]) -> Dict:
        """Analyze trends in metrics over time."""
        if len(metrics) < 2:
            return {}  # Need at least 2 data points for trends
            
        # Get metrics from last 24 hours
        cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
        recent_metrics = [m for m in metrics if m.get('timestamp', '') >= cutoff_time]
        
        trends = {}
        
        # Calculate trends for numerical metrics
        numeric_metrics = ['cpu_percent', 'memory_percent']
        for metric in numeric_metrics:
            values = [m.get(metric) for m in recent_metrics if metric in m and m.get(metric) is not None]
            
            if len(values) >= 2:
                # Calculate change over period
                first_val = values[0]
                last_val = values[-1]
                change = last_val - first_val
                
                # Calculate trend (1=up, 0=stable, -1=down)
                if abs(change) < 5:  # Less than 5% change is considered stable
                    trend = 0
                else:
                    trend = 1 if change > 0 else -1
                
                # Calculate volatility (standard deviation)
                if len(values) >= 3:
                    volatility = statistics.stdev(values)
                else:
                    volatility = 0
                    
                trends[metric] = {
                    'change': change,
                    'trend': trend, 
                    'volatility': volatility,
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values)
                }
        
        return trends
    
    def _generate_explanations(self, metrics: Dict, trends: Dict) -> Dict:
        """Generate plain language explanations for metrics and trends."""
        explanations = {}
        
        # CPU usage explanation
        if 'cpu_percent' in metrics:
            cpu_percent = metrics['cpu_percent']
            explanation = f"The service is currently using {cpu_percent:.1f}% of the available CPU resources."
            
            # Add context based on thresholds
            if cpu_percent >= self.default_thresholds['cpu']['critical']:
                explanation += " This is a critically high level of CPU usage, indicating the service is under heavy load."
            elif cpu_percent >= self.default_thresholds['cpu']['high']:
                explanation += " This is elevated CPU usage, which may impact performance if it continues."
            elif cpu_percent >= 50:
                explanation += " This is moderate CPU usage, which is generally healthy."
            else:
                explanation += " This indicates the service has plenty of CPU capacity available."
                
            # Add trend information if available
            if 'cpu_percent' in trends:
                cpu_trend = trends['cpu_percent']
                if cpu_trend['trend'] == 1:
                    explanation += f" CPU usage has been increasing over the past 24 hours (by {cpu_trend['change']:.1f}%)."
                elif cpu_trend['trend'] == -1:
                    explanation += f" CPU usage has been decreasing over the past 24 hours (by {abs(cpu_trend['change']):.1f}%)."
                else:
                    explanation += " CPU usage has been stable over the past 24 hours."
                    
                if cpu_trend['volatility'] > 20:
                    explanation += " The CPU usage is highly variable, suggesting sporadic workloads or scheduled tasks."
            
            explanations['cpu'] = explanation
        
        # Memory usage explanation
        if 'memory_percent' in metrics:
            memory_percent = metrics['memory_percent']
            memory_unit = metrics.get('memory_unit', 'MB')
            
            explanation = f"The service is using {memory_percent:.1f}% of its allocated memory."
            
            if 'memory_used' in metrics and 'memory_total' in metrics:
                used = metrics['memory_used']
                total = metrics['memory_total']
                explanation += f" ({used:.1f} {memory_unit} used out of {total:.1f} {memory_unit} total)"
                
            # Add context based on thresholds
            if memory_percent >= self.default_thresholds['memory']['critical']:
                explanation += " This is a critically high level of memory usage, which could lead to performance issues or service failures."
            elif memory_percent >= self.default_thresholds['memory']['high']:
                explanation += " This is elevated memory usage, which should be monitored."
            elif memory_percent >= 50:
                explanation += " This is moderate memory usage, which is generally healthy."
            else:
                explanation += " This indicates the service has plenty of memory available."
                
            # Add trend information if available
            if 'memory_percent' in trends:
                mem_trend = trends['memory_percent']
                if mem_trend['trend'] == 1:
                    explanation += f" Memory usage has been increasing over the past 24 hours (by {mem_trend['change']:.1f}%)."
                elif mem_trend['trend'] == -1:
                    explanation += f" Memory usage has been decreasing over the past 24 hours (by {abs(mem_trend['change']):.1f}%)."
                else:
                    explanation += " Memory usage has been stable over the past 24 hours."
                    
                if 'max' in mem_trend and mem_trend['max'] > self.default_thresholds['memory']['critical']:
                    explanation += f" Memory usage peaked at {mem_trend['max']:.1f}% in the last 24 hours, which is a critical level."
            
            explanations['memory'] = explanation
            
        # Network usage explanation
        if 'network_io' in metrics:
            network_io = metrics['network_io']
            explanation = f"Network I/O: {network_io}"
            
            # Parse values if in standard format
            if ' / ' in network_io:
                try:
                    in_traffic, out_traffic = network_io.split(' / ')
                    explanation = f"The service is transferring {in_traffic} of data in and {out_traffic} out."
                except ValueError:
                    pass
            
            explanations['network'] = explanation
            
        # Disk I/O explanation
        if 'disk_io' in metrics:
            disk_io = metrics['disk_io']
            explanation = f"Disk I/O: {disk_io}"
            
            # Parse values if in standard format
            if ' / ' in disk_io:
                try:
                    read, write = disk_io.split(' / ')
                    explanation = f"The service is reading {read} from disk and writing {write} to disk."
                except ValueError:
                    pass
            
            explanations['disk'] = explanation
            
        return explanations
    
    def _generate_recommendations(self, metrics: Dict, trends: Dict) -> List[str]:
        """Generate recommendations based on metrics and trends."""
        recommendations = []
        
        # CPU recommendations
        if 'cpu_percent' in metrics:
            cpu_percent = metrics['cpu_percent']
            
            if cpu_percent >= self.default_thresholds['cpu']['critical']:
                recommendations.append("Consider increasing the CPU allocation for this service or optimizing its workload.")
            elif cpu_percent >= self.default_thresholds['cpu']['high']:
                recommendations.append("Monitor CPU usage to ensure it doesn't impact performance.")
                
            # Check for increasing trend
            if 'cpu_percent' in trends and trends['cpu_percent']['trend'] == 1 and trends['cpu_percent']['change'] > 15:
                recommendations.append("Investigate the cause of increasing CPU usage before it becomes problematic.")
        
        # Memory recommendations
        if 'memory_percent' in metrics:
            memory_percent = metrics['memory_percent']
            
            if memory_percent >= self.default_thresholds['memory']['critical']:
                recommendations.append("Increase the memory allocation for this service to prevent potential failures.")
            elif memory_percent >= self.default_thresholds['memory']['high']:
                recommendations.append("Consider increasing memory allocation or optimize the service's memory usage.")
                
            # Check for increasing trend
            if 'memory_percent' in trends and trends['memory_percent']['trend'] == 1 and trends['memory_percent']['change'] > 15:
                recommendations.append("Monitor the increasing memory usage trend and plan for additional resources if needed.")
                
            # Check for potential memory leak
            if ('memory_percent' in trends and trends['memory_percent']['trend'] == 1 
                    and not ('cpu_percent' in trends and trends['cpu_percent']['trend'] == 1)
                    and trends['memory_percent']['change'] > 10):
                recommendations.append("The pattern of increasing memory usage without corresponding CPU increase might indicate a memory leak.")
                
        # General recommendations
        if len(metrics.keys()) <= 2:  # Limited metrics available
            recommendations.append("Enable more detailed metrics collection for better insights.")
            
        return recommendations
    
    def generate_dashboard_report(self, service_id: str) -> Dict:
        """Generate a consolidated natural language dashboard report.
        
        Args:
            service_id: ID of the service to generate report for
            
        Returns:
            Report dictionary with natural language dashboard report
        """
        # Get dashboard data first
        dashboard_result = self.get_service_dashboard(service_id)
        if not dashboard_result.get('success'):
            return {
                "success": False,
                "message": dashboard_result.get('message', 'Failed to get dashboard data'),
                "report": f"Unable to generate a metrics dashboard for {service_id}."
            }
            
        dashboard = dashboard_result['dashboard']
        service_name = dashboard['service_name']
        
        # Build report sections
        sections = []
        
        # Summary section
        summary = f"## {service_name} Metrics Dashboard\n\n"
        
        # Add timestamp
        try:
            timestamp = datetime.fromisoformat(dashboard['last_updated'])
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            summary += f"Last updated: {formatted_time}\n\n"
        except (ValueError, TypeError):
            summary += "Last updated: Unknown\n\n"
        
        sections.append(summary)
        
        # Metrics explanations
        explanations = dashboard['explanations']
        if explanations:
            metrics_section = "### Resource Usage\n\n"
            
            # CPU explanation
            if 'cpu' in explanations:
                metrics_section += f"**CPU**: {explanations['cpu']}\n\n"
                
            # Memory explanation
            if 'memory' in explanations:
                metrics_section += f"**Memory**: {explanations['memory']}\n\n"
                
            # Network explanation
            if 'network' in explanations:
                metrics_section += f"**Network**: {explanations['network']}\n\n"
                
            # Disk explanation
            if 'disk' in explanations:
                metrics_section += f"**Storage**: {explanations['disk']}\n\n"
                
            sections.append(metrics_section)
        
        # Recommendations
        recommendations = dashboard['recommendations']
        if recommendations:
            rec_section = "### Recommendations\n\n"
            for i, rec in enumerate(recommendations, 1):
                rec_section += f"{i}. {rec}\n"
            rec_section += "\n"
            sections.append(rec_section)
            
        # Combine all sections
        full_report = '\n'.join(sections)
        
        # Add health report if health monitor is available
        if self.health_monitor:
            try:
                health_report = self.health_monitor.get_health_report(service_id)
                if health_report.get('success'):
                    health_section = "### Health Status\n\n"
                    health_section += health_report['summary'] + "\n\n"
                    
                    # Add uptime information
                    uptime_parts = health_report['report'].split("\n\n")
                    if len(uptime_parts) > 2:  # Format is status, resource usage, uptime
                        health_section += uptime_parts[2] + "\n\n"
                        
                    # Add issues if any
                    if health_report.get('has_issues'):
                        issues_section = [p for p in uptime_parts if "active issue" in p.lower()]
                        if issues_section:
                            health_section += issues_section[0] + "\n\n"
                            
                    full_report += "\n" + health_section
            except Exception as e:
                logger.warning(f"Error adding health report to dashboard: {str(e)}")
        
        return {
            "success": True,
            "message": "Dashboard report generated successfully",
            "report": full_report,
            "dashboard": dashboard
        }
        
    def get_system_dashboard(self) -> Dict:
        """Get a system-wide dashboard with metrics for all services.
        
        Returns:
            Dashboard dictionary with metrics for all services
        """
        services_metrics = []
        
        for service_id in self.metrics_history:
            dashboard_result = self.get_service_dashboard(service_id)
            if dashboard_result.get('success'):
                dashboard = dashboard_result['dashboard']
                services_metrics.append({
                    "service_id": service_id,
                    "service_name": dashboard['service_name'],
                    "last_updated": dashboard['last_updated'],
                    "metrics": dashboard['metrics'],
                    "has_recommendations": len(dashboard.get('recommendations', [])) > 0
                })
        
        # Sort services by those with recommendations first, then by name
        services_metrics.sort(key=lambda s: (not s['has_recommendations'], s['service_name']))
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "services": services_metrics,
            "total_count": len(services_metrics)
        }
        
    def generate_system_dashboard_report(self) -> Dict:
        """Generate a natural language system-wide dashboard report.
        
        Returns:
            Report dictionary with natural language system dashboard
        """
        system_dashboard = self.get_system_dashboard()
        services = system_dashboard.get('services', [])
        
        if not services:
            return {
                "success": True,
                "report": "No services with metrics data available for dashboard."
            }
        
        # Build report sections
        sections = []
        
        # Summary section
        total = len(services)
        services_with_recommendations = [s for s in services if s.get('has_recommendations', False)]
        
        summary = f"## System Metrics Dashboard\n\n"
        summary += f"Monitoring {total} {'service' if total == 1 else 'services'}. "
        
        if services_with_recommendations:
            summary += f"{len(services_with_recommendations)} {'service requires' if len(services_with_recommendations) == 1 else 'services require'} attention.\n\n"
        else:
            summary += "All services are operating within normal parameters.\n\n"
        
        sections.append(summary)
        
        # Services with recommendations
        if services_with_recommendations:
            attention_section = "### Services Requiring Attention\n\n"
            for service in services_with_recommendations:
                attention_section += f"- **{service['service_name']}**: "
                
                metrics = service.get('metrics', {})
                issues = []
                
                if 'cpu_percent' in metrics and metrics['cpu_percent'] >= self.default_thresholds['cpu']['high']:
                    issues.append(f"CPU usage at {metrics['cpu_percent']:.1f}%")
                    
                if 'memory_percent' in metrics and metrics['memory_percent'] >= self.default_thresholds['memory']['high']:
                    issues.append(f"Memory usage at {metrics['memory_percent']:.1f}%")
                    
                if issues:
                    attention_section += ", ".join(issues)
                else:
                    attention_section += "Requires review"
                    
                attention_section += "\n"
                
            attention_section += "\n"
            sections.append(attention_section)
        
        # Resource summary
        resource_section = "### Resource Usage Summary\n\n"
        
        # Calculate average CPU and memory usage
        cpu_values = [s['metrics'].get('cpu_percent') for s in services if 'cpu_percent' in s.get('metrics', {})]
        memory_values = [s['metrics'].get('memory_percent') for s in services if 'memory_percent' in s.get('metrics', {})]
        
        if cpu_values:
            avg_cpu = sum(cpu_values) / len(cpu_values)
            max_cpu = max(cpu_values)
            max_cpu_service = next(s['service_name'] for s in services if s['metrics'].get('cpu_percent') == max_cpu)
            
            resource_section += f"Average CPU usage across all services: {avg_cpu:.1f}%\n"
            resource_section += f"Highest CPU usage: {max_cpu:.1f}% ({max_cpu_service})\n\n"
            
        if memory_values:
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
            max_memory_service = next(s['service_name'] for s in services if s['metrics'].get('memory_percent') == max_memory)
            
            resource_section += f"Average memory usage across all services: {avg_memory:.1f}%\n"
            resource_section += f"Highest memory usage: {max_memory:.1f}% ({max_memory_service})\n"
            
        sections.append(resource_section)
        
        # Combine all sections
        full_report = '\n'.join(sections)
        
        return {
            "success": True,
            "report": full_report,
            "dashboard": system_dashboard
        }
        
    def generate_plain_language_dashboard(self, service_id: str) -> Dict:
        """Generate a dashboard with plain language explanations for a service.
        
        Args:
            service_id: ID of the service to generate dashboard for
            
        Returns:
            Dictionary with dashboard data and explanations
        """
        # Get service information
        service_info = self.service_manager.get_service_info(service_id)
        if not service_info.get('success', False):
            return {
                'success': False,
                'message': f'Failed to get service info: {service_info.get("message")}'
            }
            
        service = service_info.get('service', {})
        service_name = service.get('name', 'Unknown Service')
        
        # Get latest metrics for the service
        metrics = self.get_service_metrics(service_id)
        if not metrics.get('success', False):
            return {
                'success': False,
                'message': f'Failed to get service metrics: {metrics.get("message")}'
            }
            
        metric_data = metrics.get('metrics', {})
        
        # Generate dashboard with explanations
        dashboard = {
            'service_id': service_id,
            'service_name': service_name,
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'summary': self._generate_service_summary(service_id, metric_data),
            'recommendations': self._generate_recommendations(service_id, metric_data)
        }
        
        # Process each metric with plain language explanation
        for metric_name, value in metric_data.items():
            if metric_name in self.metric_explanations:
                explanation = self.metric_explanations[metric_name]
                
                # Determine the status level
                status = self._determine_metric_status(metric_name, value)
                
                # Get the appropriate explanation for this status
                status_explanation = explanation.get(status, '')
                
                dashboard['metrics'][metric_name] = {
                    'name': explanation['name'],
                    'value': value,
                    'unit': explanation['unit'],
                    'status': status,
                    'description': explanation['description'],
                    'explanation': status_explanation,
                    'good_range': explanation['good_range']
                }
        
        return {
            'success': True,
            'message': f'Dashboard generated for {service_name}',
            'dashboard': dashboard
        }
    
    def _determine_metric_status(self, metric_name: str, value: float) -> str:
        """Determine the status level of a metric.
        
        Args:
            metric_name: Name of the metric
            value: Current value of the metric
            
        Returns:
            Status level (low, normal, high, critical)
        """
        if metric_name not in self.default_thresholds:
            return 'normal'
            
        thresholds = self.default_thresholds[metric_name]
        
        # For metrics where lower is better (like error_rate, response_time)
        if metric_name in ['error_rate', 'response_time']:
            if value < thresholds.get('low', 1):
                return 'low'
            elif value < thresholds.get('high', 2):
                return 'normal'
            elif value < thresholds.get('critical', 5):
                return 'high'
            else:
                return 'critical'
        # For metrics where higher can be better (like uptime)
        elif metric_name in ['uptime']:
            if value > 99.9:
                return 'high'
            elif value > 99:
                return 'normal'
            else:
                return 'low'
        # For standard metrics (cpu, memory, disk_space)
        else:
            if value < 10:
                return 'low'
            elif value < thresholds.get('high', 80):
                return 'normal'
            elif value < thresholds.get('critical', 90):
                return 'high'
            else:
                return 'critical'
    
    def _generate_service_summary(self, service_id: str, metrics: Dict) -> str:
        """Generate a plain language summary of service health.
        
        Args:
            service_id: ID of the service
            metrics: Dictionary of current metrics
            
        Returns:
            Plain language summary
        """
        service_info = self.service_manager.get_service_info(service_id)
        service_name = service_info.get('service', {}).get('name', 'The service')
        
        # Count metrics by status
        status_counts = {
            'critical': 0,
            'high': 0,
            'normal': 0,
            'low': 0
        }
        
        for metric_name, value in metrics.items():
            if metric_name in self.metric_explanations:
                status = self._determine_metric_status(metric_name, value)
                status_counts[status] += 1
        
        # Generate summary based on status counts
        if status_counts['critical'] > 0:
            return f"{service_name} is experiencing critical issues. Immediate attention is required to prevent service disruption."
        elif status_counts['high'] > 1:
            return f"{service_name} is under heavy load. While still functioning, it's approaching resource limits in multiple areas."
        elif status_counts['high'] == 1:
            # Find which metric is high
            high_metric = next((name for name, value in metrics.items() 
                              if name in self.metric_explanations and 
                              self._determine_metric_status(name, value) == 'high'), None)
            
            if high_metric:
                return f"{service_name} is generally healthy, but {self.metric_explanations[high_metric]['name'].lower()} is higher than normal."
            else:
                return f"{service_name} is generally healthy, but one metric is higher than normal."
        elif status_counts['low'] > status_counts['normal']:
            return f"{service_name} is underutilized. It's using fewer resources than expected, which might indicate it's not being fully used."
        else:
            return f"{service_name} is healthy and operating normally. All metrics are within expected ranges."
    
    def _generate_recommendations(self, service_id: str, metrics: Dict) -> List[str]:
        """Generate recommendations based on service metrics.
        
        Args:
            service_id: ID of the service
            metrics: Dictionary of current metrics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check CPU usage
        if 'cpu' in metrics:
            cpu_value = metrics['cpu']
            if cpu_value > self.default_thresholds['cpu']['critical']:
                recommendations.append("Consider allocating more CPU resources to this service or optimizing its code to reduce CPU usage.")
            elif cpu_value > self.default_thresholds['cpu']['high']:
                recommendations.append("Monitor CPU usage closely. If it remains high, consider allocating more CPU resources.")
            elif cpu_value < 10:
                recommendations.append("This service is using very little CPU. Consider reducing allocated CPU resources to save energy.")
        
        # Check memory usage
        if 'memory' in metrics:
            memory_value = metrics['memory']
            if memory_value > self.default_thresholds['memory']['critical']:
                recommendations.append("Increase memory allocation to prevent potential crashes or performance issues.")
            elif memory_value > self.default_thresholds['memory']['high']:
                recommendations.append("Monitor memory usage closely. If it remains high, consider increasing memory allocation.")
            elif memory_value < 20:
                recommendations.append("This service is using very little memory. Consider reducing allocated memory if this pattern continues.")
        
        # Check disk space
        if 'disk_space' in metrics:
            disk_value = metrics['disk_space']
            if disk_value > self.default_thresholds['disk_space']['critical']:
                recommendations.append("Urgent: Add more storage space or clean up unnecessary data to prevent service failure.")
            elif disk_value > self.default_thresholds['disk_space']['high']:
                recommendations.append("Plan to add more storage space soon or implement data cleanup procedures.")
        
        # Check response time
        if 'response_time' in metrics:
            response_value = metrics['response_time']
            if response_value > self.default_thresholds['response_time']['critical']:
                recommendations.append("Investigate the cause of slow response times. This could be due to resource constraints or code inefficiencies.")
            elif response_value > self.default_thresholds['response_time']['high']:
                recommendations.append("Monitor response times closely. If they remain high, investigate potential bottlenecks.")
        
        # Check error rate
        if 'error_rate' in metrics and metrics['error_rate'] > 1:
            recommendations.append("Investigate the cause of errors. Review logs to identify and fix the most common error types.")
        
        # If no specific recommendations, provide a general one
        if not recommendations:
            recommendations.append("All metrics look good. Continue monitoring to maintain optimal performance.")
        
        return recommendations