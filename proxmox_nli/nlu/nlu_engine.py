import re
import nltk
import logging
import os
from typing import Dict, Any, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to download required NLTK resources (minimal required set)
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.warning(f"Could not download NLTK resources: {str(e)}")

from .preprocessing import Preprocessor
from .context_management import ContextManager
from .entity_extraction import EntityExtractor
from .intent_identification import IntentIdentifier
from .ollama_client import OllamaClient

class NLU_Engine:
    def __init__(self, use_ollama=True, ollama_model="llama3", ollama_url=None):
        """Initialize the NLU Engine with optional Ollama integration"""
        self.preprocessor = Preprocessor()
        self.context_manager = ContextManager()
        self.entity_extractor = EntityExtractor()
        self.intent_identifier = IntentIdentifier()
        
        # Initialize Ollama client if requested
        self.use_ollama = use_ollama and os.getenv("DISABLE_OLLAMA", "").lower() != "true"
        self.ollama_client = None
        
        if self.use_ollama:
            try:
                self.ollama_client = OllamaClient(
                    model_name=os.getenv("OLLAMA_MODEL", ollama_model),
                    base_url=os.getenv("OLLAMA_API_URL", ollama_url)
                )
                logger.info(f"Ollama integration activated with model: {self.ollama_client.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {str(e)}")
                logger.warning("NLU will fall back to basic pattern matching")
                self.use_ollama = False

    def process_query(self, query: str):
        """
        Process a natural language query
        
        Args:
            query: The user's natural language query string
            
        Returns:
            Tuple of (intent, args, entities)
        """
        try:
            # Preprocess the query
            preprocessed_query = self.preprocessor.preprocess_query(query)
            
            # Get conversation history for context
            conversation_history = self.context_manager.conversation_history
            
            # Try Ollama for intent recognition and entity extraction if available
            if self.use_ollama and self.ollama_client:
                try:
                    # Pass conversation history for contextual understanding
                    intent, args, entities = self.ollama_client.get_intent_and_entities(
                        query, 
                        conversation_history=conversation_history
                    )
                    
                    # If Ollama returned a valid intent, use it
                    if intent and intent != "unknown":
                        # Update conversation context
                        self.context_manager.update_context(intent, entities)
                        
                        # Resolve contextual references (for any entities Ollama might have missed)
                        entities = self.context_manager.resolve_contextual_references(query, entities)
                        
                        logger.info(f"Ollama identified intent: {intent} with entities: {entities}")
                        return intent, args, entities
                except Exception as e:
                    logger.warning(f"Error using Ollama for NLU: {str(e)}")
                    logger.warning("Falling back to traditional NLU pipeline")
            
            # Fallback to traditional NLU pipeline
            logger.info("Using traditional NLU pipeline")
            
            # Extract entities first for context
            entities = self.entity_extractor.extract_entities(query)
            
            # Resolve contextual references
            resolved_entities = self.context_manager.resolve_contextual_references(query, entities)
            
            # Pass context to intent identifier
            self.intent_identifier.context = self.context_manager.context
            
            # Identify intent
            intent, args = self.intent_identifier.identify_intent(preprocessed_query)
            
            # Check if we have required entities for this intent
            is_valid, missing = self.entity_extractor.validate_entities(resolved_entities, intent)
            
            # If we're missing required entities but have them in context, try to resolve
            if not is_valid and missing:
                context_data = self.context_manager.get_active_context()
                for entity in missing:
                    context_key = f"current_{entity.lower()}"
                    if context_key in context_data and context_data[context_key]:
                        resolved_entities[entity] = context_data[context_key]
            
            # Update conversation context with final entities
            self.context_manager.update_context(intent, resolved_entities)
            
            logger.info(f"Traditional pipeline identified intent: {intent} with entities: {resolved_entities}")
            return intent, args, resolved_entities
        
        except Exception as e:
            # Fallback to basic intent recognition if any step fails
            logger.error(f"Error in NLU processing: {str(e)}", exc_info=True)
            
            # Basic intent detection for critical commands
            intent = 'help'  # Default to help
            args = []
            entities = {}
            
            # Very basic intent detection
            query_lower = query.lower()
            if 'list vm' in query_lower:
                intent = 'list_vms'
            elif 'help' in query_lower:
                intent = 'help'
                
            logger.info(f"Fallback identified intent: {intent}")
            return intent, args, entities
    
    def enhance_response(self, query: str, intent: str, result: Dict[str, Any]) -> Optional[str]:
        """
        Enhance a response with natural language using Ollama if available
        
        Args:
            query: Original user query
            intent: Identified intent
            result: Command execution result dictionary
            
        Returns:
            Enhanced natural language response or None if not available
        """
        if self.use_ollama and self.ollama_client:
            try:
                return self.ollama_client.enhance_response(query, intent, result)
            except Exception as e:
                logger.warning(f"Error enhancing response: {str(e)}")
        return None
    
    def save_context(self, filepath: str) -> bool:
        """Save current context to a file"""
        return self.context_manager.save_context(filepath)
    
    def load_context(self, filepath: str) -> bool:
        """Load context from a file"""
        return self.context_manager.load_context(filepath)
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation history"""
        return self.context_manager.get_conversation_summary()