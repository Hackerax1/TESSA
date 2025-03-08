import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import time
import base64

# Add the project root to the Python path to import modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from proxmox_nli.commands.vm_command import VMCommand


class TestVMCommand(unittest.TestCase):
    def setUp(self):
        # Create mock API
        self.mock_api = MagicMock()
        
        # Create the VMCommand instance with mocked API
        self.vm_command = VMCommand(self.mock_api)
        
    def test_execute_command_success(self):
        """Test successfully executing a command in a VM"""
        # Mock API responses
        vm_status_response = {"success": True, "status": "running"}
        console_open_response = {"success": True, "console_id": "console-100"}
        command_send_response = {"success": True, "message": "Command sent"}
        console_output_response = {"success": True, "output": "command output"}
        console_close_response = {"success": True, "message": "Console closed"}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            vm_status_response,  # For _get_vm_status
            console_open_response,  # For _open_console
            command_send_response,  # For _send_command
            console_output_response,  # For _get_console_output
            console_close_response,  # For _close_console
        ]
        
        # Call the execute_command method
        result = self.vm_command.execute_command("100", "node1", "echo 'Hello World'", timeout=1)
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "command output")
        
        # Verify the API calls
        expected_calls = [
            # For _get_vm_status
            ('GET', 'nodes/node1/qemu/100/status/current'),
            # For _open_console
            ('POST', 'nodes/node1/qemu/100/agent/exec', {'command': 'exec-command', 'synchronous': False, 'args': ['bash', '-c', 'exec > /tmp/vm_command_output_100.txt 2>&1']}),
            # For _send_command
            ('POST', 'nodes/node1/qemu/100/agent/exec', {'command': 'exec-command', 'synchronous': True, 'args': ['bash', '-c', "echo 'Hello World'"]}),
            # For _get_console_output
            ('GET', 'nodes/node1/qemu/100/agent/exec-status'),
            # For _close_console
            ('POST', 'nodes/node1/qemu/100/agent/exec', {'command': 'exec-command', 'synchronous': True, 'args': ['bash', '-c', 'rm -f /tmp/vm_command_output_100.txt']})
        ]
        
        # Check that the API was called correctly
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])
            if len(args) > 2:
                self.assertEqual(args[2], expected_calls[i][2])

    def test_execute_command_vm_not_running(self):
        """Test executing a command when VM is not running"""
        # Mock API response for get_vm_status
        self.mock_api.api_request.return_value = {"success": True, "status": "stopped"}
        
        # Call the execute_command method
        result = self.vm_command.execute_command("100", "node1", "echo 'Hello World'")
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "VM 100 is not running")
        
        # Verify the API call for get_vm_status
        self.mock_api.api_request.assert_called_once_with('GET', 'nodes/node1/qemu/100/status/current')

    def test_execute_command_console_failure(self):
        """Test executing a command when opening console fails"""
        # Mock API responses
        vm_status_response = {"success": True, "status": "running"}
        console_open_response = {"success": False, "message": "Failed to open console"}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            vm_status_response,  # For _get_vm_status
            console_open_response,  # For _open_console
        ]
        
        # Call the execute_command method
        result = self.vm_command.execute_command("100", "node1", "echo 'Hello World'")
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Failed to open console")
        
        # Verify the API calls were made correctly
        expected_calls = [
            # For _get_vm_status
            ('GET', 'nodes/node1/qemu/100/status/current'),
            # For _open_console
            ('POST', 'nodes/node1/qemu/100/agent/exec', {'command': 'exec-command', 'synchronous': False, 'args': ['bash', '-c', 'exec > /tmp/vm_command_output_100.txt 2>&1']})
        ]
        
        # Check that the API was called correctly
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])
            if len(args) > 2:
                self.assertEqual(args[2], expected_calls[i][2])

    def test_execute_command_send_failure(self):
        """Test executing a command when sending command fails"""
        # Mock API responses
        vm_status_response = {"success": True, "status": "running"}
        console_open_response = {"success": True, "console_id": "console-100"}
        command_send_response = {"success": False, "message": "Failed to send command"}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            vm_status_response,  # For _get_vm_status
            console_open_response,  # For _open_console
            command_send_response,  # For _send_command
        ]
        
        # Call the execute_command method
        result = self.vm_command.execute_command("100", "node1", "echo 'Hello World'")
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Failed to send command")
        
        # Verify the API calls were made correctly
        expected_calls = [
            # For _get_vm_status
            ('GET', 'nodes/node1/qemu/100/status/current'),
            # For _open_console
            ('POST', 'nodes/node1/qemu/100/agent/exec', {'command': 'exec-command', 'synchronous': False, 'args': ['bash', '-c', 'exec > /tmp/vm_command_output_100.txt 2>&1']}),
            # For _send_command
            ('POST', 'nodes/node1/qemu/100/agent/exec', {'command': 'exec-command', 'synchronous': True, 'args': ['bash', '-c', "echo 'Hello World'"]})
        ]
        
        # Check that the API was called correctly
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])
            if len(args) > 2:
                self.assertEqual(args[2], expected_calls[i][2])

    @patch('time.sleep', return_value=None)  # Mock sleep to speed up tests
    def test_run_cli_command_success(self, mock_sleep):
        """Test running a CLI command successfully"""
        # Mock API responses for _get_vm_location
        vm_location_response = {"success": True, "node": "node1"}
        vm_status_response = {"success": True, "status": "running"}
        console_open_response = {"success": True, "console_id": "console-100"}
        command_send_response = {"success": True, "message": "Command sent"}
        console_output_response = {"success": True, "output": "CLI command output"}
        console_close_response = {"success": True, "message": "Console closed"}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            # For _get_vm_location
            {"success": True, "data": [{"vmid": "100", "node": "node1"}]},
            # For _get_vm_status
            vm_status_response,
            # For _open_console
            console_open_response,
            # For _send_command
            command_send_response,
            # For _get_console_output
            console_output_response,
            # For _close_console
            console_close_response,
        ]
        
        # Call the run_cli_command method
        result = self.vm_command.run_cli_command("100", "df -h", timeout=1)
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "CLI command output")
        
        # Verify the API calls
        self.assertEqual(self.mock_api.api_request.call_count, 6)


if __name__ == '__main__':
    unittest.main()