# workflow_manager

Workflow manager module for Proxmox NLI.
Handles execution and tracking of multi-step automated workflows.

**Module Path**: `proxmox_nli.core.automation.workflow_manager`

## Classes

### WorkflowStatus

Workflow status enum

### StepStatus

Workflow step status enum

### WorkflowManager

Manages execution of multi-step workflows

#### __init__(storage_path: str)

Initialize the workflow manager

Args:
    storage_path: Path to store workflow definitions and state

#### define_workflow(name: str, description: str, steps: List[Dict[(str, Any)]] = '')

Define a new workflow

Args:
    name: Name of the workflow
    description: Description of the workflow
    steps: List of workflow steps
    
Returns:
    Dict with workflow definition

**Returns**: `Dict[(str, Any)]`

#### get_workflow(workflow_id: str)

Get a workflow definition by ID

**Returns**: `Optional[Dict[(str, Any)]]`

#### list_workflows()

List all workflow definitions

**Returns**: `List[Dict[(str, Any)]]`

#### delete_workflow(workflow_id: str)

Delete a workflow definition

**Returns**: `bool`

#### update_workflow(workflow_id: str, updates: Dict[(str, Any)])

Update a workflow definition

**Returns**: `Optional[Dict[(str, Any)]]`

#### execute_workflow(workflow_id: str, params: Dict[(str, Any)])

Execute a workflow

Args:
    workflow_id: ID of the workflow to execute
    params: Parameters for the workflow execution
    
Returns:
    Dict with execution information

**Returns**: `Dict[(str, Any)]`

#### get_execution_status(execution_id: str)

Get the status of a workflow execution

**Returns**: `Optional[Dict[(str, Any)]]`

#### list_executions(workflow_id: str)

List workflow executions

Args:
    workflow_id: Optional ID to filter by workflow
    
Returns:
    List of executions

**Returns**: `List[Dict[(str, Any)]]`

#### cancel_execution(execution_id: str)

Cancel a running workflow execution

**Returns**: `Dict[(str, Any)]`

#### add_workflow_step(workflow_id: str, step_name: str, step_type: str, step_params: Dict[(str, Any)])

Add a step to a workflow

Args:
    workflow_id: ID of the workflow
    step_name: Name of the step
    step_type: Type of step (function, api_call, etc)
    step_params: Parameters for the step
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### remove_workflow_step(workflow_id: str, step_index: int)

Remove a step from a workflow

Args:
    workflow_id: ID of the workflow
    step_index: Index of the step to remove
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### update_workflow_step(workflow_id: str, step_index: int, updates: Dict[(str, Any)])

Update a workflow step

Args:
    workflow_id: ID of the workflow
    step_index: Index of the step to update
    updates: Dict with fields to update
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

