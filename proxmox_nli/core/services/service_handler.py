"""
Service handler module for managing service-related operations.
"""

class ServiceHandler:
    def __init__(self, base_nli):
        self.service_catalog = base_nli.service_catalog
        self.service_manager = base_nli.service_manager
        self.nlu = base_nli.nlu

    def handle_service_intent(self, intent, args, entities):
        """Handle service-related intents"""
        if intent == 'list_available_services':
            services = self.service_catalog.get_all_services()
            service_list = "\n".join([f"- {s['name']}: {s['description']}" for s in services])
            return {
                "success": True,
                "message": f"Available services:\n\n{service_list if service_list else 'No services available'}"
            }
        
        elif intent == 'list_deployed_services':
            result = self.service_manager.list_deployed_services()
            if result["success"] and result["services"]:
                service_list = "\n".join([f"- {s['name']} (ID: {s['service_id']}) on VM {s['vm_id']}" for s in result["services"]])
                return {
                    "success": True,
                    "message": f"Deployed services:\n\n{service_list}"
                }
            return {
                "success": True,
                "message": "No services are currently deployed"
            }
        
        elif intent == 'find_service':
            query = args[0] if args else entities.get('QUERY')
            if not query:
                return {"success": False, "message": "Please specify what kind of service you're looking for"}
                
            matching_services = self.service_manager.find_service(query)
            if matching_services:
                service_list = "\n".join([f"- {s['name']} (ID: {s['id']}): {s['description']}" for s in matching_services])
                return {
                    "success": True,
                    "message": f"Found these services matching '{query}':\n\n{service_list}\n\nTo deploy one, use 'deploy SERVICE_ID'"
                }
            return {
                "success": True,
                "message": f"No services found matching '{query}'. Please check our available services with 'list services'."
            }
        
        elif intent == 'deploy_service':
            service_id = args[0] if args else entities.get('SERVICE_ID')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            custom_params = entities.get('SERVICE_PARAMS', {})
            
            if not service_id:
                return {"success": False, "message": "Please specify which service you want to deploy"}
                
            result = self.service_manager.deploy_service(service_id, vm_id, custom_params)
            
            if result["success"]:
                # Save context for follow-up commands
                self.nlu.context_manager.set_context({
                    'current_service': service_id,
                    'current_service_vm': result.get('vm_id')
                })
                
            return result
        
        elif intent == 'service_status':
            service_id = args[0] if args else entities.get('SERVICE_ID')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            
            if not service_id or not vm_id:
                return {"success": False, "message": "Please specify the service ID and VM ID"}
                
            return self.service_manager.get_service_status(service_id, vm_id)
        
        elif intent == 'stop_service':
            service_id = args[0] if args else entities.get('SERVICE_ID')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            
            if not service_id or not vm_id:
                return {"success": False, "message": "Please specify the service ID and VM ID"}
                
            return self.service_manager.stop_service(service_id, vm_id)
        
        elif intent == 'remove_service':
            service_id = args[0] if args else entities.get('SERVICE_ID')
            vm_id = args[1] if args and len(args) > 1 else entities.get('VM_ID')
            remove_vm = entities.get('REMOVE_VM', False)
            
            if not service_id or not vm_id:
                return {"success": False, "message": "Please specify the service ID and VM ID"}
                
            return self.service_manager.remove_service(service_id, vm_id, remove_vm)
            
        return {"success": False, "message": "Unknown service command"}