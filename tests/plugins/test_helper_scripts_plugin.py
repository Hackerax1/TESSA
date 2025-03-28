"""
Integration test for the Proxmox VE Helper-Scripts plugin.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from proxmox_nli.plugins.helper_scripts.plugin import ProxmoxHelperScriptsPlugin
from proxmox_nli.core.core_nli import ProxmoxNLI

class TestHelperScriptsPlugin(unittest.TestCase):
    """Test the Proxmox VE Helper-Scripts plugin."""
    
    def setUp(self):
        """Set up a test environment for the plugin."""
        self.plugin = ProxmoxHelperScriptsPlugin()
        
        # Create a mock NLI instance
        self.mock_nli = MagicMock(spec=ProxmoxNLI)
        
        # Create a temp directory for script downloads
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('requests.get')
    def test_plugin_initialization(self, mock_get):
        """Test the plugin initialization."""
        # Mock the responses from the GitHub API
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = [
            {"name": "backup", "type": "dir"},
            {"name": "storage", "type": "dir"}
        ]
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = [
            {"name": "backup-vm.sh", "type": "file"},
            {"name": "README.md", "type": "file"}
        ]
        
        mock_response3 = MagicMock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = [
            {"name": "zfs-snapshot.sh", "type": "file"},
            {"name": "README.md", "type": "file"}
        ]
        
        # Configure the mock to return different responses for different URLs
        mock_get.side_effect = lambda url, **kwargs: {
            f"{self.plugin.REPO_API_URL}/scripts": mock_response1,
            f"{self.plugin.REPO_API_URL}/scripts/backup": mock_response2,
            f"{self.plugin.REPO_API_URL}/scripts/storage": mock_response3
        }.get(url, MagicMock(status_code=404))
        
        # Set up temporary scripts directory
        self.plugin._scripts_dir = self.temp_dir
        
        # Initialize the plugin
        with patch('os.makedirs'):
            result = self.plugin.initialize(self.mock_nli)
            
        self.assertTrue(result)
        self.assertEqual(self.plugin.name, "Proxmox VE Helper-Scripts")
        self.assertEqual(self.plugin.version, "1.0.0")
    
    @patch('requests.get')
    def test_list_helper_scripts(self, mock_get):
        """Test listing helper scripts."""
        # Similar to the initialization test but focusing on the list functionality
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = [
            {"name": "backup", "type": "dir"},
            {"name": "network", "type": "dir"}
        ]
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = [
            {"name": "backup-vm.sh", "type": "file"},
        ]
        
        mock_response3 = MagicMock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = [
            {"name": "setup-vlan.sh", "type": "file"},
        ]
        
        # Configure the mock
        mock_get.side_effect = lambda url, **kwargs: {
            f"{self.plugin.REPO_API_URL}/scripts": mock_response1,
            f"{self.plugin.REPO_API_URL}/scripts/backup": mock_response2,
            f"{self.plugin.REPO_API_URL}/scripts/network": mock_response3
        }.get(url, MagicMock(status_code=404))
        
        # Initialize the plugin
        with patch('os.makedirs'):
            self.plugin.initialize(self.mock_nli)
        
        # Test list all categories
        result = self.plugin.list_helper_scripts()
        self.assertIn('categories', result)
        self.assertEqual(len(result['categories']), 2)
        
        # Test list specific category
        result = self.plugin.list_helper_scripts('backup')
        self.assertEqual(result['category'], 'backup')
        self.assertEqual(len(result['scripts']), 1)
        self.assertEqual(result['scripts'][0]['name'], 'backup-vm.sh')
    
    @patch('requests.get')
    def test_search_helper_scripts(self, mock_get):
        """Test searching for helper scripts."""
        # Setup similar to previous tests
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = [
            {"name": "backup", "type": "dir"},
        ]
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = [
            {"name": "backup-vm.sh", "type": "file"},
            {"name": "backup-container.sh", "type": "file"},
        ]
        
        # Configure the mock
        mock_get.side_effect = lambda url, **kwargs: {
            f"{self.plugin.REPO_API_URL}/scripts": mock_response1,
            f"{self.plugin.REPO_API_URL}/scripts/backup": mock_response2,
        }.get(url, MagicMock(status_code=404))
        
        # Initialize the plugin
        with patch('os.makedirs'):
            self.plugin.initialize(self.mock_nli)
        
        # Test search
        result = self.plugin.search_helper_scripts('vm')
        self.assertEqual(result['query'], 'vm')
        self.assertEqual(result['results_count'], 1)
        self.assertEqual(result['results'][0]['name'], 'backup-vm.sh')

if __name__ == '__main__':
    unittest.main()