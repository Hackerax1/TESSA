"""
Container engines abstraction layer.

This module provides an abstraction layer for different container engines (Docker, Podman, etc.)
to allow interchangeable usage while maintaining a consistent interface.
"""

from .base_engine import ContainerEngine
from .docker_engine import DockerEngine
from .podman_engine import PodmanEngine
from .factory import ContainerEngineFactory

__all__ = ['ContainerEngine', 'DockerEngine', 'PodmanEngine', 'ContainerEngineFactory']