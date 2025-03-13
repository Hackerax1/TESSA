"""
Services module for handling deployment of common self-hosted services.
This module provides functionality to deploy, configure, and manage various
services through Proxmox VE using natural language commands.
"""

# Base service management
from .service_catalog import ServiceCatalog
from .service_manager import ServiceManager

# Goal-based service organization
from .goal_mapper import GoalMapper
from .goal_based_catalog import GoalBasedCatalog
from .goal_based_setup import GoalBasedSetupWizard

# Dependency management
from .dependency_manager import DependencyManager

# Importing deployment submodule
from . import deployment

__all__ = [
    'ServiceCatalog',
    'ServiceManager',
    'GoalMapper',
    'GoalBasedCatalog',
    'GoalBasedSetupWizard',
    'DependencyManager',
    'deployment'
]