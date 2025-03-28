"""
Context bridge module for connecting NLU context management with the memory system.

This module provides a bridge between the NLU context management system and 
the memory/topic management systems, enabling seamless integration of conversation
context across different components.
"""
import logging
from typing import Dict, Any, Optional, List

from proxmox_nli.nlu.context_management import ContextManager
from proxmox_nli.core.memory_manager import MemoryManager
from proxmox_nli.core.topic_manager import TopicManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextBridge:
    """
    Bridge class for connecting NLU context management with memory and topic systems.
    """
    
    def __init__(self, nlu_context_manager: ContextManager, 
                memory_manager: MemoryManager, 
                topic_manager: TopicManager):
        """
        Initialize the context bridge.
        
        Args:
            nlu_context_manager: The NLU context manager
            memory_manager: The memory manager
            topic_manager: The topic manager
        """
        self.nlu_context = nlu_context_manager
        self.memory_manager = memory_manager
        self.topic_manager = topic_manager
        
        # Connect the NLU context manager with the topic manager
        self.nlu_context.set_topic_manager(self.topic_manager)
        
    def sync_context(self, user_id: str) -> None:
        """
        Synchronize context between all systems.
        
        Args:
            user_id: The user's ID
        """
        # Get current topic from topic manager
        current_topic = self.topic_manager.current_topic
        previous_topic = self.topic_manager.previous_topic
        
        if current_topic:
            # Update NLU context with current topic
            self.nlu_context.context['current_topic'] = current_topic
            self.nlu_context.context['previous_topic'] = previous_topic
            
            # Update topic history in NLU context
            self.nlu_context.context['topic_history'] = self.topic_manager.topic_history
            
            # Get memories related to the current topic
            memories = self.memory_manager.get_memories_by_topic(user_id, current_topic)
            
            # Add memories to cross-session memory in NLU context
            if memories and current_topic not in self.nlu_context.context['cross_session_memory']:
                self.nlu_context.context['cross_session_memory'][current_topic] = []
                
            for memory in memories:
                if 'entities' in memory and memory['entities']:
                    # Add memory entities to cross-session memory
                    self.nlu_context.context['cross_session_memory'][current_topic].append({
                        'entities': memory['entities'],
                        'timestamp': memory.get('created_at', '')
                    })
    
    def enhance_response(self, response: str, query: str, intent: str, 
                        entities: Dict[str, Any], user_id: str) -> str:
        """
        Enhance a response with context and memory.
        
        Args:
            response: The original response
            query: The user's query
            intent: The detected intent
            entities: The detected entities
            user_id: The user's ID
            
        Returns:
            Enhanced response
        """
        # First try to enhance with memory manager
        enhanced_response = self.memory_manager.enhance_response_with_memory(
            response,
            current_topic=self.topic_manager.current_topic,
            previous_topic=self.topic_manager.previous_topic,
            user_id=user_id
        )
        
        # If memory manager didn't enhance the response, try the topic manager
        if enhanced_response == response:
            enhanced_response = self.topic_manager.enhance_response_with_memory(response)
        
        return enhanced_response
    
    def extract_and_store_context(self, query: str, intent: str, 
                                entities: Dict[str, Any], response: str, 
                                user_id: str) -> None:
        """
        Extract context from a conversation and store it in the memory system.
        
        Args:
            query: The user's query
            intent: The detected intent
            entities: The detected entities
            response: The system response
            user_id: The user's ID
        """
        # Skip for basic intents
        if intent in ["unknown", "error", "help"]:
            return
            
        # Get current topic
        current_topic = self.topic_manager.current_topic or intent.replace('_', ' ')
        
        # Store memory
        self.memory_manager.add_memory(
            user_id=user_id,
            topic=current_topic,
            content=response,
            entities=entities,
            importance=0.8  # Default importance
        )
        
        # Create topic associations if topic has changed
        if (self.topic_manager.previous_topic and 
            self.topic_manager.previous_topic != current_topic):
            self.memory_manager.add_topic_association(
                self.topic_manager.previous_topic,
                current_topic,
                strength=0.8,
                relationship_type='continuation'
            )
    
    def get_context_for_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """
        Get relevant context for a query.
        
        Args:
            query: The user's query
            user_id: The user's ID
            
        Returns:
            Dictionary of context information
        """
        context = {}
        
        # Get current topic
        if self.topic_manager.current_topic:
            context['current_topic'] = self.topic_manager.current_topic
            
            # Get memories related to the current topic
            memories = self.memory_manager.get_memories_by_topic(
                user_id, self.topic_manager.current_topic, limit=2
            )
            
            if memories:
                context['related_memories'] = [memory.get('content', '') for memory in memories]
        
        # Get active context from NLU context manager
        nlu_active_context = self.nlu_context.get_active_context()
        for key, value in nlu_active_context.items():
            if key not in context and key not in ['last_query_time', 'session_start_time']:
                context[key] = value
        
        return context
