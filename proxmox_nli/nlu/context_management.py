class ContextManager:
    def __init__(self):
        self.conversation_history = []
        self.context = {
            'current_vm': None,
            'current_node': None,
            'current_container': None,
            'last_intent': None,
            'last_entities': None,
            'favorite_vms': [],
            'favorite_nodes': [],
            'quick_services': [],
            'user_preferences': {}
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

    def set_context(self, context_data):
        """Set specific context values
        
        Args:
            context_data: Dictionary of context values to update
        """
        for key, value in context_data.items():
            self.context[key] = value

    def resolve_contextual_references(self, query, entities):
        """Resolve contextual references like 'it', 'that one', 'this vm', etc."""
        # List of pronouns and references to resolve
        contextual_refs = ['it', 'that', 'this', 'the vm', 'the machine', 'that one', 'this one']
        
        query_lower = query.lower()
        has_contextual_ref = any(ref in query_lower for ref in contextual_refs)
        
        # Resolve references using current context
        if has_contextual_ref and self.context['current_vm'] and 'VM_ID' not in entities:
            # If query has contextual reference and we have a VM in context, use it
            entities['VM_ID'] = self.context['current_vm']
        
        if has_contextual_ref and self.context['current_container'] and 'CONTAINER_NAME' not in entities:
            # If query has contextual reference and we have a container in context, use it
            entities['CONTAINER_NAME'] = self.context['current_container']
        
        if 'there' in query_lower and self.context['current_node'] and 'NODE' not in entities:
            # Resolve location references
            entities['NODE'] = self.context['current_node']
            
        # Enhance resolution with user preferences if no specific entity was found
        if 'VM_ID' not in entities:
            # Try to infer VM from query based on frequently used VMs
            entities = self._infer_vm_from_query(query_lower, entities)
        
        if 'NODE' not in entities:
            # Try to infer node from query based on frequently used nodes
            entities = self._infer_node_from_query(query_lower, entities)
            
        # For service-related queries, try to use most recent or favorite service
        if 'SERVICE_ID' not in entities and any(kw in query_lower for kw in ['service', 'app', 'application']):
            entities = self._infer_service_from_query(query_lower, entities)
        
        return entities
        
    def _infer_vm_from_query(self, query_lower, entities):
        """Try to infer VM ID from the query using favorites and user history"""
        # If there are favorite VMs, try to match based on VM names or descriptions
        if self.context.get('favorite_vms') and 'VM_ID' not in entities:
            # Check if the query contains an implicit reference to a favorite VM
            for vm in self.context['favorite_vms']:
                if vm.get('vm_name') and vm['vm_name'].lower() in query_lower:
                    entities['VM_ID'] = vm['vm_id']
                    entities['VM_NAME'] = vm['vm_name']
                    break
            
            # If no match and there's only one favorite VM, and the query seems to need a VM
            if 'VM_ID' not in entities and len(self.context['favorite_vms']) == 1:
                vm_keywords = ['vm', 'machine', 'virtual', 'on', 'server']
                if any(kw in query_lower for kw in vm_keywords):
                    entities['VM_ID'] = self.context['favorite_vms'][0]['vm_id']
                    if self.context['favorite_vms'][0].get('vm_name'):
                        entities['VM_NAME'] = self.context['favorite_vms'][0]['vm_name']
        
        return entities
        
    def _infer_node_from_query(self, query_lower, entities):
        """Try to infer node name from the query using favorites and user history"""
        # If there are favorite nodes, try to match based on node names
        if self.context.get('favorite_nodes') and 'NODE' not in entities:
            # Check if the query contains an implicit reference to a favorite node
            for node in self.context['favorite_nodes']:
                if node['node_name'].lower() in query_lower:
                    entities['NODE'] = node['node_name']
                    break
            
            # If no match and there's only one favorite node, and the query seems to need a node
            if 'NODE' not in entities and len(self.context['favorite_nodes']) == 1:
                node_keywords = ['node', 'host', 'server', 'cluster']
                if any(kw in query_lower for kw in node_keywords):
                    entities['NODE'] = self.context['favorite_nodes'][0]['node_name']
        
        return entities
        
    def _infer_service_from_query(self, query_lower, entities):
        """Try to infer service ID from the query using quick access services"""
        # If there are quick access services, try to match
        if self.context.get('quick_services') and 'SERVICE_ID' not in entities:
            # If we have only one service, use it for service-related queries
            if len(self.context['quick_services']) == 1:
                service_keywords = ['service', 'app', 'application', 'container', 'deployed']
                if any(kw in query_lower for kw in service_keywords):
                    entities['SERVICE_ID'] = self.context['quick_services'][0]['service_id']
                    if self.context['quick_services'][0]['vm_id']:
                        entities['VM_ID'] = self.context['quick_services'][0]['vm_id']
        
        return entities
