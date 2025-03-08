from typing import Dict, List, Optional, Any, NamedTuple

class HardwareCompatibility(NamedTuple):
    """Result of hardware compatibility check with possible fallback options."""
    component: str
    is_compatible: bool
    message: str
    severity: str  # 'critical', 'warning', or 'info'
    fallback_available: bool
    fallback_option: Optional[str] = None
    fallback_description: Optional[str] = None

class DriverInfo(NamedTuple):
    """Information about a hardware driver."""
    device_id: str           # PCI/USB ID or other identifier
    device_name: str         # Human-readable device name
    driver_name: str         # Current driver name if installed, or recommended driver
    is_installed: bool       # Whether the driver is currently installed
    status: str              # 'working', 'missing', 'outdated', etc.
    install_method: str      # How to install: 'package', 'module', 'firmware', etc.
    package_name: Optional[str] = None  # Package name if applicable
    source_url: Optional[str] = None    # Source URL for manual download
    install_commands: Optional[List[str]] = None  # Commands to run for installation