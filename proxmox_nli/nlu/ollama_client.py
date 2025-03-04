"""
Ollama integration for enhanced NLU capabilities in Proxmox NLI.
This module provides a client to interact with Ollama models for intent recognition,
entity extraction, and natural language understanding.
"""

import os
import json
import requests
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
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify that we can connect to the Ollama API"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                if not any(model["name"] == self.model_name for model in models):
                    print(f"Warning: Model {self.model_name} not found in Ollama. Available models: {[model['name'] for model in models]}")
                    if models:
                        self.model_name = models[0]["name"]
                        print(f"Using {self.model_name} as fallback model")
        except Exception as e:
            print(f"Warning: Failed to connect to Ollama API at {self.base_url}: {str(e)}")
            print("NLU will fall back to basic pattern matching")
    
    def get_intent_and_entities(self, query: str) -> Tuple[str, List[Any], Dict[str, Any]]:
        """
        Process a query to extract intent and entities using Ollama.
        
        Args:
            query: The natural language query to process
            
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
        - list_containers: List all LXC containers
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
        - help: Show help information
        
        Return your analysis in strict JSON format with these fields:
        {
            "intent": "intent_name",
            "args": ["arg1", "arg2"],
            "entities": {
                "VM_ID": "123",
                "NODE": "node1",
                "CONTAINER_NAME": "container1",
                "IMAGE_NAME": "ubuntu:latest",
                "COMMAND": "ls -la",
                "PARAMS": {"memory": 1024, "cores": 2, "disk": 20}
            }
        }
        
        Don't include any entities that aren't present in the query.
        """
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": query,
                    "system": system_prompt,
                    "format": "json",
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                try:
                    response_text = response.json().get("response", "{}")
                    # Extract JSON from the response text if it's wrapped in markdown or other text
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response_text[json_start:json_end]
                        result = json.loads(json_str)
                    else:
                        result = json.loads(response_text)
                    
                    intent = result.get("intent", "unknown")
                    args = result.get("args", [])
                    entities = result.get("entities", {})
                    return intent, args, entities
                except json.JSONDecodeError:
                    print(f"Warning: Failed to parse Ollama response as JSON: {response_text}")
            else:
                print(f"Warning: Ollama API returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Warning: Error calling Ollama API: {str(e)}")
        
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
        """
        
        prompt = f"""
        User query: {query}
        Intent: {intent}
        Result data: {json.dumps(result)}
        
        Generate a natural language response summarizing this information:
        """
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                enhanced_response = response.json().get("response", "")
                if enhanced_response:
                    return enhanced_response.strip()
        except Exception as e:
            print(f"Warning: Error generating enhanced response: {str(e)}")
        
        # Fallback to original result if enhancement fails
        return None