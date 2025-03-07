"""
GUI tabs package for the Proxmox NLI installer.
Each tab represents a step in the installation process.
"""

from .welcome import create_welcome_tab
from .prerequisites import create_prerequisites_tab
from .config import create_config_tab 
from .install import create_install_tab

__all__ = [
    'create_welcome_tab',
    'create_prerequisites_tab',
    'create_config_tab',
    'create_install_tab'
]