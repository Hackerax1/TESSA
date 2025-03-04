import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import os

# Try to download required NLTK resources (minimal required set)
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    print(f"Warning: Could not download NLTK resources: {str(e)}")

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
                print(f"Ollama integration activated with model: {self.ollama_client.model_name}")
            except Exception as e:
                print(f"Warning: Failed to initialize Ollama client: {str(e)}")
                print("NLU will fall back to basic pattern matching")
                self.use_ollama = False

    def process_query(self, query):
        """Process a natural language query"""
        try:
            # Preprocess the query
            preprocessed_query = self.preprocessor.preprocess_query(query)
            
            # Try Ollama for intent recognition and entity extraction if available
            if self.use_ollama and self.ollama_client:
                try:
                    intent, args, entities = self.ollama_client.get_intent_and_entities(query)
                    
                    # If Ollama returned a valid intent, use it
                    if intent and intent != "unknown":
                        # Update conversation context
                        self.context_manager.update_context(intent, entities)
                        
                        # Resolve contextual references
                        entities = self.context_manager.resolve_contextual_references(query, entities)
                        
                        return intent, args, entities
                except Exception as e:
                    print(f"Warning: Error using Ollama for NLU: {str(e)}")
                    print("Falling back to traditional NLU pipeline")
            
            # Fallback to traditional NLU pipeline
            # Extract entities
            entities = self.entity_extractor.extract_entities(query)
            
            # Identify intent
            intent, args = self.intent_identifier.identify_intent(preprocessed_query)
            
            # Update conversation context
            self.context_manager.update_context(intent, entities)
            
            # Resolve contextual references
            entities = self.context_manager.resolve_contextual_references(query, entities)
            
            return intent, args, entities
        except Exception as e:
            # Fallback to basic intent recognition if any step fails
            print(f"Warning: Error in NLU processing: {str(e)}")
            
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
            
            return intent, args, entities