"""
Configuration management for the Proxmox NLI installer.
Handles loading, saving, and validating installer configuration.
"""
import os
import json
import tkinter as tk
from typing import Dict, Any
import socket
import requests
import re
import time

class ConfigManager:
    def __init__(self):
        # Initialize configuration variables
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
        self._load_config()

    def get_config(self) -> Dict[str, tk.Variable]:
        """Get the current configuration variables"""
        return self.config

    def _load_config(self):
        """Load configuration from file if it exists"""
        config_path = self._get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                for key, value in saved_config.items():
                    if key in self.config:
                        self.config[key].set(value)
            except:
                pass

    def save_config(self):
        """Save current configuration to file"""
        config_to_save = {
            key: var.get() for key, var in self.config.items()
            if key != "proxmox_password"  # Don't save password
        }
        try:
            with open(self._get_config_path(), 'w') as f:
                json.dump(config_to_save, f, indent=2)
        except:
            pass

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate the current configuration
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        # Validate host
        host = self.config["proxmox_host"].get()
        if not host:
            errors.append("Proxmox Host is required")
        else:
            is_valid_host = False
            # Check if IP address
            if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', host):
                try:
                    octets = list(map(int, host.split('.')))
                    is_valid_host = all(0 <= octet <= 255 for octet in octets)
                    if not is_valid_host:
                        errors.append("Invalid IP address format")
                except:
                    errors.append("Invalid IP address format")
            # Check if hostname
            elif re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', host):
                is_valid_host = True
            else:
                errors.append("Invalid hostname format")

            if is_valid_host:
                try:
                    socket.gethostbyname(host)
                except socket.error:
                    errors.append(f"Cannot resolve host: {host}")

        # Validate credentials
        if not self.config["proxmox_user"].get():
            errors.append("Username is required")
        if not self.config["proxmox_password"].get():
            errors.append("Password is required")

        # Validate port
        try:
            port = int(self.config["port"].get())
            if not 1 <= port <= 65535:
                errors.append("Port must be between 1 and 65535")
        except ValueError:
            errors.append("Port must be a valid number")

        return len(errors) == 0, errors

    def test_proxmox_connection(self) -> tuple[bool, str]:
        """Test connection to Proxmox server
        Returns:
            tuple: (success, message)
        """
        try:
            host = self.config["proxmox_host"].get()
            verify = self.config["verify_ssl"].get()
            api_url = f"https://{host}:8006/api2/json/version"
            
            response = requests.get(api_url, verify=verify, timeout=5)
            if response.status_code in [200, 401]:  # 401 means auth required but server reachable
                return True, "Connection successful"
            return False, f"Server returned status code {response.status_code}"
        except requests.exceptions.SSLError:
            return False, "SSL certificate verification failed"
        except requests.exceptions.ConnectionError:
            return False, "Could not connect to server"
        except requests.exceptions.Timeout:
            return False, "Connection timed out"
        except Exception as e:
            return False, str(e)

    def save_validation_report(self):
        """Generate and save a validation report"""
        report = {
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

        # Check if port is available
        try:
            port = int(self.config["port"].get())
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                report["validation_results"]["port_available"] = False
                report["validation_results"]["port_warning"] = f"Port {port} is already in use"
            sock.close()
        except:
            report["validation_results"]["port_check_error"] = "Could not check port availability"

        try:
            with open(self._get_validation_report_path(), 'w') as f:
                json.dump(report, f, indent=2)
        except:
            pass

    def _get_config_path(self) -> str:
        """Get the path to the config file"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "installer_config.json")

    def _get_validation_report_path(self) -> str:
        """Get the path to the validation report file"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_validation.json")