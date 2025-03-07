#!/usr/bin/env python3
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import webbrowser
import time
import json
import re
import socket
import requests
import qrcode
from PIL import Image, ImageTk
from pathlib import Path

class ProxmoxNLIInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Proxmox NLI Installer")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Set icon if available
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img", "favicon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        # Variables
        self.config = {
            "proxmox_host": tk.StringVar(),
            "proxmox_user": tk.StringVar(value="root"),
            "proxmox_password": tk.StringVar(),
            "proxmox_realm": tk.StringVar(value="pam"),
            "verify_ssl": tk.BooleanVar(value=False),
            "start_web_interface": tk.BooleanVar(value=True),
            "debug_mode": tk.BooleanVar(value=False),
            "autostart": tk.BooleanVar(value=False),
            "port": tk.StringVar(value="5000"),
            "unattended_installation": tk.BooleanVar(value=False)
        }
        
        # Create the notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create tabs
        self.welcome_tab = ttk.Frame(self.notebook)
        self.prerequisites_tab = ttk.Frame(self.notebook)
        self.config_tab = ttk.Frame(self.notebook)
        self.install_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.welcome_tab, text="Welcome")
        self.notebook.add(self.prerequisites_tab, text="Prerequisites")
        self.notebook.add(self.config_tab, text="Configuration")
        self.notebook.add(self.install_tab, text="Installation")
        
        # Create the welcome tab
        self._create_welcome_tab()
        
        # Create the prerequisites tab
        self._create_prerequisites_tab()
        
        # Create the configuration tab
        self._create_config_tab()
        
        # Create the installation tab
        self._create_install_tab()

    def _create_welcome_tab(self):
        # Welcome message
        welcome_frame = ttk.Frame(self.welcome_tab)
        welcome_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ttk.Label(welcome_frame, text="Welcome to Proxmox NLI Setup Wizard", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        
        ttk.Label(welcome_frame, text="This wizard will guide you through installing and configuring the Proxmox Natural Language Interface.\n\n"
                                     "This tool allows you to manage your Proxmox environment using natural language commands.", 
                 wraplength=500, justify="center").pack(pady=10)
        
        # Next button
        ttk.Button(welcome_frame, text="Next >", 
                  command=lambda: self.notebook.select(self.prerequisites_tab)).pack(pady=10)

    def _create_prerequisites_tab(self):
        # Prerequisites frame
        prereq_frame = ttk.Frame(self.prerequisites_tab)
        prereq_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ttk.Label(prereq_frame, text="Checking Prerequisites", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Create a frame for the checklist
        checklist_frame = ttk.Frame(prereq_frame)
        checklist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status variables
        self.python_status = tk.StringVar(value="⏳ Checking...")
        self.pip_status = tk.StringVar(value="⏳ Checking...")
        self.venv_status = tk.StringVar(value="⏳ Checking...")
        self.network_status = tk.StringVar(value="⏳ Checking...")
        
        # Create checklist
        ttk.Label(checklist_frame, text="Python 3.8+ installed:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(checklist_frame, textvariable=self.python_status).grid(row=0, column=1, sticky="w", pady=5)
        
        ttk.Label(checklist_frame, text="Pip installed:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(checklist_frame, textvariable=self.pip_status).grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(checklist_frame, text="Virtual environment support:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Label(checklist_frame, textvariable=self.venv_status).grid(row=2, column=1, sticky="w", pady=5)
        
        ttk.Label(checklist_frame, text="Network connectivity:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Label(checklist_frame, textvariable=self.network_status).grid(row=3, column=1, sticky="w", pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(prereq_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        self.check_button = ttk.Button(buttons_frame, text="Check Prerequisites", command=self._check_prerequisites)
        self.check_button.pack(side=tk.LEFT, padx=5)
        
        self.next_prereq_button = ttk.Button(buttons_frame, text="Next >", state="disabled",
                                           command=lambda: self.notebook.select(self.config_tab))
        self.next_prereq_button.pack(side=tk.RIGHT, padx=5)
        
        # Run prerequisites check automatically when tab is shown
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _create_config_tab(self):
        # Configuration frame
        config_frame = ttk.Frame(self.config_tab)
        config_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ttk.Label(config_frame, text="Proxmox Configuration", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Create a frame for the form
        form_frame = ttk.Frame(config_frame)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create form fields
        ttk.Label(form_frame, text="Proxmox Host:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.config["proxmox_host"], width=30).grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(form_frame, text="(e.g., 192.168.1.100 or proxmox.local)").grid(row=0, column=2, sticky="w", pady=5)
        
        ttk.Label(form_frame, text="Username:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.config["proxmox_user"], width=30).grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.config["proxmox_password"], show="*", width=30).grid(row=2, column=1, sticky="w", pady=5)
        
        ttk.Label(form_frame, text="Realm:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.config["proxmox_realm"], width=30).grid(row=3, column=1, sticky="w", pady=5)
        ttk.Label(form_frame, text="(usually 'pam')").grid(row=3, column=2, sticky="w", pady=5)
        
        ttk.Checkbutton(form_frame, text="Verify SSL", variable=self.config["verify_ssl"]).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Separator(form_frame, orient="horizontal").grid(row=5, column=0, columnspan=3, sticky="ew", pady=10)
        
        ttk.Label(form_frame, text="Application Settings", font=("Arial", 12, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Checkbutton(form_frame, text="Start Web Interface by default", variable=self.config["start_web_interface"]).grid(row=7, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Label(form_frame, text="Web Port:").grid(row=8, column=0, sticky="w", pady=5)
        ttk.Entry(form_frame, textvariable=self.config["port"], width=10).grid(row=8, column=1, sticky="w", pady=5)
        
        ttk.Checkbutton(form_frame, text="Debug Mode", variable=self.config["debug_mode"]).grid(row=9, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Checkbutton(form_frame, text="Create autostart shortcut", variable=self.config["autostart"]).grid(row=10, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Checkbutton(form_frame, text="Unattended Installation", variable=self.config["unattended_installation"]).grid(row=11, column=0, columnspan=2, sticky="w", pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(config_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        ttk.Button(buttons_frame, text="< Back", 
                  command=lambda: self.notebook.select(self.prerequisites_tab)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Next >", 
                  command=self._validate_and_proceed).pack(side=tk.RIGHT, padx=5)
        
        # Try to load saved config
        self._load_config()

    def _create_install_tab(self):
        # Install frame
        install_frame = ttk.Frame(self.install_tab)
        install_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ttk.Label(install_frame, text="Installation Progress", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Progress bar and status
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(install_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=20, pady=10)
        
        self.status_var = tk.StringVar(value="Ready to install")
        ttk.Label(install_frame, textvariable=self.status_var).pack(pady=5)
        
        # Log area
        ttk.Label(install_frame, text="Installation Log:").pack(anchor="w", padx=20, pady=5)
        
        log_frame = ttk.Frame(install_frame)
        log_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=60, wrap="word")
        self.log_text.pack(side=tk.LEFT, fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(install_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        self.back_install_button = ttk.Button(buttons_frame, text="< Back", 
                                           command=lambda: self.notebook.select(self.config_tab))
        self.back_install_button.pack(side=tk.LEFT, padx=5)
        
        self.install_button = ttk.Button(buttons_frame, text="Install", command=self._run_installation)
        self.install_button.pack(side=tk.RIGHT, padx=5)
        
        self.finish_button = ttk.Button(buttons_frame, text="Finish & Launch", state="disabled", command=self._finish_and_launch)
        self.finish_button.pack(side=tk.RIGHT, padx=5)

    def _on_tab_changed(self, event):
        current_tab = self.notebook.select()
        if current_tab == str(self.prerequisites_tab) and self.python_status.get() == "⏳ Checking...":
            # Run the check when the prerequisites tab is first shown
            self._check_prerequisites()

    def _check_prerequisites(self):
        self.check_button.config(state="disabled")
        
        # Reset status
        self.python_status.set("⏳ Checking...")
        self.pip_status.set("⏳ Checking...")
        self.venv_status.set("⏳ Checking...")
        self.network_status.set("⏳ Checking...")
        self.root.update()
        
        # Helper function to update status with delay to make it more readable
        def update_status(var, status, delay=0.5):
            time.sleep(delay)
            var.set(status)
            self.root.update()
        
        # Check Python version
        try:
            result = subprocess.run([sys.executable, "-c", "import sys; print(sys.version)"], 
                                    capture_output=True, text=True, check=True)
            version = result.stdout.strip().split()[0]
            if float(version.split(".")[:2]) >= 3.8:
                update_status(self.python_status, f"✅ Python {version} detected")
                python_ok = True
            else:
                update_status(self.python_status, f"❌ Python {version} (3.8+ required)")
                python_ok = False
        except Exception as e:
            update_status(self.python_status, "❌ Error checking Python")
            python_ok = False
        
        # Check pip
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                    capture_output=True, text=True, check=True)
            update_status(self.pip_status, "✅ Pip detected")
            pip_ok = True
        except Exception as e:
            update_status(self.pip_status, "❌ Pip not found")
            pip_ok = False
        
        # Check venv
        try:
            result = subprocess.run([sys.executable, "-c", "import venv"], 
                                    capture_output=True, text=True, check=True)
            update_status(self.venv_status, "✅ Virtual environment support available")
            venv_ok = True
        except Exception as e:
            update_status(self.venv_status, "❌ Virtual environment not available")
            venv_ok = False
        
        # Check network (try to reach pypi.org)
        try:
            result = subprocess.run([sys.executable, "-c", 
                                    "import urllib.request; urllib.request.urlopen('https://pypi.org', timeout=5)"], 
                                    capture_output=True, text=True, check=True)
            update_status(self.network_status, "✅ Internet connection available")
            network_ok = True
        except Exception as e:
            update_status(self.network_status, "❌ No internet connection detected")
            network_ok = False
        
        # Enable next button if all checks pass
        all_ok = python_ok and pip_ok and venv_ok and network_ok
        self.next_prereq_button.config(state="normal" if all_ok else "disabled")
        
        # Enable check button again
        self.check_button.config(state="normal")

    def _validate_and_proceed(self):
        # Enhanced validation with more detailed error messages
        validation_errors = []
        
        # Check Proxmox host
        host = self.config["proxmox_host"].get()
        if not host:
            validation_errors.append("Proxmox Host is required")
        else:
            # Validate host format (IP or hostname)
            is_valid_host = False
            # Check if IP address
            if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', host):
                # Validate IPv4 format
                try:
                    octets = list(map(int, host.split('.')))
                    is_valid_host = all(0 <= octet <= 255 for octet in octets)
                    if not is_valid_host:
                        validation_errors.append("Invalid IP address format")
                except:
                    validation_errors.append("Invalid IP address format")
            # Check if hostname
            elif re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', host):
                is_valid_host = True
            else:
                validation_errors.append("Invalid hostname format")
            
            # Test connection if format is valid
            if is_valid_host:
                try:
                    # Just test if the host is reachable
                    socket.gethostbyname(host)
                except socket.error:
                    validation_errors.append(f"Cannot resolve host: {host}. Make sure it's reachable.")
        
        # Check username
        if not self.config["proxmox_user"].get():
            validation_errors.append("Username is required")
        
        # Check password
        if not self.config["proxmox_password"].get():
            validation_errors.append("Password is required")
        
        # Validate port
        try:
            port = int(self.config["port"].get())
            if not 1 <= port <= 65535:
                validation_errors.append("Port must be between 1 and 65535")
        except ValueError:
            validation_errors.append("Port must be a valid number")
        
        # If errors, show them all at once
        if validation_errors:
            messagebox.showerror("Validation Error", "\n".join(validation_errors))
            return
        
        # Verify Proxmox connectivity
        if messagebox.askyesno("Verify Connection", "Would you like to test the connection to your Proxmox server before proceeding?"):
            self.status_var.set("Testing Proxmox connection...")
            self.root.update()
            
            try:
                # Construct the API URL
                api_url = f"https://{host}:8006/api2/json/version"
                
                # Skip SSL verification if requested
                verify = self.config["verify_ssl"].get()
                
                # For a simple connectivity test, don't need auth
                response = requests.get(api_url, verify=verify, timeout=5)
                
                if response.status_code == 200 or response.status_code == 401:  # 401 is auth error but server is reachable
                    messagebox.showinfo("Connection Test", "Proxmox server is reachable!")
                else:
                    if not messagebox.askyesno("Connection Warning", 
                                           f"Received status code {response.status_code} from Proxmox server. Continue anyway?"):
                        return
            except requests.exceptions.SSLError:
                if not messagebox.askyesno("SSL Warning", 
                                       "SSL certificate verification failed. This could be due to a self-signed certificate. Continue anyway?"):
                    return
            except requests.exceptions.ConnectionError:
                if not messagebox.askyesno("Connection Error", 
                                       "Could not connect to the Proxmox server. Continue anyway?"):
                    return
            except requests.exceptions.Timeout:
                if not messagebox.askyesno("Connection Timeout", 
                                       "Connection to Proxmox server timed out. Continue anyway?"):
                    return
            except Exception as e:
                if not messagebox.askyesno("Connection Error", 
                                       f"Error connecting to Proxmox server: {str(e)}. Continue anyway?"):
                    return
        
        # Save config
        self._save_config()
        
        # Save a configuration validation report file
        self._save_validation_report()
            
        # Move to install tab
        self.notebook.select(self.install_tab)
    
    def _save_validation_report(self):
        """Generate a validation report for the configuration"""
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_validation.json")
        
        validation_report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "proxmox_host": self.config["proxmox_host"].get(),
            "proxmox_user": self.config["proxmox_user"].get(),
            "proxmox_realm": self.config["proxmox_realm"].get(),
            "verify_ssl": self.config["verify_ssl"].get(),
            "web_interface_enabled": self.config["start_web_interface"].get(),
            "port": self.config["port"].get(),
            "autostart": self.config["autostart"].get(),
            "validation_results": {
                "host_reachable": True,
                "port_available": True
            }
        }
        
        # Check if web port is already in use
        try:
            port = int(self.config["port"].get())
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                validation_report["validation_results"]["port_available"] = False
                validation_report["validation_results"]["port_warning"] = f"Port {port} is already in use. The application might not start correctly."
            sock.close()
        except:
            validation_report["validation_results"]["port_check_error"] = "Could not check if port is available"
        
        # Save report
        try:
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
        except:
            pass

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer_config.json")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    
                for key, value in saved_config.items():
                    if key in self.config:
                        self.config[key].set(value)
            except:
                # Ignore errors when loading config
                pass

    def _save_config(self):
        # Save configuration (excluding password)
        config_to_save = {
            "proxmox_host": self.config["proxmox_host"].get(),
            "proxmox_user": self.config["proxmox_user"].get(),
            "proxmox_realm": self.config["proxmox_realm"].get(),
            "verify_ssl": self.config["verify_ssl"].get(),
            "start_web_interface": self.config["start_web_interface"].get(),
            "debug_mode": self.config["debug_mode"].get(),
            "port": self.config["port"].get(),
            "autostart": self.config["autostart"].get(),
            "unattended_installation": self.config["unattended_installation"].get()
        }
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer_config.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config_to_save, f, indent=2)
        except:
            # Ignore errors when saving config
            pass

    def _run_installation(self):
        # Disable buttons during installation
        self.install_button.config(state="disabled")
        self.back_install_button.config(state="disabled")
        
        if self.config["unattended_installation"].get():
            self._install_process()
        else:
            # Start installation in a separate thread
            thread = threading.Thread(target=self._install_process)
            thread.daemon = True
            thread.start()

    def _install_process(self):
        # Clear log
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        # Helper functions
        def update_status(message, progress=None):
            self.status_var.set(message)
            if progress is not None:
                self.progress_var.set(progress)
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.root.update()
        
        def run_command(command, success_msg, error_msg):
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                update_status(f"{success_msg}: {result.stdout.strip()}")
                return True, result.stdout
            except subprocess.CalledProcessError as e:
                update_status(f"{error_msg}: {e.stderr.strip()}")
                return False, e.stderr
            except Exception as e:
                update_status(f"{error_msg}: {str(e)}")
                return False, str(e)
        
        try:
            # Step 1: Create .env file
            update_status("Creating environment configuration file...", 5)
            
            env_content = f"""PROXMOX_API_URL=https://{self.config["proxmox_host"].get()}:8006
PROXMOX_USER={self.config["proxmox_user"].get()}@{self.config["proxmox_realm"].get()}
PROXMOX_PASSWORD={self.config["proxmox_password"].get()}
START_WEB_INTERFACE={'true' if self.config["start_web_interface"].get() else 'false'}
PORT={self.config["port"].get()}
DEBUG_MODE={'true' if self.config["debug_mode"].get() else 'false'}
"""
            
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            update_status(".env file created successfully", 10)
            
            # Step 2: Install dependencies
            update_status("Installing Python dependencies...", 20)
            
            # Install required packages
            success, output = run_command(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                "Dependencies installed successfully",
                "Failed to install dependencies"
            )
            
            if not success:
                raise Exception("Failed to install dependencies")
            
            update_status("Python dependencies installed successfully", 40)
            
            # Step 3: Download NLTK resources
            update_status("Downloading NLTK resources...", 50)
            
            nltk_code = """
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
"""
            
            success, output = run_command(
                [sys.executable, "-c", nltk_code],
                "NLTK resources downloaded successfully",
                "Failed to download NLTK resources"
            )
            
            if not success:
                raise Exception("Failed to download NLTK resources")
            
            update_status("NLTK resources downloaded successfully", 70)

            # Step 4: Auto-configure network settings
            update_status("Configuring network settings...", 75)
            
            try:
                # Get system network configuration
                net_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "network_config.json")
                
                # Get default gateway info
                network_info = {}
                # Get default IP address that would be used for internet connection
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    # doesn't even have to be reachable
                    s.connect(('10.255.255.255', 1))
                    network_info["default_ip"] = s.getsockname()[0]
                except:
                    network_info["default_ip"] = '127.0.0.1'
                finally:
                    s.close()
                
                # Save network configuration
                with open(net_config_path, 'w') as f:
                    json.dump(network_info, f, indent=2)
                
                update_status(f"Network configured with IP: {network_info.get('default_ip', 'unknown')}", 77)
            except Exception as e:
                update_status(f"Warning: Could not auto-configure network settings: {str(e)}", 77)
            
            # Step 5: Generate QR code for first access
            update_status("Generating QR code for easy access...", 80)
            try:
                # Determine server IP for QR code
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
                qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "access_qr.png")
                img.save(qr_path)
                
                # Show in the UI
                qr_img = Image.open(qr_path)
                qr_img = qr_img.resize((150, 150), Image.LANCZOS)
                qr_photo = ImageTk.PhotoImage(qr_img)
                
                # Create a pop-up window to display the QR code
                qr_window = tk.Toplevel(self.root)
                qr_window.title("Access QR Code")
                qr_window.geometry("300x350")
                
                ttk.Label(qr_window, text="Scan this QR code to access:").pack(pady=10)
                ttk.Label(qr_window, image=qr_photo).pack(pady=5)
                ttk.Label(qr_window, text=access_url).pack(pady=10)
                ttk.Button(qr_window, text="Close", command=qr_window.destroy).pack(pady=10)
                
                # Keep a reference to prevent garbage collection
                self.qr_photo = qr_photo
                
                update_status(f"QR code generated for: {access_url}", 82)
            except Exception as e:
                update_status(f"Warning: Could not generate QR code: {str(e)}", 82)
            
            # Step 6: Create shortcuts
            update_status("Creating shortcuts...", 85)
            
            # Create launcher script
            launcher_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_proxmox_nli.bat")
            
            with open(launcher_path, 'w') as f:
                f.write('@echo off\n')
                f.write('echo Starting Proxmox NLI...\n')
                f.write(f'"{sys.executable}" main.py\n')
                f.write('pause\n')
            
            update_status("Created launcher script", 90)
            
            # Create autostart shortcut if requested
            if self.config["autostart"].get():
                try:
                    startup_folder = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
                    shortcut_path = os.path.join(startup_folder, "Proxmox NLI.bat")
                    
                    # Create a simple batch file shortcut
                    with open(shortcut_path, 'w') as f:
                        f.write('@echo off\n')
                        f.write(f'cd /d "{os.path.dirname(os.path.abspath(__file__))}"\n')
                        f.write(f'start "" "{sys.executable}" main.py --no-console\n')
                    
                    update_status("Created autostart shortcut", 95)
                except Exception as e:
                    update_status(f"Failed to create autostart shortcut: {str(e)}", 95)
            
            # Step 7: Installation complete
            update_status("Installation completed successfully!", 100)
            
            # Enable launch button
            self.finish_button.config(state="normal")
            
            if self.config["unattended_installation"].get():
                self._finish_and_launch()
            
        except Exception as e:
            update_status(f"Installation failed: {str(e)}")
            messagebox.showerror("Installation Error", f"Installation failed:\n{str(e)}")
            
            # Add troubleshooting help
            update_status("Troubleshooting suggestions:")
            update_status("1. Check your internet connection and try again")
            update_status("2. Make sure Proxmox host is accessible")
            update_status("3. Try running as Administrator if on Windows")
            update_status("4. Check the log file for more details")
            
            # Create error log
            try:
                error_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer_error.log")
                with open(error_log_path, 'w') as f:
                    f.write(f"ERROR: {str(e)}\n")
                    f.write(f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"CONFIGURATION: {json.dumps({k: v.get() for k, v in self.config.items() if k != 'proxmox_password'})}")
                update_status(f"Error details saved to {error_log_path}")
            except:
                pass
            
            # Enable back button and install button
            self.back_install_button.config(state="normal")
            self.install_button.config(state="normal")

    def _finish_and_launch(self):
        # Save current config
        self._save_config()
        
        # Launch the application
        try:
            # Run without waiting
            subprocess.Popen([sys.executable, "main.py"], 
                            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            
            # Close the installer
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Launch Error", f"Error launching application:\n{str(e)}")

def main():
    root = tk.Tk()
    app = ProxmoxNLIInstaller(root)
    root.mainloop()

if __name__ == "__main__":
    main()