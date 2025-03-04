import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Initialize lemmatizer and stop words
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

class EntityExtractor:
    def extract_entities(self, query):
        """Extract entities from the query using regex and NLTK"""
        entities = {}
        
        # Tokenize and preprocess the query
        tokens = word_tokenize(query.lower())
        filtered_tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
        preprocessed_query = ' '.join(filtered_tokens)
        
        # Look for VM IDs, node names, etc.
        vm_match = re.search(r'(?:vm|virtual\s+machine)\s+(\w+)', preprocessed_query)
        if vm_match:
            entities['VM_ID'] = vm_match.group(1)
        
        node_match = re.search(r'node\s+(\w+)', preprocessed_query)
        if node_match:
            entities['NODE'] = node_match.group(1)
        
        # Extract Docker container names
        container_match = re.search(r'container\s+([a-zA-Z0-9_-]+)', preprocessed_query)
        if container_match:
            entities['CONTAINER_NAME'] = container_match.group(1)
        
        # Extract Docker image names
        image_match = re.search(r'image\s+([a-zA-Z0-9_/.-]+(?::[a-zA-Z0-9_.-]+)?)', preprocessed_query)
        if image_match:
            entities['IMAGE_NAME'] = image_match.group(1)
        
        # Extract CLI command
        command_match = re.search(r'(?:run|execute)\s+(?:command\s+)?[\'"]([^\'"]+)[\'"]', preprocessed_query)
        if command_match:
            entities['COMMAND'] = command_match.group(1)
        
        # Extract parameters for VM creation
        if 'create' in preprocessed_query and ('vm' in preprocessed_query or 'virtual machine' in preprocessed_query):
            params = {}
            # Extract RAM
            ram_match = re.search(r'(\d+)\s*(?:GB|G|mb|MB) (?:of )?(?:RAM|memory)', preprocessed_query)
            if ram_match:
                params['memory'] = int(ram_match.group(1))
                if 'mb' in ram_match.group(0).lower() or 'MB' in ram_match.group(0):
                    params['memory'] = params['memory']
                else:  # GB
                    params['memory'] = params['memory'] * 1024
            
            # Extract CPU cores
            cpu_match = re.search(r'(\d+)\s*(?:CPU|cpu|cores|processors)', preprocessed_query)
            if cpu_match:
                params['cores'] = int(cpu_match.group(1))
            
            # Extract disk size
            disk_match = re.search(r'(\d+)\s*(?:GB|G|TB|T) (?:of )?(?:disk|storage|hdd|ssd)', preprocessed_query)
            if disk_match:
                params['disk'] = int(disk_match.group(1))
                if 'TB' in disk_match.group(0) or 'T' in disk_match.group(0):
                    params['disk'] = params['disk'] * 1024
            
            # Extract OS/template
            os_match = re.search(r'(?:with|using|on)\s+(ubuntu|debian|centos|fedora|windows|alpine)', preprocessed_query, re.IGNORECASE)
            if os_match:
                params['template'] = os_match.group(1).lower()
            
            if params:
                entities['PARAMS'] = params
        
        # Extract parameters for Docker container run
        if ('run' in preprocessed_query or 'create' in preprocessed_query) and 'docker' in preprocessed_query and 'container' in preprocessed_query:
            params = {}
            
            # Extract ports
            ports = []
            ports_match = re.findall(r'port\s+(\d+:\d+)', preprocessed_query)
            for port in ports_match:
                ports.append(port)
            
            if ports:
                params['ports'] = ports
            
            # Extract volumes
            volumes = []
            volumes_match = re.findall(r'volume\s+([a-zA-Z0-9_/.-]+:[a-zA-Z0-9_/.-]+)', preprocessed_query)
            for volume in volumes_match:
                volumes.append(volume)
            
            if volumes:
                params['volumes'] = volumes
            
            # Extract environment variables
            env_vars = []
            env_match = re.findall(r'env\s+([a-zA-Z0-9_]+=[a-zA-Z0-9_.-]+)', preprocessed_query)
            for env in env_match:
                env_vars.append(env)
            
            if env_vars:
                params['environment'] = env_vars
            
            # Extract container name
            container_name_match = re.search(r'name\s+([a-zA-Z0-9_-]+)', preprocessed_query)
            if container_name_match:
                params['container_name'] = container_name_match.group(1)
            
            if params:
                entities['DOCKER_PARAMS'] = params
        
        # ZFS Storage Entities
        # Pool name
        pool_match = re.search(r'pool\s+([a-zA-Z0-9\-_]+)', preprocessed_query, re.IGNORECASE)
        if pool_match:
            entities['POOL_NAME'] = pool_match.group(1)
        
        # Dataset name
        dataset_match = re.search(r'dataset\s+([a-zA-Z0-9\-_/]+)', preprocessed_query, re.IGNORECASE)
        if dataset_match:
            entities['DATASET_NAME'] = dataset_match.group(1)
        
        # Devices for pool creation
        devices_match = re.findall(r'device[s]?\s+([/a-zA-Z0-9\-_\s,]+)', preprocessed_query, re.IGNORECASE)
        if devices_match:
            # Split devices by comma or space
            devices = re.split(r'[,\s]+', devices_match[0].strip())
            entities['DEVICES'] = [d for d in devices if d]
        
        # RAID level
        raid_match = re.search(r'(?:raid|using)\s+(mirror|raidz|raidz2|raidz3|stripe)', preprocessed_query, re.IGNORECASE)
        if raid_match:
            entities['RAID_LEVEL'] = raid_match.group(1).lower()
        
        # Snapshot name
        snapshot_match = re.search(r'snapshot\s+([a-zA-Z0-9\-_]+)', preprocessed_query, re.IGNORECASE)
        if snapshot_match:
            entities['SNAPSHOT_NAME'] = snapshot_match.group(1)
        
        # Properties
        properties = {}
        prop_matches = re.findall(r'(?:set|with)\s+([a-z:]+)=([a-zA-Z0-9]+)', preprocessed_query, re.IGNORECASE)
        if prop_matches:
            for prop, value in prop_matches:
                properties[prop] = value
            if properties:
                entities['PROPERTIES'] = properties
        
        # Schedule for auto-snapshots
        schedule_match = re.search(r'(?:every|schedule)\s+(hourly|daily|weekly|monthly)', preprocessed_query, re.IGNORECASE)
        if schedule_match:
            entities['SCHEDULE'] = schedule_match.group(1).lower()
        
        # Recursive flag for snapshots
        if 'recursive' in preprocessed_query.lower():
            entities['RECURSIVE'] = True
        
        return entities
