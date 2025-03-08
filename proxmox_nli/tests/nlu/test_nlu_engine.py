import pytest
from unittest.mock import Mock, patch
from ...nlu.nlu_engine import NLU_Engine
from ...nlu.preprocessing import Preprocessor
from ...nlu.context_management import ContextManager
from ...nlu.entity_extraction import EntityExtractor
from ...nlu.intent_identification import IntentIdentifier
from ...nlu.ollama_client import OllamaClient

@pytest.fixture
def nlu_engine():
    """Create a base NLU engine instance for testing"""
    return NLU_Engine(use_ollama=False)  # Disable Ollama for basic tests

@pytest.fixture
def nlu_engine_with_ollama():
    """Create an NLU engine instance with Ollama for integration tests"""
    return NLU_Engine(use_ollama=True, ollama_model="llama3", ollama_url="http://localhost:11434")

class TestPreprocessing:
    def test_preprocessing_basic(self, nlu_engine):
        """Test basic query preprocessing"""
        query = "Start MY-VM-123 please"
        preprocessed = nlu_engine.preprocessor.preprocess_query(query)
        assert isinstance(preprocessed, str)
        assert len(preprocessed) > 0
        assert preprocessed.lower() == preprocessed  # Should be lowercase

    def test_preprocessing_special_chars(self, nlu_engine):
        """Test preprocessing with special characters"""
        query = "Start VM-123! And make it quick..."
        preprocessed = nlu_engine.preprocessor.preprocess_query(query)
        assert isinstance(preprocessed, str)
        assert "vm-123" in preprocessed.lower()

class TestEntityExtraction:
    def test_basic_entity_extraction(self, nlu_engine):
        """Test basic entity extraction"""
        query = "start vm-123"
        entities = nlu_engine.entity_extractor.extract_entities(query)
        assert isinstance(entities, dict)
        assert "vm_name" in entities
        assert entities["vm_name"] == "vm-123"

    def test_multiple_entities(self, nlu_engine):
        """Test extracting multiple entities"""
        query = "clone vm-123 to new-vm with 2GB RAM"
        entities = nlu_engine.entity_extractor.extract_entities(query)
        assert isinstance(entities, dict)
        assert "source_vm" in entities
        assert "target_vm" in entities
        assert "memory" in entities

class TestIntentIdentification:
    def test_basic_intent(self, nlu_engine):
        """Test basic intent identification"""
        query = "start vm-123"
        intent, args = nlu_engine.intent_identifier.identify_intent(query)
        assert isinstance(intent, str)
        assert intent == "start_vm"
        assert isinstance(args, list)

    def test_compound_intent(self, nlu_engine):
        """Test identification of more complex intents"""
        query = "create a new VM called test-vm with 2GB RAM and 2 CPUs"
        intent, args = nlu_engine.intent_identifier.identify_intent(query)
        assert intent == "create_vm"
        assert isinstance(args, list)

class TestContextManagement:
    def test_context_update(self, nlu_engine):
        """Test context updating"""
        query = "start vm-123"
        intent = "start_vm"
        entities = {"vm_name": "vm-123"}
        nlu_engine.context_manager.update_context(intent, entities)
        context = nlu_engine.context_manager.get_active_context()
        assert isinstance(context, dict)
        assert "current_vm" in context
        assert context["current_vm"] == "vm-123"

    def test_context_resolution(self, nlu_engine):
        """Test resolving references from context"""
        # Set up initial context
        nlu_engine.context_manager.update_context("start_vm", {"vm_name": "vm-123"})
        
        # Test resolution of "it" reference
        query = "stop it"
        entities = {}
        resolved = nlu_engine.context_manager.resolve_contextual_references(query, entities)
        assert "vm_name" in resolved
        assert resolved["vm_name"] == "vm-123"

@pytest.mark.integration
class TestOllamaIntegration:
    def test_ollama_intent_extraction(self, nlu_engine_with_ollama):
        """Test Ollama-based intent extraction"""
        query = "I want to create a new virtual machine called test-vm"
        intent, args, entities = nlu_engine_with_ollama.process_query(query)
        assert isinstance(intent, str)
        assert intent == "create_vm"
        assert "vm_name" in entities
        assert entities["vm_name"] == "test-vm"

    def test_ollama_fallback(self, nlu_engine_with_ollama):
        """Test fallback to traditional NLU when Ollama fails"""
        with patch.object(OllamaClient, 'get_intent_and_entities', side_effect=Exception("Ollama error")):
            query = "start vm-123"
            intent, args, entities = nlu_engine_with_ollama.process_query(query)
            assert isinstance(intent, str)
            assert intent == "start_vm"
            assert "vm_name" in entities

class TestEndToEnd:
    def test_full_query_processing(self, nlu_engine):
        """Test complete query processing pipeline"""
        query = "start vm-123 and wait for it to be ready"
        intent, args, entities = nlu_engine.process_query(query)
        assert isinstance(intent, str)
        assert isinstance(args, list)
        assert isinstance(entities, dict)
        assert intent == "start_vm"
        assert "vm_name" in entities
        assert entities["vm_name"] == "vm-123"

    def test_conversation_flow(self, nlu_engine):
        """Test processing a sequence of related queries"""
        # First query
        intent1, args1, entities1 = nlu_engine.process_query("start vm-123")
        assert intent1 == "start_vm"
        assert entities1["vm_name"] == "vm-123"

        # Follow-up query using context
        intent2, args2, entities2 = nlu_engine.process_query("stop it")
        assert intent2 == "stop_vm"
        assert entities2["vm_name"] == "vm-123"  # Should be resolved from context

    def test_error_handling(self, nlu_engine):
        """Test graceful handling of invalid queries"""
        query = ""  # Empty query
        intent, args, entities = nlu_engine.process_query(query)
        assert intent == "help"  # Should default to help intent
        assert isinstance(args, list)
        assert isinstance(entities, dict)