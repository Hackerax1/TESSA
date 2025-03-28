"""
Conversation persistence module for saving and loading conversation topics and context between sessions.

This module allows TESSA to remember conversation topics across different user sessions,
enabling more natural conversations with continuity and context awareness.
"""
import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationPersistence:
    """
    Class for managing persistence of conversations across sessions.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the conversation persistence manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        if not db_path:
            # Use default path in the data directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "conversations.db")
        
        self.db_path = db_path
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize the database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create conversations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        started_at TIMESTAMP NOT NULL,
                        last_updated_at TIMESTAMP NOT NULL,
                        topic TEXT
                    )
                ''')
                
                # Create messages table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id INTEGER NOT NULL,
                        message_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        intent TEXT,
                        entities TEXT,
                        timestamp TIMESTAMP NOT NULL,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                    )
                ''')
                
                # Create topics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_topics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic_name TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP NOT NULL
                    )
                ''')
                
                # Create conversation topics table (many-to-many)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_topic_mapping (
                        conversation_id INTEGER NOT NULL,
                        topic_id INTEGER NOT NULL,
                        relevance FLOAT NOT NULL DEFAULT 1.0,
                        PRIMARY KEY (conversation_id, topic_id),
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                        FOREIGN KEY (topic_id) REFERENCES conversation_topics(id) ON DELETE CASCADE
                    )
                ''')
                
                conn.commit()
                logger.info("Conversation persistence database initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize conversation database: {e}")
            
    def start_conversation(self, user_id: str, session_id: str) -> int:
        """
        Start a new conversation.
        
        Args:
            user_id: The user's ID
            session_id: The session ID
            
        Returns:
            The conversation ID
        """
        now = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversations 
                    (user_id, session_id, started_at, last_updated_at) 
                    VALUES (?, ?, ?, ?)
                ''', (user_id, session_id, now, now))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            return -1
    
    def add_message(self, conversation_id: int, message_type: str, content: str, 
                   intent: Optional[str] = None, entities: Optional[Dict[str, Any]] = None) -> int:
        """
        Add a message to the conversation.
        
        Args:
            conversation_id: The conversation ID
            message_type: Type of message (user/system)
            content: Message content
            intent: The detected intent (for user messages)
            entities: The detected entities (for user messages)
            
        Returns:
            The message ID
        """
        now = datetime.now().isoformat()
        entities_json = json.dumps(entities) if entities else None
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update the last_updated_at timestamp for the conversation
                cursor.execute('''
                    UPDATE conversations SET last_updated_at = ? WHERE id = ?
                ''', (now, conversation_id))
                
                # Insert the message
                cursor.execute('''
                    INSERT INTO conversation_messages 
                    (conversation_id, message_type, content, intent, entities, timestamp) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (conversation_id, message_type, content, intent, entities_json, now))
                
                conn.commit()
                message_id = cursor.lastrowid
                
                # Extract and save topics if this is a user message
                if message_type == 'user' and content:
                    self._extract_and_save_topics(conversation_id, content, intent, entities)
                    
                return message_id
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return -1
    
    def update_conversation_topic(self, conversation_id: int, topic: str) -> bool:
        """
        Update the main topic of a conversation.
        
        Args:
            conversation_id: The conversation ID
            topic: The main topic of the conversation
            
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE conversations SET topic = ? WHERE id = ?
                ''', (topic, conversation_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update conversation topic: {e}")
            return False
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        Get conversation details by ID.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            The conversation details or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM conversations WHERE id = ?
                ''', (conversation_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                    
                conversation = dict(row)
                
                # Get messages
                cursor.execute('''
                    SELECT * FROM conversation_messages 
                    WHERE conversation_id = ? 
                    ORDER BY timestamp
                ''', (conversation_id,))
                
                messages = []
                for msg_row in cursor.fetchall():
                    msg = dict(msg_row)
                    # Parse entities JSON
                    if msg['entities']:
                        try:
                            msg['entities'] = json.loads(msg['entities'])
                        except json.JSONDecodeError:
                            msg['entities'] = {}
                    messages.append(msg)
                
                conversation['messages'] = messages
                
                # Get topics
                cursor.execute('''
                    SELECT t.topic_name, ctm.relevance 
                    FROM conversation_topic_mapping ctm
                    JOIN conversation_topics t ON t.id = ctm.topic_id
                    WHERE ctm.conversation_id = ?
                    ORDER BY ctm.relevance DESC
                ''', (conversation_id,))
                
                conversation['topics'] = {row['topic_name']: row['relevance'] for row in cursor.fetchall()}
                
                return conversation
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
    
    def get_recent_conversations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversations for a user.
        
        Args:
            user_id: The user's ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of recent conversations
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM conversations 
                    WHERE user_id = ? 
                    ORDER BY last_updated_at DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append(dict(row))
                
                return conversations
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []
    
    def find_conversations_by_topic(self, user_id: str, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find conversations related to a specific topic.
        
        Args:
            user_id: The user's ID
            topic: The topic to search for
            limit: Maximum number of conversations to return
            
        Returns:
            List of relevant conversations
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # First try exact topic match
                cursor.execute('''
                    SELECT c.* FROM conversations c
                    JOIN conversation_topic_mapping ctm ON c.id = ctm.conversation_id
                    JOIN conversation_topics t ON t.id = ctm.topic_id
                    WHERE c.user_id = ? AND t.topic_name = ?
                    ORDER BY ctm.relevance DESC, c.last_updated_at DESC
                    LIMIT ?
                ''', (user_id, topic, limit))
                
                rows = cursor.fetchall()
                
                # If no exact matches, try LIKE search
                if not rows:
                    cursor.execute('''
                        SELECT c.* FROM conversations c
                        JOIN conversation_topic_mapping ctm ON c.id = ctm.conversation_id
                        JOIN conversation_topics t ON t.id = ctm.topic_id
                        WHERE c.user_id = ? AND t.topic_name LIKE ?
                        ORDER BY ctm.relevance DESC, c.last_updated_at DESC
                        LIMIT ?
                    ''', (user_id, f"%{topic}%", limit))
                    rows = cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conversations.append(dict(row))
                
                return conversations
        except Exception as e:
            logger.error(f"Failed to find conversations by topic: {e}")
            return []
    
    def get_active_conversation(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the active conversation for the current session.
        
        Args:
            user_id: The user's ID
            session_id: The session ID
            
        Returns:
            The active conversation or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM conversations 
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY last_updated_at DESC 
                    LIMIT 1
                ''', (user_id, session_id))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return self.get_conversation(row['id'])
        except Exception as e:
            logger.error(f"Failed to get active conversation: {e}")
            return None
    
    def get_relevant_past_conversations(self, user_id: str, current_topic: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get relevant past conversations based on the current topic.
        
        Args:
            user_id: The user's ID
            current_topic: The current conversation topic
            limit: Maximum number of conversations to return
            
        Returns:
            List of relevant past conversations
        """
        return self.find_conversations_by_topic(user_id, current_topic, limit)
    
    def _extract_and_save_topics(self, conversation_id: int, content: str, intent: Optional[str], entities: Optional[Dict]) -> None:
        """
        Extract topics from a message and save them.
        
        Args:
            conversation_id: The conversation ID
            content: The message content
            intent: The detected intent
            entities: The detected entities
        """
        # Set of potential topics from the message
        topics: Set[str] = set()
        
        # Add intent as a topic if available
        if intent:
            topics.add(intent.replace('_', ' '))
        
        # Add entity values as potential topics
        if entities:
            for entity_type, entity_value in entities.items():
                if isinstance(entity_value, str):
                    # Add clean entity value (remove underscores, limit length)
                    clean_value = entity_value.replace('_', ' ')
                    if 3 <= len(clean_value) <= 50:  # Reasonable topic length
                        topics.add(clean_value)
                        
                # Add entity type as a topic (e.g., "vm", "service")
                clean_type = entity_type.replace('_', ' ')
                topics.add(clean_type)
        
        # Save identified topics
        for topic in topics:
            self._save_topic(conversation_id, topic)
    
    def _save_topic(self, conversation_id: int, topic: str, relevance: float = 1.0) -> None:
        """
        Save a topic and associate it with a conversation.
        
        Args:
            conversation_id: The conversation ID
            topic: The topic name
            relevance: The topic relevance score (0-1)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, get or create the topic
                cursor.execute('''
                    SELECT id FROM conversation_topics WHERE topic_name = ?
                ''', (topic,))
                
                row = cursor.fetchone()
                if row:
                    topic_id = row[0]
                else:
                    # Create new topic
                    now = datetime.now().isoformat()
                    cursor.execute('''
                        INSERT INTO conversation_topics (topic_name, created_at)
                        VALUES (?, ?)
                    ''', (topic, now))
                    conn.commit()
                    topic_id = cursor.lastrowid
                
                # Associate topic with conversation
                cursor.execute('''
                    INSERT OR REPLACE INTO conversation_topic_mapping 
                    (conversation_id, topic_id, relevance)
                    VALUES (?, ?, ?)
                ''', (conversation_id, topic_id, relevance))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save topic: {e}")
    
    def get_topic_history(self, user_id: str) -> Dict[str, int]:
        """
        Get topic usage history for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary mapping topics to usage counts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT t.topic_name, COUNT(*) as count
                    FROM conversation_topic_mapping ctm
                    JOIN conversation_topics t ON t.id = ctm.topic_id
                    JOIN conversations c ON c.id = ctm.conversation_id
                    WHERE c.user_id = ?
                    GROUP BY t.topic_name
                    ORDER BY count DESC
                ''', (user_id,))
                
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get topic history: {e}")
            return {}
            
    def get_conversation_transition(self, user_id: str, from_topic: str, to_topic: str) -> Optional[str]:
        """
        Get a natural transition phrase between two topics based on past conversations.
        
        Args:
            user_id: The user's ID
            from_topic: The source topic
            to_topic: The target topic
            
        Returns:
            A transition phrase or None
        """
        # Default transitions
        default_transitions = [
            f"Speaking of {to_topic}, I remember we discussed this before.",
            f"This reminds me of our previous conversation about {to_topic}.",
            f"We've talked about {to_topic} in the past.",
            f"Going back to {to_topic} that we discussed earlier.",
            f"Transitioning from {from_topic} to {to_topic}, which we've covered before."
        ]
        
        # Try to find actual conversations that link these topics
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Find conversations that contain both topics
                cursor.execute('''
                    SELECT c.id 
                    FROM conversations c
                    JOIN conversation_topic_mapping ctm1 ON c.id = ctm1.conversation_id
                    JOIN conversation_topics t1 ON t1.id = ctm1.topic_id
                    JOIN conversation_topic_mapping ctm2 ON c.id = ctm2.conversation_id
                    JOIN conversation_topics t2 ON t2.id = ctm2.topic_id
                    WHERE c.user_id = ? AND t1.topic_name = ? AND t2.topic_name = ?
                    ORDER BY c.last_updated_at DESC
                    LIMIT 1
                ''', (user_id, from_topic, to_topic))
                
                row = cursor.fetchone()
                if not row:
                    # No matching conversation, return default transition
                    import random
                    return random.choice(default_transitions)
                
                # Get messages from this conversation to extract a more natural transition
                conversation_id = row['id']
                cursor.execute('''
                    SELECT content FROM conversation_messages
                    WHERE conversation_id = ? AND message_type = 'system'
                    ORDER BY timestamp DESC
                    LIMIT 3
                ''', (conversation_id,))
                
                messages = [row['content'] for row in cursor.fetchall()]
                if messages:
                    return f"Last time we discussed {to_topic}, I mentioned: '{messages[0]}'"
                
                return default_transitions[0]
                
        except Exception as e:
            logger.error(f"Failed to get conversation transition: {e}")
            import random
            return random.choice(default_transitions)