# task_scheduler

Task scheduler module for Proxmox NLI.
Handles scheduling and management of recurring tasks.

**Module Path**: `proxmox_nli.core.automation.task_scheduler`

## Classes

### TaskScheduler

Handles scheduling and execution of recurring tasks

#### __init__()

#### start()

Start the scheduler in a background thread

#### stop()

Stop the scheduler

#### schedule_task(task_id: str, func: Callable, interval: Union[(str, int)])

Schedule a task to run at specified intervals

Args:
    task_id: Unique identifier for the task
    func: Function to call
    interval: Either a string like "daily", "hourly", or number of minutes
    *args, **kwargs: Arguments to pass to the function

**Returns**: `bool`

#### schedule_at_time(task_id: str, func: Callable, time_str: str)

Schedule a task to run daily at a specific time

Args:
    task_id: Unique identifier for the task
    func: Function to call
    time_str: Time string in HH:MM format (24-hour)
    *args, **kwargs: Arguments to pass to the function

**Returns**: `bool`

#### schedule_cron(task_id: str, func: Callable, cron_expression: str)

Schedule a task using cron-like expressions (limited support via schedule package)

Args:
    task_id: Unique identifier for the task
    func: Function to call
    cron_expression: Limited cron expression (see schedule package)
    *args, **kwargs: Arguments to pass to the function

**Returns**: `bool`

#### cancel_task(task_id: str)

Cancel a scheduled task

**Returns**: `bool`

#### list_tasks()

List all scheduled tasks

**Returns**: `List[Dict[(str, Any)]]`

#### get_task(task_id: str)

Get details about a specific task

**Returns**: `Optional[Dict[(str, Any)]]`

