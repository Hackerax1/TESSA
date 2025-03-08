import re
import nltk
import logging
import os
from typing import Dict, Any, List, Tuple, Optional
from nltk.tokenize import word_tokenize

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to download required NLTK resources (minimal required set)
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
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
        
        # Share context manager's context with intent identifier
        self.intent_identifier.context = self.context_manager.context
        
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
        """Process a natural language query"""
        try:
            # Preprocess the query
            preprocessed_query = self.preprocessor.preprocess_query(query)
            
            # Try Ollama first if available
            if self.use_ollama and self.ollama_client:
                try:
                    # Pass conversation history for contextual understanding
                    intent, args, entities = self.ollama_client.get_intent_and_entities(
                        query, 
                        conversation_history=self.context_manager.get_active_context()
                    )
                    
                    # If Ollama returned a valid intent, use it
                    if intent and intent != "unknown":
                        # Convert entities to lowercase keys and preserve original VM names
                        entities = {k.lower(): v for k, v in entities.items()}
                        
                        # Update conversation context
                        self.context_manager.update_context(intent, entities)
                        
                        # Resolve contextual references
                        entities = self.context_manager.resolve_contextual_references(query, entities)
                        
                        # Keep intent identifier's context in sync
                        self.intent_identifier.context = self.context_manager.context
                        
                        logger.info(f"Ollama identified intent: {intent} with entities: {entities}")
                        return intent, list(args) if args else [], entities
                except Exception as e:
                    logger.warning(f"Error using Ollama for NLU: {str(e)}")
                    logger.warning("Falling back to traditional NLU pipeline")
            
            # Fallback to traditional NLU pipeline
            logger.info("Using traditional NLU pipeline")
            
            # First check the context for any references
            context = self.context_manager.get_active_context()
            resolved_query = query
            
            # If query contains pronouns, check if we have context
            if any(word in query.lower() for word in ['it', 'its', 'this', 'that']):
                # Try to resolve the pronoun using context
                if context.get('current_vm'):
                    resolved_query = query.lower().replace('it', context['current_vm'])
                    resolved_query = resolved_query.replace('its', context['current_vm'] + "'s")
                    resolved_query = resolved_query.replace('this', context['current_vm'])
                    resolved_query = resolved_query.replace('that', context['current_vm'])
            
            # Extract entities from the resolved query
            entities = self.entity_extractor.extract_entities(resolved_query)
            
            # Update context with any new entities
            self.context_manager.update_context(None, entities)
            
            # Keep intent identifier's context in sync
            self.intent_identifier.context = self.context_manager.context
            
            # Try to identify intent from the processed query
            intent, args = self.intent_identifier.identify_intent(preprocessed_query)
            
            # Convert tuple args to list if needed
            args = list(args) if isinstance(args, tuple) else args if args else []
            
            # If intent is 'help' but we have context, try again with contextual commands
            if intent == 'help' and context.get('current_vm'):
                # Explicitly check for common contextual commands
                tokens = set(word_tokenize(query.lower()))
                if 'stop' in tokens:
                    intent = 'stop_vm'
                    args = [context['current_vm']]
                elif 'start' in tokens:
                    intent = 'start_vm'
                    args = [context['current_vm']]
                elif 'restart' in tokens or 'reboot' in tokens:
                    intent = 'restart_vm'
                    args = [context['current_vm']]
                elif any(word in tokens for word in ['status', 'check', 'how']):
                    intent = 'vm_status'
                    args = [context['current_vm']]
            
            # Update context with identified intent
            self.context_manager.update_context(intent, entities)
            
            # Convert entities to lowercase keys
            entities = {k.lower(): v for k, v in entities.items()}
            
            # Check if we have required entities for this intent
            is_valid, missing = self.entity_extractor.validate_entities(entities, intent)
            
            # If we're missing required entities but have them in context, use those
            if not is_valid and missing:
                context_data = self.context_manager.get_active_context()
                for entity in missing:
                    context_key = entity.lower()
                    if context_key in context_data and context_data[context_key]:
                        entities[context_key] = context_data[context_key]
            
            logger.info(f"Traditional pipeline identified intent: {intent} with entities: {entities}")
            return intent, args, entities
        
        except Exception as e:
            # Log the full error for debugging
            logger.error(f"Error in NLU processing: {str(e)}", exc_info=True)
            return 'help', [], {}
    
    def enhance_response(self, query: str, intent: str, result: Dict[str, Any]) -> Optional[str]:
        """Enhance a response with natural language using Ollama if available"""
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