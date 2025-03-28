"""
Test script for conversation memory and natural transitions.

This script demonstrates how the conversation memory and natural transitions work
by simulating a conversation with the NLI.
"""
import os
import sys
import logging
import uuid
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from proxmox_nli.core.base_nli import BaseNLI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockNLU:
    """Mock NLU engine for testing."""
    
    def __init__(self):
        """Initialize the mock NLU engine."""
        from proxmox_nli.nlu.context_management import ContextManager
        self.context_manager = ContextManager()
        
    def get_intent_and_entities(self, query):
        """Mock intent and entity extraction."""
        query_lower = query.lower()
        
        # Default response
        intent = "unknown"
        entities = {}
        
        # VM related intents
        if "virtual machine" in query_lower or " vm" in query_lower or "vms" in query_lower:
            intent = "list_vms"
            
        if "start" in query_lower and ("vm" in query_lower or "virtual machine" in query_lower):
            intent = "start_vm"
            entities = {"vm_name": "vm-100"}
            
        if "stop" in query_lower or "shutdown" in query_lower:
            intent = "stop_vm"
            entities = {"vm_name": "vm-100"}
            
        if "create" in query_lower and ("vm" in query_lower or "virtual machine" in query_lower):
            intent = "create_vm"
            
        # Backup related intents
        if "backup" in query_lower:
            intent = "backup_info"
            
        if "schedule" in query_lower or "how often" in query_lower:
            intent = "backup_schedule"
            
        # Network related intents
        if "network" in query_lower:
            intent = "network_info"
            
        if "bridge" in query_lower:
            intent = "network_bridge"
            entities = {"bridge_name": "vmbr0"}
            
        if "connect" in query_lower and "vm" in query_lower and "bridge" in query_lower:
            intent = "connect_vm_network"
            entities = {"vm_name": "vm-100", "bridge_name": "vmbr0"}
            
        # Memory/recall intents
        if "remember" in query_lower or "talked about" in query_lower or "discussed" in query_lower:
            if "backup" in query_lower:
                intent = "recall_topic"
                entities = {"topic": "backup"}
            elif "vm" in query_lower:
                intent = "recall_topic"
                entities = {"topic": "virtual machine"}
                
        return {"intent": intent, "entities": entities}

class TestNLI(BaseNLI):
    """Test NLI class with mock responses."""
    
    def __init__(self):
        """Initialize the test NLI."""
        super().__init__()
        
        # Register mock commands
        self.register_command("list_vms", self.list_vms, "List virtual machines")
        self.register_command("start_vm", self.start_vm, "Start a virtual machine")
        self.register_command("stop_vm", self.stop_vm, "Stop a virtual machine")
        self.register_command("create_vm", self.create_vm, "Create a virtual machine")
        self.register_command("backup_info", self.backup_info, "Get backup information")
        self.register_command("backup_schedule", self.backup_schedule, "Get backup schedule recommendations")
        self.register_command("network_info", self.network_info, "Get network information")
        self.register_command("network_bridge", self.network_bridge, "Get bridge setup information")
        self.register_command("connect_vm_network", self.connect_vm_network, "Connect VM to network bridge")
        self.register_command("recall_topic", self.recall_topic, "Recall previous conversation topic")
        
        # Set mock NLU engine
        self.set_nlu_engine(MockNLU())
    
    def list_vms(self, nli, entities, args):
        """Mock list VMs command."""
        return {"success": True, "message": "You have 3 virtual machines: vm-100 (Ubuntu), vm-101 (Debian), and vm-102 (Windows)."}
    
    def start_vm(self, nli, entities, args):
        """Mock start VM command."""
        vm_name = entities.get("vm_name", "unknown VM")
        return {"success": True, "message": f"Starting {vm_name}. The VM will be available in a few seconds."}
    
    def stop_vm(self, nli, entities, args):
        """Mock stop VM command."""
        vm_name = entities.get("vm_name", "unknown VM")
        return {"success": True, "message": f"Stopping {vm_name}. The VM will be shut down gracefully."}
    
    def create_vm(self, nli, entities, args):
        """Mock create VM command."""
        return {"success": True, "message": "To create a new VM, you need to specify the OS template, CPU cores, memory, and disk size. Would you like me to guide you through the process?"}
    
    def backup_info(self, nli, entities, args):
        """Mock backup info command."""
        return {"success": True, "message": "Proxmox VE includes a built-in backup solution that allows you to create consistent backups of your VMs and containers. You can schedule backups, set retention policies, and restore from backups easily."}
    
    def backup_schedule(self, nli, entities, args):
        """Mock backup schedule command."""
        return {"success": True, "message": "For most home lab environments, I recommend daily backups for critical VMs and weekly backups for less important ones. You should also consider keeping at least 7 daily backups, 4 weekly backups, and 2 monthly backups for a good retention policy."}
    
    def network_info(self, nli, entities, args):
        """Mock network info command."""
        return {"success": True, "message": "Proxmox VE networking is based on Linux networking. You can configure bridges, bonds, VLANs, and more to create complex network setups for your virtual environment."}
    
    def network_bridge(self, nli, entities, args):
        """Mock network bridge command."""
        return {"success": True, "message": "To set up a bridge in Proxmox, go to the node's Network view, click Create, and select Linux Bridge. You'll need to specify a name (like vmbr0), and optionally assign an IP address if this bridge will be used for the node's connectivity."}
    
    def connect_vm_network(self, nli, entities, args):
        """Mock connect VM to network command."""
        vm_name = entities.get("vm_name", "unknown VM")
        bridge_name = entities.get("bridge_name", "unknown bridge")
        return {"success": True, "message": f"Yes, you can connect {vm_name} to {bridge_name}. Edit the VM's hardware configuration, add a network device, and select {bridge_name} as the bridge."}
    
    def recall_topic(self, nli, entities, args):
        """Mock recall previous topic command."""
        topic = entities.get("topic", "unknown topic")
        if topic == "backup":
            return {"success": True, "message": "Yes, we did discuss backups before. I mentioned that Proxmox has a built-in backup solution that allows you to create consistent backups of your VMs and containers."}
        elif topic == "virtual machine":
            return {"success": True, "message": "Yes, we previously talked about virtual machines. I mentioned that you have 3 VMs and we discussed how to start and stop them."}
        return {"success": True, "message": f"I don't recall discussing {topic} before."}

def main():
    """Run the conversation memory test."""
    # Initialize the test NLI
    nli = TestNLI()
    
    # Generate a unique user ID for testing
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    # Start a session
    nli.start_user_session(user_id)
    
    # Simulate a conversation
    print("\n=== Starting Conversation Test ===\n")
    
    # First conversation about VMs
    print("User: Tell me about my virtual machines")
    result = nli.process_query("Tell me about my virtual machines", user_id)
    print(f"TESSA: {result['message']}\n")
    
    print("User: How do I start a VM?")
    result = nli.process_query("How do I start a VM?", user_id)
    print(f"TESSA: {result['message']}\n")
    
    print("User: What about stopping it?")
    result = nli.process_query("What about stopping it?", user_id)
    print(f"TESSA: {result['message']}\n")
    
    # Switch to a different topic
    print("User: Tell me about backups")
    result = nli.process_query("Tell me about backups", user_id)
    print(f"TESSA: {result['message']}\n")
    
    print("User: How often should I run backups?")
    result = nli.process_query("How often should I run backups?", user_id)
    print(f"TESSA: {result['message']}\n")
    
    # Return to the VM topic
    print("User: Going back to VMs, how do I create a new one?")
    result = nli.process_query("Going back to VMs, how do I create a new one?", user_id)
    print(f"TESSA: {result['message']}\n")
    
    # Simulate ending the session
    print("=== Session Ended ===\n")
    
    # Simulate starting a new session later
    print("=== Starting New Session ===\n")
    
    # Create a new session ID
    nli.session_id = str(uuid.uuid4())
    
    # Start a new session with the same user
    nli.start_user_session(user_id)
    
    # Reference previous conversation
    print("User: Remember we talked about backups yesterday?")
    result = nli.process_query("Remember we talked about backups yesterday?", user_id)
    print(f"TESSA: {result['message']}\n")
    
    print("User: What was that schedule you recommended?")
    result = nli.process_query("What was that schedule you recommended?", user_id)
    print(f"TESSA: {result['message']}\n")
    
    # Switch to a new topic
    print("User: Let's talk about network configuration")
    result = nli.process_query("Let's talk about network configuration", user_id)
    print(f"TESSA: {result['message']}\n")
    
    print("User: How do I set up a bridge?")
    result = nli.process_query("How do I set up a bridge?", user_id)
    print(f"TESSA: {result['message']}\n")
    
    # Reference VM topic from first session
    print("User: Can I connect my VMs to this bridge?")
    result = nli.process_query("Can I connect my VMs to this bridge?", user_id)
    print(f"TESSA: {result['message']}\n")
    
    print("\n=== Test Complete ===")
    
    # Print topic and memory stats
    print("\n=== Topic History ===")
    print(f"Current topic: {nli.topic_manager.current_topic}")
    print(f"Previous topic: {nli.topic_manager.previous_topic}")
    print(f"Topic history: {nli.topic_manager.topic_history}")
    
    # Get memory stats
    try:
        with open(nli.memory_manager.db_path, 'r') as f:
            print(f"\nMemory database created at: {nli.memory_manager.db_path}")
    except:
        print(f"\nMemory database created at: {nli.memory_manager.db_path}")

if __name__ == "__main__":
    main()
