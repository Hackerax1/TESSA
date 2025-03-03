import time
import base64

class VMCommand:
    def __init__(self, api):
        self.api = api

    def execute_command(self, vm_id, node, command, timeout=60, wait_for_prompt=True):
        """Execute a command on a VM via the Proxmox API"""
        # First check if VM is running
        vm_status = self._get_vm_status(vm_id, node)
        if not vm_status['success']:
            return vm_status
        
        if vm_status['status'] != 'running':
            return {"success": False, "message": f"VM {vm_id} is not running"}
        
        # Open a console connection to the VM
        console_result = self._open_console(vm_id, node)
        if not console_result['success']:
            return console_result
        
        console_id = console_result['console_id']
        
        # Wait for the console to be ready
        if wait_for_prompt:
            time.sleep(2)  # Wait for prompt to appear
        
        # Send the command
        send_result = self._send_command(console_id, node, command)
        if not send_result['success']:
            return send_result
        
        # Wait for the command to complete
        output = ""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Get console output
            output_result = self._get_console_output(console_id, node)
            if not output_result['success']:
                return output_result
            
            output = output_result['output']
            
            # Check if command has completed
            if wait_for_prompt and self._is_command_completed(output, command):
                break
                
            time.sleep(1)
        
        # Close the console
        self._close_console(console_id, node)
        
        # Process the output
        processed_output = self._process_command_output(output, command)
        
        return {"success": True, "output": processed_output}

    def run_cli_command(self, vm_id, command, timeout=60):
        """Run a CLI command on a VM - public interface method"""
        # Get the VM location
        vm_info = self._get_vm_location(vm_id)
        if not vm_info['success']:
            return vm_info
        
        node = vm_info['node']
        
        # Execute the command
        return self.execute_command(vm_id, node, command, timeout)
    
    def _open_console(self, vm_id, node):
        """Open a console connection to a VM"""
        # Implementation depends on the Proxmox API
        # This is a simplified example using VNC or SSH
        try:
            # Create a console connection using Proxmox API
            result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/agent/exec', {
                'command': 'exec-command',
                'synchronous': True,
                'args': ['bash', '-c', 'echo "Connection established"']
            })
            
            if result['success']:
                # Extract console ID or connection info
                return {"success": True, "console_id": f"{node}-{vm_id}-console", "message": "Console opened"}
            else:
                return {"success": False, "message": f"Failed to open console: {result['message']}"}
        except Exception as e:
            return {"success": False, "message": f"Error opening console: {str(e)}"}
    
    def _send_command(self, console_id, node, command):
        """Send a command to an open console"""
        try:
            # Extract VM ID from console_id
            vm_id = console_id.split('-')[1]
            
            # Send command via agent (if available)
            result = self.api.api_request('POST', f'nodes/{node}/qemu/{vm_id}/agent/exec', {
                'command': 'exec-command',
                'synchronous': True,
                'args': ['bash', '-c', command]
            })
            
            if result['success']:
                return {"success": True, "message": "Command sent"}
            else:
                return {"success": False, "message": f"Failed to send command: {result['message']}"}
        except Exception as e:
            return {"success": False, "message": f"Error sending command: {str(e)}"}
    
    def _get_console_output(self, console_id, node):
        """Get output from an open console"""
        try:
            # Extract VM ID from console_id
            vm_id = console_id.split('-')[1]
            
            # Get command output from agent
            result = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/agent/exec-status')
            
            if result['success']:
                # Process the output based on Proxmox API response format
                output = ""
                if 'out-data' in result['data']:
                    # Base64 decode if needed
                    try:
                        output = base64.b64decode(result['data']['out-data']).decode('utf-8')
                    except:
                        output = result['data']['out-data']
                
                return {"success": True, "output": output}
            else:
                return {"success": False, "message": f"Failed to get console output: {result['message']}"}
        except Exception as e:
            return {"success": False, "message": f"Error getting console output: {str(e)}"}
    
    def _close_console(self, console_id, node):
        """Close a console connection"""
        # This might not be needed if using QEMU agent, but included for completeness
        return {"success": True, "message": "Console closed"}
    
    def _is_command_completed(self, output, command):
        """Check if a command has completed based on console output"""
        # This is a simplified implementation
        # In a real scenario, you'd look for shell prompts or command completion markers
        return True
    
    def _process_command_output(self, output, command):
        """Process command output to remove command echo and prompts"""
        # Remove command from the beginning if it appears there
        output_lines = output.strip().split('\n')
        processed_lines = []
        
        # Skip the first line if it contains the command
        start_idx = 0
        if output_lines and command in output_lines[0]:
            start_idx = 1
        
        # Process remaining lines (remove prompt from the last line)
        for i in range(start_idx, len(output_lines)):
            line = output_lines[i]
            # Skip lines containing standard shell prompts
            if i == len(output_lines) - 1 and any(prompt in line for prompt in ['$ ', '# ', '> ']):
                continue
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _get_vm_status(self, vm_id, node):
        """Get the current status of a VM"""
        result = self.api.api_request('GET', f'nodes/{node}/qemu/{vm_id}/status/current')
        if result['success']:
            return {"success": True, "status": result['data']['status']}
        else:
            return {"success": False, "message": result['message']}
    
    def _get_vm_location(self, vm_id):
        """Get the node where a VM is located"""
        result = self.api.api_request('GET', 'cluster/resources?type=vm')
        if not result['success']:
            return result
        
        for vm in result['data']:
            if str(vm['vmid']) == str(vm_id):
                return {"success": True, "node": vm['node']}
        
        return {"success": False, "message": f"VM {vm_id} not found"}