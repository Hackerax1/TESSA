# job_queue

Job queue module for Proxmox NLI.
Handles job scheduling, prioritization, and execution.

**Module Path**: `proxmox_nli.core.automation.job_queue`

## Classes

### JobStatus

Job status enum

### JobPriority

Job priority levels

### Job

Represents a job in the queue

#### __init__(func: Callable, args: tuple, kwargs: dict = None, name: str = None, priority: JobPriority = None, timeout: int = ...)

Initialize a job

Args:
    func: Function to execute
    args: Positional arguments for the function
    kwargs: Keyword arguments for the function
    name: Name of the job
    priority: Priority level
    timeout: Timeout in seconds

#### to_dict()

Convert job to dictionary

**Returns**: `Dict[(str, Any)]`

### JobQueue

Queue for managing and executing jobs

#### __init__(num_workers: int, storage_path: str = 1)

Initialize the job queue

Args:
    num_workers: Number of worker threads
    storage_path: Path to store job history

#### start()

Start worker threads

#### stop()

Stop worker threads

#### submit(func: Callable, args: tuple, kwargs: dict = None, name: str = None, priority: JobPriority = None, timeout: int = ...)

Submit a job to the queue

Args:
    func: Function to execute
    args: Positional arguments
    kwargs: Keyword arguments
    name: Job name
    priority: Job priority
    timeout: Timeout in seconds
    
Returns:
    Job ID

**Returns**: `str`

#### get_job(job_id: str)

Get job status and details

Args:
    job_id: Job ID
    
Returns:
    Job details dictionary or None if not found

**Returns**: `Optional[Dict[(str, Any)]]`

#### cancel_job(job_id: str)

Cancel a pending job

Args:
    job_id: Job ID
    
Returns:
    True if job was cancelled, False otherwise

**Returns**: `bool`

#### list_jobs(status: JobStatus, limit: int = None)

List jobs with optional filtering

Args:
    status: Filter by job status
    limit: Maximum number of jobs to return
    
Returns:
    List of job dictionaries

**Returns**: `List[Dict[(str, Any)]]`

#### clear_history()

Clear job history

Returns:
    Number of jobs cleared

**Returns**: `int`

