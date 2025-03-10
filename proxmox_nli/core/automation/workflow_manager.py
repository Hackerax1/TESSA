"""
Workflow manager module for Proxmox NLI.
Handles execution and tracking of multi-step automated workflows.
"""
import logging
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class StepStatus(Enum):
    """Workflow step status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowManager:
    """Manages execution of multi-step workflows"""
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the workflow manager
        
        Args:
            storage_path: Path to store workflow definitions and state
        """
        self.workflows = {}
        self.running_workflows = {}
        
        if storage_path:
            self.storage_path = storage_path
        else:
            # Default to a directory in the user's home
            self.storage_path = os.path.expanduser(os.path.join("~", ".proxmox_nli", "workflows"))
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load existing workflow definitions
        self._load_workflows()
    
    def _load_workflows(self):
        """Load workflow definitions from storage"""
        try:
            workflows_path = os.path.join(self.storage_path, "workflow_definitions.json")
            if os.path.exists(workflows_path):
                with open(workflows_path, 'r') as f:
                    self.workflows = json.load(f)
                logger.info(f"Loaded {len(self.workflows)} workflow definitions")
        except Exception as e:
            logger.error(f"Error loading workflow definitions: {str(e)}")
    
    def _save_workflows(self):
        """Save workflow definitions to storage"""
        try:
            workflows_path = os.path.join(self.storage_path, "workflow_definitions.json")
            with open(workflows_path, 'w') as f:
                json.dump(self.workflows, f)
            logger.info(f"Saved {len(self.workflows)} workflow definitions")
        except Exception as e:
            logger.error(f"Error saving workflow definitions: {str(e)}")
    
    def define_workflow(self, name: str, description: str = "", steps: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Define a new workflow
        
        Args:
            name: Name of the workflow
            description: Description of the workflow
            steps: List of workflow steps
            
        Returns:
            Dict with workflow definition
        """
        workflow_id = str(uuid.uuid4())
        
        workflow = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "steps": steps or []
        }
        
        self.workflows[workflow_id] = workflow
        self._save_workflows()
        
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a workflow definition by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflow definitions"""
        return list(self.workflows.values())
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow definition"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            self._save_workflows()
            return True
        return False
    
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a workflow definition"""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow not found: {workflow_id}")
            return None
        
        # Update allowed fields
        allowed_fields = ["name", "description", "steps"]
        for field in allowed_fields:
            if field in updates:
                self.workflows[workflow_id][field] = updates[field]
        
        self.workflows[workflow_id]["updated_at"] = datetime.now().isoformat()
        self._save_workflows()
        
        return self.workflows[workflow_id]
    
    def execute_workflow(self, workflow_id: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a workflow
        
        Args:
            workflow_id: ID of the workflow to execute
            params: Parameters for the workflow execution
            
        Returns:
            Dict with execution information
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return {
                "success": False,
                "message": f"Workflow not found: {workflow_id}"
            }
        
        execution_id = str(uuid.uuid4())
        
        # Create execution context
        execution = {
            "id": execution_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow["name"],
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": WorkflowStatus.RUNNING.value,
            "params": params or {},
            "steps": [],
            "results": {},
            "current_step": 0
        }
        
        # Initialize steps
        for i, step in enumerate(workflow["steps"]):
            execution["steps"].append({
                "index": i,
                "name": step["name"],
                "status": StepStatus.PENDING.value if i > 0 else StepStatus.RUNNING.value,
                "started_at": datetime.now().isoformat() if i == 0 else None,
                "completed_at": None,
                "result": None
            })
        
        # Store execution
        self.running_workflows[execution_id] = execution
        
        # Start execution in a separate thread
        import threading
        thread = threading.Thread(target=self._process_workflow_steps, args=(execution_id,))
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "message": f"Workflow execution started: {workflow['name']}",
            "execution_id": execution_id
        }
    
    def _process_workflow_steps(self, execution_id: str):
        """
        Process workflow steps in sequence
        
        Args:
            execution_id: ID of the execution to process
        """
        if execution_id not in self.running_workflows:
            logger.error(f"Execution not found: {execution_id}")
            return
        
        execution = self.running_workflows[execution_id]
        workflow_id = execution["workflow_id"]
        workflow = self.get_workflow(workflow_id)
        
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            execution["status"] = WorkflowStatus.FAILED.value
            execution["updated_at"] = datetime.now().isoformat()
            return
        
        try:
            # Process each step
            for i, step in enumerate(workflow["steps"]):
                # Skip steps that aren't pending
                if execution["steps"][i]["status"] != StepStatus.PENDING.value and i != 0:
                    continue
                
                # Update step status
                execution["steps"][i]["status"] = StepStatus.RUNNING.value
                execution["steps"][i]["started_at"] = datetime.now().isoformat()
                execution["current_step"] = i
                
                # Execute the step
                try:
                    # This is where we would typically call the function defined by the step
                    # For now, we'll just simulate success
                    logger.info(f"Executing step {i}: {step['name']}")
                    
                    # Simulate step execution
                    import time
                    time.sleep(1)  # Simulate work
                    
                    # Save step result
                    execution["steps"][i]["status"] = StepStatus.COMPLETED.value
                    execution["steps"][i]["completed_at"] = datetime.now().isoformat()
                    execution["steps"][i]["result"] = {"success": True, "message": "Step completed"}
                    
                except Exception as e:
                    # Handle step failure
                    logger.error(f"Error executing step {i}: {str(e)}")
                    execution["steps"][i]["status"] = StepStatus.FAILED.value
                    execution["steps"][i]["completed_at"] = datetime.now().isoformat()
                    execution["steps"][i]["result"] = {"success": False, "message": str(e)}
                    
                    # Mark workflow as failed
                    execution["status"] = WorkflowStatus.FAILED.value
                    execution["updated_at"] = datetime.now().isoformat()
                    return
            
            # If all steps completed successfully
            execution["status"] = WorkflowStatus.COMPLETED.value
            execution["updated_at"] = datetime.now().isoformat()
            execution["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            # Handle overall workflow failure
            logger.error(f"Error processing workflow: {str(e)}")
            execution["status"] = WorkflowStatus.FAILED.value
            execution["updated_at"] = datetime.now().isoformat()
            execution["error"] = str(e)
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow execution"""
        return self.running_workflows.get(execution_id)
    
    def list_executions(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """
        List workflow executions
        
        Args:
            workflow_id: Optional ID to filter by workflow
            
        Returns:
            List of executions
        """
        if workflow_id:
            return [exec for exec in self.running_workflows.values() 
                   if exec["workflow_id"] == workflow_id]
        else:
            return list(self.running_workflows.values())
    
    def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """Cancel a running workflow execution"""
        if execution_id not in self.running_workflows:
            return {
                "success": False,
                "message": f"Execution not found: {execution_id}"
            }
        
        execution = self.running_workflows[execution_id]
        if execution["status"] not in [WorkflowStatus.RUNNING.value, WorkflowStatus.PENDING.value]:
            return {
                "success": False,
                "message": f"Cannot cancel execution with status: {execution['status']}"
            }
        
        # Update execution status
        execution["status"] = WorkflowStatus.CANCELLED.value
        execution["updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": f"Execution cancelled: {execution_id}"
        }
    
    def add_workflow_step(self, workflow_id: str, step_name: str, 
                         step_type: str, step_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add a step to a workflow
        
        Args:
            workflow_id: ID of the workflow
            step_name: Name of the step
            step_type: Type of step (function, api_call, etc)
            step_params: Parameters for the step
            
        Returns:
            Dict with operation result
        """
        if workflow_id not in self.workflows:
            return {
                "success": False,
                "message": f"Workflow not found: {workflow_id}"
            }
        
        workflow = self.workflows[workflow_id]
        
        # Create new step
        step = {
            "name": step_name,
            "type": step_type,
            "params": step_params or {}
        }
        
        # Add step to workflow
        workflow["steps"].append(step)
        workflow["updated_at"] = datetime.now().isoformat()
        self._save_workflows()
        
        return {
            "success": True,
            "message": f"Step added to workflow: {step_name}",
            "workflow": workflow
        }
    
    def remove_workflow_step(self, workflow_id: str, step_index: int) -> Dict[str, Any]:
        """
        Remove a step from a workflow
        
        Args:
            workflow_id: ID of the workflow
            step_index: Index of the step to remove
            
        Returns:
            Dict with operation result
        """
        if workflow_id not in self.workflows:
            return {
                "success": False,
                "message": f"Workflow not found: {workflow_id}"
            }
        
        workflow = self.workflows[workflow_id]
        
        if step_index < 0 or step_index >= len(workflow["steps"]):
            return {
                "success": False,
                "message": f"Invalid step index: {step_index}"
            }
        
        # Remove step
        removed_step = workflow["steps"].pop(step_index)
        workflow["updated_at"] = datetime.now().isoformat()
        self._save_workflows()
        
        return {
            "success": True,
            "message": f"Step removed from workflow: {removed_step['name']}",
            "workflow": workflow
        }
    
    def update_workflow_step(self, workflow_id: str, step_index: int, 
                            updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a workflow step
        
        Args:
            workflow_id: ID of the workflow
            step_index: Index of the step to update
            updates: Dict with fields to update
            
        Returns:
            Dict with operation result
        """
        if workflow_id not in self.workflows:
            return {
                "success": False,
                "message": f"Workflow not found: {workflow_id}"
            }
        
        workflow = self.workflows[workflow_id]
        
        if step_index < 0 or step_index >= len(workflow["steps"]):
            return {
                "success": False,
                "message": f"Invalid step index: {step_index}"
            }
        
        # Update step fields
        for key, value in updates.items():
            if key in ["name", "type", "params"]:
                workflow["steps"][step_index][key] = value
        
        workflow["updated_at"] = datetime.now().isoformat()
        self._save_workflows()
        
        return {
            "success": True,
            "message": f"Step updated: {workflow['steps'][step_index]['name']}",
            "workflow": workflow
        }