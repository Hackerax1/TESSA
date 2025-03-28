"""
Base NLI module defining core functionality for the Proxmox NLI.
"""
import importlib
import inspect
import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, List, Optional, Type

from proxmox_nli.core.conversation_persistence import ConversationPersistence
from proxmox_nli.core.topic_manager import TopicManager
from proxmox_nli.core.memory_manager import MemoryManager
from proxmox_nli.core.context_bridge import ContextBridge

logger = logging.getLogger(__name__)

class BaseNLI:
    """Base class for NLI functionality"""
    
    def __init__(self, host=None, user=None, password=None, realm='pam', verify_ssl=False):
        """Initialize the base NLI"""
        self.name = "Base NLI"
        self.version = "1.0"
        self.commands = type('commands', (), {})()
        self.docker_commands = type('docker_commands', (), {})()
        self.help_texts = {}
        self.nlu = None
        self.session_id = str(uuid.uuid4())
        
        # Store Proxmox connection details
        self.host = host
        self.user = user
        self.password = password
        self.realm = realm
        self.verify_ssl = verify_ssl
        
        # Initialize conversation persistence and topic manager
        self.conversation_persistence = ConversationPersistence()
        self.topic_manager = TopicManager(self.conversation_persistence)
        self.memory_manager = MemoryManager(self.conversation_persistence)
        self.context_bridge = None  # Will be initialized after NLU engine is set
        self.current_user_id = "default_user"
        self.current_conversation_id = None
        
        # Initialize pending command storage
        self.pending_command = None
        self.pending_args = None
        self.pending_entities = None
        self.require_confirmation = True
    
    def set_nlu_engine(self, nlu_engine):
        """Set the NLU engine for the NLI"""
        self.nlu = nlu_engine
        
        # Initialize context bridge if NLU has a context manager
        if hasattr(self.nlu, 'context_manager'):
            self.context_bridge = ContextBridge(
                self.nlu.context_manager,
                self.memory_manager,
                self.topic_manager
            )
    
    def start_user_session(self, user_id: str):
        """Start a new user session"""
        self.current_user_id = user_id
        self.current_conversation_id = self.topic_manager.start_session(user_id, self.session_id)
        
        # Extract memories from previous conversations if available
        if self.current_conversation_id > 0:
            # Find recent conversations to extract memories from
            recent_conversations = self.conversation_persistence.get_recent_conversations(user_id, limit=3)
            for conversation in recent_conversations:
                if conversation['id'] != self.current_conversation_id:  # Skip current conversation
                    self.memory_manager.extract_memories_from_conversation(conversation['id'], user_id)
        
        # Synchronize context between systems
        if self.context_bridge:
            self.context_bridge.sync_context(user_id)
    
    def get_intent_and_entities(self, query: str) -> Dict:
        """Get intent and entities from query"""
        if self.nlu:
            return self.nlu.get_intent_and_entities(query)
        return {"intent": "unknown", "entities": {}}
    
    def resolve_intent(self, query: str) -> Dict:
        """Resolve intent from query"""
        if not self.nlu:
            return {"intent": "unknown", "entities": {}}
            
        result = self.nlu.get_intent_and_entities(query)
        intent = result.get("intent")
        entities = result.get("entities", {})
        
        # Process user message through topic manager
        self.topic_manager.process_user_message(query, intent, entities)
        
        # Synchronize context between systems using context bridge
        if self.context_bridge:
            self.context_bridge.sync_context(self.current_user_id)
        # Fallback if context bridge is not available
        elif hasattr(self.nlu, 'context_manager') and hasattr(self.nlu.context_manager, 'add_cross_session_context'):
            # If this is related to a previous conversation, add cross-session context
            if self.topic_manager.current_topic:
                self.nlu.context_manager.add_cross_session_context(
                    self.topic_manager.current_topic, 
                    entities
                )
                
                # Create topic associations for related topics
                if self.topic_manager.previous_topic and self.topic_manager.previous_topic != self.topic_manager.current_topic:
                    self.memory_manager.add_topic_association(
                        self.topic_manager.previous_topic,
                        self.topic_manager.current_topic,
                        strength=0.8,
                        relationship_type='continuation'
                    )
        
        return {"intent": intent, "entities": entities}
    
    def execute_intent(self, intent: str, entities: Dict = None) -> Dict:
        """Execute the given intent"""
        if not entities:
            entities = {}
            
        # Check if the intent matches a command
        if hasattr(self.commands, intent):
            command_func = getattr(self.commands, intent)
            return command_func(self, entities, {})
            
        # Check if the intent matches a Docker command
        elif hasattr(self.docker_commands, intent):
            command_func = getattr(self.docker_commands, intent)
            return command_func(self, entities, {})
            
        # Unknown intent
        return {"success": False, "message": f"Unknown intent: {intent}"}
    
    def process_query(self, query: str, user_id: str = None) -> Dict:
        """Process a user query"""
        if user_id:
            self.current_user_id = user_id
        
        # Ensure we have an active conversation
        if not self.current_conversation_id:
            self.start_user_session(self.current_user_id)
        
        # Resolve intent and entities
        resolved_intent = self.resolve_intent(query)
        intent = resolved_intent.get("intent")
        entities = resolved_intent.get("entities", {})
        
        # Execute the intent
        result = self.execute_intent(intent, entities)
        
        # Process system response through topic manager
        response_message = result.get("message", "")
        if response_message:
            self.topic_manager.process_system_response(response_message)
            
            # Enhance response with context bridge if available
            if self.context_bridge:
                enhanced_response = self.context_bridge.enhance_response(
                    response_message,
                    query,
                    intent,
                    entities,
                    self.current_user_id
                )
                result["message"] = enhanced_response
                
                # Extract and store context
                self.context_bridge.extract_and_store_context(
                    query,
                    intent,
                    entities,
                    response_message,
                    self.current_user_id
                )
            else:
                # Fallback to memory manager and topic manager if context bridge is not available
                enhanced_response = self.memory_manager.enhance_response_with_memory(
                    response_message,
                    current_topic=self.topic_manager.current_topic,
                    previous_topic=self.topic_manager.previous_topic,
                    user_id=self.current_user_id
                )
                
                # If memory manager didn't enhance the response, try the topic manager
                if enhanced_response == response_message:
                    enhanced_response = self.topic_manager.enhance_response_with_memory(response_message)
                    
                result["message"] = enhanced_response
                
                # Store important information as memories
                if intent and intent not in ["unknown", "error", "help"]:
                    # Only create memories for substantive interactions
                    self.memory_manager.add_memory(
                        user_id=self.current_user_id,
                        topic=self.topic_manager.current_topic or intent.replace('_', ' '),
                        content=response_message,
                        entities=entities,
                        importance=0.8  # Default importance
                    )
        
        return result
    
    def format_response(self, result: Dict) -> str:
        """Format a result dictionary into a response string"""
        if not result:
            return "I encountered an error while processing your request."
            
        if not result.get("success", True):
            return f"Error: {result.get('message', 'Unknown error')}"
            
        return result.get("message", "Your request was processed successfully.")
    
    def get_help_text(self, command: str = None) -> str:
        """Get help text for a command or list all commands"""
        if command and command in self.help_texts:
            return self.help_texts[command]
            
        commands = sorted(list(self.help_texts.keys()))
        return "Available commands: " + ", ".join(commands)
    
    def load_custom_commands(self):
        """Load custom commands from the custom_commands directory"""
        custom_commands_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'custom_commands')
        if not os.path.exists(custom_commands_dir):
            return
        for filename in os.listdir(custom_commands_dir):
            if filename.endswith('.py'):
                module_name = filename[:-3]
                file_path = os.path.join(custom_commands_dir, filename)
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                if hasattr(module, 'register_commands'):
                    module.register_commands(self)

    def register_command(self, command_name: str, command_func, help_text: str = None):
        """Register a new command"""
        setattr(self.commands, command_name, command_func)
        if help_text:
            self.help_texts[command_name] = help_text