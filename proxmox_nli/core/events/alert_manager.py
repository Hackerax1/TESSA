"""
Alert manager for Proxmox NLI.
Handles system alerts, monitoring thresholds, and alert routing.
"""
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self, event_dispatcher=None, notification_manager=None):
        """
        Initialize the alert manager
        
        Args:
            event_dispatcher: Optional EventDispatcher instance
            notification_manager: Optional NotificationManager instance
        """
        self.event_dispatcher = event_dispatcher
        self.notification_manager = notification_manager
        self.config = self._load_config()
        self.alert_history: List[Dict[str, Any]] = []
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Register built-in alert handlers
        self._register_default_handlers()
        
        # Register for system events if dispatcher provided
        if event_dispatcher:
            self._register_event_handlers()

    def _load_config(self) -> Dict[str, Any]:
        """Load alert configuration"""
        config_path = os.path.join(os.path.dirname(__file__), 'alert_config.json')
        default_config = {
            "thresholds": {
                "cpu_usage": 90,
                "memory_usage": 85,
                "disk_usage": 85,
                "load_average": 10,
                "network_errors": 100
            },
            "alert_levels": {
                "critical": {
                    "channels": ["email", "websocket", "desktop"],
                    "retry_interval": 300,  # 5 minutes
                    "auto_resolve": False
                },
                "warning": {
                    "channels": ["websocket", "desktop"],
                    "retry_interval": 900,  # 15 minutes
                    "auto_resolve": True
                },
                "info": {
                    "channels": ["websocket"],
                    "retry_interval": 3600,  # 1 hour
                    "auto_resolve": True
                }
            },
            "retention_days": 30,
            "enabled": True
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return {**default_config, **json.load(f)}
        except Exception as e:
            logger.error(f"Error loading alert config: {str(e)}")
        
        return default_config

    def _register_event_handlers(self) -> None:
        """Register for relevant system events"""
        if self.event_dispatcher:
            self.event_dispatcher.subscribe("resource_metric", self._handle_resource_metric)
            self.event_dispatcher.subscribe("system_event", self._handle_system_event)
            self.event_dispatcher.subscribe("security_event", self._handle_security_event)

    def _register_default_handlers(self) -> None:
        """Register built-in alert handlers"""
        self.register_alert_handler("cpu_usage", self._check_cpu_threshold)
        self.register_alert_handler("memory_usage", self._check_memory_threshold)
        self.register_alert_handler("disk_usage", self._check_disk_threshold)
        self.register_alert_handler("load_average", self._check_load_threshold)
        self.register_alert_handler("network_errors", self._check_network_threshold)

    def register_alert_handler(self, metric: str, handler: Callable) -> None:
        """
        Register a new alert handler for a metric
        
        Args:
            metric: The metric to handle
            handler: Function to handle the metric
        """
        self.alert_handlers[metric].append(handler)

    def create_alert(self,
                    alert_type: str,
                    message: str,
                    level: str = "warning",
                    source: str = None,
                    metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new alert
        
        Args:
            alert_type: Type of alert (e.g., cpu_usage, disk_full)
            message: Alert message
            level: Alert level (critical, warning, info)
            source: Source of the alert
            metadata: Additional alert metadata
            
        Returns:
            Dict containing alert details
        """
        if level not in self.config["alert_levels"]:
            level = "warning"

        alert_id = f"{alert_type}_{source if source else 'system'}_{datetime.now().timestamp()}"
        
        alert = {
            "id": alert_id,
            "type": alert_type,
            "message": message,
            "level": level,
            "source": source,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "notification_count": 0
        }

        # Store in active alerts
        self.active_alerts[alert_id] = alert
        
        # Add to history
        self.alert_history.append(alert.copy())
        
        # Send notifications based on level configuration
        if self.notification_manager:
            level_config = self.config["alert_levels"][level]
            self.notification_manager.send_notification(
                message=message,
                level=level,
                title=f"{level.capitalize()} Alert: {alert_type}",
                channels=level_config["channels"],
                metadata=metadata
            )

        # Publish alert event if dispatcher available
        if self.event_dispatcher:
            self.event_dispatcher.publish("alert_created", alert)

        return alert

    def update_alert(self,
                    alert_id: str,
                    updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing alert
        
        Args:
            alert_id: ID of the alert to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated alert dict or None if not found
        """
        if alert_id not in self.active_alerts:
            return None

        alert = self.active_alerts[alert_id]
        
        # Update allowed fields
        allowed_fields = ["message", "level", "metadata", "status"]
        for field in allowed_fields:
            if field in updates:
                alert[field] = updates[field]
        
        alert["updated_at"] = datetime.now().isoformat()
        
        # Update history
        self.alert_history.append(alert.copy())
        
        # Publish update event
        if self.event_dispatcher:
            self.event_dispatcher.publish("alert_updated", alert)

        return alert

    def resolve_alert(self, alert_id: str, resolution: str = None) -> bool:
        """
        Resolve an active alert
        
        Args:
            alert_id: ID of the alert to resolve
            resolution: Optional resolution message
            
        Returns:
            bool indicating success
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert["status"] = "resolved"
        alert["resolved_at"] = datetime.now().isoformat()
        if resolution:
            alert["resolution"] = resolution

        # Update history
        self.alert_history.append(alert.copy())
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        # Publish resolution event
        if self.event_dispatcher:
            self.event_dispatcher.publish("alert_resolved", alert)

        return True

    def _handle_resource_metric(self, metric_data: Dict[str, Any]) -> None:
        """Handle incoming resource metrics"""
        metric_type = metric_data.get("type")
        if metric_type in self.alert_handlers:
            for handler in self.alert_handlers[metric_type]:
                try:
                    handler(metric_data)
                except Exception as e:
                    logger.error(f"Error in alert handler for {metric_type}: {str(e)}")

    def _handle_system_event(self, event_data: Dict[str, Any]) -> None:
        """Handle system events"""
        event_type = event_data.get("type", "unknown")
        if event_type in ["system_error", "service_down"]:
            self.create_alert(
                alert_type=event_type,
                message=event_data.get("message", "System error occurred"),
                level="critical",
                source=event_data.get("source"),
                metadata=event_data
            )

    def _handle_security_event(self, event_data: Dict[str, Any]) -> None:
        """Handle security events"""
        event_type = event_data.get("type", "unknown")
        if event_type in ["unauthorized_access", "suspicious_activity"]:
            self.create_alert(
                alert_type=event_type,
                message=event_data.get("message", "Security event detected"),
                level="critical",
                source=event_data.get("source"),
                metadata=event_data
            )

    def _check_cpu_threshold(self, metric_data: Dict[str, Any]) -> None:
        """Check CPU usage threshold"""
        usage = metric_data.get("value", 0)
        threshold = self.config["thresholds"]["cpu_usage"]
        
        if usage > threshold:
            self.create_alert(
                alert_type="cpu_usage",
                message=f"CPU usage exceeds threshold: {usage}% > {threshold}%",
                level="warning" if usage < threshold + 10 else "critical",
                source=metric_data.get("source"),
                metadata=metric_data
            )

    def _check_memory_threshold(self, metric_data: Dict[str, Any]) -> None:
        """Check memory usage threshold"""
        usage = metric_data.get("value", 0)
        threshold = self.config["thresholds"]["memory_usage"]
        
        if usage > threshold:
            self.create_alert(
                alert_type="memory_usage",
                message=f"Memory usage exceeds threshold: {usage}% > {threshold}%",
                level="warning" if usage < threshold + 10 else "critical",
                source=metric_data.get("source"),
                metadata=metric_data
            )

    def _check_disk_threshold(self, metric_data: Dict[str, Any]) -> None:
        """Check disk usage threshold"""
        usage = metric_data.get("value", 0)
        threshold = self.config["thresholds"]["disk_usage"]
        
        if usage > threshold:
            self.create_alert(
                alert_type="disk_usage",
                message=f"Disk usage exceeds threshold: {usage}% > {threshold}%",
                level="warning" if usage < threshold + 10 else "critical",
                source=metric_data.get("source"),
                metadata=metric_data
            )

    def _check_load_threshold(self, metric_data: Dict[str, Any]) -> None:
        """Check system load threshold"""
        load = metric_data.get("value", 0)
        threshold = self.config["thresholds"]["load_average"]
        
        if load > threshold:
            self.create_alert(
                alert_type="load_average",
                message=f"System load exceeds threshold: {load} > {threshold}",
                level="warning" if load < threshold + 5 else "critical",
                source=metric_data.get("source"),
                metadata=metric_data
            )

    def _check_network_threshold(self, metric_data: Dict[str, Any]) -> None:
        """Check network errors threshold"""
        errors = metric_data.get("value", 0)
        threshold = self.config["thresholds"]["network_errors"]
        
        if errors > threshold:
            self.create_alert(
                alert_type="network_errors",
                message=f"Network errors exceed threshold: {errors} > {threshold}",
                level="warning" if errors < threshold + 50 else "critical",
                source=metric_data.get("source"),
                metadata=metric_data
            )

    def get_active_alerts(self,
                         level: str = None,
                         alert_type: str = None) -> List[Dict[str, Any]]:
        """
        Get active alerts with optional filtering
        
        Args:
            level: Optional alert level to filter by
            alert_type: Optional alert type to filter by
            
        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())
        
        if level:
            alerts = [a for a in alerts if a["level"] == level]
        if alert_type:
            alerts = [a for a in alerts if a["type"] == alert_type]
            
        return sorted(alerts, key=lambda x: x["created_at"], reverse=True)

    def get_alert_history(self,
                         start_time: datetime = None,
                         end_time: datetime = None,
                         level: str = None,
                         alert_type: str = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get alert history with optional filtering
        
        Args:
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            level: Optional alert level to filter by
            alert_type: Optional alert type to filter by
            limit: Maximum number of alerts to return
            
        Returns:
            List of historical alerts
        """
        alerts = self.alert_history
        
        if start_time:
            alerts = [a for a in alerts if datetime.fromisoformat(a["created_at"]) >= start_time]
        if end_time:
            alerts = [a for a in alerts if datetime.fromisoformat(a["created_at"]) <= end_time]
        if level:
            alerts = [a for a in alerts if a["level"] == level]
        if alert_type:
            alerts = [a for a in alerts if a["type"] == alert_type]
            
        return sorted(alerts, key=lambda x: x["created_at"], reverse=True)[:limit]

    def clean_old_alerts(self, days: int = None) -> int:
        """
        Clean up old alerts from history
        
        Args:
            days: Number of days to keep, defaults to config retention_days
            
        Returns:
            Number of alerts removed
        """
        if days is None:
            days = self.config["retention_days"]

        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self.alert_history)
        
        self.alert_history = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert["created_at"]) > cutoff
        ]
        
        return original_count - len(self.alert_history)

    def update_thresholds(self, new_thresholds: Dict[str, Any]) -> None:
        """
        Update alert thresholds
        
        Args:
            new_thresholds: Dictionary of threshold updates
        """
        self.config["thresholds"].update(new_thresholds)
        self._save_config()

    def _save_config(self) -> None:
        """Save alert configuration to file"""
        config_path = os.path.join(os.path.dirname(__file__), 'alert_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving alert config: {str(e)}")