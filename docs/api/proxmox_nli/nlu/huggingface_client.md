# huggingface_client

Hugging Face integration for enhanced NLU capabilities in Proxmox NLI.
This module provides a client to interact with Hugging Face models for intent recognition,
entity extraction, and natural language understanding.

**Module Path**: `proxmox_nli.nlu.huggingface_client`

## Classes

### HuggingFaceClient

#### __init__(model_name: str, api_key: str = 'mistralai/Mistral-7B-Instruct-v0.2', base_url: str = None)

Initialize the Hugging Face client with the specified model.

Args:
    model_name: Name of the Hugging Face model to use (default: "mistralai/Mistral-7B-Instruct-v0.2")
    api_key: Hugging Face API key (default: read from env var HUGGINGFACE_API_KEY)
    base_url: URL of the Hugging Face API (default: https://api-inference.huggingface.co/models/)

#### get_intent_and_entities(query: str, conversation_history: List[Dict[(str, Any)]])

Process a query to extract intent and entities using Hugging Face.

Args:
    query: The natural language query to process
    conversation_history: Previous conversation context
    
Returns:
    Tuple containing:
        - intent name (str)
        - intent arguments (list)
        - extracted entities (dict)

**Returns**: `Tuple[(str, List[Any], Dict[(str, Any)])]`

#### enhance_response(query: str, intent: str, result: Dict[(str, Any)])

Enhance a response using Hugging Face for better natural language generation.

Args:
    query: Original user query
    intent: Identified intent
    result: Command execution result dictionary
    
Returns:
    Enhanced natural language response

**Returns**: `str`

#### get_contextual_information()

Get current conversation context information

Returns:
    Dictionary containing conversation context

**Returns**: `Dict[(str, Any)]`

