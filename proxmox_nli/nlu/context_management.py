import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        """Initialize the context manager with default values"""
        self.conversation_history = []
        self.context = {
            'current_vm': None,
            'current_vm_name': None,
            'current_node': None,
            'current_container': None,
            'current_service': None,
            'current_service_vm': None,
            'last_intent': None,
            'last_entities': None,
            'last_query_time': None,
            'session_start_time': datetime.now(),
            'favorite_vms': [],
            'favorite_nodes': [],
            'quick_services': [],
            'user_preferences': {}
        }
        
        # Define reference resolution patterns
        self.reference_patterns = {
            'VM_ID': [
                r'it', r'that vm', r'this vm', r'that machine', r'this machine',
                r'that one', r'this one', r'the vm', r'the machine', r'the server',
            ],
            'NODE': [
                r'that node', r'this node', r'there', r'that host', r'this host',
                r'that server', r'this server', r'the node', r'the host', r'the server'
            ],
            'CONTAINER_NAME': [
                r'that container', r'this container', r'it', r'that one', 'this one',
                r'the container'
            ],
            'SERVICE_NAME': [
                r'that service', r'this service', r'it', r'that app', r'this app',
                r'the service', r'the application'
            ]
        }
        
        # Track context significance weights
        self.context_weights = {
            'current_vm': 1.0,
            'current_node': 0.8,
            'current_container': 0.7,
            'current_service': 0.9
        }
        
        # Track context decay (seconds until context becomes less relevant)
        self.context_decay_time = 300  # 5 minutes
        
    def update_context(self, intent, entities):
        """Update the conversation context
        
        Args:
            intent: The identified intent
            entities: Dictionary of entities extracted from the query
        """
        # Update basic context
        self.context['last_intent'] = intent
        self.context['last_entities'] = entities
        self.context['last_query_time'] = datetime.now()

        # Update specific context based on the intent and entities
        if 'VM_ID' in entities:
            self.context['current_vm'] = entities['VM_ID']
            if 'VM_NAME' in entities:
                self.context['current_vm_name'] = entities['VM_NAME']
        
        if 'NODE' in entities:
            self.context['current_node'] = entities['NODE']
        
        if 'CONTAINER_NAME' in entities:
            self.context['current_container'] = entities['CONTAINER_NAME']
        
        if 'SERVICE_NAME' in entities:
            self.context['current_service'] = entities['SERVICE_NAME']
            if 'VM_ID' in entities:
                self.context['current_service_vm'] = entities['VM_ID']

        # Add to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'intent': intent,
            'entities': entities,
            'context': self._get_current_context_snapshot()
        })
        
        # Keep only last 10 interactions for context
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)
            
        # Ensure favorite VMs list contains unique entries
        if 'VM_ID' in entities and entities['VM_ID']:
            self._update_favorites('vm', entities['VM_ID'], entities.get('VM_NAME'))
    
    def set_context(self, context_data):
        """Set specific context values
        
        Args:
            context_data: Dictionary of context values to update
        """
        for key, value in context_data.items():
            if key in self.context:
                self.context[key] = value
                logger.info(f"Updated context: {key} = {value}")
    
    def resolve_contextual_references(self, query, entities):
        """Resolve contextual references like 'it', 'that one', 'this vm', etc.
        
        Args:
            query: The original user query
            entities: Dictionary of already extracted entities
            
        Returns:
            Updated entities dictionary with resolved references
        """
        # Check if the query contains contextual references
        query_lower = query.lower()
        
        # Track which entity types need resolution
        needs_resolution = {}
        
        # Check for contextual references for each entity type
        for entity_type, patterns in self.reference_patterns.items():
            # If the entity is not already present and we have a reference to it
            if entity_type not in entities and any(re.search(rf'\b{pattern}\b', query_lower) for pattern in patterns):
                needs_resolution[entity_type] = True
        
        # If we have context and need to resolve references
        if needs_resolution:
            # Resolve VM_ID references
            if 'VM_ID' in needs_resolution and self.context['current_vm']:
                entities['VM_ID'] = self.context['current_vm']
                if self.context['current_vm_name']:
                    entities['VM_NAME'] = self.context['current_vm_name']
            
            # Resolve NODE references
            if 'NODE' in needs_resolution and self.context['current_node']:
                entities['NODE'] = self.context['current_node']
            
            # Resolve CONTAINER_NAME references
            if 'CONTAINER_NAME' in needs_resolution and self.context['current_container']:
                entities['CONTAINER_NAME'] = self.context['current_container']
            
            # Resolve SERVICE_NAME references
            if 'SERVICE_NAME' in needs_resolution and self.context['current_service']:
                entities['SERVICE_NAME'] = self.context['current_service']
                if self.context['current_service_vm']:
                    entities['VM_ID'] = self.context['current_service_vm']
            
        # Try more advanced resolution for missing entities
        if 'VM_ID' not in entities:
            entities = self._infer_vm_from_query(query_lower, entities)
        
        if 'NODE' not in entities:
            entities = self._infer_node_from_query(query_lower, entities)
        
        if 'SERVICE_NAME' not in entities and any(kw in query_lower for kw in ['service', 'app', 'application']):
            entities = self._infer_service_from_query(query_lower, entities)
        
        # If intent implies continuation of previous command, provide relevant context
        if self.context['last_intent'] and len(self.conversation_history) > 1:
            entities = self._infer_continuation_context(query_lower, entities)
            
        return entities
    
    def _get_current_context_snapshot(self):
        """Get a snapshot of the current context for history"""
        return {
            'current_vm': self.context['current_vm'],
            'current_vm_name': self.context['current_vm_name'],
            'current_node': self.context['current_node'],
            'current_container': self.context['current_container'],
            'current_service': self.context['current_service']
        }
    
    def _update_favorites(self, item_type, item_id, item_name=None):
        """Update favorite items based on usage frequency"""
        if item_type == 'vm':
            # Check if VM already in favorites
            vm_exists = False
            for vm in self.context['favorite_vms']:
                if vm['vm_id'] == item_id:
                    vm['count'] += 1
                    vm_exists = True
                    if item_name and not vm.get('vm_name'):
                        vm['vm_name'] = item_name
                    break
            
            # Add new VM to favorites
            if not vm_exists:
                self.context['favorite_vms'].append({
                    'vm_id': item_id,
                    'vm_name': item_name,
                    'count': 1,
                    'last_used': datetime.now()
                })
            
            # Sort by usage count (most used first)
            self.context['favorite_vms'] = sorted(
                self.context['favorite_vms'],
                key=lambda x: x['count'],
                reverse=True
            )
    
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
        if self.context.get('quick_services') and 'SERVICE_NAME' not in entities:
            # Try to match service name in query
            for service in self.context['quick_services']:
                if service['service_name'].lower() in query_lower:
                    entities['SERVICE_NAME'] = service['service_name']
                    if service.get('vm_id'):
                        entities['VM_ID'] = service['vm_id']
                    break
                
            # If no match and there's only one service, use it for service-related queries
            if 'SERVICE_NAME' not in entities and len(self.context['quick_services']) == 1:
                service_keywords = ['service', 'app', 'application', 'container', 'deployed']
                if any(kw in query_lower for kw in service_keywords):
                    entities['SERVICE_NAME'] = self.context['quick_services'][0]['service_name']
                    if self.context['quick_services'][0].get('vm_id'):
                        entities['VM_ID'] = self.context['quick_services'][0]['vm_id']
        
        return entities
    
    def _infer_continuation_context(self, query_lower, entities):
        """Infer context from conversation continuation patterns"""
        # Words that suggest continuation of previous actions
        continuation_words = ['again', 'also', 'too', 'as well', 'same', 'like before', 'similarly']
        
        # Check if query seems to be a continuation
        is_continuation = any(word in query_lower for word in continuation_words)
        
        if is_continuation and self.conversation_history:
            # Get previous interaction
            prev_interaction = self.conversation_history[-1]
            prev_entities = prev_interaction.get('entities', {})
            
            # Copy relevant context entities if they're missing from current entities
            for key in ['VM_ID', 'NODE', 'CONTAINER_NAME', 'SERVICE_NAME']:
                if key not in entities and key in prev_entities:
                    entities[key] = prev_entities[key]
                    
            # For related intents (like start_vm -> stop_vm, create_vm -> delete_vm)
            # Copy the relevant entity from previous context
            related_intent_pairs = [
                ('start_', 'stop_'), ('create_', 'delete_'),
                ('deploy_', 'remove_'), ('show_', 'hide_')
            ]
            
            # If this is a related action to the previous one, maintain context
            curr_prefix = self.context['last_intent'].split('_')[0] + '_' if self.context['last_intent'] else ''
            for prefix_a, prefix_b in related_intent_pairs:
                if (curr_prefix == prefix_a and prev_interaction['intent'].startswith(prefix_b)) or \
                   (curr_prefix == prefix_b and prev_interaction['intent'].startswith(prefix_a)):
                    # Copy relevant entities from previous interaction
                    for key, value in prev_entities.items():
                        if key not in entities:
                            entities[key] = value
                        
        return entities
    
    def get_conversation_summary(self):
        """Generate a summary of the conversation history"""
        if not self.conversation_history:
            return "No conversation history available."
        
        recent_history = self.conversation_history[-5:]  # Last 5 interactions
        
        summary = []
        for i, interaction in enumerate(recent_history):
            timestamp = interaction.get('timestamp', '').strftime('%H:%M:%S') if interaction.get('timestamp') else 'Unknown'
            intent = interaction.get('intent', 'unknown')
            entities_str = ', '.join([f"{k}: {v}" for k, v in interaction.get('entities', {}).items()])
            
            summary.append(f"[{timestamp}] Intent: {intent}, Entities: {entities_str}")
        
        return "\n".join(summary)
    
    def get_active_context(self):
        """Get the currently active context information"""
        active = {}
        
        # Include only non-None values from context
        for key, value in self.context.items():
            if value is not None and key not in ['favorite_vms', 'favorite_nodes', 'quick_services', 'user_preferences']:
                active[key] = value
        
        return active
    
    def save_context(self, filepath):
        """Save the current context to a file"""
        try:
            # Convert datetime objects to strings
            context_copy = self.context.copy()
            if context_copy.get('last_query_time'):
                context_copy['last_query_time'] = context_copy['last_query_time'].isoformat()
            if context_copy.get('session_start_time'):
                context_copy['session_start_time'] = context_copy['session_start_time'].isoformat()
            
            # Prepare history for serialization
            history_copy = []
            for item in self.conversation_history:
                item_copy = item.copy()
                if item_copy.get('timestamp'):
                    item_copy['timestamp'] = item_copy['timestamp'].isoformat()
                history_copy.append(item_copy)
            
            # Combined data to save
            data = {
                'context': context_copy,
                'history': history_copy
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")
            return False
    
    def load_context(self, filepath):
        """Load context from a file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Load context
            self.context = data.get('context', {})
            
            # Convert string dates back to datetime objects
            if self.context.get('last_query_time'):
                try:
                    self.context['last_query_time'] = datetime.fromisoformat(self.context['last_query_time'])
                except ValueError:
                    self.context['last_query_time'] = datetime.now()
            
            if self.context.get('session_start_time'):
                try:
                    self.context['session_start_time'] = datetime.fromisoformat(self.context['session_start_time'])
                except ValueError:
                    self.context['session_start_time'] = datetime.now()
            
            # Load history
            self.conversation_history = data.get('history', [])
            
            # Convert string dates in history
            for item in self.conversation_history:
                if item.get('timestamp'):
                    try:
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                    except ValueError:
                        item['timestamp'] = datetime.now()
            
            return True
        except Exception as e:
            logger.error(f"Error loading context: {str(e)}")
            return False
