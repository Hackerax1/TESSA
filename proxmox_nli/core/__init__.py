"""
Core functionality module.

This module contains the core functionality that ties together all the components
of the Proxmox NLI system, including the main ProxmoxNLI class, response generator,
and interface modes.
"""

from .core_nli import ProxmoxNLI
from .cli import cli_mode
from .web import web_mode
from .response_generator import ResponseGenerator

__all__ = ['ProxmoxNLI', 'ResponseGenerator', 'cli_mode', 'web_mode']