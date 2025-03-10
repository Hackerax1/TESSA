"""
Task executor module for Proxmox NLI.
Handles execution of tasks across different execution contexts.
"""
import logging
import os
import json
import time
import threading
import subprocess
from typing import Dict, List, Any, Callable, Optional, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class TaskExecutor:
    """Handles execution of tasks in different contexts"""
    
    def __init__(self, api=None):
        """Initialize the task executor"""
        self.api = api
        self.running_tasks = {}
        self.lock = threading.Lock()
        self.config_dir = os.path.expanduser(os.path.join("~", ".proxmox_nli", "tasks"))
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
    
    def execute_shell_command(self, command: str, node: str = None, background: bool = False,
                             timeout: int = 60) -> Dict[str, Any]:
        """
        Execute a shell command locally or on a Proxmox node
        
        Args:
            command: Shell command to execute
            node: Proxmox node name (if None, run locally)
            background: Whether to run in background
            timeout: Command timeout in seconds
            
        Returns:
            Dict with execution result
        """
        task_id = str(uuid.uuid4())
        
        # Create task record
        task = {
            "id": task_id,
            "type": "shell",
            "command": command,
            "node": node,
            "background": background,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        
        # Store task in running tasks
        with self.lock:
            self.running_tasks[task_id] = task
        
        try:
            if node and self.api:
                # Run on Proxmox node
                result = self.api.api_request('POST', f'nodes/{node}/execute', {
                    'command': command
                })
                
                if not result['success']:
                    task["status"] = "failed"
                    task["error"] = result.get('message', 'Unknown error')
                    task["completed_at"] = datetime.now().isoformat()
                    return {
                        "success": False,
                        "task_id": task_id,
                        "message": task["error"]
                    }
                
                # Store result
                task["status"] = "completed"
                task["output"] = result['data'].get('stdout', '')
                task["error_output"] = result['data'].get('stderr', '')
                task["exit_code"] = result['data'].get('exitcode', 0)
                task["completed_at"] = datetime.now().isoformat()
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "output": task["output"],
                    "error_output": task["error_output"],
                    "exit_code": task["exit_code"]
                }
            else:
                # Run locally
                if background:
                    # Run in background
                    process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Store process for later checking
                    task["process"] = process
                    
                    return {
                        "success": True,
                        "task_id": task_id,
                        "message": f"Command running in background: {command}",
                        "background": True
                    }
                else:
                    # Run synchronously
                    process = subprocess.run(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=timeout
                    )
                    
                    # Store result
                    task["status"] = "completed"
                    task["output"] = process.stdout
                    task["error_output"] = process.stderr
                    task["exit_code"] = process.returncode
                    task["completed_at"] = datetime.now().isoformat()
                    
                    return {
                        "success": process.returncode == 0,
                        "task_id": task_id,
                        "output": process.stdout,
                        "error_output": process.stderr,
                        "exit_code": process.returncode
                    }
        
        except subprocess.TimeoutExpired:
            task["status"] = "failed"
            task["error"] = f"Command timed out after {timeout} seconds"
            task["completed_at"] = datetime.now().isoformat()
            
            return {
                "success": False,
                "task_id": task_id,
                "message": task["error"]
            }
        
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            task["completed_at"] = datetime.now().isoformat()
            
            return {
                "success": False,
                "task_id": task_id,
                "message": str(e)
            }
    
    def execute_api_call(self, method: str, path: str, data: Dict[str, Any] = None,
                        node: str = None) -> Dict[str, Any]:
        """
        Execute an API call to Proxmox
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path
            data: Request data
            node: Optional node name to target
            
        Returns:
            Dict with API response
        """
        if not self.api:
            return {
                "success": False,
                "message": "API client not available"
            }
        
        task_id = str(uuid.uuid4())
        
        # Create task record
        task = {
            "id": task_id,
            "type": "api",
            "method": method,
            "path": path,
            "data": data,
            "node": node,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        
        # Store task in running tasks
        with self.lock:
            self.running_tasks[task_id] = task
        
        try:
            # Modify path if node is specified
            if node and not path.startswith(f'nodes/{node}'):
                if path.startswith('/'):
                    path = path[1:]
                path = f'nodes/{node}/{path}'
            
            # Execute API call
            result = self.api.api_request(method, path, data)
            
            # Store result
            task["status"] = "completed" if result["success"] else "failed"
            task["result"] = result
            task["completed_at"] = datetime.now().isoformat()
            
            return {
                "success": result["success"],
                "task_id": task_id,
                "result": result
            }
            
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            task["completed_at"] = datetime.now().isoformat()
            
            return {
                "success": False,
                "task_id": task_id,
                "message": str(e)
            }
    
    def execute_python_function(self, func: Callable, args: tuple = None, kwargs: dict = None,
                              timeout: int = None) -> Dict[str, Any]:
        """
        Execute a Python function
        
        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            timeout: Execution timeout in seconds
            
        Returns:
            Dict with execution result
        """
        task_id = str(uuid.uuid4())
        
        # Create task record
        task = {
            "id": task_id,
            "type": "python",
            "function": func.__name__,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        
        # Store task in running tasks
        with self.lock:
            self.running_tasks[task_id] = task
        
        try:
            args = args or ()
            kwargs = kwargs or {}
            
            # Execute with optional timeout
            if timeout:
                import threading
                result_container = {}
                exception_container = {}
                
                def target():
                    try:
                        result_container['result'] = func(*args, **kwargs)
                    except Exception as e:
                        exception_container['exception'] = e
                
                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout)
                
                if thread.is_alive():
                    # Function call timed out
                    task["status"] = "failed"
                    task["error"] = f"Function timed out after {timeout} seconds"
                    task["completed_at"] = datetime.now().isoformat()
                    
                    return {
                        "success": False,
                        "task_id": task_id,
                        "message": task["error"]
                    }
                
                if 'exception' in exception_container:
                    # Function raised an exception
                    task["status"] = "failed"
                    task["error"] = str(exception_container['exception'])
                    task["completed_at"] = datetime.now().isoformat()
                    
                    return {
                        "success": False,
                        "task_id": task_id,
                        "message": task["error"]
                    }
                
                # Function completed successfully
                task["status"] = "completed"
                task["result"] = result_container.get('result')
                task["completed_at"] = datetime.now().isoformat()
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "result": task["result"]
                }
            
            else:
                # Execute without timeout
                result = func(*args, **kwargs)
                
                # Store result
                task["status"] = "completed"
                task["result"] = result
                task["completed_at"] = datetime.now().isoformat()
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "result": result
                }
            
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            task["completed_at"] = datetime.now().isoformat()
            
            return {
                "success": False,
                "task_id": task_id,
                "message": str(e)
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict with task status
        """
        task = self.running_tasks.get(task_id)
        if not task:
            return {
                "success": False,
                "message": f"Task not found: {task_id}"
            }
        
        # If task is running and has a background process, check its status
        if task["status"] == "running" and task.get("type") == "shell" and task.get("background", False):
            process = task.get("process")
            if process:
                if process.poll() is not None:
                    # Process has completed
                    stdout, stderr = process.communicate()
                    
                    task["status"] = "completed"
                    task["output"] = stdout
                    task["error_output"] = stderr
                    task["exit_code"] = process.returncode
                    task["completed_at"] = datetime.now().isoformat()
        
        # Return task info
        return {
            "success": True,
            "task": task
        }
    
    def list_running_tasks(self) -> List[Dict[str, Any]]:
        """List all running tasks"""
        return [
            task for task in self.running_tasks.values()
            if task.get("status") == "running"
        ]
    
    def list_all_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks"""
        return list(self.running_tasks.values())
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a running task
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict with operation result
        """
        task = self.running_tasks.get(task_id)
        if not task:
            return {
                "success": False,
                "message": f"Task not found: {task_id}"
            }
        
        if task["status"] != "running":
            return {
                "success": False,
                "message": f"Task is not running: {task_id}"
            }
        
        # Handle cancellation based on task type
        if task.get("type") == "shell" and task.get("background", False):
            process = task.get("process")
            if process:
                try:
                    process.terminate()
                    task["status"] = "cancelled"
                    task["completed_at"] = datetime.now().isoformat()
                    
                    return {
                        "success": True,
                        "message": f"Task cancelled: {task_id}"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Failed to cancel task: {str(e)}"
                    }
        
        # For other task types, just mark as cancelled
        task["status"] = "cancelled"
        task["completed_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": f"Task cancelled: {task_id}"
        }