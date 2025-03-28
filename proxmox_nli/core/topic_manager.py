"""
Topic manager for tracking conversation topics and generating natural transitions.

This module enhances the conversational capabilities of TESSA by tracking topics
across sessions and providing natural topic transitions.
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple

from proxmox_nli.core.conversation_persistence import ConversationPersistence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TopicManager:
    """
    Class for managing conversation topics and generating natural transitions.
    """
    
    def __init__(self, conversation_persistence: ConversationPersistence):
        """
        Initialize the topic manager.
        
        Args:
            conversation_persistence: Instance of ConversationPersistence
        """
        self.conversation_persistence = conversation_persistence
        self.current_conversation_id = None
        self.current_user_id = None
        self.current_session_id = None
        self.current_topic = None
        self.previous_topic = None
        self.topic_history = []  # List of recently discussed topics
        self.max_topic_history = 10
        
    def start_session(self, user_id: str, session_id: str) -> int:
        """
        Start a new conversation session.
        
        Args:
            user_id: The user's ID
            session_id: The session ID
            
        Returns:
            The conversation ID
        """
        self.current_user_id = user_id
        self.current_session_id = session_id
        
        # Check if there's an active conversation for this session
        active_conversation = self.conversation_persistence.get_active_conversation(user_id, session_id)
        
        if active_conversation:
            self.current_conversation_id = active_conversation['id']
            # Extract topics from the active conversation
            if active_conversation.get('topics'):
                topics = list(active_conversation['topics'].keys())
                if topics:
                    self.current_topic = topics[0]
                    self.topic_history = topics[:self.max_topic_history]
        else:
            # Start a new conversation
            self.current_conversation_id = self.conversation_persistence.start_conversation(user_id, session_id)
            
        return self.current_conversation_id
    
    def process_user_message(self, message: str, intent: Optional[str] = None, 
                           entities: Optional[Dict[str, Any]] = None) -> int:
        """
        Process a user message and track topics.
        
        Args:
            message: The user's message
            intent: The detected intent
            entities: The detected entities
            
        Returns:
            The message ID
        """
        if not self.current_conversation_id:
            logger.warning("No active conversation when processing message")
            return -1
            
        # Add the message to the conversation
        message_id = self.conversation_persistence.add_message(
            self.current_conversation_id, 'user', message, intent, entities
        )
        
        # Update current topic if needed
        new_topic = self._detect_topic_from_message(message, intent, entities)
        if new_topic and new_topic != self.current_topic:
            self.previous_topic = self.current_topic
            self.current_topic = new_topic
            
            # Update topic in the database
            self.conversation_persistence.update_conversation_topic(
                self.current_conversation_id, self.current_topic
            )
            
            # Update topic history
            if self.current_topic in self.topic_history:
                self.topic_history.remove(self.current_topic)
            self.topic_history.insert(0, self.current_topic)
            
            # Trim to max size
            if len(self.topic_history) > self.max_topic_history:
                self.topic_history = self.topic_history[:self.max_topic_history]
        
        return message_id
    
    def process_system_response(self, message: str) -> int:
        """
        Process a system response.
        
        Args:
            message: The system's response message
            
        Returns:
            The message ID
        """
        if not self.current_conversation_id:
            logger.warning("No active conversation when processing system response")
            return -1
            
        # Add the message to the conversation
        return self.conversation_persistence.add_message(
            self.current_conversation_id, 'system', message
        )
    
    def get_topic_transition(self) -> Optional[str]:
        """
        Get a natural transition phrase between the previous and current topic.
        
        Returns:
            A transition phrase or None if no transition is needed
        """
        if not self.previous_topic or not self.current_topic or self.previous_topic == self.current_topic:
            return None
            
        return self.conversation_persistence.get_conversation_transition(
            self.current_user_id, self.previous_topic, self.current_topic
        )
    
    def get_related_past_discussions(self) -> List[Dict[str, Any]]:
        """
        Get related past discussions based on the current topic.
        
        Returns:
            List of relevant past conversations
        """
        if not self.current_topic or not self.current_user_id:
            return []
            
        return self.conversation_persistence.get_relevant_past_conversations(
            self.current_user_id, self.current_topic
        )
    
    def get_topic_summary(self, topic: Optional[str] = None) -> Optional[str]:
        """
        Get a summary of past discussions about a specific topic.
        
        Args:
            topic: The topic to summarize (defaults to current topic)
            
        Returns:
            A summary or None if no discussions found
        """
        if not topic:
            topic = self.current_topic
            
        if not topic or not self.current_user_id:
            return None
            
        conversations = self.conversation_persistence.find_conversations_by_topic(
            self.current_user_id, topic
        )
        
        if not conversations:
            return None
            
        # Get the most recent conversation about this topic
        conversation = self.conversation_persistence.get_conversation(conversations[0]['id'])
        
        if not conversation or not conversation.get('messages'):
            return None
            
        # Extract system messages as a summary
        system_messages = [
            msg['content'] for msg in conversation['messages'] 
            if msg['message_type'] == 'system'
        ]
        
        if not system_messages:
            return None
            
        # Return the most recent system message as a summary
        return f"Last time we discussed {topic}, I mentioned: '{system_messages[-1]}'"
    
    def enhance_response_with_memory(self, response: str) -> str:
        """
        Enhance a system response with conversation memory.
        
        Args:
            response: The original system response
            
        Returns:
            Enhanced response with memory/context if appropriate
        """
        # Check if there's an opportunity to add a transition or memory reference
        if not self.current_topic or len(response) > 500:  # Skip for long responses
            return response
            
        # Check for related past discussions
        related_discussions = self.get_related_past_discussions()
        if not related_discussions:
            return response
            
        # Get a transition if topic has changed
        transition = self.get_topic_transition()
        
        # If we have a transition and it makes sense, add it
        if transition and self.previous_topic != self.current_topic:
            # Add transition at the beginning of the response
            enhanced_response = f"{transition} {response}"
            return enhanced_response
            
        # Otherwise, check if we can add a reference to past discussion
        topic_summary = self.get_topic_summary()
        if topic_summary:
            # Add memory reference at the end of the response
            enhanced_response = f"{response}\n\n{topic_summary}"
            return enhanced_response
            
        return response
    
    def _detect_topic_from_message(self, message: str, intent: Optional[str] = None, 
                                 entities: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Detect the main topic from a user message.
        
        Args:
            message: The user's message
            intent: The detected intent
            entities: The detected entities
            
        Returns:
            The detected topic or None
        """
        # Best topic sources in order of priority:
        # 1. Intent (most reliable)
        # 2. Important entities (vm_name, service_name, etc.)
        # 3. Keywords from the message
        
        # Check if we have an intent
        if intent:
            # Clean up the intent name to be more readable
            return intent.replace('_', ' ')
            
        # Check for important entities
        if entities:
            priority_entities = ['vm_name', 'service_name', 'node', 'container_name']
            for entity_type in priority_entities:
                if entity_type in entities and entities[entity_type]:
                    return f"{entity_type.replace('_', ' ')} {entities[entity_type]}"
        
        # Fall back to keyword extraction
        keywords = self._extract_keywords(message)
        if keywords:
            return keywords[0]  # Use the highest-scored keyword as the topic
            
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract potential keywords from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of keywords in order of importance
        """
        # Simple keyword extraction based on common patterns in proxmox/homelab context
        # In a real implementation, you might want to use NLP techniques
        
        # Look for common patterns
        patterns = [
            r'(?:virtual machines?|vms?)\s+(\w+[-\w]*)',  # VM names
            r'(?:services?|apps?|applications?)\s+(\w+[-\w]*)',  # Service names
            r'(?:nodes?|servers?|hosts?)\s+(\w+[-\w]*)',  # Node names
            r'(?:containers?|lxc)\s+(\w+[-\w]*)',  # Container names
            r'(?:backups?|restores?)\s+(\w+[-\w]*)',  # Backup operations
            r'(?:updates?|upgrades?)\s+(\w+[-\w]*)',  # Update operations
            r'(?:storages?|disks?|volumes?)\s+(\w+[-\w]*)'  # Storage operations
        ]
        
        keywords = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            keywords.extend(matches)
            
        # Add other important words as fallback
        important_words = [
            "backup", "restore", "update", "upgrade", "start", "stop",
            "create", "delete", "monitor", "performance", "network",
            "security", "storage", "cluster", "configuration", "setup"
        ]
        
        for word in important_words:
            if word in text.lower():
                keywords.append(word)
                
        return list(dict.fromkeys(keywords))  # Remove duplicates while preserving order