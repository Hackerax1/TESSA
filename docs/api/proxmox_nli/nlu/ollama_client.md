# ollama_client

Ollama integration for enhanced NLU capabilities in Proxmox NLI.
This module provides a client to interact with Ollama models for intent recognition,
entity extraction, and natural language understanding.

**Module Path**: `proxmox_nli.nlu.ollama_client`

## Classes

### OllamaClient

#### __init__(model_name: str, base_url: str = 'llama3')

Initialize the Ollama client with the specified model.

Args:
    model_name: Name of the Ollama model to use (default: "llama3")
    base_url: URL of the Ollama API (default: http://localhost:11434)

#### get_intent_and_entities(query: str, conversation_history: List[Dict[(str, Any)]])

Process a query to extract intent and entities using Ollama.

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

Enhance a response using Ollama for better natural language generation.

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

