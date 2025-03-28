import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path to import modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from proxmox_nli.commands.proxmox_commands import ProxmoxCommands


class TestProxmoxCommands(unittest.TestCase):
    def setUp(self):
        # Create mock API
        self.mock_api = MagicMock()
        
        # Create the ProxmoxCommands instance with mocked API
        self.commands = ProxmoxCommands(self.mock_api)
    
    def test_list_vms(self):
        """Test listing VMs"""
        # Mock API response for the cluster resources
        self.mock_api.api_request.side_effect = [
            {
                "success": True, 
                "data": [
                    {"vmid": 100, "name": "test-vm1", "status": "running", "node": "node1"},
                    {"vmid": 101, "name": "test-vm2", "status": "stopped", "node": "node2"}
                ]
            },
            # Mock response for first VM status
            {
                "success": True,
                "data": {
                    "status": "running",
                    "cpu": 0.5,
                    "mem": 1024*1024*1024,  # 1GB in bytes
                    "disks": {"scsi0": {"size": 32*1024*1024*1024}}  # 32GB in bytes
                }
            },
            # Mock response for second VM status
            {
                "success": True,
                "data": {
                    "status": "stopped",
                    "cpu": 0,
                    "mem": 2048*1024*1024,  # 2GB in bytes
                    "disks": {"scsi0": {"size": 64*1024*1024*1024}}  # 64GB in bytes
                }
            }
        ]
        
        # Call the list_vms method
        result = self.commands.list_vms()
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["vms"]), 2)
        self.assertEqual(result["vms"][0]["id"], 100)
        self.assertEqual(result["vms"][0]["name"], "test-vm1")
        self.assertEqual(result["vms"][0]["status"], "running")
        self.assertEqual(result["vms"][1]["id"], 101)
        
        # Verify the API calls
        self.assertEqual(self.mock_api.api_request.call_count, 3)  # 1 for list + 2 for VM status

    def test_list_vms_failure(self):
        """Test listing VMs when API call fails"""
        # Mock API response for failure
        self.mock_api.api_request.return_value = {
            "success": False, 
            "message": "API connection error"
        }
        
        # Call the list_vms method
        result = self.commands.list_vms()
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "API connection error")
        
        # Verify the API call
        self.mock_api.api_request.assert_called_once_with('GET', 'cluster/resources?type=vm')

    def test_start_vm_success(self):
        """Test starting a VM successfully"""
        # Mock API responses
        vm_location_response = {"success": True, "data": [
            {"vmid": "100", "node": "node1"}
        ]}
        
        start_vm_response = {"success": True, "data": {"upid": "task-123"}}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            vm_location_response,  # For get_vm_location
            start_vm_response,     # For VM start
        ]
        
        # Call the start_vm method
        result = self.commands.start_vm("100")
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 100 started successfully")
        
        # Verify the API calls
        expected_calls = [
            ('GET', 'cluster/resources?type=vm'),  # For get_vm_location
            ('POST', 'nodes/node1/qemu/100/status/start')  # For VM start
        ]
        
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])

    def test_start_vm_location_failure(self):
        """Test starting a VM when VM location lookup fails"""
        # Mock API response for VM location failure
        self.mock_api.api_request.return_value = {
            "success": True,
            "data": []  # Empty list means VM not found
        }
        
        # Call the start_vm method
        result = self.commands.start_vm("100")
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "VM 100 not found")
        
        # Verify the API call for get_vm_location
        self.mock_api.api_request.assert_called_once_with('GET', 'cluster/resources?type=vm')

    def test_start_vm_api_failure(self):
        """Test starting a VM when start API call fails"""
        # Mock API responses
        vm_location_response = {"success": True, "data": [
            {"vmid": "100", "node": "node1"}
        ]}
        
        start_vm_response = {"success": False, "message": "Failed to start VM"}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            vm_location_response,  # For get_vm_location
            start_vm_response,     # For VM start
        ]
        
        # Call the start_vm method
        result = self.commands.start_vm("100")
        
        # Verify the result
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Failed to start VM")
        
        # Verify the API calls
        expected_calls = [
            ('GET', 'cluster/resources?type=vm'),  # For get_vm_location
            ('POST', 'nodes/node1/qemu/100/status/start')  # For VM start
        ]
        
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])

    def test_stop_vm_success(self):
        """Test stopping a VM successfully"""
        # Mock API responses
        vm_location_response = {"success": True, "data": [
            {"vmid": "100", "node": "node1"}
        ]}
        
        stop_vm_response = {"success": True, "data": {"upid": "task-123"}}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            vm_location_response,  # For get_vm_location
            stop_vm_response,      # For VM stop
        ]
        
        # Call the stop_vm method
        result = self.commands.stop_vm("100")
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 100 stopped successfully")
        
        # Verify the API calls
        expected_calls = [
            ('GET', 'cluster/resources?type=vm'),  # For get_vm_location
            ('POST', 'nodes/node1/qemu/100/status/stop')  # For VM stop
        ]
        
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])

    def test_restart_vm_success(self):
        """Test restarting a VM successfully"""
        # Mock API responses
        vm_location_response = {"success": True, "data": [
            {"vmid": "100", "node": "node1"}
        ]}
        
        restart_vm_response = {"success": True, "data": {"upid": "task-123"}}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            vm_location_response,  # For get_vm_location
            restart_vm_response,   # For VM restart
        ]
        
        # Call the restart_vm method
        result = self.commands.restart_vm("100")
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 100 restarted successfully")
        
        # Verify the API calls
        expected_calls = [
            ('GET', 'cluster/resources?type=vm'),  # For get_vm_location
            ('POST', 'nodes/node1/qemu/100/status/reset')  # For VM restart
        ]
        
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])

    def test_create_vm_success(self):
        """Test creating a VM successfully"""
        # Mock API responses for node selection and VM creation
        nodes_response = {"success": True, "data": [
            {"node": "node1", "cpu": 0.1, "maxcpu": 8},
            {"node": "node2", "cpu": 0.5, "maxcpu": 8}
        ]}
        
        vmid_response = {"success": True, "data": 100}
        
        create_vm_response = {"success": True, "data": {"upid": "task-123"}}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            nodes_response,      # For get_available_nodes
            vmid_response,       # For get_next_vmid
            create_vm_response,  # For VM creation
        ]
        
        # Call the create_vm method with params
        vm_params = {
            "name": "test-vm",
            "memory": 2048,
            "cores": 2,
            "disk": 32
        }
        
        result = self.commands.create_vm(vm_params)
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 100 created successfully on node node1")
        
        # Verify the API calls
        expected_calls = [
            ('GET', 'nodes'),  # For get_available_nodes
            ('GET', 'cluster/nextid'),  # For get_next_vmid
            ('POST', 'nodes/node1/qemu')  # For VM creation
        ]
        
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])
            
        # Check that the create_vm API call was made with the correct parameters
        create_vm_call = self.mock_api.api_request.call_args_list[2]
        args, kwargs = create_vm_call
        
        # Verify that some of the key parameters were passed correctly
        self.assertEqual(args[2].get('vmid'), 100)
        self.assertEqual(args[2].get('name'), 'test-vm')
        self.assertEqual(args[2].get('memory'), 2048)
        self.assertEqual(args[2].get('cores'), 2)
        self.assertEqual(args[2].get('scsi0'), 'local-lvm:32')

    def test_delete_vm_success(self):
        """Test deleting a VM successfully"""
        # Mock API responses
        vm_location_response = {"success": True, "data": [
            {"vmid": "100", "node": "node1"}
        ]}
        
        delete_vm_response = {"success": True, "data": {"upid": "task-123"}}
        
        # Set up the mock API to return the expected responses
        self.mock_api.api_request.side_effect = [
            vm_location_response,  # For get_vm_location
            delete_vm_response,    # For VM deletion
        ]
        
        # Call the delete_vm method
        result = self.commands.delete_vm("100")
        
        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "VM 100 deleted successfully")
        
        # Verify the API calls
        expected_calls = [
            ('GET', 'cluster/resources?type=vm'),  # For get_vm_location
            ('DELETE', 'nodes/node1/qemu/100')  # For VM deletion
        ]
        
        self.assertEqual(len(self.mock_api.api_request.call_args_list), len(expected_calls))
        for i, call in enumerate(self.mock_api.api_request.call_args_list):
            args, kwargs = call
            self.assertEqual(args[0], expected_calls[i][0])
            self.assertEqual(args[1], expected_calls[i][1])


if __name__ == '__main__':
    unittest.main()