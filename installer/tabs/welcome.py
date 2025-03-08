"""
Welcome tab for the Proxmox NLI installer.
Provides introduction and basic information about the installer.
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable

def create_welcome_tab(parent: ttk.Notebook, on_next: Callable) -> ttk.Frame:
    """Create the welcome tab
    
    Args:
        parent: Parent notebook widget
        on_next: Callback for the next button
        
    Returns:
        The welcome tab frame
    """
    tab = ttk.Frame(parent)
    
    # Welcome message frame
    welcome_frame = ttk.Frame(tab)
    welcome_frame.pack(expand=True, fill="both", padx=20, pady=20)
    
    ttk.Label(
        welcome_frame, 
        text="Welcome to Proxmox NLI Setup Wizard",
        font=("Arial", 16, "bold")
    ).pack(pady=10)
    
    ttk.Label(
        welcome_frame,
        text=(
            "This wizard will guide you through installing and configuring "
            "the Proxmox Natural Language Interface.\n\n"
            "This tool allows you to manage your Proxmox environment using "
            "natural language commands.\n\n"
            "Click Next to begin the installation process."
        ),
        wraplength=500,
        justify="center"
    ).pack(pady=10)
    
    # Navigation frame
    nav_frame = ttk.Frame(welcome_frame)
    nav_frame.pack(fill="x", pady=10)
    
    ttk.Button(
        nav_frame,
        text="Next >",
        command=on_next
    ).pack(side=tk.RIGHT, padx=5)
    
    return tab