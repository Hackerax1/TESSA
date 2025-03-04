"""
Response generator module for producing natural language responses.
"""
import os

class ResponseGenerator:
    def __init__(self):
        """Initialize the response generator with optional Ollama integration"""
        self.use_ollama = os.getenv("DISABLE_OLLAMA_RESPONSE", "").lower() != "true"
        self.ollama_client = None
        
        # Ollama client will be set later if needed to avoid circular imports
    
    def set_ollama_client(self, ollama_client):
        """Set the Ollama client for enhanced responses"""
        self.ollama_client = ollama_client
        if ollama_client:
            print("Response generator will use Ollama for enhanced responses")

    def generate_response(self, query, intent, result):
        """Generate a natural language response"""
        # Check if this is a confirmation request
        if result.get('requires_confirmation', False):
            return result['message']
        
        # Try to use Ollama for response enhancement if available
        if self.use_ollama and self.ollama_client:
            try:
                enhanced_response = self.ollama_client.enhance_response(query, intent, result)
                if enhanced_response:
                    return enhanced_response
            except Exception as e:
                print(f"Warning: Failed to generate enhanced response: {str(e)}")
                print("Falling back to template-based response generation")
        
        # Fallback to standard response generation
        if not result['success']:
            return f"Sorry, there was an error: {result['message']}"
        
        # VM management responses
        if intent == 'list_vms':
            if not result.get('vms'):
                return "I couldn't find any virtual machines."
            
            vm_list = result['vms']
            if len(vm_list) == 0:
                return "There are no virtual machines running on your Proxmox cluster."
            
            response = f"I found {len(vm_list)} virtual machines:\n\n"
            for vm in vm_list:
                response += f"• VM {vm['id']} - {vm['name']} ({vm['status']}) on node {vm['node']}\n"
                response += f"  CPU: {vm['cpu']} cores, Memory: {vm['memory']:.1f} MB, Disk: {vm['disk']:.1f} GB\n\n"
            
            return response.strip()
        
        elif intent in ['start_vm', 'stop_vm', 'restart_vm', 'delete_vm']:
            return result['message']
        
        elif intent == 'vm_status':
            status = result['status']
            response = f"Status of VM {result['message'].split()[-1]}:\n"
            response += f"• State: {status['status']}\n"
            response += f"• CPU usage: {status['cpu']:.2f}\n"
            response += f"• Memory: {status['memory']:.1f} MB\n"
            response += f"• Disk: {status['disk']:.1f} GB"
            return response
        
        elif intent == 'create_vm':
            return result['message']
        
        # Container management responses
        elif intent == 'list_containers':
            if not result.get('containers'):
                return "I couldn't find any containers."
            
            container_list = result['containers']
            if len(container_list) == 0:
                return "There are no containers running on your Proxmox cluster."
            
            response = f"I found {len(container_list)} containers:\n\n"
            for ct in container_list:
                response += f"• Container {ct['id']} - {ct['name']} ({ct['status']}) on node {ct['node']}\n"
            
            return response.strip()
        
        # Cluster management responses
        elif intent == 'cluster_status':
            status = result['status']
            response = "Cluster status:\n"
            for node in status:
                response += f"• {node['name']} ({node['type']}): {node['status']}\n"
            return response.strip()
        
        elif intent == 'node_status':
            status = result['status']
            node_name = result['message'].split()[1]
            response = f"Status of node {node_name}:\n"
            response += f"• CPU: {status['cpuinfo']['cpus']} CPUs, {status['loadavg'][0]:.2f} load\n"
            response += f"• Memory: {status['memory']['used'] / (1024*1024):.1f} MB used of {status['memory']['total'] / (1024*1024):.1f} MB\n"
            response += f"• Uptime: {status['uptime'] // 86400} days {(status['uptime'] % 86400) // 3600} hours"
            return response
        
        elif intent == 'storage_info':
            storages = result['storages']
            response = f"I found {len(storages)} storage locations:\n\n"
            for storage in storages:
                used_percent = (storage['used'] / storage['total'] * 100) if storage['total'] > 0 else 0
                response += f"• {storage['name']} ({storage['type']}) on node {storage['node']}:\n"
                response += f"  {storage['used']:.1f} GB used of {storage['total']:.1f} GB ({used_percent:.1f}%)\n"
                response += f"  {storage['available']:.1f} GB available\n\n"
            return response.strip()
        
        # Docker management responses
        elif intent == 'list_docker_containers':
            if not result.get('containers'):
                return "I couldn't find any Docker containers on this VM."
            
            containers = result['containers']
            if len(containers) == 0:
                return "There are no Docker containers on this VM."
            
            response = f"I found {len(containers)} Docker containers:\n\n"
            for container in containers:
                response += f"• {container['name']} ({container['id']})\n"
                response += f"  Image: {container['image']}\n"
                response += f"  Status: {container['status']}\n\n"
            return response.strip()
        
        elif intent in ['start_docker_container', 'stop_docker_container']:
            return result['message']
        
        elif intent == 'docker_container_logs':
            response = f"Logs for container {result['message'].split()[-2]}:\n\n"
            response += result['logs']
            return response
        
        elif intent == 'list_docker_images':
            if not result.get('images'):
                return "I couldn't find any Docker images on this VM."
            
            images = result['images']
            if len(images) == 0:
                return "There are no Docker images on this VM."
            
            response = f"I found {len(images)} Docker images:\n\n"
            for image in images:
                response += f"• {image['name']} ({image['id']})\n"
                response += f"  Size: {image['size']}\n\n"
            return response.strip()
        
        elif intent == 'pull_docker_image':
            return f"Docker image pulled successfully. Output:\n\n{result['output']}"
        
        elif intent == 'run_docker_container':
            return f"Docker container started with ID: {result['container_id']}"
        
        # VM CLI command execution response
        elif intent == 'run_cli_command':
            response = "Command executed successfully. Output:\n\n"
            response += result['output']
            return response
        
        elif intent == 'help':
            from .core_nli import ProxmoxNLI
            return ProxmoxNLI.get_help_text(None)
        
        else:
            return "I'm not sure how to respond to that. Try asking for 'help' to see available commands."