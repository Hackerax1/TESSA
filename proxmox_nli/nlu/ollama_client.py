"""
Ollama integration for enhanced NLU capabilities in Proxmox NLI.
This module provides a client to interact with Ollama models for intent recognition,
entity extraction, and natural language understanding.
"""

import os
import json
import requests
import time
from typing import Dict, List, Any, Tuple, Optional

class OllamaClient:
    def __init__(self, model_name: str = "llama3", base_url: str = None):
        """
        Initialize the Ollama client with the specified model.
        
        Args:
            model_name: Name of the Ollama model to use (default: "llama3")
            base_url: URL of the Ollama API (default: http://localhost:11434)
        """
        self.model_name = model_name
        self.base_url = base_url or os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.api_url = f"{self.base_url}/api/generate"
        self.context = []  # Store conversation context
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify that we can connect to the Ollama API"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                # Check if specified model exists, accounting for model format (name:tag)
                specified_model_base = self.model_name.split(':')[0]
                if not any(model["name"].startswith(specified_model_base) for model in models):
                    print(f"Warning: Model {self.model_name} not found in Ollama. Available models: {model_names}")
                    if models:
                        self.model_name = models[0]["name"]
                        print(f"Using {self.model_name} as fallback model")
            else:
                print(f"Warning: Ollama API at {self.base_url} returned status {response.status_code}")
                print("NLU will fall back to basic pattern matching")
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to connect to Ollama API at {self.base_url}: {str(e)}")
            print("NLU will fall back to basic pattern matching")
    
    def _format_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract and parse JSON from response text"""
        try:
            # First, try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown or text
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                try:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Fallback: create a minimal valid structure
            return {"intent": "unknown", "args": [], "entities": {}}
    
    def get_intent_and_entities(self, query: str, conversation_history: List[Dict[str, Any]] = None) -> Tuple[str, List[Any], Dict[str, Any]]:
        """
        Process a query to extract intent and entities using Ollama.
        
        Args:
            query: The natural language query to process
            conversation_history: Previous conversation context
            
        Returns:
            Tuple containing:
                - intent name (str)
                - intent arguments (list)
                - extracted entities (dict)
        """
        system_prompt = """You are an NLU (Natural Language Understanding) system for a Proxmox management interface. 
        Your task is to identify the intent and extract entities from user queries. 
        
        Available intents:
        - list_vms: List all virtual machines
        - start_vm: Start a virtual machine (requires VM_ID)
        - stop_vm: Stop a virtual machine (requires VM_ID)
        - restart_vm: Restart a virtual machine (requires VM_ID)
        - vm_status: Get status of a VM (requires VM_ID)
        - create_vm: Create a new VM (optional PARAMS with memory, cores, disk size)
        - delete_vm: Delete a VM (requires VM_ID)
        - clone_vm: Clone a VM (requires VM_ID and optional NEW_VM_ID)
        - snapshot_vm: Create a snapshot of a VM (requires VM_ID and optional SNAPSHOT_NAME)
        - list_containers: List all LXC containers
        - start_container: Start an LXC container (requires CONTAINER_ID)
        - stop_container: Stop an LXC container (requires CONTAINER_ID)
        - cluster_status: Get cluster status
        - node_status: Get node status (requires NODE)
        - storage_info: Get storage information
        - list_docker_containers: List Docker containers (optional VM_ID)
        - start_docker_container: Start a Docker container (requires CONTAINER_NAME, VM_ID)
        - stop_docker_container: Stop a Docker container (requires CONTAINER_NAME, VM_ID)
        - docker_container_logs: Get Docker container logs (requires CONTAINER_NAME, VM_ID)
        - list_docker_images: List Docker images (requires VM_ID)
        - pull_docker_image: Pull a Docker image (requires IMAGE_NAME, VM_ID)
        - run_docker_container: Run a Docker container (requires IMAGE_NAME, VM_ID)
        - run_cli_command: Run a command on a VM (requires COMMAND, VM_ID)
        - deploy_service: Deploy a service (requires SERVICE_NAME, optional VM_ID)
        - list_deployed_services: List all deployed services
        - list_available_services: List all available services
        - service_status: Get status of a service (requires SERVICE_NAME, optional VM_ID)
        - stop_service: Stop a service (requires SERVICE_NAME, optional VM_ID)
        - start_service: Start a service (requires SERVICE_NAME, optional VM_ID)
        - backup_vm: Create a backup of a VM (requires VM_ID)
        - restore_backup: Restore a VM from backup (requires BACKUP_ID, optional VM_ID)
        - list_backups: List all available backups (optional VM_ID)
        - create_zfs_pool: Create a ZFS storage pool (requires POOL_NAME, DEVICES)
        - create_zfs_dataset: Create a ZFS dataset (requires DATASET_NAME)
        - list_zfs_pools: List all ZFS storage pools
        - create_zfs_snapshot: Create a ZFS snapshot (requires DATASET_NAME, optional SNAPSHOT_NAME)
        - help: Show help information
        
        Return your analysis in strict JSON format with these fields:
        {
            "intent": "intent_name",
            "args": ["arg1", "arg2"],
            "entities": {
                "VM_ID": "123",
                "NODE": "node1",
                "CONTAINER_NAME": "container1",
                "CONTAINER_ID": "100",
                "IMAGE_NAME": "ubuntu:latest",
                "COMMAND": "ls -la",
                "SERVICE_NAME": "nextcloud",
                "BACKUP_ID": "backup_20240601",
                "SNAPSHOT_NAME": "daily",
                "POOL_NAME": "tank",
                "DATASET_NAME": "tank/data",
                "DEVICES": ["/dev/sda", "/dev/sdb"],
                "RAID_LEVEL": "mirror",
                "PARAMS": {"memory": 1024, "cores": 2, "disk": 20}
            }
        }
        
        Don't include any entities that aren't present in the query.
        Consider any context from previous conversation when resolving pronouns like "it", "that VM", etc.
        """
        
        # Format conversation history for context
        context_prompt = ""
        if conversation_history:
            context_prompt = "Previous conversation context:\n"
            for i, entry in enumerate(conversation_history[-3:]):  # Include up to 3 most recent exchanges
                context_prompt += f"User [{i+1}]: {entry.get('query', '')}\n"
                context_prompt += f"Intent [{i+1}]: {entry.get('intent', '')}\n"
                if entry.get('entities'):
                    context_prompt += f"Entities [{i+1}]: {entry.get('entities')}\n"
            context_prompt += "\n"
        
        # Add current query
        prompt = f"{context_prompt}Current query: {query}\n\nAnalyze the intent and entities:"
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": system_prompt,
                    "format": "json",
                    "stream": False,
                    "temperature": 0.1,  # Lower temperature for more deterministic responses
                    "num_ctx": 4096,     # Larger context window
                },
                timeout=10  # 10-second timeout
            )
            
            if response.status_code == 200:
                try:
                    response_text = response.json().get("response", "{}")
                    result = self._format_json_response(response_text)
                    
                    intent = result.get("intent", "unknown")
                    args = result.get("args", [])
                    entities = result.get("entities", {})
                    
                    # Update conversation context
                    self.context.append({
                        "query": query,
                        "intent": intent,
                        "entities": entities
                    })
                    # Keep context manageable
                    if len(self.context) > 5:
                        self.context.pop(0)
                    
                    return intent, args, entities
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse Ollama response as JSON: {str(e)}")
            else:
                print(f"Warning: Ollama API returned status code {response.status_code}: {response.text}")
        except requests.exceptions.Timeout:
            print("Warning: Ollama API request timed out")
        except requests.exceptions.RequestException as e:
            print(f"Warning: Error calling Ollama API: {str(e)}")
        except Exception as e:
            print(f"Warning: Unexpected error in Ollama processing: {str(e)}")
        
        # Fallback to unknown intent if anything fails
        return "unknown", [], {}
    
    def enhance_response(self, query: str, intent: str, result: Dict[str, Any]) -> str:
        """
        Enhance a response using Ollama for better natural language generation.
        
        Args:
            query: Original user query
            intent: Identified intent
            result: Command execution result dictionary
            
        Returns:
            Enhanced natural language response
        """
        system_prompt = """You are an assistant for a Proxmox VE environment. 
        Format the response data into a helpful, natural language reply for the user.
        Keep responses concise and professional. Focus on the most important information.
        If there was an error, clearly explain what went wrong and suggest a solution.
        
        When formatting lists of items:
        - Present them in a clear, organized way
        - For VMs, include VM ID, name, status, and resource info if available
        - For services, include service name, status, and location if available
        - For Docker containers, include container name, image, and status
        
        Focus on being helpful, accurate, and direct in your response.
        """
        
        # Include recent context from conversation
        context_str = ""
        if self.context:
            context_str = "Recent conversation:\n"
            for i, ctx in enumerate(self.context[-2:]):  # Last 2 exchanges
                context_str += f"- User asked about: {ctx.get('intent', 'unknown')}\n"
        
        prompt = f"""
        {context_str}
        
        User query: {query}
        Intent: {intent}
        Result data: {json.dumps(result)}
        
        Generate a natural language response summarizing this information:
        """
        
        try:
            start_time = time.time()
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "temperature": 0.7,  # Slightly higher temperature for more natural responses
                },
                timeout=8  # 8-second timeout
            )
            
            if response.status_code == 200:
                enhanced_response = response.json().get("response", "")
                if enhanced_response:
                    # Log response time for performance monitoring
                    response_time = time.time() - start_time
                    print(f"Response generated in {response_time:.2f} seconds")
                    return enhanced_response.strip()
        except Exception as e:
            print(f"Warning: Error generating enhanced response: {str(e)}")
        
        # Fallback to original result if enhancement fails
        return None
        
    def get_contextual_information(self) -> Dict[str, Any]:
        """
        Get current conversation context information
        
        Returns:
            Dictionary containing conversation context
        """
        if not self.context:
            return {}
            
        # Extract relevant context data
        latest_context = self.context[-1]
        return {
            "last_intent": latest_context.get("intent"),
            "last_entities": latest_context.get("entities"),
            "conversation_length": len(self.context)
        }