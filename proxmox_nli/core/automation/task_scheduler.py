"""
Task scheduler module for Proxmox NLI.
Handles scheduling and management of recurring tasks.
"""
import logging
import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any, Optional, Union

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Handles scheduling and execution of recurring tasks"""
    
    def __init__(self):
        self.tasks = {}
        self.scheduler_thread = None
        self.running = False
        self.lock = threading.Lock()
        
    def start(self):
        """Start the scheduler in a background thread"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler is already running")
            return False
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Task scheduler started")
        return True
        
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
        logger.info("Task scheduler stopped")
        
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            with self.lock:
                schedule.run_pending()
            time.sleep(1)
    
    def schedule_task(self, task_id: str, func: Callable, interval: Union[str, int], *args, **kwargs) -> bool:
        """
        Schedule a task to run at specified intervals
        
        Args:
            task_id: Unique identifier for the task
            func: Function to call
            interval: Either a string like "daily", "hourly", or number of minutes
            *args, **kwargs: Arguments to pass to the function
        """
        with self.lock:
            # Cancel existing task if present
            if task_id in self.tasks:
                self.cancel_task(task_id)
            
            # Create a wrapper function that includes the task_id
            def task_wrapper():
                try:
                    logger.info(f"Running scheduled task: {task_id}")
                    result = func(*args, **kwargs)
                    logger.info(f"Task completed: {task_id}")
                    return result
                except Exception as e:
                    logger.error(f"Error in scheduled task {task_id}: {str(e)}")
                    return None
            
            # Schedule according to interval type
            job = None
            if isinstance(interval, str):
                if interval.lower() == "yearly" or interval.lower() == "annually":
                    job = schedule.every().year.do(task_wrapper)
                elif interval.lower() == "monthly":
                    job = schedule.every().month.do(task_wrapper)
                elif interval.lower() == "weekly":
                    job = schedule.every().week.do(task_wrapper)
                elif interval.lower() == "daily":
                    job = schedule.every().day.do(task_wrapper)
                elif interval.lower() == "hourly":
                    job = schedule.every().hour.do(task_wrapper)
                elif interval.lower() == "minutely":
                    job = schedule.every().minute.do(task_wrapper)
                else:
                    logger.error(f"Invalid interval string: {interval}")
                    return False
            elif isinstance(interval, int):
                # Schedule to run every X minutes
                job = schedule.every(interval).minutes.do(task_wrapper)
            else:
                logger.error(f"Invalid interval type: {type(interval)}")
                return False
            
            if job:
                self.tasks[task_id] = job
                logger.info(f"Scheduled task {task_id} with interval {interval}")
                return True
            
            return False
    
    def schedule_at_time(self, task_id: str, func: Callable, time_str: str, *args, **kwargs) -> bool:
        """
        Schedule a task to run daily at a specific time
        
        Args:
            task_id: Unique identifier for the task
            func: Function to call
            time_str: Time string in HH:MM format (24-hour)
            *args, **kwargs: Arguments to pass to the function
        """
        with self.lock:
            # Cancel existing task if present
            if task_id in self.tasks:
                self.cancel_task(task_id)
                
            # Create a wrapper function
            def task_wrapper():
                try:
                    logger.info(f"Running scheduled task at time: {task_id}")
                    result = func(*args, **kwargs)
                    logger.info(f"Task completed: {task_id}")
                    return result
                except Exception as e:
                    logger.error(f"Error in scheduled task {task_id}: {str(e)}")
                    return None
            
            try:
                # Parse the time string
                hour, minute = map(int, time_str.split(':'))
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    raise ValueError("Invalid time format")
                    
                # Schedule the job to run daily at specified time
                job = schedule.every().day.at(time_str).do(task_wrapper)
                self.tasks[task_id] = job
                logger.info(f"Scheduled task {task_id} to run daily at {time_str}")
                return True
            except Exception as e:
                logger.error(f"Error scheduling task at time: {str(e)}")
                return False
    
    def schedule_cron(self, task_id: str, func: Callable, cron_expression: str, *args, **kwargs) -> bool:
        """
        Schedule a task using cron-like expressions (limited support via schedule package)
        
        Args:
            task_id: Unique identifier for the task
            func: Function to call
            cron_expression: Limited cron expression (see schedule package)
            *args, **kwargs: Arguments to pass to the function
        """
        logger.warning("Cron expressions have limited support. Using at() and every() methods instead.")
        # This is a placeholder - the schedule package doesn't directly support cron expressions
        # We would need to parse the cron expression and convert to schedule's syntax
        
        # For now, just log a warning that this isn't fully implemented
        logger.error("schedule_cron is not fully implemented yet")
        return False
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        with self.lock:
            if task_id in self.tasks:
                schedule.cancel_job(self.tasks[task_id])
                del self.tasks[task_id]
                logger.info(f"Cancelled task: {task_id}")
                return True
            else:
                logger.warning(f"Task not found: {task_id}")
                return False
                
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks"""
        with self.lock:
            tasks_list = []
            for task_id, job in self.tasks.items():
                next_run = job.next_run
                next_run_str = next_run.isoformat() if next_run else None
                
                tasks_list.append({
                    "id": task_id,
                    "next_run": next_run_str,
                    "interval": str(job.interval),
                    "unit": str(job.unit) if hasattr(job, 'unit') else None,
                    "at_time": str(job.at_time) if hasattr(job, 'at_time') else None
                })
            
            return tasks_list
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get details about a specific task"""
        with self.lock:
            if task_id in self.tasks:
                job = self.tasks[task_id]
                next_run = job.next_run
                next_run_str = next_run.isoformat() if next_run else None
                
                return {
                    "id": task_id,
                    "next_run": next_run_str,
                    "interval": str(job.interval),
                    "unit": str(job.unit) if hasattr(job, 'unit') else None,
                    "at_time": str(job.at_time) if hasattr(job, 'at_time') else None
                }
            
            return None