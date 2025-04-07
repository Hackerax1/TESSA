"""
Base container engine interface.

Defines the common interface that all container engines must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class ContainerEngine(ABC):
    """Base interface for all container engines."""
    
    @abstractmethod
    def list_containers(self, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """List containers on a VM"""
        pass
    
    @abstractmethod
    def start_container(self, container_name: str, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Start a container"""
        pass
    
    @abstractmethod
    def stop_container(self, container_name: str, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Stop a container"""
        pass
    
    @abstractmethod
    def get_container_logs(self, container_name: str, vm_id: str, node: Optional[str] = None, lines: int = 10) -> Dict[str, Any]:
        """Get container logs"""
        pass
    
    @abstractmethod
    def get_container_info(self, container_name: str, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed container information"""
        pass
    
    @abstractmethod
    def pull_image(self, image_name: str, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Pull a container image"""
        pass
    
    @abstractmethod
    def run_container(self, 
                      image_name: str, 
                      vm_id: str, 
                      node: Optional[str] = None,
                      container_name: Optional[str] = None, 
                      ports: Optional[List[str]] = None,
                      volumes: Optional[List[str]] = None,
                      environment: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run a container"""
        pass
    
    @abstractmethod
    def list_images(self, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """List container images on a VM"""
        pass
    
    @abstractmethod
    def get_compose_command(self) -> str:
        """Get the compose command (docker-compose, podman-compose, etc.)"""
        pass
    
    @abstractmethod
    def is_installed(self, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """Check if the container engine is installed on the VM"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get container engine name"""
        pass