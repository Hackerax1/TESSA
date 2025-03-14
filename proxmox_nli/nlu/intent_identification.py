import re
from nltk.tokenize import word_tokenize

class IntentIdentifier:
    def __init__(self):
        """Initialize intent patterns and context"""
        self.context = {
            'current_vm': None,
            'current_container': None,
            'current_vm_name': None,
            'current_node': None,
            'current_service': None,
            'current_service_vm': None,
            'last_intent': None
        }

        # Command patterns
        self.patterns = {
            'list_vms': [
                r'list\s+(?:all\s+)?(?:virtual\s+)?(?:machines|vms)',
                r'show\s+(?:all\s+)?(?:virtual\s+)?(?:machines|vms)',
                r'get\s+(?:all\s+)?(?:virtual\s+)?(?:machines|vms)'
            ],
            'start_vm': [
                r'(?:start|boot|launch|power\s+on)\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)',
                r'(?:turn|power)\s+on\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)'
            ],
            'stop_vm': [
                r'(?:stop|shutdown|halt)\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)',
                r'(?:turn|power)\s+off\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)'
            ],
            'restart_vm': [
                r'(?:restart|reboot)\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)'
            ],
            'vm_status': [
                r'(?:status|check)\s+(?:of\s+)?(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)',
                r'(?:how|what)\s+is\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)(?:\s+doing)?'
            ],
            'create_vm': [
                r'create\s+(?:a\s+)?(?:new\s+)?(?:vm|virtual\s+machine)(?:\s+(?:called|named)\s+([a-zA-Z0-9-_]+))?',
                r'new\s+(?:vm|virtual\s+machine)(?:\s+(?:called|named)\s+([a-zA-Z0-9-_]+))?'
            ],
            'delete_vm': [
                r'delete\s+(?:vm|virtual\s+machine)\s+(\w+)',
                r'remove\s+(?:vm|virtual\s+machine)\s+(\w+)'
            ],
            'list_containers': [
                r'list\s+(?:all\s+)?(?:containers|cts|lxc)',
                r'show\s+(?:all\s+)?(?:containers|cts|lxc)'
            ],
            'cluster_status': [
                r'(?:show|get)\s+cluster\s+status',
                r'(?:how|what)\s+is\s+(?:the\s+)?cluster(?:\s+doing)?'
            ],
            'node_status': [
                r'(?:show|get)\s+(?:status\s+of\s+)?node\s+(\w+)',
                r'(?:how|what)\s+is\s+node\s+(\w+)(?:\s+doing)?'
            ],
            'storage_info': [
                r'(?:show|get)\s+storage\s+info(?:rmation)?',
                r'(?:how|what)\s+(?:is|about)\s+(?:the\s+)?storage'
            ],
            'list_docker_containers': [
                r'list\s+(?:all\s+)?docker\s+containers(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'show\s+(?:all\s+)?docker\s+containers(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'start_docker_container': [
                r'start\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'run\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'stop_docker_container': [
                r'stop\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'halt\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'docker_container_logs': [
                r'(?:show|get|display)\s+(?:logs|log)\s+(?:for|from)\s+docker\s+container\s+(\w+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'docker\s+container\s+(\w+)\s+logs(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'list_docker_images': [
                r'list\s+(?:all\s+)?docker\s+images(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'show\s+(?:all\s+)?docker\s+images(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'pull_docker_image': [
                r'pull\s+docker\s+image\s+(\S+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'download\s+docker\s+image\s+(\S+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'run_docker_container': [
                r'run\s+(?:a\s+)?(?:new\s+)?docker\s+container(?:\s+with|using)\s+image\s+(\S+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'create\s+(?:a\s+)?(?:new\s+)?docker\s+container(?:\s+with|using)\s+image\s+(\S+)(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'run_cli_command': [
                r'run\s+command\s+"([^"]+)"(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'execute\s+command\s+"([^"]+)"(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'run\s+command\s+\'([^\']+)\'(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'execute\s+command\s+\'([^\']+)\'(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'run\s+\'([^\']+)\'(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'execute\s+\'([^\']+)\'(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'run\s+"([^"]+)"(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'execute\s+"([^"]+)"(?:\s+on\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'list_available_services': [
                r'list\s+(?:all\s+)?(?:available\s+)?services',
                r'show\s+(?:all\s+)?(?:available\s+)?services',
                r'what\s+services\s+(?:are|can\s+you)\s+(?:available|install|deploy)',
                r'what\s+can\s+(?:I|you)\s+install'
            ],
            'find_service': [
                r'find\s+(?:a\s+)?service\s+(?:for|to)\s+(.+)',
                r'search\s+(?:for\s+)?(?:a\s+)?service\s+(?:for|to)\s+(.+)',
                r'(?:I\s+want|I\'d\s+like)\s+(?:a\s+)?(?:service\s+)?(?:for|to)\s+(.+)',
                r'(?:I\s+want|I\'d\s+like|I\s+need)\s+(?:to\s+)?(?:install|setup|deploy)\s+(?:a\s+)?(.+)',
                r'help\s+me\s+(?:setup|install|deploy)\s+(?:a\s+)?(.+)'
            ],
            'deploy_service': [
                r'deploy\s+(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'install\s+(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'setup\s+(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'service_status': [
                r'(?:show|get|what\s+is)\s+(?:the\s+)?status\s+(?:of\s+)?(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'stop_service': [
                r'stop\s+(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'halt\s+(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'remove_service': [
                r'remove\s+(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'uninstall\s+(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?',
                r'delete\s+(?:service\s+)?(\w+)(?:\s+(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+))?'
            ],
            'list_deployed_services': [
                r'list\s+(?:all\s+)?(?:my\s+)?(?:deployed|installed)\s+services',
                r'show\s+(?:all\s+)?(?:my\s+)?(?:deployed|installed)\s+services',
                r'what\s+services\s+(?:are|do\s+I\s+have)\s+(?:running|deployed|installed)'
            ],
            # Update-related patterns
            'check_updates': [
                r'check\s+(?:for\s+)?(?:available\s+)?updates(?:\s+for\s+(?:service\s+)?([a-zA-Z0-9-_]+))?',
                r'see\s+(?:if\s+there\s+are\s+)?(?:any\s+)?(?:available\s+)?updates(?:\s+for\s+(?:service\s+)?([a-zA-Z0-9-_]+))?',
                r'are\s+there\s+(?:any\s+)?updates(?:\s+for\s+(?:service\s+)?([a-zA-Z0-9-_]+))?',
                r'(?:any|find)\s+updates(?:\s+for\s+(?:service\s+)?([a-zA-Z0-9-_]+))?'
            ],
            'list_updates': [
                r'list\s+(?:all\s+)?(?:available\s+)?updates(?:\s+for\s+(?:service\s+)?([a-zA-Z0-9-_]+))?',
                r'show\s+(?:all\s+)?(?:available\s+)?updates(?:\s+for\s+(?:service\s+)?([a-zA-Z0-9-_]+))?',
                r'what\s+updates\s+(?:are|do\s+I\s+have)(?:\s+(?:available|for)\s+(?:service\s+)?([a-zA-Z0-9-_]+))?'
            ],
            'apply_updates': [
                r'apply\s+(?:all\s+)?updates(?:\s+(?:for|to)\s+(?:service\s+)?([a-zA-Z0-9-_]+))?',
                r'install\s+(?:all\s+)?updates(?:\s+(?:for|to)\s+(?:service\s+)?([a-zA-Z0-9-_]+))?',
                r'update\s+(?:service\s+)?([a-zA-Z0-9-_]+)',
                r'upgrade\s+(?:service\s+)?([a-zA-Z0-9-_]+)',
                r'update\s+all\s+services',
                r'upgrade\s+all\s+services',
                r'install\s+all\s+(?:available\s+)?updates'
            ],
            'update_settings': [
                r'(?:change|update|set|configure)\s+update\s+settings',
                r'(?:enable|disable|turn\s+on|turn\s+off)\s+automatic\s+updates',
                r'set\s+update\s+check\s+interval\s+(?:to\s+)?(\d+)(?:\s+hours)?',
                r'configure\s+update\s+(?:options|preferences|settings)'
            ],
            'get_update_status': [
                r'(?:get|show)\s+update\s+status',
                r'check\s+update\s+settings',
                r'show\s+update\s+configuration',
                r'(?:what|how)\s+(?:are|is)\s+(?:the\s+)?update\s+settings'
            ],
            'help': [
                r'help',
                r'commands',
                r'what\s+can\s+you\s+do',
                r'usage'
            ],
            'create_zfs_pool': [
                r'create\s+pool',
                r'make\s+pool',
                r'new\s+pool',
                r'setup\s+pool'
            ],
            'list_zfs_pools': [
                r'list\s+pools',
                r'show\s+pools',
                r'get\s+pools'
            ],
            'create_zfs_dataset': [
                r'create\s+dataset',
                r'new\s+dataset',
                r'make\s+dataset'
            ],
            'list_zfs_datasets': [
                r'list\s+datasets',
                r'show\s+datasets',
                r'get\s+datasets'
            ],
            'set_zfs_properties': [
                r'set\s+(?:property|properties|option|options)'
            ],
            'create_zfs_snapshot': [
                r'create\s+snapshot',
                r'take\s+snapshot',
                r'make\s+snapshot'
            ],
            'setup_zfs_auto_snapshots': [
                r'setup\s+auto\s+snapshot',
                r'configure\s+snapshot',
                r'enable\s+snapshots'
            ]
        }

    def identify_intent(self, preprocessed_query):
        """Identify the intent of the query"""
        # First check for contextual commands using pronouns
        query_lower = preprocessed_query.lower()
        tokens = set(word_tokenize(preprocessed_query))

        # Handle contextual commands using pronouns
        if ('it' in tokens or 'its' in tokens or 'this' in tokens or 'that' in tokens) and self.context.get('current_vm'):
            if any(word in tokens for word in ['start', 'boot', 'launch', 'power on']):
                return 'start_vm', [self.context['current_vm']]
            elif any(word in tokens for word in ['stop', 'shutdown', 'halt', 'power off']):
                return 'stop_vm', [self.context['current_vm']]
            elif any(word in tokens for word in ['status', 'check', 'how is']):
                return 'vm_status', [self.context['current_vm']]
            elif any(word in tokens for word in ['restart', 'reboot']):
                return 'restart_vm', [self.context['current_vm']]

        # Try exact pattern matching
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, preprocessed_query, re.IGNORECASE)
                if match:
                    # Convert tuple to list for consistency
                    args = list(match.groups()) if match.groups() else []
                    return intent, args

        # If no pattern matches, try more flexible keyword matching
        if 'list' in tokens and ('vm' in tokens or 'vms' in tokens or 'machine' in tokens or 'machines' in tokens):
            return 'list_vms', []

        if 'start' in tokens and ('vm' in tokens or 'machine' in tokens):
            # Try to extract VM name/ID
            vm_match = re.search(r'(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)', preprocessed_query)
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

        # Service related intents
        if ('list' in tokens or 'show' in tokens) and 'service' in tokens and not ('deployed' in tokens or 'installed' in tokens):
            return 'list_available_services', []

        if ('list' in tokens or 'show' in tokens) and 'service' in tokens and ('deployed' in tokens or 'installed' in tokens):
            return 'list_deployed_services', []

        if ('find' in tokens or 'search' in tokens) and 'service' in tokens:
            service_match = re.search(r'(?:for|to)\s+(.+)$', preprocessed_query)
            return 'find_service', [service_match.group(1) if service_match else None]

        # Update related intents
        if ('check' in tokens or 'search' in tokens) and 'update' in tokens:
            service_match = re.search(r'for\s+(?:service\s+)?(\w+)', preprocessed_query)
            return 'check_updates', [service_match.group(1) if service_match else None]

        if ('list' in tokens or 'show' in tokens) and 'update' in tokens:
            service_match = re.search(r'for\s+(?:service\s+)?(\w+)', preprocessed_query)
            return 'list_updates', [service_match.group(1) if service_match else None]

        if ('apply' in tokens or 'install' in tokens) and 'update' in tokens:
            service_match = re.search(r'(?:for|to)\s+(?:service\s+)?(\w+)', preprocessed_query)
            return 'apply_updates', [service_match.group(1) if service_match else None]

        if ('update' in tokens and 'settings' in tokens) or ('configure' in tokens and 'update' in tokens):
            return 'update_settings', []

        if any(word in tokens for word in ['want', 'need', 'like', 'looking']):
            if any(word in tokens for word in ['install', 'setup', 'deploy']):
                return 'find_service', [preprocessed_query]
            else:
                # This is a more generic "I want X" request that might be service-related
                return 'find_service', [preprocessed_query]

        if ('deploy' in tokens or 'install' in tokens or 'setup' in tokens) and not ('docker' in tokens) and not ('update' in tokens):
            # Try to extract service ID
            service_match = re.search(r'(?:deploy|install|setup)\s+(?:service\s+)?(\w+)', preprocessed_query)
            vm_match = re.search(r'(?:on|to)\s+(?:vm|virtual\s+machine)\s+(\w+)', preprocessed_query)
            return 'deploy_service', [service_match.group(1) if service_match else None, vm_match.group(1) if vm_match else None]

        # Simple update command
        if ('update' in tokens or 'upgrade' in tokens) and not ('settings' in tokens or 'configuration' in tokens):
            # Check for "update all" pattern
            if 'all' in tokens:
                return 'apply_updates', [None]
            # Check for "update X" pattern
            service_match = re.search(r'(?:update|upgrade)\s+(?:service\s+)?(\w+)', preprocessed_query)
            if service_match:
                return 'apply_updates', [service_match.group(1)]
        
        # Update status check
        if ('status' in tokens or 'settings' in tokens) and 'update' in tokens:
            return 'get_update_status', []

        # Handle contextual commands like "start it" or "check its status"
        if 'it' in tokens or 'its' in tokens:
            if 'start' in tokens and self.context.get('current_vm'):
                return 'start_vm', [self.context['current_vm']]
            elif ('stop' in tokens or 'shutdown' in tokens) and self.context.get('current_vm'):
                return 'stop_vm', [self.context['current_vm']]
            elif ('status' in tokens or 'check' in tokens) and self.context.get('current_vm'):
                return 'vm_status', [self.context['current_vm']]
            elif ('update' in tokens or 'upgrade' in tokens) and self.context.get('current_service'):
                return 'apply_updates', [self.context['current_service']]

        # Handle contextual commands for Docker containers
        if self.context.get('current_container') and self.context.get('current_vm'):
            if 'start' in tokens or 'run' in tokens:
                return 'start_docker_container', [self.context['current_container'], self.context['current_vm']]
            elif 'stop' in tokens or 'halt' in tokens:
                return 'stop_docker_container', [self.context['current_container'], self.context['current_vm']]
            elif 'logs' in tokens or 'log' in tokens:
                return 'docker_container_logs', [self.context['current_container'], self.context['current_vm']]

        # Handle contextual commands for services
        if self.context.get('current_service') and self.context.get('current_service_vm'):
            if 'status' in tokens or 'running' in tokens:
                return 'service_status', [self.context['current_service'], self.context['current_service_vm']]
            elif 'stop' in tokens or 'halt' in tokens:
                return 'stop_service', [self.context['current_service'], self.context['current_service_vm']]
            elif 'remove' in tokens or 'uninstall' in tokens or 'delete' in tokens:
                return 'remove_service', [self.context['current_service'], self.context['current_service_vm']]
            elif 'update' in tokens or 'upgrade' in tokens:
                return 'apply_updates', [self.context['current_service']]
            elif 'check' in tokens and 'update' in tokens:
                return 'check_updates', [self.context['current_service']]

        # Default to help intent if no other intent is identified
        return 'help', []
