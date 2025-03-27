# nlu_engine

**Module Path**: `proxmox_nli.nlu.nlu_engine`

## Classes

### NLU_Engine

#### __init__(use_ollama, use_huggingface = True, ollama_model = False, ollama_url = 'llama3', huggingface_model = None, huggingface_api_key = 'mistralai/Mistral-7B-Instruct-v0.2')

Initialize the NLU Engine with optional Ollama/Hugging Face integration

#### process_query(query: str)

Process a natural language query

#### enhance_response(query: str, intent: str, result: Dict[(str, Any)])

Enhance a response with natural language using available LLM clients

**Returns**: `Optional[str]`

#### save_context(filepath: str)

Save current context to a file

**Returns**: `bool`

#### load_context(filepath: str)

Load context from a file

**Returns**: `bool`

#### get_conversation_summary()

Get a summary of the conversation history

**Returns**: `str`

