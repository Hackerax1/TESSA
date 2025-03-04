"""
Services module for handling deployment of common self-hosted services.
This module provides functionality to deploy, configure, and manage various
services through Proxmox VE using natural language commands.
"""

from .service_catalog import ServiceCatalog
from .service_manager import ServiceManager

__all__ = ['ServiceCatalog', 'ServiceManager']