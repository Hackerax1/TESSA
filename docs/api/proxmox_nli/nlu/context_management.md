# context_management

**Module Path**: `proxmox_nli.nlu.context_management`

## Classes

### ContextManager

#### __init__()

Initialize the context manager with default values

#### update_context(intent, entities)

Update the conversation context

Args:
    intent: The identified intent
    entities: Dictionary of entities extracted from the query

#### set_context(context_data)

Set specific context values

Args:
    context_data: Dictionary of context values to update

#### resolve_contextual_references(query, entities)

Resolve contextual references like 'it', 'that one', 'this vm', etc.

Args:
    query: The original user query
    entities: Dictionary of already extracted entities
    
Returns:
    Updated entities dictionary with resolved references

**Returns**: `Updated entities dictionary with resolved references`

#### get_conversation_summary()

Generate a summary of the conversation history

#### get_active_context()

Get the currently active context information

#### save_context(filepath)

Save the current context to a file

#### load_context(filepath)

Load context from a file

