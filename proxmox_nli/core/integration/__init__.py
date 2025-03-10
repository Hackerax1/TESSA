"""
Integration module for Proxmox NLI.

This module handles integration with external systems and cloud providers.
"""

from .cloud_provider import CloudProvider
from .dns_provider import DNSProvider
from .monitoring_integration import MonitoringIntegration
from .identity_provider import IdentityProvider
from .environment_merger import EnvironmentMerger

__all__ = ['CloudProvider', 'DNSProvider', 'MonitoringIntegration', 'IdentityProvider', 'EnvironmentMerger']