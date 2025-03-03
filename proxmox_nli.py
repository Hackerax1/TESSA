#!/usr/bin/env python3
import argparse

from proxmox_api import ProxmoxAPI
from nlu_engine import NLU_Engine
from proxmox_commands import ProxmoxCommands

class ProxmoxNLI:
    def __init__(self, host, user, password, realm='pam', verify_ssl=False):
        """Initialize the Proxmox Natural Language Interface"""
        self.api = ProxmoxAPI(host, user, password, realm, verify_ssl)
        self.nlu = NLU_Engine()
        self.commands = ProxmoxCommands(self.api)
    
    def execute_intent(self, intent, args, entities):
        """Execute the identified intent"""
        if intent == 'list_vms':
            return self.commands.list_vms()
        elif intent == 'start_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.start_vm(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'stop_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.stop_vm(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'restart_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.restart_vm(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'vm_status':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.get_vm_status(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'create_vm':
            params = entities.get('PARAMS', {})
            return self.commands.create_vm(params)
        elif intent == 'delete_vm':
            vm_id = args[0] if args else entities.get('VM_ID')
            if vm_id:
                return self.commands.delete_vm(vm_id)
            else:
                return {"success": False, "message": "Please specify a VM ID"}
        elif intent == 'list_containers':
            return self.commands.list_containers()
        elif intent == 'cluster_status':
            return self.commands.get_cluster_status()
        elif intent == 'node_status':
            node = args[0] if args else entities.get('NODE')
            if node:
                return self.commands.get_node_status(node)
            else:
                return {"success": False, "message": "Please specify a node name"}
        elif intent == 'storage_info':
            return self.commands.get_storage_info()
        elif intent == 'help':
            return self.commands.get_help()
        else:
            return {"success": False, "message": "I don't understand what you want me to do. Try asking for 'help' to see available commands."}
    
    def generate_response(self, query, intent, result):
        """Generate a natural language response"""
        if not result['success']:
            return f"Sorry, there was an error: {result['message']}"
        
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
        
        elif intent == 'start_vm':
            return result['message']
        
        elif intent == 'stop_vm':
            return result['message']
        
        elif intent == 'restart_vm':
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
        
        elif intent == 'delete_vm':
            return result['message']
        
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
        
        elif intent == 'help':
            commands = result['commands']
            response = "Here are the commands you can use:\n\n"
            for command in commands:
                response += f"• {command}\n"
            return response.strip()
        
        else:
            return "I'm not sure how to respond to that. Try asking for 'help' to see available commands."
    
    def process_query(self, query):
        """Process a natural language query"""
        # Preprocess the query
        preprocessed_query = self.nlu.preprocess_query(query)
        
        # Extract entities
        entities = self.nlu.extract_entities(query)
        
        # Identify intent
        intent, args = self.nlu.identify_intent(preprocessed_query)
        
        # Update conversation context
        self.nlu.update_context(intent, entities)
        
        # Execute intent
        result = self.execute_intent(intent, args, entities)
        
        return self.generate_response(query, intent, result)


def cli_mode(args):
    """Run the Proxmox NLI in command line interface mode"""
    proxmox_nli = ProxmoxNLI(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl
    )
    
    print("Proxmox Natural Language Interface")
    print("Type 'exit' or 'quit' to exit")
    print("Type 'help' to see available commands")
    
    while True:
        query = input("\n> ")
        if query.lower() in ['exit', 'quit']:
            break
        
        response = proxmox_nli.process_query(query)
        print(response)


def web_mode(args):
    """Run the Proxmox NLI as a web server with voice recognition"""
    from app import start_app
    
    print("Starting web interface on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop the server")
    
    start_app(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl,
        debug=args.debug
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Proxmox Natural Language Interface')
    parser.add_argument('--host', required=True, help='Proxmox host')
    parser.add_argument('--user', required=True, help='Proxmox user')
    parser.add_argument('--password', required=True, help='Proxmox password')
    parser.add_argument('--realm', default='pam', help='Proxmox realm')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificate')
    parser.add_argument('--web', action='store_true', help='Start as web server with voice recognition')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (web server only)')
    
    args = parser.parse_args()
    
    try:
        if args.web:
            web_mode(args)
        else:
            cli_mode(args)
    except KeyboardInterrupt:
        print("\nExiting...")