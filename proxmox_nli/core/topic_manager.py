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
        
        # Enhanced topic detection
        self.proxmox_topic_keywords = {
            'virtual machine': ['vm', 'virtual machine', 'guest', 'instance'],
            'container': ['container', 'lxc', 'ct', 'docker'],
            'storage': ['storage', 'disk', 'volume', 'datastore', 'zfs', 'ceph'],
            'network': ['network', 'vlan', 'bridge', 'interface', 'ip', 'firewall'],
            'backup': ['backup', 'restore', 'snapshot', 'archive'],
            'cluster': ['cluster', 'node', 'quorum', 'ha', 'high availability'],
            'performance': ['performance', 'cpu', 'memory', 'ram', 'usage', 'load'],
            'security': ['security', 'permission', 'acl', 'user', 'role', 'authentication'],
            'update': ['update', 'upgrade', 'patch', 'version'],
            'configuration': ['config', 'configuration', 'setting', 'option', 'parameter']
        }
        
        # Transition templates for different scenarios
        self.transition_templates = {
            'continuation': [
                "Continuing with {topic}...",
                "Let's continue discussing {topic}.",
                "Getting back to {topic}..."
            ],
            'new_topic': [
                "Moving on to {topic}...",
                "Let's talk about {topic} now.",
                "Switching to {topic}..."
            ],
            'related_topic': [
                "Speaking of {topic}, which relates to our previous discussion...",
                "{topic} is connected to what we were just discussing.",
                "This brings us to {topic}, which is related."
            ],
            'return_to_topic': [
                "Coming back to {topic} that we discussed earlier...",
                "Returning to our previous conversation about {topic}...",
                "Let's revisit {topic} from our earlier discussion."
            ]
        }
        
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
        
        # First try to get a transition from the conversation persistence
        transition = self.conversation_persistence.get_conversation_transition(
            self.current_user_id, self.previous_topic, self.current_topic
        )
        
        if transition:
            return transition
            
        # If no transition found, generate one based on the relationship
        import random
        
        # Determine relationship type
        relationship_type = self._determine_topic_relationship(self.previous_topic, self.current_topic)
        
        # Get appropriate templates
        templates = self.transition_templates.get(relationship_type, self.transition_templates['new_topic'])
        
        # Generate transition
        return random.choice(templates).format(topic=self.current_topic)
    
    def _determine_topic_relationship(self, topic1: str, topic2: str) -> str:
        """
        Determine the relationship between two topics.
        
        Args:
            topic1: First topic
            topic2: Second topic
            
        Returns:
            Relationship type (continuation, new_topic, related_topic, return_to_topic)
        """
        # Check if topics are in the same category
        topic1_category = self._get_topic_category(topic1)
        topic2_category = self._get_topic_category(topic2)
        
        if topic1_category == topic2_category:
            return 'continuation'
            
        # Check if topic2 is in topic history (but not the immediate previous topic)
        if topic2 in self.topic_history[1:]:
            return 'return_to_topic'
            
        # Check if topics are related based on keyword similarity
        if self._are_topics_related(topic1, topic2):
            return 'related_topic'
            
        # Default to new topic
        return 'new_topic'
    
    def _get_topic_category(self, topic: str) -> Optional[str]:
        """
        Get the category of a topic based on keywords.
        
        Args:
            topic: The topic to categorize
            
        Returns:
            Category name or None
        """
        topic_lower = topic.lower()
        
        for category, keywords in self.proxmox_topic_keywords.items():
            for keyword in keywords:
                if keyword in topic_lower:
                    return category
                    
        return None
    
    def _are_topics_related(self, topic1: str, topic2: str) -> bool:
        """
        Check if two topics are related based on keyword similarity.
        
        Args:
            topic1: First topic
            topic2: Second topic
            
        Returns:
            True if related, False otherwise
        """
        # Simple implementation - check if they share words
        words1 = set(re.findall(r'\b\w+\b', topic1.lower()))
        words2 = set(re.findall(r'\b\w+\b', topic2.lower()))
        
        # If they share any significant words, consider them related
        common_words = words1.intersection(words2)
        return len(common_words) > 0
    
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
        if topic_summary and not topic_summary in response:
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
        
        # Enhanced keyword extraction
        keywords = self._extract_keywords(message)
        if keywords:
            # Try to categorize keywords into Proxmox topics
            for keyword in keywords:
                category = self._get_topic_category(keyword)
                if category:
                    return f"{category}: {keyword}"
            
            # If no categorization, use the highest-scored keyword
            return keywords[0]
            
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract potential keywords from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of keywords in order of importance
        """
        # Enhanced keyword extraction based on common patterns in proxmox/homelab context
        
        # Look for common patterns
        patterns = [
            r'(?:virtual machines?|vms?)\s+(\w+[-\w]*)',  # VM names
            r'(?:services?|apps?|applications?)\s+(\w+[-\w]*)',  # Service names
            r'(?:nodes?|servers?|hosts?)\s+(\w+[-\w]*)',  # Node names
            r'(?:containers?|lxc)\s+(\w+[-\w]*)',  # Container names
            r'(?:backups?|restores?)\s+(\w+[-\w]*)',  # Backup operations
            r'(?:updates?|upgrades?)\s+(\w+[-\w]*)',  # Update operations
            r'(?:storages?|disks?|volumes?)\s+(\w+[-\w]*)',  # Storage operations
            r'(?:networks?|interfaces?|bridges?)\s+(\w+[-\w]*)',  # Network operations
            r'(?:clusters?|quorums?|ha)\s+(\w+[-\w]*)',  # Cluster operations
            r'(?:users?|permissions?|roles?)\s+(\w+[-\w]*)'  # User/permission operations
        ]
        
        keywords = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            keywords.extend(matches)
            
        # Add other important words as fallback
        important_words = [
            "backup", "restore", "update", "upgrade", "start", "stop",
            "create", "delete", "monitor", "performance", "network",
            "security", "storage", "cluster", "configuration", "setup",
            "migrate", "clone", "snapshot", "template", "iso", "console",
            "firewall", "bandwidth", "memory", "cpu", "disk", "power",
            "status", "log", "error", "warning", "success", "failure"
        ]
        
        # Score keywords based on proximity to important words
        scored_keywords = []
        text_lower = text.lower()
        
        for word in important_words:
            if word in text_lower:
                # Find the context around the important word
                context_pattern = r'(\w+\s+){0,3}' + word + r'(\s+\w+){0,3}'
                contexts = re.findall(context_pattern, text_lower)
                
                if contexts:
                    # Extract words from contexts
                    for context in contexts:
                        context_words = re.findall(r'\b\w+\b', ' '.join(context))
                        for context_word in context_words:
                            if len(context_word) > 3 and context_word != word:  # Skip short words and the important word itself
                                scored_keywords.append((context_word, 0.8))  # Words near important words get high score
                
                # Add the important word itself
                scored_keywords.append((word, 1.0))
        
        # Add any remaining words from the text
        other_words = [w for w in re.findall(r'\b\w{4,}\b', text_lower) if w not in [kw[0] for kw in scored_keywords]]
        scored_keywords.extend([(w, 0.5) for w in other_words])  # Other words get lower score
        
        # Sort by score
        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the keywords
        return [kw[0] for kw in scored_keywords]