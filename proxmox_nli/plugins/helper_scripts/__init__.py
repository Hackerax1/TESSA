"""
Proxmox VE Helper-Scripts plugin for Proxmox NLI.

This plugin integrates with the community-maintained Proxmox VE Helper-Scripts repository
(https://community-scripts.github.io/ProxmoxVE/scripts) to allow users to browse, download,
and execute helper scripts from the community repository.
"""

from .plugin import ProxmoxHelperScriptsPlugin

__all__ = ['ProxmoxHelperScriptsPlugin']