"""
Response generator module for producing natural language responses.
"""
import os
import json
import re
from typing import Dict, Any, Optional

class ResponseGenerator:
    def __init__(self):
        """Initialize the response generator with optional LLM integration"""
        self.use_ollama = os.getenv("DISABLE_OLLAMA_RESPONSE", "").lower() != "true"
        self.use_huggingface = os.getenv("DISABLE_HUGGINGFACE_RESPONSE", "").lower() != "true"
        self.ollama_client = None
        self.huggingface_client = None
    
    def set_ollama_client(self, ollama_client):
        """Set the Ollama client for enhanced responses"""
        self.ollama_client = ollama_client
        if ollama_client:
            print("Response generator will use Ollama for enhanced responses")
            
    def set_huggingface_client(self, huggingface_client):
        """Set the Hugging Face client for enhanced responses"""
        self.huggingface_client = huggingface_client
        if huggingface_client:
            print("Response generator will use Hugging Face for enhanced responses")
    
    def generate_response(self, query, intent, result):
        """Generate a natural language response"""
        if not result:
            return "I'm sorry, I couldn't process that request."
        
        # Check if there was an error
        if result.get('error'):
            return f"Error: {result['error']}"
        
        # First try with Hugging Face if enabled
        if self.use_huggingface and self.huggingface_client:
            try:
                enhanced_response = self.huggingface_client.enhance_response(query, intent, result)
                if enhanced_response:
                    return enhanced_response
            except Exception as e:
                print(f"Error using Hugging Face for response generation: {e}")
        
        # Next try with Ollama if enabled
        if self.use_ollama and self.ollama_client:
            try:
                enhanced_response = self.ollama_client.enhance_response(query, intent, result)
                if enhanced_response:
                    return enhanced_response
            except Exception as e:
                print(f"Error using Ollama for response generation: {e}")
        
        # Fallback to basic templated responses
        response = self._generate_basic_response(intent, result)
        return response
        
    def _generate_basic_response(self, intent, result):
        """Generate a basic response without LLM assistance"""
        if intent == "list_vms":
            if not result.get('vms'):
                return "No VMs found."
            vm_list = result.get('vms', [])
            vm_strs = [f"VM {vm['id']}: {vm['name']} ({vm['status']})" for vm in vm_list]
            return f"Found {len(vm_list)} VMs:\n" + "\n".join(vm_strs)
        
        elif intent == "start_vm":
            return f"VM {result.get('vm_id')} started successfully."
            
        elif intent == "stop_vm":
            return f"VM {result.get('vm_id')} stopped successfully."
            
        elif intent == "restart_vm":
            return f"VM {result.get('vm_id')} restarted successfully."
            
        elif intent == "vm_status":
            vm = result.get('vm', {})
            return (f"VM {vm.get('id')}: {vm.get('name')}\n"
                   f"Status: {vm.get('status')}\n"
                   f"Memory: {vm.get('mem', 0)} MB, CPU: {vm.get('cpu', 0)}%\n"
                   f"Uptime: {vm.get('uptime', 'N/A')}")
        
        elif intent == "cluster_status":
            nodes = result.get('nodes', [])
            if not nodes:
                return "No cluster nodes found."
            node_strs = [f"Node {n.get('name')}: {n.get('status')} (CPU: {n.get('cpu')}%, Mem: {n.get('mem')}%)" 
                         for n in nodes]
            return "Cluster status:\n" + "\n".join(node_strs)
        
        elif intent == "deploy_service":
            return f"Service {result.get('service_name')} deployed successfully."
        
        elif intent == "help":
            # Just a basic help template, the LLM would provide more context-sensitive help
            return "Available commands include: list_vms, start_vm, stop_vm, restart_vm, vm_status, cluster_status, deploy_service"
            
        # Generic fallback for unhandled intents
        return json.dumps(result, indent=2)