"""
Job queue module for Proxmox NLI.
Handles job scheduling, prioritization, and execution.
"""
import logging
import threading
import queue
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Union
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class Job:
    """Represents a job in the queue"""
    
    def __init__(self, func: Callable, args: tuple = None, kwargs: dict = None, 
                 name: str = None, priority: JobPriority = JobPriority.NORMAL,
                 timeout: int = None):
        """
        Initialize a job
        
        Args:
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            name: Name of the job
            priority: Priority level
            timeout: Timeout in seconds
        """
        self.id = str(uuid.uuid4())
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.name = name or func.__name__
        self.priority = priority
        self.timeout = timeout
        
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority.name,
            "status": self.status.name,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": str(self.error) if self.error else None
        }

class JobQueue:
    """Queue for managing and executing jobs"""
    
    def __init__(self, num_workers: int = 1, storage_path: str = None):
        """
        Initialize the job queue
        
        Args:
            num_workers: Number of worker threads
            storage_path: Path to store job history
        """
        self.job_queue = queue.PriorityQueue()
        self.jobs = {}  # Storage for job objects by ID
        self.num_workers = num_workers
        self.workers = []
        self.running = False
        self.lock = threading.Lock()
        self.job_history = []
        self.max_history = 1000  # Maximum number of completed jobs to keep in history
        
        if storage_path:
            self.storage_path = storage_path
        else:
            # Default to a directory in the user's home
            self.storage_path = os.path.expanduser(os.path.join("~", ".proxmox_nli", "jobs"))
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load job history
        self._load_job_history()
    
    def _load_job_history(self):
        """Load job history from storage"""
        try:
            history_path = os.path.join(self.storage_path, "job_history.json")
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    self.job_history = json.load(f)
                logger.info(f"Loaded {len(self.job_history)} jobs from history")
        except Exception as e:
            logger.error(f"Error loading job history: {str(e)}")
    
    def _save_job_history(self):
        """Save job history to storage"""
        try:
            # Limit history size
            if len(self.job_history) > self.max_history:
                self.job_history = self.job_history[-self.max_history:]
            
            history_path = os.path.join(self.storage_path, "job_history.json")
            with open(history_path, 'w') as f:
                json.dump(self.job_history, f)
        except Exception as e:
            logger.error(f"Error saving job history: {str(e)}")
    
    def start(self):
        """Start worker threads"""
        if self.running:
            logger.warning("Job queue is already running")
            return False
        
        self.running = True
        
        # Create and start worker threads
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.num_workers} worker threads")
        return True
    
    def stop(self):
        """Stop worker threads"""
        self.running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=2)
        
        self.workers = []
        logger.info("Job queue stopped")
        
        # Save job history
        self._save_job_history()
    
    def _worker_loop(self):
        """Worker thread function"""
        while self.running:
            try:
                # Get job from queue with timeout to allow checking running status
                try:
                    priority, job_id = self.job_queue.get(timeout=0.5)
                    job = self.jobs.get(job_id)
                    
                    if not job:
                        # Job may have been cancelled
                        self.job_queue.task_done()
                        continue
                    
                    # Process the job
                    self._process_job(job)
                    
                    # Mark task as done
                    self.job_queue.task_done()
                    
                except queue.Empty:
                    # Queue is empty, continue checking running status
                    continue
                
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
                time.sleep(1)  # Avoid tight loops on error
    
    def _process_job(self, job: Job):
        """Process a job"""
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            # Execute job function with timeout if specified
            if job.timeout:
                # Setup a timer to handle timeout
                timer = threading.Timer(job.timeout, self._handle_timeout, args=[job])
                timer.start()
                
                # Execute function
                result = job.func(*job.args, **job.kwargs)
                
                # Cancel timer if job completes before timeout
                timer.cancel()
            else:
                # Execute without timeout
                result = job.func(*job.args, **job.kwargs)
            
            # Update job with result
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
            logger.info(f"Job completed: {job.name}")
            
        except Exception as e:
            # Handle job failure
            job.error = str(e)
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            
            logger.error(f"Job failed: {job.name} - {str(e)}")
        
        # Add to job history
        with self.lock:
            self.job_history.append(job.to_dict())
            # Save periodically
            if len(self.job_history) % 10 == 0:
                self._save_job_history()
    
    def _handle_timeout(self, job: Job):
        """Handle job timeout"""
        # This runs in a separate thread when job times out
        if job.status == JobStatus.RUNNING:
            job.error = "Job timed out"
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            
            logger.error(f"Job timed out: {job.name}")
            
            # Add to job history
            with self.lock:
                self.job_history.append(job.to_dict())
                # Save periodically
                if len(self.job_history) % 10 == 0:
                    self._save_job_history()
    
    def submit(self, func: Callable, args: tuple = None, kwargs: dict = None,
               name: str = None, priority: JobPriority = JobPriority.NORMAL,
               timeout: int = None) -> str:
        """
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
        """
        # Create job
        job = Job(func, args, kwargs, name, priority, timeout)
        
        # Store job
        self.jobs[job.id] = job
        
        # Add to queue with priority (negated for highest-first ordering)
        self.job_queue.put((-job.priority.value, job.id))
        
        logger.info(f"Job submitted: {job.name} (priority: {job.priority.name})")
        
        return job.id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status and details
        
        Args:
            job_id: Job ID
            
        Returns:
            Job details dictionary or None if not found
        """
        # First check active jobs
        job = self.jobs.get(job_id)
        if job:
            return job.to_dict()
        
        # Then check job history
        for job_data in self.job_history:
            if job_data["id"] == job_id:
                return job_data
        
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job
        
        Args:
            job_id: Job ID
            
        Returns:
            True if job was cancelled, False otherwise
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Job not found: {job_id}")
            return False
        
        # Can only cancel pending jobs
        if job.status != JobStatus.PENDING:
            logger.warning(f"Cannot cancel job with status: {job.status.name}")
            return False
        
        # Update job status
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        
        # Add to job history
        with self.lock:
            self.job_history.append(job.to_dict())
        
        # Remove from active jobs
        del self.jobs[job_id]
        
        logger.info(f"Job cancelled: {job.name}")
        
        return True
    
    def list_jobs(self, status: JobStatus = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List jobs with optional filtering
        
        Args:
            status: Filter by job status
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dictionaries
        """
        # Get active jobs
        active_jobs = [job.to_dict() for job in self.jobs.values()]
        
        # Combine with history
        all_jobs = active_jobs + self.job_history
        
        # Filter by status if requested
        if status:
            all_jobs = [j for j in all_jobs if j["status"] == status.name]
        
        # Sort by created time (descending)
        all_jobs.sort(key=lambda j: j["created_at"], reverse=True)
        
        # Apply limit
        return all_jobs[:limit]
    
    def clear_history(self) -> int:
        """
        Clear job history
        
        Returns:
            Number of jobs cleared
        """
        with self.lock:
            count = len(self.job_history)
            self.job_history = []
            self._save_job_history()
        
        logger.info(f"Cleared {count} jobs from history")
        return count