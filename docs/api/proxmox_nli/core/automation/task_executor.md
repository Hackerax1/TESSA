# task_executor

Task executor module for Proxmox NLI.
Handles execution of tasks across different execution contexts.

**Module Path**: `proxmox_nli.core.automation.task_executor`

## Classes

### TaskExecutor

Handles execution of tasks in different contexts

#### __init__(api)

Initialize the task executor

#### execute_shell_command(command: str, node: str, background: bool = None, timeout: int = False)

Execute a shell command locally or on a Proxmox node

Args:
    command: Shell command to execute
    node: Proxmox node name (if None, run locally)
    background: Whether to run in background
    timeout: Command timeout in seconds
    
Returns:
    Dict with execution result

**Returns**: `Dict[(str, Any)]`

#### execute_api_call(method: str, path: str, data: Dict[(str, Any)], node: str = None)

Execute an API call to Proxmox

Args:
    method: HTTP method (GET, POST, PUT, DELETE)
    path: API path
    data: Request data
    node: Optional node name to target
    
Returns:
    Dict with API response

**Returns**: `Dict[(str, Any)]`

#### execute_python_function(func: Callable, args: tuple, kwargs: dict = None, timeout: int = None)

Execute a Python function

Args:
    func: Function to execute
    args: Positional arguments
    kwargs: Keyword arguments
    timeout: Execution timeout in seconds
    
Returns:
    Dict with execution result

**Returns**: `Dict[(str, Any)]`

#### get_task_status(task_id: str)

Get the status of a task

Args:
    task_id: Task ID
    
Returns:
    Dict with task status

**Returns**: `Dict[(str, Any)]`

#### list_running_tasks()

List all running tasks

**Returns**: `List[Dict[(str, Any)]]`

#### list_all_tasks()

List all tasks

**Returns**: `List[Dict[(str, Any)]]`

#### cancel_task(task_id: str)

Cancel a running task

Args:
    task_id: Task ID
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

