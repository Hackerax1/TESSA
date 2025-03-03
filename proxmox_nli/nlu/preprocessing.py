import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

class Preprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

    def preprocess_query(self, query):
        """Preprocess the natural language query"""
        # Convert to lowercase
        query = query.lower()
        
        # Tokenize
        tokens = word_tokenize(query)
        
        # Remove stop words and lemmatize
        filtered_tokens = []
        for token in tokens:
            if token not in self.stop_words:
                filtered_tokens.append(self.lemmatizer.lemmatize(token))
        
        # Join back into a string
        preprocessed_query = ' '.join(filtered_tokens)
        
        return preprocessed_query
