"""
Configuration tab for the Proxmox NLI installer.
Handles Proxmox connection settings and application configuration.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from ..config_manager import ConfigManager

class ConfigTab:
    def __init__(self, parent: ttk.Notebook, config_manager: ConfigManager, on_next: Callable):
        self.tab = ttk.Frame(parent)
        self.config_manager = config_manager
        self.on_next = on_next
        self.config = config_manager.get_config()
        
        self._create_ui()
        
    def _create_ui(self):
        # Main config frame
        config_frame = ttk.Frame(self.tab)
        config_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ttk.Label(
            config_frame,
            text="Proxmox Configuration",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Create form frame
        form_frame = ttk.Frame(config_frame)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Proxmox connection settings
        self._create_connection_settings(form_frame)
        
        # Application settings
        ttk.Separator(form_frame, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=10
        )
        
        ttk.Label(
            form_frame,
            text="Application Settings",
            font=("Arial", 12, "bold")
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=5)
        
        self._create_app_settings(form_frame)
        
        # Navigation frame
        nav_frame = ttk.Frame(config_frame)
        nav_frame.pack(fill="x", pady=10)
        
        ttk.Button(
            nav_frame,
            text="Test Connection",
            command=self._test_connection
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            nav_frame,
            text="Next >",
            command=self._validate_and_proceed
        ).pack(side=tk.RIGHT, padx=5)
        
    def _create_connection_settings(self, parent: ttk.Frame):
        """Create Proxmox connection settings fields"""
        # Host
        ttk.Label(parent, text="Proxmox Host:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        ttk.Entry(
            parent,
            textvariable=self.config["proxmox_host"],
            width=30
        ).grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(
            parent,
            text="(e.g., 192.168.1.100 or proxmox.local)"
        ).grid(row=0, column=2, sticky="w", pady=5)
        
        # Username
        ttk.Label(parent, text="Username:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        ttk.Entry(
            parent,
            textvariable=self.config["proxmox_user"],
            width=30
        ).grid(row=1, column=1, sticky="w", pady=5)
        
        # Password
        ttk.Label(parent, text="Password:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        ttk.Entry(
            parent,
            textvariable=self.config["proxmox_password"],
            show="*",
            width=30
        ).grid(row=2, column=1, sticky="w", pady=5)
        
        # Realm
        ttk.Label(parent, text="Realm:").grid(
            row=3, column=0, sticky="w", pady=5
        )
        ttk.Entry(
            parent,
            textvariable=self.config["proxmox_realm"],
            width=30
        ).grid(row=3, column=1, sticky="w", pady=5)
        ttk.Label(
            parent,
            text="(usually 'pam')"
        ).grid(row=3, column=2, sticky="w", pady=5)
        
        # SSL Verification
        ttk.Checkbutton(
            parent,
            text="Verify SSL",
            variable=self.config["verify_ssl"]
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
    def _create_app_settings(self, parent: ttk.Frame):
        """Create application settings fields"""
        # Web interface
        ttk.Checkbutton(
            parent,
            text="Start Web Interface by default",
            variable=self.config["start_web_interface"]
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=5)
        
        # Port
        ttk.Label(parent, text="Web Port:").grid(
            row=8, column=0, sticky="w", pady=5
        )
        ttk.Entry(
            parent,
            textvariable=self.config["port"],
            width=10
        ).grid(row=8, column=1, sticky="w", pady=5)
        
        # Debug mode
        ttk.Checkbutton(
            parent,
            text="Debug Mode",
            variable=self.config["debug_mode"]
        ).grid(row=9, column=0, columnspan=2, sticky="w", pady=5)
        
        # Autostart
        ttk.Checkbutton(
            parent,
            text="Create autostart shortcut",
            variable=self.config["autostart"]
        ).grid(row=10, column=0, columnspan=2, sticky="w", pady=5)
        
        # Unattended installation
        ttk.Checkbutton(
            parent,
            text="Unattended Installation",
            variable=self.config["unattended_installation"]
        ).grid(row=11, column=0, columnspan=2, sticky="w", pady=5)
        
    def _test_connection(self):
        """Test connection to Proxmox server"""
        success, message = self.config_manager.test_proxmox_connection()
        if success:
            messagebox.showinfo("Connection Test", "Successfully connected to Proxmox server!")
        else:
            if messagebox.askokcancel(
                "Connection Error",
                f"Error connecting to Proxmox server: {message}\nContinue anyway?"
            ):
                return True
            return False
            
    def _validate_and_proceed(self):
        """Validate configuration and proceed to next tab"""
        # Validate configuration
        is_valid, errors = self.config_manager.validate_config()
        if not is_valid:
            messagebox.showerror(
                "Validation Error",
                "\n".join(errors)
            )
            return
            
        # Test connection if requested
        if messagebox.askyesno(
            "Test Connection",
            "Would you like to test the connection to your Proxmox server before proceeding?"
        ):
            if not self._test_connection():
                return
                
        # Save configuration
        self.config_manager.save_config()
        self.config_manager.save_validation_report()
        
        # Proceed to next tab
        self.on_next()

def create_config_tab(
    parent: ttk.Notebook,
    config_manager: ConfigManager,
    on_next: Callable
) -> ttk.Frame:
    """Create the configuration tab
    
    Args:
        parent: Parent notebook widget
        config_manager: Configuration manager instance
        on_next: Callback for the next button
        
    Returns:
        The configuration tab frame
    """
    tab = ConfigTab(parent, config_manager, on_next)
    return tab.tab