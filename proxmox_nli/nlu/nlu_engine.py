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
from .huggingface_client import HuggingFaceClient

class NLU_Engine:
    def __init__(self, use_ollama=True, use_huggingface=False, 
                 ollama_model="llama3", ollama_url=None, 
                 huggingface_model="mistralai/Mistral-7B-Instruct-v0.2", huggingface_api_key=None):
        """Initialize the NLU Engine with optional Ollama/Hugging Face integration"""
        self.preprocessor = Preprocessor()
        self.context_manager = ContextManager()
        self.entity_extractor = EntityExtractor()
        self.intent_identifier = IntentIdentifier()
        
        # Share context manager's context with intent identifier
        self.intent_identifier.context = self.context_manager.context
        
        # Initialize LLM clients
        self.use_ollama = use_ollama and os.getenv("DISABLE_OLLAMA", "").lower() != "true"
        self.use_huggingface = use_huggingface and os.getenv("DISABLE_HUGGINGFACE", "").lower() != "true"
        self.ollama_client = None
        self.huggingface_client = None
        
        # Set up Ollama client if requested
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
                
        # Set up Hugging Face client if requested
        if self.use_huggingface:
            try:
                self.huggingface_client = HuggingFaceClient(
                    model_name=os.getenv("HUGGINGFACE_MODEL", huggingface_model),
                    api_key=os.getenv("HUGGINGFACE_API_KEY", huggingface_api_key)
                )
                logger.info(f"Hugging Face integration activated with model: {self.huggingface_client.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Hugging Face client: {str(e)}")
                logger.warning("NLU will fall back to Ollama or basic pattern matching")
                self.use_huggingface = False
    
    def process_query(self, query: str):
        """Process a natural language query"""
        try:
            # Preprocess the query
            preprocessed_query = self.preprocessor.preprocess_query(query)
            
            # Try Hugging Face first if available
            if self.use_huggingface and self.huggingface_client:
                try:
                    # Pass conversation history for contextual understanding
                    intent, args, entities = self.huggingface_client.get_intent_and_entities(
                        query, 
                        conversation_history=self.context_manager.get_active_context()
                    )
                    
                    # If Hugging Face returned a valid intent, use it
                    if intent and intent != "unknown":
                        # Convert entities to lowercase keys and preserve original VM names
                        entities = {k.lower(): v for k, v in entities.items()}
                        
                        # Update conversation context
                        self.context_manager.update_context(intent, entities)
                        
                        # Resolve contextual references
                        entities = self.context_manager.resolve_contextual_references(query, entities)
                        
                        # Keep intent identifier's context in sync
                        self.intent_identifier.context = self.context_manager.context
                        
                        logger.info(f"Hugging Face identified intent: {intent} with entities: {entities}")
                        return intent, list(args) if args else [], entities
                except Exception as e:
                    logger.warning(f"Error using Hugging Face for NLU: {str(e)}")
                    logger.warning("Falling back to Ollama or traditional NLU pipeline")
            
            # Try Ollama next if available and Hugging Face failed or is not enabled
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
                    # For example, replace "Stop it" with "Stop vm-100" if that was the last VM referenced
                    resolved_query = query.lower().replace('it', context['current_vm'])
                    resolved_query = resolved_query.replace('this', context['current_vm'])
                    resolved_query = resolved_query.replace('that', context['current_vm'])
                    logger.info(f"Resolved query with context: {resolved_query}")
            
            # Check intent patterns
            intent, args = self.intent_identifier.identify_intent(resolved_query)
            
            # Extract entities
            entities = self.entity_extractor.extract_entities(resolved_query, intent)
            
            # Update context with the new entities
            self.context_manager.update_context(intent, entities)
            
            return intent, args, entities
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return "error", ["error"], {"error": str(e)}
    
    def enhance_response(self, query: str, intent: str, result: Dict[str, Any]) -> Optional[str]:
        """Enhance a response with natural language using available LLM clients"""
        # Try Hugging Face first for response enhancement
        if self.use_huggingface and self.huggingface_client:
            try:
                hf_response = self.huggingface_client.enhance_response(query, intent, result)
                if hf_response:
                    return hf_response
            except Exception as e:
                logger.warning(f"Error enhancing response with Hugging Face: {str(e)}")
        
        # Try Ollama if Hugging Face fails or is not available
        if self.use_ollama and self.ollama_client:
            try:
                return self.ollama_client.enhance_response(query, intent, result)
            except Exception as e:
                logger.warning(f"Error enhancing response with Ollama: {str(e)}")
        
        # If both failed, return None to use default response formatting
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