# core_nli

Core NLI module providing the main interface for Proxmox natural language processing.

**Module Path**: `proxmox_nli.core.core_nli`

## Classes

### ProxmoxNLI

#### __init__(host, user, password, realm, verify_ssl = 'pam')

Initialize the Proxmox NLI with all components

#### execute_intent(intent, args, entities)

Execute the identified intent

#### confirm_command(confirmed)

Handle command confirmation

#### process_query(query, user, source = None, ip_address = 'cli')

Process a natural language query and execute the corresponding action.

Args:
    query: The natural language query
    user: The user who made the query
    source: The source of the query (e.g., cli, web, voice)
    ip_address: The IP address of the user (for web queries)
    
Returns:
    str: The response to the query

**Returns**: `str: The response to the query`

#### get_recent_activity(limit)

Get recent audit logs with the specified limit

