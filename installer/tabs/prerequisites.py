"""
Prerequisites check tab for the Proxmox NLI installer.
Checks for required software and system configuration.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import time
import json
import threading
from typing import Callable, List, Dict, Any
from ..config_manager import ConfigManager
from ..hardware_detector import HardwareDetector, HardwareCompatibility, DriverInfo

class PrerequisitesTab:
    def __init__(self, parent: ttk.Notebook, config_manager: ConfigManager, on_next: Callable):
        self.tab = ttk.Frame(parent)
        self.config_manager = config_manager
        self.on_next = on_next
        self.hardware_detector = HardwareDetector()
        self.compatibility_results = []
        self.fallback_options_applied = {}
        self.missing_drivers = []
        
        # Status variables
        self.python_status = tk.StringVar(value="⏳ Checking...")
        self.pip_status = tk.StringVar(value="⏳ Checking...")
        self.venv_status = tk.StringVar(value="⏳ Checking...")
        self.network_status = tk.StringVar(value="⏳ Checking...")
        self.hardware_status = tk.StringVar(value="⏳ Checking...")
        self.drivers_status = tk.StringVar(value="⏳ Checking...")
        
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
        self._create_checklist_item(checklist_frame, "Hardware drivers:", self.drivers_status, 5)
        
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
        
        self.fallback_button = ttk.Button(
            nav_frame,
            text="Fallback Options",
            command=self._show_fallback_options,
            state="disabled"
        )
        self.fallback_button.pack(side=tk.LEFT, padx=5)
        
        self.driver_button = ttk.Button(
            nav_frame,
            text="Manage Drivers",
            command=self._show_driver_manager,
            state="disabled"
        )
        self.driver_button.pack(side=tk.LEFT, padx=5)
        
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
        self.fallback_button.config(state="disabled")
        self.driver_button.config(state="disabled")
        
        # Reset status indicators
        for var in [self.python_status, self.pip_status, self.venv_status, 
                    self.network_status, self.hardware_status, self.drivers_status]:
            var.set("⏳ Checking...")
        
        # Run checks in sequence
        python_ok = self._check_python()
        pip_ok = self._check_pip()
        venv_ok = self._check_venv()
        network_ok = self._check_network()
        hardware_ok = self._check_hardware()
        drivers_ok = self._check_drivers()
        
        # Enable/disable navigation based on results
        software_ok = python_ok and pip_ok and venv_ok and network_ok
        
        # Hardware can proceed if either fully compatible or has fallback options
        can_proceed = software_ok and (hardware_ok or self._has_viable_fallbacks())
        
        self.next_button.config(state="normal" if can_proceed else "disabled")
        self.check_button.config(state="normal")
        self.details_button.config(state="normal")
        
        # Only show fallback button if there are fallback options
        has_fallbacks = any(result.fallback_available for result in self.compatibility_results)
        self.fallback_button.config(state="normal" if has_fallbacks else "disabled")
        
        # Only show driver button if there are missing drivers
        has_missing_drivers = bool(self.missing_drivers)
        self.driver_button.config(state="normal" if has_missing_drivers else "disabled")

    def _has_viable_fallbacks(self) -> bool:
        """Check if there are viable fallback options for hardware"""
        if not self.compatibility_results:
            return False
            
        # Check if any critical issues don't have fallbacks
        critical_issues_without_fallback = [
            r for r in self.compatibility_results
            if not r.is_compatible and r.severity == "critical" and not r.fallback_available
        ]
        
        return len(critical_issues_without_fallback) == 0

    def _check_hardware(self) -> bool:
        """Check hardware compatibility using the new system with fallback options"""
        try:
            # Get hardware compatibility results
            self.compatibility_results = self.hardware_detector.check_hardware_compatibility()
            
            # Count the various types of results
            total_issues = len([r for r in self.compatibility_results if not r.is_compatible])
            critical_issues = len([r for r in self.compatibility_results if not r.is_compatible and r.severity == "critical"])
            warning_issues = len([r for r in self.compatibility_results if not r.is_compatible and r.severity == "warning"])
            
            # Update status based on issues
            if critical_issues > 0:
                if self._has_viable_fallbacks():
                    self._update_status(
                        self.hardware_status, 
                        f"⚠️ {critical_issues} critical issues (fallbacks available)"
                    )
                else:
                    self._update_status(
                        self.hardware_status, 
                        f"❌ {critical_issues} critical compatibility issues"
                    )
                return False
            elif warning_issues > 0:
                self._update_status(
                    self.hardware_status, 
                    f"⚠️ {warning_issues} minor compatibility issues"
                )
                return False
            else:
                self._update_status(self.hardware_status, "✅ Hardware fully compatible")
                return True
            
        except Exception as e:
            self._update_status(self.hardware_status, "❌ Error checking hardware")
            return False
            
    def _check_drivers(self) -> bool:
        """Check for missing hardware drivers"""
        try:
            # Get driver information
            all_drivers = self.hardware_detector.get_driver_info()
            
            # Filter for missing drivers only
            self.missing_drivers = [d for d in all_drivers 
                                    if not d.is_installed and d.status in ["missing", "outdated", "error"]]
            
            # Update status
            if len(self.missing_drivers) > 0:
                self._update_status(
                    self.drivers_status,
                    f"⚠️ {len(self.missing_drivers)} missing drivers"
                )
                return False
            else:
                self._update_status(self.drivers_status, "✅ All drivers installed")
                return True
                
        except Exception as e:
            self._update_status(self.drivers_status, "⚠️ Unable to check drivers")
            return True  # Don't block progress for driver issues
    
    def _show_driver_manager(self):
        """Show driver management window"""
        if not self.missing_drivers:
            messagebox.showinfo("Drivers", "No missing drivers detected.")
            return
            
        # Create driver management window
        driver_window = tk.Toplevel(self.tab)
        driver_window.title("Hardware Driver Manager")
        driver_window.geometry("750x500")
        
        # Configure fonts
        header_font = ("Arial", 12, "bold")
        section_font = ("Arial", 11)
        
        # Main frame
        main_frame = ttk.Frame(driver_window, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        ttk.Label(
            main_frame, 
            text="Hardware Driver Manager",
            font=header_font
        ).pack(pady=(0, 10), anchor="w")
        
        ttk.Label(
            main_frame,
            text=f"{len(self.missing_drivers)} drivers need attention",
            font=section_font
        ).pack(pady=(0, 10), anchor="w")
        
        # Create a frame for the driver list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        # Create a treeview for the drivers
        columns = ("device", "status", "driver", "action")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Set column headings
        tree.heading("device", text="Device")
        tree.heading("status", text="Status")
        tree.heading("driver", text="Driver")
        tree.heading("action", text="Installation Method")
        
        # Set column widths
        tree.column("device", width=250)
        tree.column("status", width=100)
        tree.column("driver", width=150)
        tree.column("action", width=150)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Pack the scrollbars and treeview
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        
        # Add drivers to the treeview
        for i, driver in enumerate(self.missing_drivers):
            # Map status to display text
            status_map = {
                "missing": "Missing",
                "outdated": "Outdated",
                "error": "Error",
                "available_not_loaded": "Not Loaded"
            }
            status_text = status_map.get(driver.status, driver.status.capitalize())
            
            # Map installation method to display text
            method_map = {
                "package": f"Package: {driver.package_name}" if driver.package_name else "Package",
                "module": "Kernel Module",
                "firmware": "Firmware",
                "windows_update": "Windows Update"
            }
            method_text = method_map.get(driver.install_method, driver.install_method.capitalize())
            
            tree.insert("", "end", iid=str(i), values=(
                driver.device_name,
                status_text,
                driver.driver_name,
                method_text
            ))
        
        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="Driver Details", padding=10)
        info_frame.pack(fill="x", pady=10)
        
        # Info labels
        device_var = tk.StringVar()
        driver_var = tk.StringVar()
        status_var = tk.StringVar()
        method_var = tk.StringVar()
        command_var = tk.StringVar()
        
        # Label and value layout
        details_grid = ttk.Frame(info_frame)
        details_grid.pack(fill="x", pady=5)
        
        ttk.Label(details_grid, text="Device:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, textvariable=device_var).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(details_grid, text="Driver:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, textvariable=driver_var).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(details_grid, text="Status:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, textvariable=status_var).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(details_grid, text="Installation Method:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, textvariable=method_var).grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(details_grid, text="Command:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, textvariable=command_var).grid(row=4, column=1, sticky="w", padx=5, pady=2)
        
        # Status and progress frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=10)
        
        status_label = ttk.Label(status_frame, text="Select a driver to view details")
        status_label.pack(side="left", padx=5)
        
        progress = ttk.Progressbar(status_frame, mode="indeterminate", length=200)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        def on_tree_select(event):
            """Handle treeview selection"""
            selected_items = tree.selection()
            if not selected_items:
                return
                
            idx = int(selected_items[0])
            driver = self.missing_drivers[idx]
            
            device_var.set(driver.device_name)
            driver_var.set(driver.driver_name)
            status_var.set(status_map.get(driver.status, driver.status.capitalize()))
            method_var.set(method_map.get(driver.install_method, driver.install_method.capitalize()))
            
            if driver.install_commands and driver.install_commands[0]:
                command_var.set(driver.install_commands[0])
            else:
                command_var.set("No automatic installation available")
        
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        
        def install_selected_driver():
            """Install the selected driver"""
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showinfo("Selection Required", "Please select a driver to install")
                return
                
            idx = int(selected_items[0])
            driver = self.missing_drivers[idx]
            
            if not driver.install_commands:
                messagebox.showinfo(
                    "Manual Installation Required", 
                    f"The driver '{driver.driver_name}' for '{driver.device_name}' cannot be installed automatically.\n\n"
                    "Please install it manually using your system's package manager or driver tools."
                )
                return
                
            # Show progress bar
            status_label.config(text=f"Installing driver for {driver.device_name}...")
            progress.pack(side="right", padx=5)
            progress.start()
            
            # Disable buttons during installation
            install_button.config(state="disabled")
            install_all_button.config(state="disabled")
            close_button.config(state="disabled")
            
            # Run installation in a background thread to keep UI responsive
            def install_thread():
                result = self.hardware_detector.install_driver(driver)
                
                # Update UI from main thread
                driver_window.after(0, lambda: installation_complete(result, idx))
            
            threading.Thread(target=install_thread).start()
            
        def installation_complete(result, idx):
            """Handle completion of driver installation"""
            # Hide progress bar
            progress.stop()
            progress.pack_forget()
            
            # Re-enable buttons
            install_button.config(state="normal")
            install_all_button.config(state="normal")
            close_button.config(state="normal")
            
            # Update status
            if result["success"]:
                status_label.config(text=f"Installation successful: {result['message']}")
                # Update tree item
                tree.item(str(idx), values=(
                    self.missing_drivers[idx].device_name,
                    "Installed",
                    self.missing_drivers[idx].driver_name,
                    "Completed"
                ))
                # Refresh driver status
                self._check_drivers()
                
                # Check if all drivers are installed
                if not self.missing_drivers:
                    messagebox.showinfo("Installation Complete", "All drivers have been successfully installed.")
                    driver_window.destroy()
            else:
                status_label.config(text=f"Installation failed: {result['message']}")
                messagebox.showerror("Installation Failed", 
                                     f"Failed to install driver: {result['message']}\n\n"
                                     "See system logs for more details.")
        
        def install_all_drivers():
            """Install all missing drivers"""
            if not self.missing_drivers:
                messagebox.showinfo("No Drivers", "No missing drivers to install")
                return
                
            # Count installable drivers
            installable = [d for d in self.missing_drivers if d.install_commands]
            if not installable:
                messagebox.showinfo(
                    "Manual Installation Required", 
                    "None of the missing drivers can be installed automatically.\n\n"
                    "Please install them manually using your system's package manager or driver tools."
                )
                return
                
            if messagebox.askyesno(
                "Confirm Installation", 
                f"This will attempt to install {len(installable)} drivers. Continue?"
            ):
                # Start with the first driver
                idx = 0
                driver = installable[0]
                
                # Show progress
                status_label.config(text=f"Installing driver for {driver.device_name}...")
                progress.pack(side="right", padx=5)
                progress.start()
                
                # Disable buttons during installation
                install_button.config(state="disabled")
                install_all_button.config(state="disabled")
                close_button.config(state="disabled")
                
                # Create a function to install drivers in sequence
                def install_sequence(current_idx=0):
                    if current_idx >= len(installable):
                        # All done
                        progress.stop()
                        progress.pack_forget()
                        install_button.config(state="normal")
                        install_all_button.config(state="normal")
                        close_button.config(state="normal")
                        status_label.config(text="All installations completed")
                        
                        # Refresh driver status
                        self._check_drivers()
                        
                        messagebox.showinfo("Installation Complete", 
                                           f"Installed {current_idx} of {len(installable)} drivers.")
                        return
                        
                    # Get the driver to install
                    driver = installable[current_idx]
                    
                    # Update status
                    status_label.config(text=f"Installing driver {current_idx+1}/{len(installable)}: {driver.device_name}")
                    
                    # Do installation in a thread
                    def install_thread():
                        result = self.hardware_detector.install_driver(driver)
                        
                        # Find the real index in the main list
                        real_idx = self.missing_drivers.index(driver)
                        
                        # Update UI from main thread
                        driver_window.after(0, lambda: installation_step_complete(result, real_idx, current_idx+1))
                    
                    threading.Thread(target=install_thread).start()
                
                def installation_step_complete(result, tree_idx, next_idx):
                    """Handle completion of a single driver installation step"""
                    if result["success"]:
                        # Update tree item
                        tree.item(str(tree_idx), values=(
                            self.missing_drivers[tree_idx].device_name,
                            "Installed",
                            self.missing_drivers[tree_idx].driver_name,
                            "Completed"
                        ))
                    else:
                        # Update tree item to show failure
                        tree.item(str(tree_idx), values=(
                            self.missing_drivers[tree_idx].device_name,
                            "Failed",
                            self.missing_drivers[tree_idx].driver_name,
                            "Error"
                        ))
                    
                    # Continue with next driver
                    install_sequence(next_idx)
                
                # Start the installation sequence
                install_sequence()
        
        # Add buttons
        install_button = ttk.Button(
            button_frame,
            text="Install Selected Driver",
            command=install_selected_driver
        )
        install_button.pack(side="left", padx=5)
        
        install_all_button = ttk.Button(
            button_frame,
            text="Install All Drivers",
            command=install_all_drivers
        )
        install_all_button.pack(side="left", padx=5)
        
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=driver_window.destroy
        )
        close_button.pack(side="right", padx=5)
        
        # Make the window modal
        driver_window.transient(self.tab)
        driver_window.grab_set()
        self.tab.wait_window(driver_window)
        
        # Refresh driver status after window is closed
        self._check_drivers()

    def _show_fallback_options(self):
        """Show available fallback options for hardware compatibility issues"""
        if not self.compatibility_results:
            messagebox.showinfo("No Data", "Hardware compatibility data not available.")
            return
        
        # Create fallback options window
        fallback_window = tk.Toplevel(self.tab)
        fallback_window.title("Hardware Fallback Options")
        fallback_window.geometry("650x500")
        
        # Header
        header_frame = ttk.Frame(fallback_window)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(
            header_frame,
            text="Hardware Compatibility Fallback Options",
            font=("Arial", 12, "bold")
        ).pack(side=tk.LEFT, pady=5)
        
        # Create scrollable frame for fallback options
        main_frame = ttk.Frame(fallback_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add canvas for scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add fallback options to the scrollable frame
        row = 0
        applied_vars = {}
        
        # Filter to show only incompatible components with fallbacks
        issues_with_fallbacks = [
            result for result in self.compatibility_results
            if not result.is_compatible and result.fallback_available
        ]
        
        if not issues_with_fallbacks:
            ttk.Label(
                scroll_frame,
                text="No fallback options available."
            ).grid(row=0, column=0, columnspan=3, sticky="w", pady=10)
        else:
            # Headers
            ttk.Label(
                scroll_frame, 
                text="Component", 
                font=("Arial", 10, "bold")
            ).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            
            ttk.Label(
                scroll_frame, 
                text="Issue", 
                font=("Arial", 10, "bold")
            ).grid(row=row, column=1, sticky="w", padx=5, pady=5)
            
            ttk.Label(
                scroll_frame, 
                text="Fallback Option", 
                font=("Arial", 10, "bold")
            ).grid(row=row, column=2, sticky="w", padx=5, pady=5)
            
            row += 1
            
            # Add each fallback option
            for result in issues_with_fallbacks:
                # Component name
                ttk.Label(
                    scroll_frame,
                    text=result.component
                ).grid(row=row, column=0, sticky="w", padx=5, pady=5)
                
                # Issue (with severity indicator)
                severity_icon = "🛑 " if result.severity == "critical" else "⚠️ "
                ttk.Label(
                    scroll_frame,
                    text=f"{severity_icon}{result.message}"
                ).grid(row=row, column=1, sticky="w", padx=5, pady=5)
                
                # Fallback option with checkbox
                fallback_frame = ttk.Frame(scroll_frame)
                fallback_frame.grid(row=row, column=2, sticky="w", padx=5, pady=5)
                
                # Check if this fallback is already applied
                is_applied = (
                    result.component in self.fallback_options_applied and 
                    self.fallback_options_applied[result.component] == result.fallback_option
                )
                
                # Create variable for checkbox
                var = tk.BooleanVar(value=is_applied)
                applied_vars[(result.component, result.fallback_option)] = var
                
                ttk.Checkbutton(
                    fallback_frame,
                    text="Apply",
                    variable=var
                ).pack(side=tk.LEFT)
                
                ttk.Label(
                    fallback_frame,
                    text=f"{result.fallback_description}"
                ).pack(side=tk.LEFT, padx=5)
                
                row += 1
        
        # Buttons frame
        button_frame = ttk.Frame(fallback_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def apply_selected_fallbacks():
            # Update fallback options based on selections
            for (component, option), var in applied_vars.items():
                if var.get():
                    # Apply the fallback option
                    result = self.hardware_detector.apply_fallback_configuration(component, option)
                    if result["success"]:
                        self.fallback_options_applied[component] = option
                        
                        # Save the applied changes to the config manager
                        self.config_manager.set(
                            f"fallbacks.{component.lower().replace(' ', '_')}", 
                            {
                                "option": option,
                                "changes": result["applied_changes"]
                            }
                        )
                else:
                    # Remove the fallback option if it was previously applied
                    if component in self.fallback_options_applied:
                        del self.fallback_options_applied[component]
                        self.config_manager.remove(f"fallbacks.{component.lower().replace(' ', '_')}")
            
            # Save config and close the window
            self.config_manager.save()
            
            # Re-run the hardware check and update the UI
            self._check_hardware()
            
            # If fallbacks make the system viable, enable the next button
            software_ok = all([
                self.python_status.get().startswith("✅"),
                self.pip_status.get().startswith("✅"),
                self.venv_status.get().startswith("✅"),
                self.network_status.get().startswith("✅")
            ])
            
            if software_ok and self._has_viable_fallbacks():
                self.next_button.config(state="normal")
            
            fallback_window.destroy()
            messagebox.showinfo("Fallbacks Applied", "Selected fallback options have been applied to your configuration.")
        
        ttk.Button(
            button_frame,
            text="Apply Selected Fallbacks",
            command=apply_selected_fallbacks
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=fallback_window.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _show_hardware_details(self):
        """Show detailed hardware information"""
        hw_info = self.hardware_detector.get_hardware_summary()
        
        details_window = tk.Toplevel(self.tab)
        details_window.title("Hardware Details")
        details_window.geometry("600x500")
        
        # Create tabbed interface for hardware details
        notebook = ttk.Notebook(details_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs for each hardware category
        self._create_system_info_tab(notebook, hw_info)
        self._create_compatibility_tab(notebook, hw_info.get("compatibility", []))
        self._create_driver_info_tab(notebook, hw_info.get("drivers", []))
        
        # Add close button
        ttk.Button(
            details_window,
            text="Close",
            command=details_window.destroy
        ).pack(pady=10)

    def _create_driver_info_tab(self, notebook, driver_info):
        """Create a tab for driver information"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Drivers")
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Add header
        ttk.Label(
            scroll_frame,
            text="Hardware Drivers",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        if not driver_info:
            ttk.Label(
                scroll_frame,
                text="No driver information available"
            ).grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=20)
            return
            
        # Header row
        ttk.Label(
            scroll_frame,
            text="Device",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        ttk.Label(
            scroll_frame,
            text="Driver",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(
            scroll_frame,
            text="Status",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        # Add separator
        separator = ttk.Separator(scroll_frame, orient="horizontal")
        separator.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        
        # Display driver results
        row = 3
        for result in driver_info:
            # Convert from dictionary if needed (from saved results)
            if isinstance(result, dict):
                device_name = result.get("device_name", "Unknown")
                driver_name = result.get("driver_name", "Unknown")
                status = result.get("status", "Unknown")
                is_installed = result.get("is_installed", False)
            else:
                device_name = result.device_name
                driver_name = result.driver_name
                status = result.status
                is_installed = result.is_installed
            
            # Device name
            ttk.Label(
                scroll_frame,
                text=device_name,
                wraplength=250
            ).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            
            # Driver name
            ttk.Label(
                scroll_frame,
                text=driver_name
            ).grid(row=row, column=1, sticky="w", padx=5, pady=5)
            
            # Status with icon
            if is_installed:
                status_text = "✅ Installed"
            else:
                if status == "missing":
                    status_text = "❌ Missing"
                elif status == "outdated":
                    status_text = "⚠️ Outdated"
                elif status == "error":
                    status_text = "⚠️ Error"
                else:
                    status_text = f"ℹ️ {status.capitalize()}"
            
            ttk.Label(
                scroll_frame,
                text=status_text
            ).grid(row=row, column=2, sticky="w", padx=5, pady=5)
            
            row += 1

    def _create_system_info_tab(self, notebook, hw_info):
        """Create a tab with basic system information"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="System Information")
        
        # Create scrollable text widget
        text_widget = tk.Text(tab, wrap=tk.WORD, width=70, height=25)
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tab, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Add tags for formatting
        text_widget.tag_configure("heading", font=("Arial", 10, "bold"))
        
        # Format and display information
        text_widget.insert(tk.END, "System Information\n", "heading")
        text_widget.insert(tk.END, "-----------------\n")
        for key, value in hw_info["system_info"].items():
            text_widget.insert(tk.END, f"{key.title()}: {value}\n")
            
        text_widget.insert(tk.END, "\nCPU Information\n", "heading")
        text_widget.insert(tk.END, "--------------\n")
        cpu_info = hw_info["cpu_info"]
        text_widget.insert(tk.END, f"Model: {cpu_info.get('model', 'Unknown')}\n")
        text_widget.insert(tk.END, f"Physical Cores: {cpu_info['physical_cores']}\n")
        text_widget.insert(tk.END, f"Total Cores: {cpu_info['total_cores']}\n")
        if 'max_frequency' in cpu_info:
            text_widget.insert(tk.END, f"Max Frequency: {cpu_info['max_frequency']:.2f} MHz\n")
        text_widget.insert(tk.END, f"Current Usage: {cpu_info['cpu_usage']}%\n")
        
        # Add virtualization information if available
        if 'virtualization_support' in cpu_info:
            text_widget.insert(tk.END, "\nVirtualization Support:\n")
            if isinstance(cpu_info['virtualization_support'], dict):
                for key, value in cpu_info['virtualization_support'].items():
                    text_widget.insert(tk.END, f"  {key}: {value}\n")
            else:
                text_widget.insert(tk.END, f"  {cpu_info['virtualization_support']}\n")
        
        text_widget.insert(tk.END, "\nMemory Information\n", "heading")
        text_widget.insert(tk.END, "-----------------\n")
        mem_info = hw_info["memory_info"]
        text_widget.insert(tk.END, f"Total RAM: {mem_info['total'] / (1024**3):.1f} GB\n")
        text_widget.insert(tk.END, f"Available: {mem_info['available'] / (1024**3):.1f} GB\n")
        text_widget.insert(tk.END, f"Used: {mem_info['used'] / (1024**3):.1f} GB\n")
        text_widget.insert(tk.END, f"Usage: {mem_info['percentage']}%\n")
        
        if 'swap' in mem_info:
            text_widget.insert(tk.END, f"\nSwap Total: {mem_info['swap']['total'] / (1024**3):.1f} GB\n")
            text_widget.insert(tk.END, f"Swap Used: {mem_info['swap']['used'] / (1024**3):.1f} GB\n")
            text_widget.insert(tk.END, f"Swap Free: {mem_info['swap']['free'] / (1024**3):.1f} GB\n")
        
        text_widget.insert(tk.END, "\nDisk Information\n", "heading")
        text_widget.insert(tk.END, "----------------\n")
        for disk in hw_info["disk_info"]:
            text_widget.insert(tk.END, f"\nMount: {disk['mountpoint']}\n")
            text_widget.insert(tk.END, f"Device: {disk['device']}\n")
            text_widget.insert(tk.END, f"File System: {disk['fstype']}\n")
            text_widget.insert(tk.END, f"Total: {disk['total'] / (1024**3):.1f} GB\n")
            text_widget.insert(tk.END, f"Free: {disk['free'] / (1024**3):.1f} GB\n")
            text_widget.insert(tk.END, f"Used: {disk['used'] / (1024**3):.1f} GB\n")
            text_widget.insert(tk.END, f"Usage: {disk['percentage']}%\n")
        
        # Network interfaces
        text_widget.insert(tk.END, "\nNetwork Information\n", "heading")
        text_widget.insert(tk.END, "------------------\n")
        text_widget.insert(tk.END, f"Hostname: {hw_info['network_info']['hostname']}\n")
        if 'primary_ip' in hw_info['network_info']:
            text_widget.insert(tk.END, f"Primary IP: {hw_info['network_info']['primary_ip']}\n")
        
        text_widget.insert(tk.END, "\nInterfaces:\n")
        for interface in hw_info['network_info']['interfaces']:
            text_widget.insert(tk.END, f"\n  {interface['name']} - {'Up' if interface['is_up'] else 'Down'}\n")
            if 'speed' in interface and interface['speed'] is not None:
                text_widget.insert(tk.END, f"  Speed: {interface['speed']} Mbps\n")
            
            # Show addresses
            for addr in interface['addresses']:
                text_widget.insert(tk.END, f"  {addr['family']}: {addr['address']}\n")
                if 'netmask' in addr:
                    text_widget.insert(tk.END, f"    Netmask: {addr['netmask']}\n")
        
        # GPU information if available
        if hw_info["gpu_info"]:
            text_widget.insert(tk.END, "\nGPU Information\n", "heading")
            text_widget.insert(tk.END, "--------------\n")
            for i, gpu in enumerate(hw_info["gpu_info"]):
                text_widget.insert(tk.END, f"\nGPU {i+1}: {gpu.get('name', 'Unknown')}\n")
                if 'memory' in gpu:
                    memory_gb = gpu['memory'] / (1024**3) if gpu['memory'] > 1024**2 else gpu['memory'] / (1024**2)
                    unit = "GB" if gpu['memory'] > 1024**2 else "MB"
                    text_widget.insert(tk.END, f"Memory: {memory_gb:.1f} {unit}\n")
                if 'driver_version' in gpu:
                    text_widget.insert(tk.END, f"Driver: {gpu['driver_version']}\n")
        
        # Make text widget read-only
        text_widget.config(state=tk.DISABLED)

    def _create_compatibility_tab(self, notebook, compatibility_results):
        """Create a tab showing compatibility and fallback options"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Compatibility")
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Add header
        ttk.Label(
            scroll_frame,
            text="Hardware Compatibility Analysis",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        # Header row
        ttk.Label(
            scroll_frame,
            text="Component",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        ttk.Label(
            scroll_frame,
            text="Status",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(
            scroll_frame,
            text="Fallback Option",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        # Add separator
        separator = ttk.Separator(scroll_frame, orient="horizontal")
        separator.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        
        # Display compatibility results
        row = 3
        for result in compatibility_results:
            # Convert from dictionary if needed (from saved results)
            if isinstance(result, dict):
                component = result.get("component", "Unknown")
                is_compatible = result.get("is_compatible", False)
                message = result.get("message", "")
                severity = result.get("severity", "info")
                fallback_available = result.get("fallback_available", False)
                fallback_option = result.get("fallback_option", None)
                fallback_description = result.get("fallback_description", None)
            else:
                component = result.component
                is_compatible = result.is_compatible
                message = result.message
                severity = result.severity
                fallback_available = result.fallback_available
                fallback_option = result.fallback_option
                fallback_description = result.fallback_description
            
            # Component
            ttk.Label(
                scroll_frame,
                text=component
            ).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            
            # Status with icon
            if is_compatible:
                status_text = "✅ Compatible"
            else:
                if severity == "critical":
                    status_text = "🛑 Critical"
                elif severity == "warning":
                    status_text = "⚠️ Warning"
                else:
                    status_text = "ℹ️ Info"
                    
                status_text += f": {message}"
            
            ttk.Label(
                scroll_frame,
                text=status_text,
                wraplength=300
            ).grid(row=row, column=1, sticky="w", padx=5, pady=5)
            
            # Fallback option (if available)
            if not is_compatible and fallback_available and fallback_description:
                # Check if fallback is applied
                is_applied = (
                    component in self.fallback_options_applied and 
                    self.fallback_options_applied[component] == fallback_option
                )
                
                fallback_text = f"{fallback_description}"
                if is_applied:
                    fallback_text = "✓ " + fallback_text
                
                ttk.Label(
                    scroll_frame,
                    text=fallback_text,
                    wraplength=300
                ).grid(row=row, column=2, sticky="w", padx=5, pady=5)
            else:
                ttk.Label(
                    scroll_frame,
                    text="N/A"
                ).grid(row=row, column=2, sticky="w", padx=5, pady=5)
            
            row += 1

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