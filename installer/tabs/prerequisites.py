"""
Prerequisites check tab for the Proxmox NLI installer.
Checks for required software and system configuration.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import time
from typing import Callable
from ..config_manager import ConfigManager
from ..hardware_detector import HardwareDetector

class PrerequisitesTab:
    def __init__(self, parent: ttk.Notebook, config_manager: ConfigManager, on_next: Callable):
        self.tab = ttk.Frame(parent)
        self.config_manager = config_manager
        self.on_next = on_next
        self.hardware_detector = HardwareDetector()
        
        # Status variables
        self.python_status = tk.StringVar(value="⏳ Checking...")
        self.pip_status = tk.StringVar(value="⏳ Checking...")
        self.venv_status = tk.StringVar(value="⏳ Checking...")
        self.network_status = tk.StringVar(value="⏳ Checking...")
        self.hardware_status = tk.StringVar(value="⏳ Checking...")
        
        self._create_ui()

    def _create_ui(self):
        # Prerequisites frame
        prereq_frame = ttk.Frame(self.tab)
        prereq_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ttk.Label(
            prereq_frame, 
            text="Checking Prerequisites",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Create checklist frame
        checklist_frame = ttk.Frame(prereq_frame)
        checklist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create checklist items
        self._create_checklist_item(checklist_frame, "Python 3.8+ installed:", self.python_status, 0)
        self._create_checklist_item(checklist_frame, "Pip installed:", self.pip_status, 1)
        self._create_checklist_item(checklist_frame, "Virtual environment support:", self.venv_status, 2)
        self._create_checklist_item(checklist_frame, "Network connectivity:", self.network_status, 3)
        self._create_checklist_item(checklist_frame, "Hardware compatibility:", self.hardware_status, 4)
        
        # Navigation frame
        nav_frame = ttk.Frame(prereq_frame)
        nav_frame.pack(fill="x", pady=10)
        
        self.check_button = ttk.Button(
            nav_frame,
            text="Check Prerequisites",
            command=self._check_prerequisites
        )
        self.check_button.pack(side=tk.LEFT, padx=5)
        
        self.details_button = ttk.Button(
            nav_frame,
            text="Hardware Details",
            command=self._show_hardware_details,
            state="disabled"
        )
        self.details_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ttk.Button(
            nav_frame,
            text="Next >",
            command=self.on_next,
            state="disabled"
        )
        self.next_button.pack(side=tk.RIGHT, padx=5)

    def _create_checklist_item(self, parent: ttk.Frame, label: str, var: tk.StringVar, row: int):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Label(parent, textvariable=var).grid(row=row, column=1, sticky="w", pady=5)
        
    def _check_prerequisites(self):
        """Run all prerequisite checks"""
        self.check_button.config(state="disabled")
        self.next_button.config(state="disabled")
        self.details_button.config(state="disabled")
        
        # Reset status indicators
        for var in [self.python_status, self.pip_status, self.venv_status, self.network_status, self.hardware_status]:
            var.set("⏳ Checking...")
        
        # Run checks in sequence
        python_ok = self._check_python()
        pip_ok = self._check_pip()
        venv_ok = self._check_venv()
        network_ok = self._check_network()
        hardware_ok = self._check_hardware()
        
        # Enable/disable navigation based on results
        all_ok = python_ok and pip_ok and venv_ok and network_ok and hardware_ok
        self.next_button.config(state="normal" if all_ok else "disabled")
        self.check_button.config(state="normal")
        self.details_button.config(state="normal")

    def _check_hardware(self) -> bool:
        """Check hardware compatibility"""
        try:
            hw_info = self.hardware_detector.get_hardware_summary()
            
            # Check CPU cores (minimum 2 cores recommended)
            cpu_cores = hw_info["cpu_info"]["total_cores"]
            if cpu_cores < 2:
                self._update_status(self.hardware_status, f"⚠️ Low CPU cores ({cpu_cores})")
                return False
                
            # Check memory (minimum 4GB recommended)
            total_ram_gb = hw_info["memory_info"]["total"] / (1024**3)
            if total_ram_gb < 4:
                self._update_status(self.hardware_status, f"⚠️ Low memory ({total_ram_gb:.1f}GB)")
                return False
                
            # Check disk space (minimum 10GB free recommended)
            has_sufficient_space = False
            for disk in hw_info["disk_info"]:
                free_space_gb = disk["free"] / (1024**3)
                if free_space_gb >= 10:
                    has_sufficient_space = True
                    break
                    
            if not has_sufficient_space:
                self._update_status(self.hardware_status, "⚠️ Insufficient disk space")
                return False
                
            self._update_status(self.hardware_status, "✅ Hardware compatible")
            return True
            
        except Exception as e:
            self._update_status(self.hardware_status, "❌ Error checking hardware")
            return False

    def _show_hardware_details(self):
        """Show detailed hardware information"""
        hw_info = self.hardware_detector.get_hardware_summary()
        
        details_window = tk.Toplevel(self.tab)
        details_window.title("Hardware Details")
        details_window.geometry("500x400")
        
        # Create text widget for details
        text_widget = tk.Text(details_window, wrap=tk.WORD, width=60, height=20)
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(details_window, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Format and display information
        text_widget.insert(tk.END, "System Information\n", "heading")
        text_widget.insert(tk.END, "-----------------\n")
        for key, value in hw_info["system_info"].items():
            text_widget.insert(tk.END, f"{key.title()}: {value}\n")
            
        text_widget.insert(tk.END, "\nCPU Information\n", "heading")
        text_widget.insert(tk.END, "--------------\n")
        cpu_info = hw_info["cpu_info"]
        text_widget.insert(tk.END, f"Physical Cores: {cpu_info['physical_cores']}\n")
        text_widget.insert(tk.END, f"Total Cores: {cpu_info['total_cores']}\n")
        text_widget.insert(tk.END, f"Max Frequency: {cpu_info['max_frequency']:.2f} MHz\n")
        text_widget.insert(tk.END, f"Current Usage: {cpu_info['cpu_usage']}%\n")
        
        text_widget.insert(tk.END, "\nMemory Information\n", "heading")
        text_widget.insert(tk.END, "-----------------\n")
        mem_info = hw_info["memory_info"]
        text_widget.insert(tk.END, f"Total RAM: {mem_info['total'] / (1024**3):.1f} GB\n")
        text_widget.insert(tk.END, f"Available: {mem_info['available'] / (1024**3):.1f} GB\n")
        text_widget.insert(tk.END, f"Used: {mem_info['used'] / (1024**3):.1f} GB\n")
        text_widget.insert(tk.END, f"Usage: {mem_info['percentage']}%\n")
        
        text_widget.insert(tk.END, "\nDisk Information\n", "heading")
        text_widget.insert(tk.END, "----------------\n")
        for disk in hw_info["disk_info"]:
            text_widget.insert(tk.END, f"\nMount: {disk['mountpoint']}\n")
            text_widget.insert(tk.END, f"Total: {disk['total'] / (1024**3):.1f} GB\n")
            text_widget.insert(tk.END, f"Free: {disk['free'] / (1024**3):.1f} GB\n")
            text_widget.insert(tk.END, f"Used: {disk['used'] / (1024**3):.1f} GB\n")
            text_widget.insert(tk.END, f"Usage: {disk['percentage']}%\n")
        
        # Make text widget read-only
        text_widget.config(state=tk.DISABLED)
        
        # Add close button
        ttk.Button(
            details_window,
            text="Close",
            command=details_window.destroy
        ).pack(pady=10)

    def _check_python(self) -> bool:
        """Check Python version"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", "import sys; print(sys.version)"],
                capture_output=True, text=True, check=True
            )
            version = result.stdout.strip().split()[0]
            if float('.'.join(version.split('.')[:2])) >= 3.8:
                self._update_status(self.python_status, f"✅ Python {version} detected")
                return True
            else:
                self._update_status(self.python_status, f"❌ Python {version} (3.8+ required)")
                return False
        except Exception as e:
            self._update_status(self.python_status, "❌ Error checking Python")
            return False
            
    def _check_pip(self) -> bool:
        """Check pip installation"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True, text=True, check=True
            )
            self._update_status(self.pip_status, "✅ Pip detected")
            return True
        except Exception as e:
            self._update_status(self.pip_status, "❌ Pip not found")
            return False
            
    def _check_venv(self) -> bool:
        """Check virtual environment support"""
        try:
            subprocess.run(
                [sys.executable, "-c", "import venv"],
                capture_output=True, text=True, check=True
            )
            self._update_status(self.venv_status, "✅ Virtual environment support available")
            return True
        except Exception as e:
            self._update_status(self.venv_status, "❌ Virtual environment not available")
            return False
            
    def _check_network(self) -> bool:
        """Check network connectivity"""
        try:
            subprocess.run(
                [sys.executable, "-c", "import urllib.request; urllib.request.urlopen('https://pypi.org', timeout=5)"],
                capture_output=True, text=True, check=True
            )
            self._update_status(self.network_status, "✅ Internet connection available")
            return True
        except Exception as e:
            self._update_status(self.network_status, "❌ No internet connection detected")
            return False
            
    def _update_status(self, var: tk.StringVar, status: str, delay: float = 0.5):
        """Update a status variable with optional delay"""
        time.sleep(delay)  # Add delay to make the UI more readable
        var.set(status)

def create_prerequisites_tab(
    parent: ttk.Notebook,
    config_manager: ConfigManager,
    on_next: Callable
) -> ttk.Frame:
    """Create the prerequisites tab
    
    Args:
        parent: Parent notebook widget
        config_manager: Configuration manager instance
        on_next: Callback for the next button
        
    Returns:
        The prerequisites tab frame
    """
    tab = PrerequisitesTab(parent, config_manager, on_next)
    return tab.tab