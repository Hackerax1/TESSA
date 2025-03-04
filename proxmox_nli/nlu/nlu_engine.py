import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

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

class NLU_Engine:
    def __init__(self):
        self.preprocessor = Preprocessor()
        self.context_manager = ContextManager()
        self.entity_extractor = EntityExtractor()
        self.intent_identifier = IntentIdentifier()

    def process_query(self, query):
        """Process a natural language query"""
        try:
            # Preprocess the query
            preprocessed_query = self.preprocessor.preprocess_query(query)
            
            # Extract entities
            entities = self.entity_extractor.extract_entities(query)
            
            # Identify intent
            intent, args = self.intent_identifier.identify_intent(preprocessed_query)
            
            # Update conversation context
            self.context_manager.update_context(intent, entities)
            
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