"""
Event dispatcher for Proxmox NLI.
Handles event subscription and publishing using a pub/sub pattern.
"""
import logging
from typing import Dict, List, Callable, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class EventDispatcher:
    def __init__(self):
        """Initialize the event dispatcher"""
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000  # Keep last 1000 events

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: The type of event to subscribe to
            callback: Function to be called when event occurs
        """
        if callback not in self.subscribers[event_type]:
            self.subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        Unsubscribe from an event type
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: Function to be removed from subscribers
        """
        if event_type in self.subscribers:
            self.subscribers[event_type] = [
                cb for cb in self.subscribers[event_type] if cb != callback
            ]
            logger.debug(f"Unsubscribed from event: {event_type}")

    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event_type: The type of event being published
            data: Event data to be passed to subscribers
        """
        if event_type in self.subscribers:
            # Store in history
            self.event_history.append({"type": event_type, "data": data})
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)

            # Notify subscribers
            for callback in self.subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event subscriber for {event_type}: {str(e)}")

    def get_event_history(self, event_type: str = None) -> List[Dict[str, Any]]:
        """
        Get historical events, optionally filtered by type
        
        Args:
            event_type: Optional event type to filter by
            
        Returns:
            List of historical events
        """
        if event_type:
            return [event for event in self.event_history if event["type"] == event_type]
        return self.event_history.copy()

    def clear_history(self) -> None:
        """Clear the event history"""
        self.event_history.clear()