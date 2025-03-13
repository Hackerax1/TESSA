"""
Webhook handler for Proxmox NLI.
Manages webhook registrations and dispatches events to external services.
"""
import logging
import json
import os
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import hmac
import hashlib

logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self, event_dispatcher=None):
        """Initialize the webhook handler"""
        self.event_dispatcher = event_dispatcher
        self.config = self._load_config()
        self.webhook_history: List[Dict[str, Any]] = []
        self.max_retries = 3
        
        # Register for system events if dispatcher provided
        if event_dispatcher:
            self._register_event_handlers()

    def _load_config(self) -> Dict[str, Any]:
        """Load webhook configuration"""
        config_path = os.path.join(os.path.dirname(__file__), 'webhook_config.json')
        default_config = {
            "webhooks": [],
            "max_retries": 3,
            "timeout": 10,
            "enabled": True
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return {**default_config, **json.load(f)}
        except Exception as e:
            logger.error(f"Error loading webhook config: {str(e)}")
        
        return default_config

    def _register_event_handlers(self) -> None:
        """Register for relevant system events"""
        if self.event_dispatcher:
            self.event_dispatcher.subscribe("system_event", self.handle_event)
            self.event_dispatcher.subscribe("vm_event", self.handle_event)
            self.event_dispatcher.subscribe("backup_event", self.handle_event)

    def register_webhook(self, webhook: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new webhook
        
        Args:
            webhook: Dictionary containing webhook configuration
                    Required keys: url, events
                    Optional: secret, headers, enabled
                    
        Returns:
            Dict with registration status
        """
        required_fields = ["url", "events"]
        if not all(field in webhook for field in required_fields):
            raise ValueError("Missing required webhook fields")

        webhook_id = len(self.config["webhooks"]) + 1
        webhook_config = {
            "id": webhook_id,
            "url": webhook["url"],
            "events": webhook["events"],
            "secret": webhook.get("secret", ""),
            "headers": webhook.get("headers", {}),
            "enabled": webhook.get("enabled", True),
            "created_at": datetime.now().isoformat()
        }

        self.config["webhooks"].append(webhook_config)
        self._save_config()

        return {"success": True, "webhook_id": webhook_id}

    def unregister_webhook(self, webhook_id: int) -> Dict[str, bool]:
        """
        Unregister a webhook
        
        Args:
            webhook_id: ID of the webhook to unregister
            
        Returns:
            Dict with unregistration status
        """
        self.config["webhooks"] = [w for w in self.config["webhooks"] if w["id"] != webhook_id]
        self._save_config()
        return {"success": True}

    def handle_event(self, event_data: Dict[str, Any]) -> None:
        """
        Handle an event by dispatching to relevant webhooks
        
        Args:
            event_data: Event data to be sent to webhooks
        """
        if not self.config["enabled"]:
            return

        event_type = event_data.get("type", "unknown")
        
        # Find webhooks subscribed to this event
        relevant_webhooks = [
            w for w in self.config["webhooks"]
            if w["enabled"] and (event_type in w["events"] or "*" in w["events"])
        ]

        # Dispatch event to each webhook
        for webhook in relevant_webhooks:
            asyncio.create_task(self._dispatch_webhook(webhook, event_data))

    async def _dispatch_webhook(self, webhook: Dict[str, Any], event_data: Dict[str, Any]) -> None:
        """
        Dispatch an event to a webhook with retries
        
        Args:
            webhook: Webhook configuration
            event_data: Event data to send
        """
        headers = {**webhook.get("headers", {})}
        
        # Add signature if secret is configured
        if webhook.get("secret"):
            signature = self._generate_signature(event_data, webhook["secret"])
            headers["X-Webhook-Signature"] = signature

        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.post(
                        webhook["url"],
                        json=event_data,
                        headers=headers,
                        timeout=self.config["timeout"]
                    ) as response:
                        success = 200 <= response.status < 300
                        
                        # Log the attempt
                        self._log_webhook_attempt(webhook["id"], event_data, response.status, success)
                        
                        if success:
                            return
                        
                except Exception as e:
                    logger.error(f"Webhook delivery error: {str(e)}")
                    self._log_webhook_attempt(webhook["id"], event_data, 0, False, str(e))
                    
                    if attempt == self.max_retries - 1:
                        break
                    
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

    def _generate_signature(self, data: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        payload = json.dumps(data, sort_keys=True).encode()
        return hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

    def _log_webhook_attempt(self,
                           webhook_id: int,
                           event_data: Dict[str, Any],
                           status_code: int,
                           success: bool,
                           error: str = None) -> None:
        """Log a webhook delivery attempt"""
        attempt = {
            "webhook_id": webhook_id,
            "timestamp": datetime.now().isoformat(),
            "event_data": event_data,
            "status_code": status_code,
            "success": success,
            "error": error
        }
        
        self.webhook_history.append(attempt)
        
        # Keep history size manageable
        if len(self.webhook_history) > 1000:
            self.webhook_history = self.webhook_history[-1000:]

    def get_webhook_history(self,
                          webhook_id: Optional[int] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get webhook delivery history
        
        Args:
            webhook_id: Optional webhook ID to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of webhook delivery attempts
        """
        history = self.webhook_history
        if webhook_id is not None:
            history = [h for h in history if h["webhook_id"] == webhook_id]
        return list(reversed(history))[:limit]

    def _save_config(self) -> None:
        """Save webhook configuration to file"""
        config_path = os.path.join(os.path.dirname(__file__), 'webhook_config.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving webhook config: {str(e)}")