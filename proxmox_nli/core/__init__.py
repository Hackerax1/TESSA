"""
Core functionality module.

This module contains the core functionality that ties together all the components
of the Proxmox NLI system, including the main ProxmoxNLI class.
"""

from .proxmox_nli import ProxmoxNLI, cli_mode, web_mode

__all__ = ['ProxmoxNLI', 'cli_mode', 'web_mode']