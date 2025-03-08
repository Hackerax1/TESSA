"""
Installation tab for the Proxmox NLI installer.
Handles the installation process, progress tracking, and final setup.
"""
import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
import qrcode
from PIL import Image, ImageTk
import socket
import json
from ..config_manager import ConfigManager

class InstallTab:
    def __init__(self, parent: ttk.Notebook, config_manager: ConfigManager, on_finish: Callable):
        self.tab = ttk.Frame(parent)
        self.config_manager = config_manager
        self.on_finish = on_finish
        self.config = config_manager.get_config()
        
        # Progress tracking
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready to install")
        
        self._create_ui()
        
    def _create_ui(self):
        # Main install frame
        install_frame = ttk.Frame(self.tab)
        install_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ttk.Label(
            install_frame,
            text="Installation Progress",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            install_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress.pack(fill="x", padx=20, pady=10)
        
        # Status label
        ttk.Label(
            install_frame,
            textvariable=self.status_var
        ).pack(pady=5)
        
        # Log area
        ttk.Label(
            install_frame,
            text="Installation Log:"
        ).pack(anchor="w", padx=20, pady=5)
        
        log_frame = ttk.Frame(install_frame)
        log_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=60, wrap="word")
        self.log_text.pack(side=tk.LEFT, fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Button frame
        button_frame = ttk.Frame(install_frame)
        button_frame.pack(fill="x", pady=10)
        
        self.back_button = ttk.Button(
            button_frame,
            text="< Back",
            command=self._on_back
        )
        self.back_button.pack(side=tk.LEFT, padx=5)
        
        self.install_button = ttk.Button(
            button_frame,
            text="Install",
            command=self._start_installation
        )
        self.install_button.pack(side=tk.RIGHT, padx=5)
        
        self.finish_button = ttk.Button(
            button_frame,
            text="Finish & Launch",
            state="disabled",
            command=self._finish_installation
        )
        self.finish_button.pack(side=tk.RIGHT, padx=5)
        
    def _on_back(self):
        """Handle back button click"""
        if self.install_button["state"] != "disabled":
            # Only allow going back if installation hasn't started
            self.tab.master.select(self.tab.master.index(self.tab) - 1)
            
    def _start_installation(self):
        """Start the installation process"""
        self.install_button.config(state="disabled")
        self.back_button.config(state="disabled")
        
        # Start installation in a thread if not unattended
        if self.config["unattended_installation"].get():
            self._run_installation()
        else:
            thread = threading.Thread(target=self._run_installation)
            thread.daemon = True
            thread.start()
            
    def _update_status(self, message: str, progress: float = None):
        """Update status message and progress"""
        self.status_var.set(message)
        if progress is not None:
            self.progress_var.set(progress)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.tab.update()
        
    def _run_command(self, command: list, success_msg: str, error_msg: str) -> tuple[bool, str]:
        """Run a command and handle output"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            self._update_status(f"{success_msg}: {result.stdout.strip()}")
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            self._update_status(f"{error_msg}: {e.stderr.strip()}")
            return False, e.stderr
        except Exception as e:
            self._update_status(f"{error_msg}: {str(e)}")
            return False, str(e)
            
    def _run_installation(self):
        """Run the installation process"""
        try:
            # Step 1: Create .env file
            self._update_status("Creating environment configuration...", 5)
            self._create_env_file()
            
            # Step 2: Install dependencies
            self._update_status("Installing Python dependencies...", 20)
            success, _ = self._run_command(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                "Dependencies installed successfully",
                "Failed to install dependencies"
            )
            if not success:
                raise Exception("Failed to install dependencies")
                
            # Step 3: Download NLTK resources
            self._update_status("Downloading NLTK resources...", 50)
            nltk_code = """
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
"""
            success, _ = self._run_command(
                [sys.executable, "-c", nltk_code],
                "NLTK resources downloaded successfully",
                "Failed to download NLTK resources"
            )
            if not success:
                raise Exception("Failed to download NLTK resources")
                
            # Step 4: Configure network
            self._update_status("Configuring network settings...", 75)
            network_info = self._configure_network()
            
            # Step 5: Generate QR code
            self._update_status("Generating QR code for easy access...", 80)
            self._generate_qr_code(network_info)
            
            # Step 6: Create shortcuts
            self._update_status("Creating shortcuts...", 85)
            self._create_shortcuts()
            
            # Installation complete
            self._update_status("Installation completed successfully!", 100)
            self.finish_button.config(state="normal")
            
            if self.config["unattended_installation"].get():
                self._finish_installation()
                
        except Exception as e:
            self._handle_installation_error(e)
            
    def _create_env_file(self):
        """Create the .env configuration file"""
        env_content = f"""PROXMOX_API_URL=https://{self.config["proxmox_host"].get()}:8006
PROXMOX_USER={self.config["proxmox_user"].get()}@{self.config["proxmox_realm"].get()}
PROXMOX_PASSWORD={self.config["proxmox_password"].get()}
START_WEB_INTERFACE={'true' if self.config["start_web_interface"].get() else 'false'}
PORT={self.config["port"].get()}
DEBUG_MODE={'true' if self.config["debug_mode"].get() else 'false'}
"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        with open(env_path, 'w') as f:
            f.write(env_content)
            
    def _configure_network(self) -> dict:
        """Configure network settings and return network info"""
        network_info = {}
        
        # Get default IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            network_info["default_ip"] = s.getsockname()[0]
        except:
            network_info["default_ip"] = '127.0.0.1'
        finally:
            s.close()
            
        # Save network configuration
        net_config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "network_config.json"
        )
        with open(net_config_path, 'w') as f:
            json.dump(network_info, f, indent=2)
            
        return network_info
        
    def _generate_qr_code(self, network_info: dict):
        """Generate QR code for easy access"""
        server_ip = network_info.get("default_ip", "localhost")
        port = self.config["port"].get()
        access_url = f"http://{server_ip}:{port}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(access_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "access_qr.png"
        )
        img.save(qr_path)
        
        # Show QR code in UI
        qr_img = Image.open(qr_path)
        qr_img = qr_img.resize((150, 150), Image.LANCZOS)
        qr_photo = ImageTk.PhotoImage(qr_img)
        
        # Create popup window
        qr_window = tk.Toplevel(self.tab)
        qr_window.title("Access QR Code")
        qr_window.geometry("300x350")
        
        ttk.Label(qr_window, text="Scan this QR code to access:").pack(pady=10)
        ttk.Label(qr_window, image=qr_photo).pack(pady=5)
        ttk.Label(qr_window, text=access_url).pack(pady=10)
        ttk.Button(qr_window, text="Close", command=qr_window.destroy).pack(pady=10)
        
        # Keep reference to prevent garbage collection
        self.qr_photo = qr_photo
        
    def _create_shortcuts(self):
        """Create application shortcuts"""
        # Create launcher script
        launcher_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "run_proxmox_nli.bat"
        )
        with open(launcher_path, 'w') as f:
            f.write('@echo off\n')
            f.write('echo Starting Proxmox NLI...\n')
            f.write(f'"{sys.executable}" main.py\n')
            f.write('pause\n')
            
        # Create autostart shortcut if requested
        if self.config["autostart"].get():
            try:
                startup_folder = os.path.join(
                    os.environ["APPDATA"],
                    "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
                )
                shortcut_path = os.path.join(startup_folder, "Proxmox NLI.bat")
                
                with open(shortcut_path, 'w') as f:
                    f.write('@echo off\n')
                    f.write(f'cd /d "{os.path.dirname(os.path.dirname(os.path.dirname(__file__)))}"\n')
                    f.write(f'start "" "{sys.executable}" main.py --no-console\n')
            except Exception as e:
                self._update_status(f"Warning: Failed to create autostart shortcut: {str(e)}")
                
    def _handle_installation_error(self, error: Exception):
        """Handle installation errors"""
        error_message = str(error)
        self._update_status(f"Installation failed: {error_message}")
        messagebox.showerror("Installation Error", f"Installation failed:\n{error_message}")
        
        # Add troubleshooting help
        self._update_status("\nTroubleshooting suggestions:")
        self._update_status("1. Check your internet connection and try again")
        self._update_status("2. Make sure Proxmox host is accessible")
        self._update_status("3. Try running as Administrator if on Windows")
        self._update_status("4. Check the log file for more details")
        
        # Create error log
        try:
            error_log_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "installer_error.log"
            )
            with open(error_log_path, 'w') as f:
                f.write(f"ERROR: {error_message}\n")
                f.write(f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                config_dump = {
                    k: v.get() for k, v in self.config.items()
                    if k != "proxmox_password"
                }
                f.write(f"CONFIGURATION: {json.dumps(config_dump)}")
            self._update_status(f"Error details saved to {error_log_path}")
        except:
            pass
            
        # Re-enable buttons
        self.back_button.config(state="normal")
        self.install_button.config(state="normal")
        
    def _finish_installation(self):
        """Complete installation and launch application"""
        # Save final configuration
        self.config_manager.save_config()
        
        # Launch application
        try:
            subprocess.Popen(
                [sys.executable, "main.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            self.on_finish()
        except Exception as e:
            messagebox.showerror(
                "Launch Error",
                f"Error launching application:\n{str(e)}"
            )

def create_install_tab(
    parent: ttk.Notebook,
    config_manager: ConfigManager,
    on_finish: Callable
) -> ttk.Frame:
    """Create the installation tab
    
    Args:
        parent: Parent notebook widget
        config_manager: Configuration manager instance
        on_finish: Callback when installation is complete
        
    Returns:
        The installation tab frame
    """
    tab = InstallTab(parent, config_manager, on_finish)
    return tab.tab