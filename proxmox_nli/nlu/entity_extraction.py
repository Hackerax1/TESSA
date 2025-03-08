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
            'vm_name', 'node', 'container_name', 'container_id', 'image_name', 'command',
            'service_name', 'params', 'docker_params', 'pool_name', 'dataset_name',
            'devices', 'raid_level', 'snapshot_name', 'properties', 'schedule',
            'recursive', 'backup_id', 'source_vm', 'target_vm', 'port'
        }
        
        # Regex patterns for common entity extraction
        self.patterns = {
            'vm_name': [
                r'\b((?:vm|virtual\s*machine)?[-_]?\d+)\b',  # Matches vm-123, vm_123, 123
                r'(?:vm|virtual\s+machine)\s+(?:named|called)?\s*["\']?([^"\'\s]+)["\']?',  # Matches quoted or unquoted names
                r'(?:vm|virtual\s+machine)[-_]?id\s*[=:]\s*([^"\'\s]+)',  # Matches vm-id=value
                r'["\']([^"\']+)["\']\s+(?:vm|virtual\s+machine)'  # Matches quoted names before vm
            ],
            'node': [
                r'node\s+(\w+)',
                r'(?:on|to|from)\s+(?:node|host|server)\s+(\w+)',
                r'node[-_]?id\s*[=:]\s*(\w+)'
            ],
            'container_name': [
                r'container\s+(?:named|called)?\s+["\']?([a-zA-Z0-9_-]+)["\']?',
                r'container[-_]name\s*[=:]\s*["\']?([^"\']+)["\']?'
            ],
            'container_id': [
                r'container\s+(?:id|number)\s+(\d+)',
                r'container[-_]?id\s*[=:]\s*(\d+)',
                r'\bct[-_]?(\d+)\b'
            ],
            'image_name': [
                r'image\s+([a-zA-Z0-9_/.-]+(?::[a-zA-Z0-9_.-]+)?)',
                r'docker\s+image\s+([a-zA-Z0-9_/.-]+(?::[a-zA-Z0-9_.-]+)?)',
                r'using\s+(?:image|docker\s+image)\s+([a-zA-Z0-9_/.-]+(?::[a-zA-Z0-9_.-]+)?)'
            ],
            'service_name': [
                r'service\s+["\']?([a-zA-Z0-9_-]+)["\']?',
                r'deploy\s+["\']?([a-zA-Z0-9_-]+)["\']?',
                r'install\s+["\']?([a-zA-Z0-9_-]+)["\']?'
            ],
            'backup_id': [
                r'backup\s+(?:id|name)?\s+["\']?([a-zA-Z0-9_-]+)["\']?',
                r'from\s+backup\s+["\']?([a-zA-Z0-9_-]+)["\']?'
            ],
            'pool_name': [
                r'pool\s+["\']?([a-zA-Z0-9\-_]+)["\']?',
                r'zfs\s+pool\s+["\']?([a-zA-Z0-9\-_]+)["\']?'
            ],
            'dataset_name': [
                r'dataset\s+["\']?([a-zA-Z0-9\-_/]+)["\']?',
                r'zfs\s+dataset\s+["\']?([a-zA-Z0-9\-_/]+)["\']?'
            ],
            'snapshot_name': [
                r'snapshot\s+["\']?([a-zA-Z0-9\-_]+)["\']?',
                r'named\s+["\']?([a-zA-Z0-9\-_]+)["\']?(?:\s+snapshot)'
            ],
            'port': [
                r'port\s+(\d+)',
                r'on\s+port\s+(\d+)',
                r'ports?\s+(\d+(?::\d+)?)'
            ],
            'source_vm': [
                r'(?:clone|copy)\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)',
                r'from\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)'
            ],
            'target_vm': [
                r'(?:to|as|named?)\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)',
                r'(?:with|the)\s+name\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)'
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

        # First extract any VM parameters (memory, CPU, disk)
        if any(word in query_lower for word in ['with', 'using', 'having', 'gb', 'mb', 'ram', 'memory', 'cpu', 'core', 'cores']):
            params = self._extract_vm_creation_params(query_lower)
            if params:
                entities.update(params)

        # Special handling for clone/copy operations
        if any(word in query_lower for word in ['clone', 'copy']):
            # First try to find source VM
            source_match = re.search(r'(?:clone|copy)\s+(?:vm|virtual\s+machine)?[-_]?([a-zA-Z0-9-_]+)', query_lower)
            if source_match:
                source_value = source_match.group(1).strip()
                if not source_value.lower().startswith('vm-'):
                    source_value = f"vm-{source_value}"
                entities['source_vm'] = source_value
                entities['vm_name'] = source_value  # Use source VM as current context

            # Look for target VM after "to" or "as"
            target_match = re.search(r'\s+(?:to|as)\s+(?:vm[-_]?)?([a-zA-Z0-9-_]+)', query_lower)
            if target_match:
                target_value = target_match.group(1).strip()
                if not target_value.lower().startswith('vm-'):
                    target_value = f"vm-{target_value}"
                entities['target_vm'] = target_value
                
        # Process other entities
        for entity_type, patterns in self.patterns.items():
            # Skip source/target VM as we already processed them
            if entity_type in ['source_vm', 'target_vm']:
                continue
                
            for pattern in patterns:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match and match.group(1):
                    value = match.group(1).strip()
                    # Only add vm- prefix for vm_name if needed and not in a "new" context
                    if entity_type == 'vm_name':
                        if 'new' in query_lower or 'create' in query_lower:
                            # For new VMs, keep the name as is
                            entities[entity_type] = value
                        elif not value.lower().startswith('vm-'):
                            # For existing VMs, ensure vm- prefix
                            entities[entity_type] = f"vm-{value}"
                        else:
                            entities[entity_type] = value
                    else:
                        entities[entity_type] = value
                    break

        return entities

    def _extract_vm_creation_params(self, preprocessed_query):
        """Extract parameters for VM creation or modification"""
        params = {}
        
        # Extract RAM/memory with improved pattern
        ram_patterns = [
            r'(\d+)\s*(?:GB|G|mb|MB|M|gb|g|gib)\s*(?:of\s+)?(?:RAM|memory|ram)?',  # e.g., 2GB RAM
            r'(?:RAM|memory|ram)\s+(?:of\s+)?(\d+)\s*(?:GB|G|mb|MB|M|gb|g|gib)',  # e.g., RAM of 2GB
            r'(?:with|using|having)\s+(\d+)\s*(?:GB|G|mb|MB|M|gb|g|gib)\s*(?:of\s+)?(?:RAM|memory|ram)?'  # e.g., with 2GB
        ]
        
        for pattern in ram_patterns:
            ram_match = re.search(pattern, preprocessed_query)
            if ram_match:
                memory = int(ram_match.group(1))
                match_text = ram_match.group(0).lower()
                # Convert to MB for consistency
                if any(unit in match_text for unit in ['gb', 'g', 'gib']):
                    memory *= 1024
                params['memory'] = memory
                break
        
        # Extract CPU cores
        cpu_patterns = [
            r'(\d+)\s*(?:CPU|cpu|core|cores|processor|processors)',
            r'(?:CPU|cpu|core|cores|processor|processors)\s*(?:count|number)?\s*(?:of)?\s*(\d+)'
        ]
        
        for pattern in cpu_patterns:
            cpu_match = re.search(pattern, preprocessed_query)
            if cpu_match:
                params['cores'] = int(cpu_match.group(1))
                break
        
        # Extract disk size
        disk_patterns = [
            r'(\d+)\s*(?:GB|G|TB|T)\s*(?:disk|storage|hdd|ssd)',
            r'(?:disk|storage|hdd|ssd)\s*(?:of|size|capacity)?\s*(\d+)\s*(?:GB|G|TB|T)',
            r'(?:with|using|having)\s+(\d+)\s*(?:GB|G|TB|T)\s*(?:disk|storage|hdd|ssd)?'
        ]
        
        for pattern in disk_patterns:
            disk_match = re.search(pattern, preprocessed_query)
            if disk_match:
                disk_size = int(disk_match.group(1))
                match_text = disk_match.group(0).lower()
                # Convert to GB for consistency
                if 'tb' in match_text or 't' in match_text:
                    disk_size *= 1024
                params['disk'] = disk_size
                break
        
        return params

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
                entities['raid_level'] = level
                break
        
        # Schedule for auto-snapshots
        schedules = ['hourly', 'daily', 'weekly', 'monthly', 'yearly']
        for schedule in schedules:
            if schedule in preprocessed_query:
                entities['schedule'] = schedule
                break
                
        # Properties
        properties = {}
        prop_matches = re.findall(r'(?:set|with)\s+([a-z:]+)=([a-zA-Z0-9]+)', preprocessed_query, re.IGNORECASE)
        if prop_matches:
            for prop, value in prop_matches:
                properties[prop] = value
            if properties:
                entities['properties'] = properties
                
    def validate_entities(self, entities, intent):
        """Validate extracted entities against the required entities for the intent"""
        # Define required entities for each intent
        required_entities = {
            'start_vm': ['vm_name'],
            'stop_vm': ['vm_name'],
            'restart_vm': ['vm_name'],
            'vm_status': ['vm_name'],
            'delete_vm': ['vm_name'],
            'clone_vm': ['source_vm', 'target_vm'],
            'snapshot_vm': ['vm_name'],
            'start_container': ['container_id'],
            'stop_container': ['container_id'],
            'node_status': ['node'],
            'start_docker_container': ['container_name', 'vm_name'],
            'stop_docker_container': ['container_name', 'vm_name'],
            'docker_container_logs': ['container_name', 'vm_name'],
            'pull_docker_image': ['image_name', 'vm_name'],
            'run_docker_container': ['image_name', 'vm_name'],
            'run_cli_command': ['command', 'vm_name'],
            'deploy_service': ['service_name'],
            'service_status': ['service_name'],
            'stop_service': ['service_name'],
            'start_service': ['service_name'],
            'create_zfs_pool': ['pool_name', 'devices'],
            'create_zfs_dataset': ['dataset_name'],
            'create_zfs_snapshot': ['dataset_name'],
            'backup_vm': ['vm_name'],
            'restore_backup': ['backup_id']
        }
        
        if intent not in required_entities:
            # No validation needed for intents with no required entities
            return True, []
        
        missing = []
        for required in required_entities[intent]:
            if required not in entities:
                missing.append(required)
                
        return len(missing) == 0, missing
