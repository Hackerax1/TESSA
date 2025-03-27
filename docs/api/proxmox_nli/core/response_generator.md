# response_generator

Response generator module for producing natural language responses.

**Module Path**: `proxmox_nli.core.response_generator`

## Classes

### ResponseGenerator

#### __init__()

Initialize the response generator with optional LLM integration

#### set_ollama_client(ollama_client)

Set the Ollama client for enhanced responses

#### set_huggingface_client(huggingface_client)

Set the Hugging Face client for enhanced responses

#### generate_response(query, intent, result)

Generate a natural language response

