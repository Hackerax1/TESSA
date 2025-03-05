import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize NLTK resources safely
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.warning(f"NLTK resource download failed: {str(e)}")

# Initialize lemmatizer and stop words with error handling
try:
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
except Exception as e:
    logger.warning(f"Failed to initialize NLTK components: {str(e)}")
    lemmatizer = None
    stop_words = set()

class EntityExtractor:
    def __init__(self):
        """Initialize entity extraction patterns and resources"""
        # Define known entity types for validation
        self.entity_types = {
            'VM_ID', 'NODE', 'CONTAINER_NAME', 'CONTAINER_ID', 'IMAGE_NAME', 'COMMAND',
            'SERVICE_NAME', 'PARAMS', 'DOCKER_PARAMS', 'POOL_NAME', 'DATASET_NAME',
            'DEVICES', 'RAID_LEVEL', 'SNAPSHOT_NAME', 'PROPERTIES', 'SCHEDULE',
            'RECURSIVE', 'BACKUP_ID', 'VM_NAME', 'NEW_VM_ID', 'PORT'
        }
        
        # Regex patterns for common entity extraction
        self.patterns = {
            'VM_ID': [
                r'(?:vm|virtual\s+machine)\s+(\w+)',
                r'vm[-_]?id\s*[=:]\s*(\w+)',
                r'\bvm[-_]?(\d+)\b'
            ],
            'VM_NAME': [
                r'(?:vm|virtual\s+machine)\s+(?:named|called)\s+["\']([^"\']+)["\']',
                r'["\']([^"\']+)["\']\s+(?:vm|virtual\s+machine)'
            ],
            'NODE': [
                r'node\s+(\w+)',
                r'(?:on|to|from)\s+(?:node|host|server)\s+(\w+)',
                r'node[-_]?id\s*[=:]\s*(\w+)'
            ],
            'CONTAINER_NAME': [
                r'container\s+(?:named|called)?\s+["\']?([a-zA-Z0-9_-]+)["\']?',
                r'container[-_]name\s*[=:]\s*["\']?([^"\']+)["\']?'
            ],
            'CONTAINER_ID': [
                r'container\s+(?:id|number)\s+(\d+)',
                r'container[-_]?id\s*[=:]\s*(\d+)',
                r'\bct[-_]?(\d+)\b'
            ],
            'IMAGE_NAME': [
                r'image\s+([a-zA-Z0-9_/.-]+(?::[a-zA-Z0-9_.-]+)?)',
                r'docker\s+image\s+([a-zA-Z0-9_/.-]+(?::[a-zA-Z0-9_.-]+)?)',
                r'using\s+(?:image|docker\s+image)\s+([a-zA-Z0-9_/.-]+(?::[a-zA-Z0-9_.-]+)?)'
            ],
            'SERVICE_NAME': [
                r'service\s+["\']?([a-zA-Z0-9_-]+)["\']?',
                r'deploy\s+["\']?([a-zA-Z0-9_-]+)["\']?',
                r'install\s+["\']?([a-zA-Z0-9_-]+)["\']?'
            ],
            'BACKUP_ID': [
                r'backup\s+(?:id|name)?\s+["\']?([a-zA-Z0-9_-]+)["\']?',
                r'from\s+backup\s+["\']?([a-zA-Z0-9_-]+)["\']?'
            ],
            'POOL_NAME': [
                r'pool\s+["\']?([a-zA-Z0-9\-_]+)["\']?',
                r'zfs\s+pool\s+["\']?([a-zA-Z0-9\-_]+)["\']?'
            ],
            'DATASET_NAME': [
                r'dataset\s+["\']?([a-zA-Z0-9\-_/]+)["\']?',
                r'zfs\s+dataset\s+["\']?([a-zA-Z0-9\-_/]+)["\']?'
            ],
            'SNAPSHOT_NAME': [
                r'snapshot\s+["\']?([a-zA-Z0-9\-_]+)["\']?',
                r'named\s+["\']?([a-zA-Z0-9\-_]+)["\']?(?:\s+snapshot)'
            ],
            'PORT': [
                r'port\s+(\d+)',
                r'on\s+port\s+(\d+)',
                r'ports?\s+(\d+(?::\d+)?)'
            ],
            'NEW_VM_ID': [
                r'new\s+(?:vm|id)\s+(\w+)',
                r'to\s+(?:vm|id)\s+(\w+)',
                r'as\s+(?:vm|id)\s+(\w+)'
            ]
        }
        
        # Common commands that might be executed
        self.common_commands = [
            'ls', 'cat', 'grep', 'ps', 'top', 'df', 'du', 'free', 'ifconfig',
            'ip', 'ping', 'netstat', 'systemctl', 'service', 'apt', 'apt-get',
            'yum', 'dnf', 'pacman', 'docker', 'docker-compose', 'kubectl'
        ]

    def extract_entities(self, query):
        """Extract entities from the query using regex patterns and NLTK"""
        entities = {}
        
        # Lowercase the query for case-insensitive matching
        query_lower = query.lower()
        
        # Tokenize and preprocess the query if NLTK is available
        if lemmatizer:
            try:
                tokens = word_tokenize(query_lower)
                filtered_tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
                preprocessed_query = ' '.join(filtered_tokens)
            except Exception as e:
                logger.warning(f"Tokenization failed: {str(e)}")
                preprocessed_query = query_lower
        else:
            # Fallback simple preprocessing
            preprocessed_query = query_lower
        
        # Extract entities using regex patterns
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, preprocessed_query, re.IGNORECASE)
                if match and match.group(1):
                    # Store the entity and break out of the pattern loop
                    entities[entity_type] = match.group(1).strip()
                    break
        
        # Extract command for execution
        if 'COMMAND' not in entities:
            # Look for commands in quotes
            command_match = re.search(r'(?:run|execute)\s+(?:command\s+)?[\'"]([^\'"]+)[\'"]', query)
            if command_match:
                entities['COMMAND'] = command_match.group(1)
            else:
                # Look for common command patterns at the beginning of a quote
                for cmd in self.common_commands:
                    cmd_match = re.search(r'[\'"](' + re.escape(cmd) + r'\s+[^\'"]*)[\'""]', query)
                    if cmd_match:
                        entities['COMMAND'] = cmd_match.group(1)
                        break
        
        # Extract parameters for VM creation
        if any(kw in preprocessed_query for kw in ['create vm', 'create virtual machine', 'new vm', 'new virtual machine']):
            params = self._extract_vm_creation_params(preprocessed_query)
            if params:
                entities['PARAMS'] = params
        
        # Extract parameters for Docker container run
        if any(kw in preprocessed_query for kw in ['run container', 'create container', 'docker container']):
            docker_params = self._extract_docker_params(preprocessed_query)
            if docker_params:
                entities['DOCKER_PARAMS'] = docker_params
        
        # Extract ZFS-related entities
        self._extract_zfs_entities(preprocessed_query, entities)
        
        # Extract lists of devices
        devices_match = re.findall(r'device[s]?\s+([/a-zA-Z0-9\-_\s,]+)', preprocessed_query, re.IGNORECASE)
        if devices_match:
            # Split devices by comma or space
            devices = re.split(r'[,\s]+', devices_match[0].strip())
            entities['DEVICES'] = [d for d in devices if d and d.startswith('/')]
        
        # If the query contains a recursive flag
        if 'recursive' in preprocessed_query:
            entities['RECURSIVE'] = True
            
        return entities
        
    def _extract_vm_creation_params(self, preprocessed_query):
        """Extract parameters for VM creation"""
        params = {}
        
        # Extract RAM
        ram_match = re.search(r'(\d+)\s*(?:GB|G|mb|MB|M)(?:\s+of)?(?:\s+RAM|\s+memory)?', preprocessed_query)
        if ram_match:
            memory = int(ram_match.group(1))
            unit = ram_match.group(0).lower()
            # Convert to MB
            if 'gb' in unit or 'g' in unit:
                memory = memory * 1024
            params['memory'] = memory
        
        # Extract CPU cores
        cpu_match = re.search(r'(\d+)\s*(?:CPU|cpu|core|cores|processor|processors)', preprocessed_query)
        if cpu_match:
            params['cores'] = int(cpu_match.group(1))
        
        # Extract disk size
        disk_match = re.search(r'(\d+)\s*(?:GB|G|TB|T)(?:\s+of)?(?:\s+disk|\s+storage|\s+hdd|\s+ssd)?', preprocessed_query)
        if disk_match:
            disk_size = int(disk_match.group(1))
            unit = disk_match.group(0).lower()
            # Convert to GB
            if 'tb' in unit or 't' in unit:
                disk_size = disk_size * 1024
            params['disk'] = disk_size
        
        # Extract OS/template
        templates = {
            'ubuntu': ['ubuntu', 'debian'],
            'centos': ['centos', 'rhel', 'redhat'],
            'debian': ['debian'],
            'alpine': ['alpine'],
            'windows': ['windows', 'win'],
            'fedora': ['fedora']
        }
        
        for template, keywords in templates.items():
            if any(kw in preprocessed_query for kw in keywords):
                params['template'] = template
                break
                
        # Extract OS version if specified
        version_match = re.search(r'(?:version|v)\s+(\d+(?:\.\d+)?)', preprocessed_query)
        if version_match and 'template' in params:
            params['version'] = version_match.group(1)
            
        return params if params else None
    
    def _extract_docker_params(self, preprocessed_query):
        """Extract parameters for Docker container creation"""
        params = {}
        
        # Extract ports with format port_host:port_container
        ports = []
        port_matches = re.findall(r'port\s+(\d+:\d+|\d+)', preprocessed_query)
        for port in port_matches:
            # If port is just a number, assume host:container are the same
            if ':' not in port:
                ports.append(f"{port}:{port}")
            else:
                ports.append(port)
        
        if ports:
            params['ports'] = ports
        
        # Extract volumes with format path_host:path_container
        volumes = []
        volume_matches = re.findall(r'volume\s+([a-zA-Z0-9_/.-]+:[a-zA-Z0-9_/.-]+)', preprocessed_query)
        for volume in volume_matches:
            volumes.append(volume)
        
        if volumes:
            params['volumes'] = volumes
        
        # Extract environment variables
        env_vars = []
        env_matches = re.findall(r'(?:env|environment|variable)\s+([a-zA-Z0-9_]+=[^,\s]+)', preprocessed_query)
        for env in env_matches:
            env_vars.append(env)
        
        if env_vars:
            params['environment'] = env_vars
        
        # Extract container name
        container_name_match = re.search(r'name\s+([a-zA-Z0-9_-]+)', preprocessed_query)
        if container_name_match:
            params['container_name'] = container_name_match.group(1)
        
        # Network mode
        network_match = re.search(r'network\s+(bridge|host|none|container:[a-zA-Z0-9_-]+)', preprocessed_query)
        if network_match:
            params['network'] = network_match.group(1)
            
        # Restart policy
        restart_match = re.search(r'restart\s+(always|on-failure|unless-stopped|no)', preprocessed_query)
        if restart_match:
            params['restart_policy'] = restart_match.group(1)
            
        return params if params else None
    
    def _extract_zfs_entities(self, preprocessed_query, entities):
        """Extract ZFS-specific entities"""
        # RAID level
        raid_levels = ['mirror', 'raidz', 'raidz1', 'raidz2', 'raidz3', 'stripe']
        for level in raid_levels:
            if level in preprocessed_query:
                entities['RAID_LEVEL'] = level
                break
        
        # Schedule for auto-snapshots
        schedules = ['hourly', 'daily', 'weekly', 'monthly', 'yearly']
        for schedule in schedules:
            if schedule in preprocessed_query:
                entities['SCHEDULE'] = schedule
                break
                
        # Properties
        properties = {}
        prop_matches = re.findall(r'(?:set|with)\s+([a-z:]+)=([a-zA-Z0-9]+)', preprocessed_query, re.IGNORECASE)
        if prop_matches:
            for prop, value in prop_matches:
                properties[prop] = value
            if properties:
                entities['PROPERTIES'] = properties
                
    def validate_entities(self, entities, intent):
        """Validate extracted entities against the required entities for the intent"""
        # Define required entities for each intent
        required_entities = {
            'start_vm': ['VM_ID'],
            'stop_vm': ['VM_ID'],
            'restart_vm': ['VM_ID'],
            'vm_status': ['VM_ID'],
            'delete_vm': ['VM_ID'],
            'clone_vm': ['VM_ID'],
            'snapshot_vm': ['VM_ID'],
            'start_container': ['CONTAINER_ID'],
            'stop_container': ['CONTAINER_ID'],
            'node_status': ['NODE'],
            'start_docker_container': ['CONTAINER_NAME', 'VM_ID'],
            'stop_docker_container': ['CONTAINER_NAME', 'VM_ID'],
            'docker_container_logs': ['CONTAINER_NAME', 'VM_ID'],
            'pull_docker_image': ['IMAGE_NAME', 'VM_ID'],
            'run_docker_container': ['IMAGE_NAME', 'VM_ID'],
            'run_cli_command': ['COMMAND', 'VM_ID'],
            'deploy_service': ['SERVICE_NAME'],
            'service_status': ['SERVICE_NAME'],
            'stop_service': ['SERVICE_NAME'],
            'start_service': ['SERVICE_NAME'],
            'create_zfs_pool': ['POOL_NAME', 'DEVICES'],
            'create_zfs_dataset': ['DATASET_NAME'],
            'create_zfs_snapshot': ['DATASET_NAME'],
            'backup_vm': ['VM_ID'],
            'restore_backup': ['BACKUP_ID']
        }
        
        if intent not in required_entities:
            # No validation needed for intents with no required entities
            return True, []
        
        missing = []
        for required in required_entities[intent]:
            if required not in entities:
                missing.append(required)
                
        return len(missing) == 0, missing
