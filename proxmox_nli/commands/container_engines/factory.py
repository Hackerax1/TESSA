"""
Container engine factory.

Provides a factory for creating the appropriate container engine based on configuration
or detection of installed engines on the target VM.
"""
import logging
from typing import Dict, Optional, List, Any
from .base_engine import ContainerEngine
from .docker_engine import DockerEngine
from .podman_engine import PodmanEngine

logger = logging.getLogger(__name__)

class ContainerEngineFactory:
    """Factory for container engines."""
    
    def __init__(self, api):
        """Initialize factory with API client"""
        self.api = api
        self._engines = {
            'docker': DockerEngine(api),
            'podman': PodmanEngine(api)
        }
        # Default engine to use when no preference specified
        self._default_engine = 'docker'
    
    def get_engine(self, engine_name: Optional[str] = None) -> ContainerEngine:
        """
        Get a container engine by name or use default.
        
        Args:
            engine_name: Name of the container engine to get. If None, returns the default engine.
            
        Returns:
            ContainerEngine: The requested container engine
            
        Raises:
            ValueError: If the requested engine is not supported
        """
        if not engine_name:
            engine_name = self._default_engine
            
        engine_name = engine_name.lower()
        
        if engine_name not in self._engines:
            raise ValueError(f"Unsupported container engine: {engine_name}")
            
        return self._engines[engine_name]
    
    def detect_available_engines(self, vm_id: str, node: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect which container engines are available on the given VM.
        
        Args:
            vm_id: ID of the VM to check
            node: Optional node name where VM is located
            
        Returns:
            Dict containing results with available engines and their versions
        """
        available_engines = {}
        errors = []
        
        for engine_name, engine in self._engines.items():
            try:
                result = engine.is_installed(vm_id, node)
                if result['success'] and result.get('installed', False):
                    available_engines[engine_name] = {
                        'version': result.get('version', 'Unknown'),
                        'engine': engine
                    }
            except Exception as e:
                errors.append(f"Error checking {engine_name}: {str(e)}")
                logger.error(f"Error checking {engine_name} on VM {vm_id}: {str(e)}")
        
        return {
            "success": True,
            "available_engines": available_engines,
            "preferred_engine": self._select_preferred_engine(available_engines),
            "errors": errors
        }
    
    def _select_preferred_engine(self, available_engines: Dict[str, Dict]) -> Optional[str]:
        """
        Select the preferred engine from available engines.
        
        Args:
            available_engines: Dictionary of available engines
            
        Returns:
            Name of the preferred engine or None if no engines are available
        """
        if not available_engines:
            return None
            
        # Preference order: docker, podman, others
        for engine_name in ['docker', 'podman']:
            if engine_name in available_engines:
                return engine_name
                
        # If none of the preferred engines are available, return the first one
        return list(available_engines.keys())[0]
    
    def register_engine(self, name: str, engine: ContainerEngine) -> None:
        """
        Register a new container engine.
        
        Args:
            name: Name of the engine
            engine: Engine implementation
        """
        self._engines[name.lower()] = engine
        
    def set_default_engine(self, engine_name: str) -> None:
        """
        Set the default container engine.
        
        Args:
            engine_name: Name of the engine to set as default
            
        Raises:
            ValueError: If the specified engine is not supported
        """
        if engine_name.lower() not in self._engines:
            raise ValueError(f"Cannot set default engine: {engine_name} is not supported")
            
        self._default_engine = engine_name.lower()
        
    def get_supported_engines(self) -> List[str]:
        """
        Get list of supported container engines.
        
        Returns:
            List of supported engine names
        """
        return list(self._engines.keys())