"""
Main GUI module for the Proxmox NLI installer.
Contains the installer wizard class and tab management.
"""
import tkinter as tk
from tkinter import ttk
from .tabs.welcome import create_welcome_tab
from .tabs.prerequisites import create_prerequisites_tab
from .tabs.config import create_config_tab
from .tabs.install import create_install_tab
from .config_manager import ConfigManager

class ProxmoxNLIInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Proxmox NLI Installer")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Create the notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create and add tabs
        self.welcome_tab = create_welcome_tab(self.notebook, self._next_tab)
        self.prerequisites_tab = create_prerequisites_tab(self.notebook, self.config_manager, self._next_tab)
        self.config_tab = create_config_tab(self.notebook, self.config_manager, self._next_tab)
        self.install_tab = create_install_tab(self.notebook, self.config_manager, self._finish_installer)
        
        self.notebook.add(self.welcome_tab, text="Welcome")
        self.notebook.add(self.prerequisites_tab, text="Prerequisites")
        self.notebook.add(self.config_tab, text="Configuration")
        self.notebook.add(self.install_tab, text="Installation")
        
    def _next_tab(self):
        """Move to the next tab"""
        current = self.notebook.index(self.notebook.select())
        self.notebook.select(current + 1)
        
    def _finish_installer(self):
        """Clean up and close the installer"""
        self.root.destroy()

    def run(self):
        """Start the installer GUI"""
        self.root.mainloop()