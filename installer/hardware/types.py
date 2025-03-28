"""Hardware compatibility and driver types."""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class HardwareCompatibility:
    """Hardware compatibility check result."""
    component: str
    is_compatible: bool
    message: str
    severity: str  # "info", "warning", or "critical"
    fallback_available: bool
    fallback_option: Optional[str] = None
    fallback_description: Optional[str] = None

@dataclass
class DriverInfo:
    """Driver information."""
    device_id: str
    device_name: str
    driver_name: str
    is_installed: bool
    status: str  # "working", "error", "missing", "unknown"
    install_method: Optional[str] = None
    package_name: Optional[str] = None
    install_commands: Optional[List[str]] = None