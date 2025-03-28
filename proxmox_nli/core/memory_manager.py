"""
Memory manager for long-term conversation memory and natural transitions.

This module enhances TESSA's ability to remember past conversations and generate
natural transitions between topics across different sessions.
"""
import json
import logging
import os
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple

from proxmox_nli.core.conversation_persistence import ConversationPersistence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Class for managing long-term memory of conversations and generating natural transitions.
    """
    
    def __init__(self, conversation_persistence: ConversationPersistence, db_path: str = None):
        """
        Initialize the memory manager.
        
        Args:
            conversation_persistence: Instance of ConversationPersistence
            db_path: Path to the SQLite database file
        """
        self.conversation_persistence = conversation_persistence
        
        if not db_path:
            # Use default path in the data directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "memory.db")
        
        self.db_path = db_path
        self._initialize_database()
        
        # Memory settings
        self.max_memories_per_topic = 10
        self.max_topic_associations = 20
        self.memory_decay_days = 90  # Memories older than this will have reduced relevance
        
        # Transition phrases for different relationship types
        self.transition_phrases = {
            'continuation': [
                "Continuing our previous conversation about {topic}...",
                "Picking up where we left off with {topic}...",
                "Getting back to our discussion about {topic}...",
                "To continue what we were discussing about {topic}..."
            ],
            'related': [
                "Speaking of {topic}, I remember we talked about {related_topic} before.",
                "This reminds me of our conversation about {related_topic}.",
                "{topic} is related to {related_topic}, which we discussed earlier.",
                "This is similar to the {related_topic} topic we covered previously."
            ],
            'contrast': [
                "Unlike {related_topic} that we discussed before, {topic} works differently.",
                "While {topic} is different from {related_topic} we talked about earlier...",
                "In contrast to our previous discussion about {related_topic}, {topic} has different characteristics.",
                "Compared to {related_topic}, {topic} has some key differences."
            ],
            'time_based': [
                "Last time we talked about {topic}, you were interested in {detail}.",
                "When we discussed {topic} {time_ago}, we covered {detail}.",
                "You previously asked about {topic}, specifically about {detail}.",
                "In our {time_ago} conversation about {topic}, we focused on {detail}."
            ]
        }
        
    def _initialize_database(self):
        """Initialize the database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create memories table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        content TEXT NOT NULL,
                        entities TEXT,
                        importance FLOAT NOT NULL DEFAULT 1.0,
                        created_at TIMESTAMP NOT NULL,
                        last_accessed TIMESTAMP NOT NULL,
                        access_count INTEGER NOT NULL DEFAULT 1
                    )
                ''')
                
                # Create topic associations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS topic_associations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic_a TEXT NOT NULL,
                        topic_b TEXT NOT NULL,
                        strength FLOAT NOT NULL DEFAULT 1.0,
                        relationship_type TEXT,
                        created_at TIMESTAMP NOT NULL,
                        last_accessed TIMESTAMP NOT NULL,
                        UNIQUE(topic_a, topic_b)
                    )
                ''')
                
                # Create topic transitions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS topic_transitions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        from_topic TEXT NOT NULL,
                        to_topic TEXT NOT NULL,
                        transition_text TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        last_used TIMESTAMP,
                        use_count INTEGER NOT NULL DEFAULT 0
                    )
                ''')
                
                conn.commit()
                logger.info("Memory database initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize memory database: {e}")
    
    def add_memory(self, user_id: str, topic: str, content: str, 
                  entities: Optional[Dict[str, Any]] = None, 
                  importance: float = 1.0) -> int:
        """
        Add a new memory to the database.
        
        Args:
            user_id: The user's ID
            topic: The main topic of the memory
            content: The content of the memory
            entities: Dictionary of entities related to the memory
            importance: Importance score (0-1)
            
        Returns:
            The memory ID
        """
        now = datetime.now().isoformat()
        entities_json = json.dumps(entities) if entities else None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if we already have a similar memory
                cursor.execute('''
                    SELECT id, access_count FROM memories 
                    WHERE user_id = ? AND topic = ? AND content = ?
                ''', (user_id, topic, content))
                
                existing = cursor.fetchone()
                if existing:
                    # Update existing memory
                    memory_id, access_count = existing
                    cursor.execute('''
                        UPDATE memories SET 
                        entities = ?,
                        importance = ?,
                        last_accessed = ?,
                        access_count = ?
                        WHERE id = ?
                    ''', (entities_json, importance, now, access_count + 1, memory_id))
                    conn.commit()
                    return memory_id
                
                # Insert new memory
                cursor.execute('''
                    INSERT INTO memories 
                    (user_id, topic, content, entities, importance, created_at, last_accessed) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, topic, content, entities_json, importance, now, now))
                
                conn.commit()
                memory_id = cursor.lastrowid
                
                # Prune old memories if we have too many for this topic
                self._prune_old_memories(user_id, topic)
                
                return memory_id
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            return -1
    
    def _prune_old_memories(self, user_id: str, topic: str):
        """
        Remove old memories if we have too many for a topic.
        
        Args:
            user_id: The user's ID
            topic: The topic to prune
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count memories for this topic
                cursor.execute('''
                    SELECT COUNT(*) FROM memories 
                    WHERE user_id = ? AND topic = ?
                ''', (user_id, topic))
                
                count = cursor.fetchone()[0]
                
                # If we have too many, remove the oldest and least accessed ones
                if count > self.max_memories_per_topic:
                    # Calculate how many to remove
                    to_remove = count - self.max_memories_per_topic
                    
                    # Get IDs of memories to remove (oldest and least accessed first)
                    cursor.execute('''
                        SELECT id FROM memories 
                        WHERE user_id = ? AND topic = ?
                        ORDER BY importance ASC, access_count ASC, last_accessed ASC
                        LIMIT ?
                    ''', (user_id, topic, to_remove))
                    
                    memory_ids = [row[0] for row in cursor.fetchall()]
                    
                    # Remove memories
                    for memory_id in memory_ids:
                        cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
                    
                    conn.commit()
                    logger.info(f"Pruned {len(memory_ids)} old memories for topic '{topic}'")
        except Exception as e:
            logger.error(f"Failed to prune old memories: {e}")
    
    def add_topic_association(self, topic_a: str, topic_b: str, 
                             strength: float = 1.0, 
                             relationship_type: Optional[str] = None) -> bool:
        """
        Add or update an association between two topics.
        
        Args:
            topic_a: First topic
            topic_b: Second topic
            strength: Association strength (0-1)
            relationship_type: Type of relationship (continuation, related, contrast, etc.)
            
        Returns:
            Success status
        """
        now = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if association already exists
                cursor.execute('''
                    SELECT id, strength FROM topic_associations 
                    WHERE (topic_a = ? AND topic_b = ?) OR (topic_a = ? AND topic_b = ?)
                ''', (topic_a, topic_b, topic_b, topic_a))
                
                existing = cursor.fetchone()
                if existing:
                    # Update existing association
                    association_id, current_strength = existing
                    # Blend old and new strength (70% old, 30% new)
                    new_strength = (current_strength * 0.7) + (strength * 0.3)
                    cursor.execute('''
                        UPDATE topic_associations SET 
                        strength = ?,
                        relationship_type = ?,
                        last_accessed = ?
                        WHERE id = ?
                    ''', (new_strength, relationship_type, now, association_id))
                else:
                    # Insert new association
                    cursor.execute('''
                        INSERT INTO topic_associations 
                        (topic_a, topic_b, strength, relationship_type, created_at, last_accessed) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (topic_a, topic_b, strength, relationship_type, now, now))
                
                conn.commit()
                
                # Prune old associations if we have too many
                self._prune_old_associations()
                
                return True
        except Exception as e:
            logger.error(f"Failed to add topic association: {e}")
            return False
    
    def _prune_old_associations(self):
        """Remove old associations if we have too many."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count total associations
                cursor.execute('SELECT COUNT(*) FROM topic_associations')
                count = cursor.fetchone()[0]
                
                # If we have too many, remove the weakest and oldest ones
                if count > self.max_topic_associations:
                    # Calculate how many to remove
                    to_remove = count - self.max_topic_associations
                    
                    # Get IDs of associations to remove
                    cursor.execute('''
                        SELECT id FROM topic_associations 
                        ORDER BY strength ASC, last_accessed ASC
                        LIMIT ?
                    ''', (to_remove,))
                    
                    association_ids = [row[0] for row in cursor.fetchall()]
                    
                    # Remove associations
                    for association_id in association_ids:
                        cursor.execute('DELETE FROM topic_associations WHERE id = ?', (association_id,))
                    
                    conn.commit()
                    logger.info(f"Pruned {len(association_ids)} old topic associations")
        except Exception as e:
            logger.error(f"Failed to prune old associations: {e}")
    
    def add_topic_transition(self, from_topic: str, to_topic: str, transition_text: str) -> bool:
        """
        Add a natural transition between topics.
        
        Args:
            from_topic: Source topic
            to_topic: Target topic
            transition_text: The transition phrase
            
        Returns:
            Success status
        """
        now = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert new transition
                cursor.execute('''
                    INSERT INTO topic_transitions 
                    (from_topic, to_topic, transition_text, created_at) 
                    VALUES (?, ?, ?, ?)
                ''', (from_topic, to_topic, transition_text, now))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to add topic transition: {e}")
            return False
    
    def get_memories_by_topic(self, user_id: str, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get memories related to a specific topic.
        
        Args:
            user_id: The user's ID
            topic: The topic to search for
            limit: Maximum number of memories to return
            
        Returns:
            List of memories
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get memories for this topic
                cursor.execute('''
                    SELECT * FROM memories 
                    WHERE user_id = ? AND topic = ?
                    ORDER BY importance DESC, access_count DESC, last_accessed DESC
                    LIMIT ?
                ''', (user_id, topic, limit))
                
                memories = []
                now = datetime.now()
                
                for row in cursor.fetchall():
                    memory = dict(row)
                    
                    # Parse entities JSON
                    if memory.get('entities'):
                        try:
                            memory['entities'] = json.loads(memory['entities'])
                        except json.JSONDecodeError:
                            memory['entities'] = {}
                    
                    # Update access count and last accessed
                    cursor.execute('''
                        UPDATE memories SET 
                        access_count = access_count + 1,
                        last_accessed = ?
                        WHERE id = ?
                    ''', (now.isoformat(), memory['id']))
                    
                    memories.append(memory)
                
                conn.commit()
                return memories
        except Exception as e:
            logger.error(f"Failed to get memories by topic: {e}")
            return []
    
    def get_related_topics(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get topics related to the given topic.
        
        Args:
            topic: The topic to find related topics for
            limit: Maximum number of related topics to return
            
        Returns:
            List of related topics with relationship information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get related topics
                cursor.execute('''
                    SELECT * FROM topic_associations 
                    WHERE topic_a = ? OR topic_b = ?
                    ORDER BY strength DESC, last_accessed DESC
                    LIMIT ?
                ''', (topic, topic, limit))
                
                related_topics = []
                now = datetime.now().isoformat()
                
                for row in cursor.fetchall():
                    association = dict(row)
                    
                    # Determine the related topic
                    related_topic = association['topic_b'] if association['topic_a'] == topic else association['topic_a']
                    
                    related_topics.append({
                        'topic': related_topic,
                        'strength': association['strength'],
                        'relationship_type': association['relationship_type']
                    })
                    
                    # Update last accessed
                    cursor.execute('''
                        UPDATE topic_associations SET 
                        last_accessed = ?
                        WHERE id = ?
                    ''', (now, association['id']))
                
                conn.commit()
                return related_topics
        except Exception as e:
            logger.error(f"Failed to get related topics: {e}")
            return []
    
    def get_topic_transition(self, from_topic: str, to_topic: str) -> Optional[str]:
        """
        Get a natural transition phrase between two topics.
        
        Args:
            from_topic: Source topic
            to_topic: Target topic
            
        Returns:
            A transition phrase or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Try to find an existing transition
                cursor.execute('''
                    SELECT transition_text, use_count FROM topic_transitions 
                    WHERE from_topic = ? AND to_topic = ?
                    ORDER BY use_count ASC
                    LIMIT 1
                ''', (from_topic, to_topic))
                
                row = cursor.fetchone()
                now = datetime.now().isoformat()
                
                if row:
                    # Update usage count and last used
                    transition_text, use_count = row
                    cursor.execute('''
                        UPDATE topic_transitions SET 
                        use_count = ?,
                        last_used = ?
                        WHERE from_topic = ? AND to_topic = ? AND transition_text = ?
                    ''', (use_count + 1, now, from_topic, to_topic, transition_text))
                    conn.commit()
                    return transition_text
                
                # If no existing transition, check for relationship type
                cursor.execute('''
                    SELECT relationship_type FROM topic_associations 
                    WHERE (topic_a = ? AND topic_b = ?) OR (topic_a = ? AND topic_b = ?)
                    LIMIT 1
                ''', (from_topic, to_topic, to_topic, from_topic))
                
                row = cursor.fetchone()
                relationship_type = row[0] if row else 'related'
                
                # Generate a transition based on relationship type
                import random
                if relationship_type in self.transition_phrases:
                    templates = self.transition_phrases[relationship_type]
                    transition = random.choice(templates).format(
                        topic=to_topic, 
                        related_topic=from_topic,
                        detail="its features",  # This would be replaced with actual details
                        time_ago="a while back"  # This would be replaced with actual time
                    )
                else:
                    # Default transition
                    transition = f"Speaking of {to_topic}, which is related to our previous topic {from_topic}..."
                
                # Save this transition for future use
                self.add_topic_transition(from_topic, to_topic, transition)
                
                return transition
        except Exception as e:
            logger.error(f"Failed to get topic transition: {e}")
            
            # Fallback to a simple transition
            return f"Speaking of {to_topic}..."
    
    def extract_memories_from_conversation(self, conversation_id: int, user_id: str) -> List[int]:
        """
        Extract and save memories from a conversation.
        
        Args:
            conversation_id: The conversation ID
            user_id: The user's ID
            
        Returns:
            List of created memory IDs
        """
        try:
            # Get the conversation from persistence
            conversation = self.conversation_persistence.get_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return []
            
            # Extract the main topic
            main_topic = conversation.get('topic')
            if not main_topic:
                logger.warning(f"Conversation {conversation_id} has no topic")
                return []
            
            # Get the messages
            messages = conversation.get('messages', [])
            if not messages:
                logger.warning(f"Conversation {conversation_id} has no messages")
                return []
            
            # Extract system responses (these contain the knowledge)
            system_messages = [msg for msg in messages if msg.get('message_type') == 'system']
            if not system_messages:
                logger.warning(f"Conversation {conversation_id} has no system messages")
                return []
            
            # Create memories from system messages
            memory_ids = []
            for msg in system_messages:
                content = msg.get('content', '')
                if not content:
                    continue
                
                # Extract entities if available
                entities = None
                if msg.get('entities'):
                    entities = msg['entities']
                
                # Create a memory
                memory_id = self.add_memory(
                    user_id=user_id,
                    topic=main_topic,
                    content=content,
                    entities=entities,
                    importance=1.0  # Default importance
                )
                
                if memory_id > 0:
                    memory_ids.append(memory_id)
            
            # Extract topic relationships
            topics = conversation.get('topics', {})
            if topics and len(topics) > 1:
                # Create associations between topics
                topic_list = list(topics.keys())
                for i in range(len(topic_list)):
                    for j in range(i+1, len(topic_list)):
                        topic_a = topic_list[i]
                        topic_b = topic_list[j]
                        strength = min(topics.get(topic_a, 0.5), topics.get(topic_b, 0.5))
                        
                        self.add_topic_association(
                            topic_a=topic_a,
                            topic_b=topic_b,
                            strength=strength,
                            relationship_type='related'  # Default relationship type
                        )
            
            return memory_ids
        except Exception as e:
            logger.error(f"Failed to extract memories from conversation: {e}")
            return []
    
    def enhance_response_with_memory(self, response: str, current_topic: str, 
                                    previous_topic: Optional[str] = None, 
                                    user_id: str = "default_user") -> str:
        """
        Enhance a response with memory and natural transitions.
        
        Args:
            response: The original response
            current_topic: The current conversation topic
            previous_topic: The previous topic (if any)
            user_id: The user's ID
            
        Returns:
            Enhanced response with memory/transitions
        """
        # Skip for very long responses
        if len(response) > 500:
            return response
        
        try:
            enhanced_response = response
            
            # Add transition if topic has changed
            if previous_topic and previous_topic != current_topic:
                transition = self.get_topic_transition(previous_topic, current_topic)
                if transition:
                    # Add transition at the beginning
                    enhanced_response = f"{transition}\n\n{response}"
            
            # Add relevant memory if appropriate
            memories = self.get_memories_by_topic(user_id, current_topic, limit=1)
            if memories and len(enhanced_response) < 1000:  # Don't make very long responses
                memory = memories[0]
                memory_content = memory.get('content', '')
                
                # Only use memory if it's relevant and not too similar to the response
                if memory_content and not self._is_text_similar(memory_content, response):
                    # Add memory reference at the end
                    enhanced_response = f"{enhanced_response}\n\nI recall that {memory_content}"
            
            return enhanced_response
        except Exception as e:
            logger.error(f"Failed to enhance response with memory: {e}")
            return response
    
    def _is_text_similar(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """
        Check if two texts are similar using a simple similarity measure.
        
        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if texts are similar, False otherwise
        """
        # Simple implementation - in a real system, you might use more sophisticated methods
        # like cosine similarity with word embeddings
        
        # Normalize and tokenize
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return False
            
        similarity = intersection / union
        return similarity > threshold
