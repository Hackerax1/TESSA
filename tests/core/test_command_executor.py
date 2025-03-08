import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path to import modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from proxmox_nli.core.command_executor import CommandExecutor
from proxmox_nli.commands.proxmox_commands import ProxmoxCommands
from proxmox_nli.commands.docker_commands import DockerCommands
from proxmox_nli.commands.vm_command import VMCommand


class TestCommandExecutor(unittest.TestCase):
    def setUp(self):
        # Create mock objects for dependencies
        self.mock_base_nli = MagicMock()
        self.mock_commands = MagicMock(spec=ProxmoxCommands)
        self.mock_docker_commands = MagicMock(spec=DockerCommands)
        self.mock_vm_command = MagicMock(spec=VMCommand)
        self.mock_get_help = MagicMock(return_value={"success": True, "message": "Help content"})
        
        # Assign mocks to the base_nli object
        self.mock_base_nli.commands = self.mock_commands
        self.mock_base_nli.docker_commands = self.mock_docker_commands
        self.mock_base_nli.vm_command = self.mock_vm_command
        self.mock_base_nli.get_help = self.mock_get_help
        
        # Create the CommandExecutor instance with mocked dependencies
        self.command_executor = CommandExecutor(self.mock_base_nli)

    def test_execute_vm_management_commands(self):
        """Test VM management command execution"""
        # Test list_vms command
        self.mock_commands.list_vms.return_value = {"success": True, "vms": [{"vmid": 100, "name": "test-vm"}]}
        result = self.command_executor._execute_command("list_vms", [], {})
        self.assertTrue(result["success"])
        self.assertEqual(result["vms"], [{"vmid": 100, "name": "test-vm"}])
        self.mock_commands.list_vms.assert_called_once()
        
        # Test start_vm command
        self.mock_commands.start_vm.return_value = {"success": True, "message": "VM 100 started successfully"}
        result = self.command_executor._execute_command("start_vm", ["100"], {})
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 100 started successfully")
        self.mock_commands.start_vm.assert_called_once_with("100")
        
        # Test stop_vm command with entities
        self.mock_commands.stop_vm.return_value = {"success": True, "message": "VM 101 stopped successfully"}
        result = self.command_executor._execute_command("stop_vm", [], {"VM_ID": "101"})
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 101 stopped successfully")
        self.mock_commands.stop_vm.assert_called_once_with("101")
        
        # Test restart_vm command
        self.mock_commands.restart_vm.return_value = {"success": True, "message": "VM 102 restarted successfully"}
        result = self.command_executor._execute_command("restart_vm", ["102"], {})
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 102 restarted successfully")
        self.mock_commands.restart_vm.assert_called_once_with("102")
        
        # Test delete_vm command
        self.mock_commands.delete_vm.return_value = {"success": True, "message": "VM 103 deleted successfully"}
        result = self.command_executor._execute_command("delete_vm", ["103"], {})
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 103 deleted successfully")
        self.mock_commands.delete_vm.assert_called_once_with("103")
        
        # Test vm_status command
        self.mock_commands.get_vm_status.return_value = {"success": True, "status": "running"}
        result = self.command_executor._execute_command("vm_status", ["104"], {})
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "running")
        self.mock_commands.get_vm_status.assert_called_once_with("104")
        
        # Test create_vm command
        vm_params = {"name": "new-vm", "memory": 2048, "cores": 2}
        self.mock_commands.create_vm.return_value = {"success": True, "message": "VM created successfully"}
        result = self.command_executor._execute_command("create_vm", [], {"PARAMS": vm_params})
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM created successfully")
        self.mock_commands.create_vm.assert_called_once_with(vm_params)

    def test_execute_docker_commands(self):
        """Test Docker command execution"""
        # Test list_docker_containers command
        self.mock_docker_commands.list_docker_containers.return_value = {
            "success": True, 
            "containers": [
                {"name": "container1", "status": "running"}
            ]
        }
        result = self.command_executor._execute_command("list_docker_containers", ["100"], {})
        self.assertTrue(result["success"])
        self.assertEqual(len(result["containers"]), 1)
        self.mock_docker_commands.list_docker_containers.assert_called_once_with("100")
        
        # Test start_docker_container command
        self.mock_docker_commands.start_docker_container.return_value = {
            "success": True,
            "message": "Container started successfully"
        }
        result = self.command_executor._execute_command(
            "start_docker_container", 
            ["container1", "101"], 
            {}
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Container started successfully")
        self.mock_docker_commands.start_docker_container.assert_called_once_with("container1", "101")
        
        # Test stop_docker_container command with entities
        self.mock_docker_commands.stop_docker_container.return_value = {
            "success": True, 
            "message": "Container stopped successfully"
        }
        result = self.command_executor._execute_command(
            "stop_docker_container", 
            [], 
            {"CONTAINER_NAME": "container2", "VM_ID": "102"}
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Container stopped successfully")
        self.mock_docker_commands.stop_docker_container.assert_called_once_with("container2", "102")

    def test_execute_cli_command(self):
        """Test CLI command execution inside VMs"""
        # Test run_cli_command command
        self.mock_vm_command.run_cli_command.return_value = {
            "success": True,
            "output": "Command output"
        }
        
        # Test with positional args
        result = self.command_executor._execute_command(
            "run_cli_command", 
            ["ls -la", "100"], 
            {}
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "Command output")
        self.mock_vm_command.run_cli_command.assert_called_once_with("100", "ls -la")
        
        # Reset mock for next test
        self.mock_vm_command.run_cli_command.reset_mock()
        
        # Test with entities
        result = self.command_executor._execute_command(
            "run_cli_command", 
            [], 
            {"COMMAND": "df -h", "VM_ID": "101"}
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "Command output")
        self.mock_vm_command.run_cli_command.assert_called_once_with("101", "df -h")

    def test_invalid_command(self):
        """Test handling of invalid commands"""
        result = self.command_executor._execute_command("invalid_command", [], {})
        self.assertFalse(result["success"])
        self.assertIn("don't understand", result["message"])

    def test_missing_parameters(self):
        """Test handling of missing required parameters"""
        # Test start_vm with missing VM_ID
        result = self.command_executor._execute_command("start_vm", [], {})
        self.assertFalse(result["success"])
        self.assertIn("Please specify a VM ID", result["message"])
        
        # Test run_cli_command with missing parameters
        result = self.command_executor._execute_command("run_cli_command", ["ls -la"], {})
        self.assertFalse(result["success"])
        self.assertIn("Please specify", result["message"])

    def test_help_command(self):
        """Test help command execution"""
        result = self.command_executor._execute_command("help", [], {})
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Help content")
        self.mock_get_help.assert_called_once()


if __name__ == '__main__':
    unittest.main()