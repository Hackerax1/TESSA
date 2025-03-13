"""
Notification manager for Proxmox NLI.
Handles sending notifications through various channels (email, websocket, desktop notifications).
"""
import logging
import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, event_dispatcher=None):
        """Initialize the notification manager"""
        self.event_dispatcher = event_dispatcher
        self.config = self._load_config()
        self.notification_history: List[Dict[str, Any]] = []
        
        # Register for system events if dispatcher provided
        if event_dispatcher:
            self._register_event_handlers()

    def _load_config(self) -> Dict[str, Any]:
        """Load notification configuration"""
        config_path = os.path.join(os.path.dirname(__file__), 'notification_config.json')
        default_config = {
            "email": {
                "enabled": False,
                "smtp_host": "",
                "smtp_port": 587,
                "smtp_user": "",
                "smtp_password": "",
                "from_address": "",
                "recipients": []
            },
            "websocket": {
                "enabled": True
            },
            "desktop": {
                "enabled": True
            },
            "notification_levels": ["critical", "warning", "info"]
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return {**default_config, **json.load(f)}
        except Exception as e:
            logger.error(f"Error loading notification config: {str(e)}")
        
        return default_config

    def _register_event_handlers(self) -> None:
        """Register for relevant system events"""
        if self.event_dispatcher:
            self.event_dispatcher.subscribe("system_alert", self.send_notification)
            self.event_dispatcher.subscribe("security_event", self.send_notification)
            self.event_dispatcher.subscribe("resource_warning", self.send_notification)

    def send_notification(self, 
                         message: str,
                         level: str = "info",
                         title: str = None,
                         channels: List[str] = None,
                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a notification through configured channels
        
        Args:
            message: The notification message
            level: Notification level (critical, warning, info)
            title: Optional notification title
            channels: List of channels to use (email, websocket, desktop)
            metadata: Additional notification metadata
            
        Returns:
            Dict with notification status
        """
        if level not in self.config["notification_levels"]:
            level = "info"

        if not channels:
            channels = ["websocket"]  # Default to websocket notifications

        notification = {
            "id": len(self.notification_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "title": title or f"{level.capitalize()} Notification",
            "message": message,
            "level": level,
            "metadata": metadata or {}
        }

        results = {"success": True, "channels": {}}

        # Send through each requested channel
        for channel in channels:
            try:
                if channel == "email" and self.config["email"]["enabled"]:
                    self._send_email_notification(notification)
                    results["channels"]["email"] = "success"
                elif channel == "websocket" and self.config["websocket"]["enabled"]:
                    self._send_websocket_notification(notification)
                    results["channels"]["websocket"] = "success"
                elif channel == "desktop" and self.config["desktop"]["enabled"]:
                    self._send_desktop_notification(notification)
                    results["channels"]["desktop"] = "success"
            except Exception as e:
                logger.error(f"Error sending {channel} notification: {str(e)}")
                results["channels"][channel] = str(e)
                results["success"] = False

        # Store in history
        self.notification_history.append(notification)
        
        return results

    def _send_email_notification(self, notification: Dict[str, Any]) -> None:
        """Send email notification"""
        if not self.config["email"]["smtp_host"]:
            raise ValueError("Email configuration incomplete")

        msg = MIMEMultipart()
        msg["From"] = self.config["email"]["from_address"]
        msg["To"] = ", ".join(self.config["email"]["recipients"])
        msg["Subject"] = notification["title"]

        body = f"""
        Level: {notification['level']}
        Time: {notification['timestamp']}
        
        {notification['message']}
        
        Additional Information:
        {json.dumps(notification['metadata'], indent=2)}
        """

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(self.config["email"]["smtp_host"], 
                         self.config["email"]["smtp_port"]) as server:
            server.starttls()
            if self.config["email"]["smtp_user"]:
                server.login(
                    self.config["email"]["smtp_user"],
                    self.config["email"]["smtp_password"]
                )
            server.send_message(msg)

    def _send_websocket_notification(self, notification: Dict[str, Any]) -> None:
        """Send websocket notification"""
        if self.event_dispatcher:
            self.event_dispatcher.publish("notification", notification)

    def _send_desktop_notification(self, notification: Dict[str, Any]) -> None:
        """Send desktop notification"""
        try:
            import platform
            system = platform.system()

            if system == "Linux":
                os.system(f'notify-send "{notification["title"]}" "{notification["message"]}"')
            elif system == "Darwin":  # macOS
                os.system(f'osascript -e \'display notification "{notification["message"]}" with title "{notification["title"]}"\'')
            elif system == "Windows":
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    notification["title"],
                    notification["message"],
                    duration=5,
                    threaded=True
                )
        except ImportError:
            logger.warning("Desktop notifications not available - missing required packages")

    def get_notification_history(self, 
                               level: str = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get notification history, optionally filtered by level
        
        Args:
            level: Optional notification level to filter by
            limit: Maximum number of notifications to return
            
        Returns:
            List of historical notifications
        """
        history = self.notification_history
        if level:
            history = [n for n in history if n["level"] == level]
        return list(reversed(history))[:limit]

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update notification configuration
        
        Args:
            new_config: New configuration to merge with existing
        """
        self.config = {**self.config, **new_config}
        config_path = os.path.join(os.path.dirname(__file__), 'notification_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving notification config: {str(e)}")