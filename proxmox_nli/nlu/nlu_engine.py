import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import spacy

# Download required NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

class NLU_Engine:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.conversation_history = []
        self.context = {
            'current_vm': None,
            'current_node': None,
            'current_container': None,
            'last_intent': None,
            'last_entities': None
        }
        
        # Command patterns
        self.patterns = {
            # VM related patterns
            'list_vms': [r'list\s+(?:all\s+)?(?:virtual\s+)?(?:machines|vms)', 
                         r'show\s+(?:all\s+)?(?:virtual\s+)?(?:machines|vms)', 
                         r'get\s+(?:all\s+)?(?:virtual\s+)?(?:machines|vms)'],
            'start_vm': [r'start\s+(?:vm|virtual\s+machine)\s+(\w+)', 
                         r'power\s+on\s+(?:vm|virtual\s+machine)\s+(\w+)'],
            'stop_vm': [r'stop\s+(?:vm|virtual\s+machine)\s+(\w+)', 
                        r'shutdown\s+(?:vm|virtual\s+machine)\s+(\w+)', 
                        r'power\s+off\s+(?:vm|virtual\s+machine)\s+(\w+)'],
            'restart_vm': [r'restart\s+(?:vm|virtual\s+machine)\s+(\w+)', 
                          r'reboot\s+(?:vm|virtual\s+machine)\s+(\w+)'],
            'vm_status': [r'status\s+(?:of\s+)?(?:vm|virtual\s+machine)\s+(\w+)', 
                         r'get\s+status\s+(?:of\s+)?(?:vm|virtual\s+machine)\s+(\w+)'],
            'create_vm': [r'create\s+(?:a\s+)?(?:new\s+)?(?:vm|virtual\s+machine)(?:\s+with\s+(.+))?'],
            'delete_vm': [r'delete\s+(?:vm|virtual\s+machine)\s+(\w+)', 
                         r'remove\s+(?:vm|virtual\s+machine)\s+(\w+)'],
            
            # Container related patterns
            'list_containers': [r'list\s+(?:all\s+)?(?:containers|cts|lxc)', 
                              r'show\s+(?:all\s+)?(?:containers|cts|lxc)'],
            
            # Cluster related patterns
            'cluster_status': [r'(?:show|get)\s+cluster\s+status', 
                             r'(?:how|what)\s+is\s+(?:the\s+)?cluster(?:\s+doing)?'],
            'node_status': [r'(?:show|get)\s+(?:status\s+of\s+)?node\s+(\w+)', 
                          r'(?:how|what)\s+is\s+node\s+(\w+)(?:\s+doing)?'],
            'storage_info': [r'(?:show|get)\s+storage\s+info(?:rmation)?', 
                           r'(?:how|what)\s+(?:is|about)\s+(?:the\s+)?storage'],
            
            # New Docker related patterns
            'list_docker_containers': [r'list\s+(?:all\s+)?docker\s+containers(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                                     r'show\s+(?:all\s+)?docker\s+containers(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'],
            'start_docker_container': [r'start\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                                     r'run\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'],
            'stop_docker_container': [r'stop\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                                    r'halt\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'],
            'docker_container_logs': [r'(?:show|get|display)\s+(?:logs|log)\s+(?:for|from)\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                                    r'docker\s+container\s+(\w+)\s+logs(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'],
            'list_docker_images': [r'list\s+(?:all\s+)?docker\s+images(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                                 r'show\s+(?:all\s+)?docker\s+images(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'],
            'pull_docker_image': [r'pull\s+docker\s+image\s+(\S+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                                r'download\s+docker\s+image\s+(\S+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'],
            'run_docker_container': [r'run\s+(?:a\s+)?(?:new\s+)?docker\s+container(?:\s+with|using)\s+image\s+(\S+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                                   r'create\s+(?:a\s+)?(?:new\s+)?docker\s+container(?:\s+with|using)\s+image\s+(\S+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'],
            
            # CLI command execution pattern
            'run_cli_command': [r'run\s+command\s+"([^"]+)"(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                              r'execute\s+command\s+"([^"]+)"(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                              r'run\s+command\s+\'([^\']+)\'(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                              r'execute\s+command\s+\'([^\']+)\'(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                              r'run\s+\'([^\']+)\'(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                              r'execute\s+\'([^\']+)\'(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                              r'run\s+"([^"]+)"(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                              r'execute\s+"([^"]+)"(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'],
            
            # Help pattern
            'help': [r'help', r'commands', r'what\s+can\s+you\s+do', r'usage']
        }
    
    def preprocess_query(self, query):
        """Preprocess the natural language query"""
        # Convert to lowercase
        query = query.lower()
        
        # Tokenize
        tokens = word_tokenize(query)
        
        # Remove stop words and lemmatize
        filtered_tokens = []
        for token in tokens:
            if token not in self.stop_words:
                filtered_tokens.append(self.lemmatizer.lemmatize(token))
        
        # Join back into a string
        preprocessed_query = ' '.join(filtered_tokens)
        
        return preprocessed_query
    
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

    def extract_entities(self, query):
        """Extract entities from the query using spaCy"""
        doc = nlp(query)
        entities = {}
        
        # Extract entities
        for ent in doc.ents:
            entities[ent.label_] = ent.text
        
        # Look for VM IDs, node names, etc.
        vm_match = re.search(r'(?:vm|virtual\s+machine)\s+(\w+)', query)
        if vm_match:
            entities['VM_ID'] = vm_match.group(1)
        
        node_match = re.search(r'node\s+(\w+)', query)
        if node_match:
            entities['NODE'] = node_match.group(1)
        
        # Extract Docker container names
        container_match = re.search(r'container\s+([a-zA-Z0-9_-]+)', query)
        if container_match:
            entities['CONTAINER_NAME'] = container_match.group(1)
        
        # Extract Docker image names
        image_match = re.search(r'image\s+([a-zA-Z0-9_/.-]+(?::[a-zA-Z0-9_.-]+)?)', query)
        if image_match:
            entities['IMAGE_NAME'] = image_match.group(1)
        
        # Extract CLI command
        command_match = re.search(r'(?:run|execute)\s+(?:command\s+)?[\'"]([^\'"]+)[\'"]', query)
        if command_match:
            entities['COMMAND'] = command_match.group(1)
        
        # Extract parameters for VM creation
        if 'create' in query and ('vm' in query or 'virtual machine' in query):
            params = {}
            # Extract RAM
            ram_match = re.search(r'(\d+)\s*(?:GB|G|mb|MB) (?:of )?(?:RAM|memory)', query)
            if ram_match:
                params['memory'] = int(ram_match.group(1))
                if 'mb' in ram_match.group(0).lower() or 'MB' in ram_match.group(0):
                    params['memory'] = params['memory']
                else:  # GB
                    params['memory'] = params['memory'] * 1024
            
            # Extract CPU cores
            cpu_match = re.search(r'(\d+)\s*(?:CPU|cpu|cores|processors)', query)
            if cpu_match:
                params['cores'] = int(cpu_match.group(1))
            
            # Extract disk size
            disk_match = re.search(r'(\d+)\s*(?:GB|G|TB|T) (?:of )?(?:disk|storage|hdd|ssd)', query)
            if disk_match:
                params['disk'] = int(disk_match.group(1))
                if 'TB' in disk_match.group(0) or 'T' in disk_match.group(0):
                    params['disk'] = params['disk'] * 1024
            
            # Extract OS/template
            os_match = re.search(r'(?:with|using|on)\s+(ubuntu|debian|centos|fedora|windows|alpine)', query, re.IGNORECASE)
            if os_match:
                params['template'] = os_match.group(1).lower()
            
            if params:
                entities['PARAMS'] = params
        
        # Extract parameters for Docker container run
        if ('run' in query or 'create' in query) and 'docker' in query and 'container' in query:
            params = {}
            
            # Extract ports
            ports = []
            ports_match = re.findall(r'port\s+(\d+:\d+)', query)
            for port in ports_match:
                ports.append(port)
            
            if ports:
                params['ports'] = ports
            
            # Extract volumes
            volumes = []
            volumes_match = re.findall(r'volume\s+([a-zA-Z0-9_/.-]+:[a-zA-Z0-9_/.-]+)', query)
            for volume in volumes_match:
                volumes.append(volume)
            
            if volumes:
                params['volumes'] = volumes
            
            # Extract environment variables
            env_vars = []
            env_match = re.findall(r'env\s+([a-zA-Z0-9_]+=[a-zA-Z0-9_.-]+)', query)
            for env in env_match:
                env_vars.append(env)
            
            if env_vars:
                params['environment'] = env_vars
            
            # Extract container name
            container_name_match = re.search(r'name\s+([a-zA-Z0-9_-]+)', query)
            if container_name_match:
                params['container_name'] = container_name_match.group(1)
            
            if params:
                entities['DOCKER_PARAMS'] = params
        
        # Resolve contextual references
        entities = self.resolve_contextual_references(query, entities)
        
        return entities
    
    def identify_intent(self, preprocessed_query):
        """Identify the intent of the query"""
        # First try exact pattern matching
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, preprocessed_query, re.IGNORECASE)
                if match:
                    return intent, match.groups()
        
        # If no pattern matches, try a more flexible approach using keywords
        tokens = set(word_tokenize(preprocessed_query))
        
        # VM related intents
        if 'list' in tokens and ('vm' in tokens or 'machine' in tokens):
            return 'list_vms', []
        
        if 'start' in tokens and ('vm' in tokens or 'machine' in tokens):
            # Try to extract VM ID
            vm_match = re.search(r'(\w+)', preprocessed_query.split('machine')[-1] if 'machine' in preprocessed_query else preprocessed_query.split('vm')[-1])
            return 'start_vm', [vm_match.group(1) if vm_match else None]
        
        # Docker related intents
        if 'list' in tokens and 'docker' in tokens and 'container' in tokens:
            return 'list_docker_containers', []
        
        if 'list' in tokens and 'docker' in tokens and 'image' in tokens:
            return 'list_docker_images', []
        
        if ('start' in tokens or 'run' in tokens) and 'docker' in tokens and 'container' in tokens:
            # Try to extract container name
            container_match = re.search(r'container\s+(\w+)', preprocessed_query)
            vm_match = re.search(r'vm\s+(\w+)', preprocessed_query)
            return 'start_docker_container', [container_match.group(1) if container_match else None, vm_match.group(1) if vm_match else None]
        
        # CLI command execution
        if ('run' in tokens or 'execute' in tokens) and ('command' in tokens or '"' in preprocessed_query or "'" in preprocessed_query):
            command_match = re.search(r'(?:run|execute)\s+(?:command\s+)?[\'"]([^\'"]+)[\'"]', preprocessed_query)
            vm_match = re.search(r'vm\s+(\w+)', preprocessed_query)
            return 'run_cli_command', [command_match.group(1) if command_match else None, vm_match.group(1) if vm_match else None]
        
        # Handle contextual commands like "start it" or "check its status"
        if self.context['current_vm']:
            if any(word in tokens for word in ['start', 'boot', 'power']):
                return 'start_vm', [self.context['current_vm']]
            elif any(word in tokens for word in ['stop', 'shutdown', 'halt']):
                return 'stop_vm', [self.context['current_vm']]
            elif any(word in tokens for word in ['restart', 'reboot']):
                return 'restart_vm', [self.context['current_vm']]
            elif any(word in tokens for word in ['status', 'check']):
                return 'vm_status', [self.context['current_vm']]
        
        # Handle contextual commands for Docker containers
        if self.context['current_container'] and self.context['current_vm']:
            if any(word in tokens for word in ['start', 'run']):
                return 'start_docker_container', [self.context['current_container'], self.context['current_vm']]
            elif any(word in tokens for word in ['stop', 'halt']):
                return 'stop_docker_container', [self.context['current_container'], self.context['current_vm']]
            elif any(word in tokens for word in ['logs', 'log']):
                return 'docker_container_logs', [self.context['current_container'], self.context['current_vm']]
        
        # Default if no intent is identified
        return 'unknown', []