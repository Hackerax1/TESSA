import pytest
import requests
from unittest.mock import Mock, patch
from proxmox_nli.api.proxmox_api import ProxmoxAPI

# Register the integration mark
integration = pytest.mark.integration

@pytest.fixture
def api():
    """Create a ProxmoxAPI instance for testing"""
    return ProxmoxAPI(
        host="test.proxmox.local",
        user="test_user",
        password="test_pass",
        realm="pam",
        verify_ssl=False
    )

@pytest.fixture
def mock_response():
    """Create a mock response"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"data": {"result": "success"}}
    return response

@pytest.fixture
def authenticated_api(api, mock_response):
    """Create a pre-authenticated API instance"""
    mock_response.json.return_value = {
        "data": {
            "ticket": "test-ticket",
            "CSRFPreventionToken": "test-token"
        }
    }
    with patch("requests.post", return_value=mock_response):
        api.authenticate()
    return api

class TestAuthentication:
    def test_successful_auth(self, api, mock_response):
        """Test successful authentication"""
        mock_response.json.return_value = {
            "data": {
                "ticket": "test-ticket",
                "CSRFPreventionToken": "test-token"
            }
        }
        
        with patch("requests.post", return_value=mock_response):
            assert api.authenticate() is True
            assert api.ticket == "test-ticket"
            assert api.csrf_token == "test-token"

    def test_failed_auth(self, api):
        """Test failed authentication"""
        failed_response = Mock()
        failed_response.status_code = 401
        failed_response.text = "Authentication failed"
        
        with patch("requests.post", return_value=failed_response):
            assert api.authenticate() is False
            assert api.ticket is None
            assert api.csrf_token is None

class TestAPIRequests:
    def test_get_request(self, authenticated_api, mock_response):
        """Test GET request"""
        with patch("requests.get", return_value=mock_response):
            result = authenticated_api.api_request("GET", "nodes")
            assert result["success"] is True
            assert "data" in result

    def test_post_request(self, authenticated_api, mock_response):
        """Test POST request with data"""
        test_data = {"name": "test-vm", "memory": 1024}
        with patch("requests.post", return_value=mock_response):
            result = authenticated_api.api_request("POST", "nodes/node1/qemu", data=test_data)
            assert result["success"] is True
            assert "data" in result

    def test_request_without_auth(self, api):
        """Test request behavior when not authenticated"""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 401
            result = api.api_request("GET", "nodes")
            assert result["success"] is False
            assert "Authentication failed" in result["message"]

    def test_invalid_method(self, authenticated_api):
        """Test invalid HTTP method"""
        result = authenticated_api.api_request("INVALID", "nodes")
        assert result["success"] is False
        assert "Unsupported method" in result["message"]

    def test_connection_error(self, authenticated_api):
        """Test handling of connection errors"""
        with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
            result = authenticated_api.api_request("GET", "nodes")
            assert result["success"] is False
            assert "message" in result

@integration
class TestLiveAPI:
    """Integration tests for live Proxmox API - only run when configured"""
    
    @pytest.fixture
    def live_api(self):
        """Create a ProxmoxAPI instance for live testing - requires environment variables"""
        import os
        host = os.getenv("PROXMOX_HOST")
        user = os.getenv("PROXMOX_USER")
        password = os.getenv("PROXMOX_PASSWORD")
        
        if not all([host, user, password]):
            pytest.skip("Live API credentials not configured")
        
        return ProxmoxAPI(host, user, password)

    def test_live_auth(self, live_api):
        """Test authentication against live Proxmox server"""
        assert live_api.authenticate() is True

    def test_live_version(self, live_api):
        """Test getting version from live Proxmox server"""
        result = live_api.api_request("GET", "version")
        assert result["success"] is True
        assert "data" in result