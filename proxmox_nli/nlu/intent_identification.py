import re
from nltk.tokenize import word_tokenize

class IntentIdentifier:
    def __init__(self):
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
