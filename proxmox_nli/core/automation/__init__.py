"""
Automation module for Proxmox NLI.

This module handles task scheduling, workflow automation, and recurring operations.
"""

from .task_scheduler import TaskScheduler
from .workflow_manager import WorkflowManager
from .job_queue import JobQueue
from .task_executor import TaskExecutor

__all__ = ['TaskScheduler', 'WorkflowManager', 'JobQueue', 'TaskExecutor']