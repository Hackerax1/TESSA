"""
Test for the Hugging Face client implementation
"""
import pytest
from unittest.mock import patch, MagicMock
import json
import os
from proxmox_nli.nlu.huggingface_client import HuggingFaceClient

class TestHuggingFaceClient:
    @patch('proxmox_nli.nlu.huggingface_client.requests')
    def test_init_and_verify_connection(self, mock_requests):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        # Create client with test parameters
        client = HuggingFaceClient(
            model_name="test-model",
            api_key="test-api-key",
            base_url="https://test-url/models/"
        )
        
        # Verify requests were made correctly
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert call_args[0][0] == "https://test-url/models/test-model"
        assert call_args[1]['headers']['Authorization'] == "Bearer test-api-key"

    @patch('proxmox_nli.nlu.huggingface_client.requests')
    def test_format_json_response(self, mock_requests):
        client = HuggingFaceClient(api_key="test-key")
        
        # Test direct JSON parsing
        valid_json = '{"intent": "list_vms", "args": [], "entities": {"VM_ID": "123"}}'
        parsed = client._format_json_response(valid_json)
        assert parsed == {
            "intent": "list_vms",
            "args": [],
            "entities": {"VM_ID": "123"}
        }
        
        # Test JSON extraction from text
        text_with_json = 'Here is the JSON: {"intent": "start_vm", "args": [], "entities": {"VM_ID": "456"}}'
        parsed = client._format_json_response(text_with_json)
        assert parsed == {
            "intent": "start_vm",
            "args": [],
            "entities": {"VM_ID": "456"}
        }
        
        # Test fallback for invalid JSON
        invalid_json = "This is not valid JSON"
        parsed = client._format_json_response(invalid_json)
        assert parsed == {"intent": "unknown", "args": [], "entities": {}}

    @patch('proxmox_nli.nlu.huggingface_client.requests')
    def test_get_intent_and_entities(self, mock_requests):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": '{"intent": "start_vm", "args": [], "entities": {"VM_ID": "123"}}'}
        ]
        mock_requests.post.return_value = mock_response
        
        # Create client and test
        client = HuggingFaceClient(api_key="test-key")
        intent, args, entities = client.get_intent_and_entities("Start VM 123")
        
        # Verify correct parsing
        assert intent == "start_vm"
        assert args == []
        assert entities == {"VM_ID": "123"}
        
        # Check that context is updated
        assert len(client.context) == 1
        assert client.context[0]["query"] == "Start VM 123"
        assert client.context[0]["intent"] == "start_vm"

    @patch('proxmox_nli.nlu.huggingface_client.requests')
    def test_get_intent_with_conversation_history(self, mock_requests):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": '{"intent": "stop_vm", "args": [], "entities": {"VM_ID": "123"}}'}
        ]
        mock_requests.post.return_value = mock_response
        
        # Create client
        client = HuggingFaceClient(api_key="test-key")
        
        # Create conversation history
        history = [
            {"query": "Show me VM 123", "intent": "vm_status", "entities": {"VM_ID": "123"}},
            {"query": "What is its status?", "intent": "vm_status", "entities": {"VM_ID": "123"}}
        ]
        
        # Run test with history
        intent, args, entities = client.get_intent_and_entities("Stop it", history)
        
        # Check that history was included in the request
        request_body = mock_requests.post.call_args[1]['json']
        assert "Previous conversation context" in request_body['inputs'][1]['content']
        
        # Verify correct parsing
        assert intent == "stop_vm"
        assert entities == {"VM_ID": "123"}

    @patch('proxmox_nli.nlu.huggingface_client.requests')
    def test_enhance_response(self, mock_requests):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"generated_text": "VM 123 has been started successfully."}
        ]
        mock_requests.post.return_value = mock_response
        
        # Create client and test
        client = HuggingFaceClient(api_key="test-key")
        result = {"success": True, "vm_id": "123"}
        
        response = client.enhance_response("Start VM 123", "start_vm", result)
        
        # Verify enhancement
        assert response == "VM 123 has been started successfully."
        
        # Check that the API call included the result data
        request_body = mock_requests.post.call_args[1]['json']
        assert "Result data" in request_body['inputs'][1]['content']
        assert "123" in request_body['inputs'][1]['content']

    @patch('proxmox_nli.nlu.huggingface_client.requests')
    def test_error_handling(self, mock_requests):
        # Setup mock response for error
        mock_response = MagicMock()
        mock_response.status_code = 401  # Unauthorized
        mock_requests.post.return_value = mock_response
        
        # Create client with invalid credentials
        client = HuggingFaceClient(api_key="invalid-key")
        
        # Test error handling in intent extraction
        intent, args, entities = client.get_intent_and_entities("Start VM 123")
        assert intent == "unknown"
        assert args == []
        assert entities == {}