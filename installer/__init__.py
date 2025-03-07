"""
Proxmox NLI Installer Package
Provides a GUI wizard for installing and configuring the Proxmox NLI system.
"""
import tkinter as tk
from .gui import ProxmoxNLIInstaller

def create_installer():
    """Create and return a new installer instance"""
    root = tk.Tk()
    return ProxmoxNLIInstaller(root)