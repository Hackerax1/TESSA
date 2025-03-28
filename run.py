#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
from check_requirements import RequirementsChecker
import shutil
from pathlib import Path
import webbrowser
import time
import requests
import socket
import argparse

def is_docker():
    """Check if running in a Docker container"""
    path = '/proc/self/cgroup'
    return os.path.exists('/.dockerenv') or (os.path.exists(path) and any('docker' in line for line in open(path)))

def setup_docker():
    """Setup for Docker environment"""
    # In Docker, we assume all requirements are met
    # Just create the .env if it doesn't exist
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print("Created default .env file. Please edit it with your configuration.")
        sys.exit(1)
    return True

def setup_windows(skip_build_check=False):
    """Setup for Windows environment"""
    print("Checking system requirements...")
    checker = RequirementsChecker()
    
    if skip_build_check:
        # Manually run all checks except build tools check
        print("Skipping build tools check as requested...")
        python_ok = checker.check_python_version()
        pip_ok = checker.check_pip()
        venv_ok = checker.check_venv()
        dev_ok = checker.check_python_dev()
        ssl_ok = checker.check_ssl_dev()
        # Force build_ok to True
        build_ok = True
        if checker.issues and not all([python_ok, pip_ok, venv_ok, dev_ok, ssl_ok]):
            print("\n⚠️  Some requirements are missing!")
            checker.print_installation_instructions()
            return False
        # Clear any issues related to build tools
        checker.issues = [issue for issue in checker.issues if not issue.startswith("Build Tools")]
    else:
        # Run all checks normally
        if not checker.run_checks():
            return False
        
    # Create virtual environment if it doesn't exist
    if not os.path.exists('venv'):
        print("\nCreating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        
        # Install requirements
        pip_cmd = os.path.join('venv', 'Scripts', 'pip.exe')
        print("\nInstalling dependencies...")
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
    
    # Create .env if it doesn't exist
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print("\nCreated default .env file. Please edit it with your configuration.")
        return False
        
    return True

def check_server_ready(port=5000, max_attempts=10):
    """Check if the Flask server is ready to accept connections"""
    print("Waiting for server to start...")
    for attempt in range(max_attempts):
        try:
            # First check if port is open
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    # Port is open, try to make a request
                    response = requests.get(f"http://localhost:{port}/", timeout=2)
                    if response.status_code == 200:
                        print(f"Server is ready on port {port}")
                        return True
            print(f"Waiting for server to start (attempt {attempt+1}/{max_attempts})...")
            time.sleep(2)
        except (requests.RequestException, socket.error):
            time.sleep(2)
    print("Server did not start properly in the expected time.")
    return False

def start_app():
    """Start the application"""
    if is_docker():
        # In Docker, we use the system Python
        python_cmd = sys.executable
    else:
        # In Windows, we use the virtual environment Python
        python_cmd = os.path.join('venv', 'Scripts', 'python.exe')
    
    print("\nStarting Proxmox NLI...")
    # Use main.py with --web flag instead of app.py directly
    port = os.environ.get('API_PORT', '5000')
    process = subprocess.Popen([python_cmd, 'main.py', '--web'])
    
    # Wait for server to start
    if check_server_ready(int(port)):
        # Open the browser
        webbrowser.open(f'http://localhost:{port}')
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        process.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Proxmox NLI application")
    parser.add_argument("--skip-build-check", action="store_true", 
                        help="Skip C++ build tools check (use if you know tools are installed but check fails)")
    args = parser.parse_args()
    
    if is_docker():
        if setup_docker():
            start_app()
    else:
        if setup_windows(skip_build_check=args.skip_build_check):
            start_app()