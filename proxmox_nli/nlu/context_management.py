class ContextManager:
    def __init__(self):
        self.conversation_history = []
        self.context = {
            'current_vm': None,
            'current_node': None,
            'current_container': None,
            'last_intent': None,
            'last_entities': None
        }

    def update_context(self, intent, entities):
        """Update the conversation context"""
        self.context['last_intent'] = intent
        self.context['last_entities'] = entities

        # Update specific context based on the intent and entities
        if 'VM_ID' in entities:
            self.context['current_vm'] = entities['VM_ID']
        if 'NODE' in entities:
            self.context['current_node'] = entities['NODE']
        if 'CONTAINER_NAME' in entities:
            self.context['current_container'] = entities['CONTAINER_NAME']

        # Add to conversation history
        self.conversation_history.append({
            'intent': intent,
            'entities': entities
        })
        # Keep only last 5 interactions for context
        if len(self.conversation_history) > 5:
            self.conversation_history.pop(0)

    def resolve_contextual_references(self, query, entities):
        """Resolve contextual references like 'it', 'that one', 'this vm', etc."""
        # List of pronouns and references to resolve
        contextual_refs = ['it', 'that', 'this', 'the vm', 'the machine', 'that one', 'this one']
        
        query_lower = query.lower()
        has_contextual_ref = any(ref in query_lower for ref in contextual_refs)
        
        if has_contextual_ref and self.context['current_vm'] and 'VM_ID' not in entities:
            # If query has contextual reference and we have a VM in context, use it
            entities['VM_ID'] = self.context['current_vm']
        
        if has_contextual_ref and self.context['current_container'] and 'CONTAINER_NAME' not in entities:
            # If query has contextual reference and we have a container in context, use it
            entities['CONTAINER_NAME'] = self.context['current_container']
        
        if 'there' in query_lower and self.context['current_node'] and 'NODE' not in entities:
            # Resolve location references
            entities['NODE'] = self.context['current_node']
        
        return entities
