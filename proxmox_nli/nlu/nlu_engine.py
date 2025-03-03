import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

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
        # Preprocess the query
        preprocessed_query = self.preprocessor.preprocess_query(query)
        
        # Extract entities
        entities = self.entity_extractor.extract_entities(query)
        
        # Identify intent
        intent, args = self.intent_identifier.identify_intent(preprocessed_query)
        
        # Update conversation context
        self.context_manager.update_context(intent, entities)
        
        return intent, args, entities