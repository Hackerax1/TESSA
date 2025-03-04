import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import os

# Ensure NLTK data directory exists
nltk_data_dir = os.path.join(os.path.expanduser('~'), 'nltk_data')
if not os.path.exists(nltk_data_dir):
    os.makedirs(nltk_data_dir, exist_ok=True)

# Download required NLTK resources with verification
def download_nltk_data():
    resources = ['punkt', 'stopwords', 'wordnet', 'punkt_tab']
    for resource in resources:
        try:
            if resource == 'punkt_tab':
                # Special handling for punkt_tab which needs to be accessed differently
                try:
                    nltk.data.find(f'tokenizers/punkt_tab/english')
                    print(f"NLTK {resource} already downloaded")
                except LookupError:
                    print(f"Downloading NLTK {resource}...")
                    nltk.download('punkt', quiet=False)
                    # punkt_tab is actually part of the punkt package
            else:
                nltk.data.find(f'tokenizers/{resource}')
                print(f"NLTK {resource} already downloaded")
        except LookupError:
            print(f"Downloading NLTK {resource}...")
            nltk.download(resource, quiet=False)

# Download data
download_nltk_data()

class Preprocessor:
    def __init__(self):
        # Ensure the data is downloaded before initializing
        download_nltk_data()
        
        self.lemmatizer = WordNetLemmatizer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            print("Warning: Could not load stopwords. Using empty set.")
            self.stop_words = set()

    def preprocess_query(self, query):
        """Preprocess the natural language query"""
        # Convert to lowercase
        query = query.lower()
        
        try:
            # Tokenize - using a more robust approach
            try:
                tokens = word_tokenize(query)
            except LookupError:
                # Fallback tokenization if word_tokenize fails
                tokens = query.split()
            
            # Remove stop words and lemmatize
            filtered_tokens = []
            for token in tokens:
                if token not in self.stop_words:
                    filtered_tokens.append(self.lemmatizer.lemmatize(token))
            
            # Join back into a string
            preprocessed_query = ' '.join(filtered_tokens)
            
            return preprocessed_query
        except Exception as e:
            # Fallback if processing fails
            print(f"Warning: Query preprocessing failed: {str(e)}")
            return query.lower()
