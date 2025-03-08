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

def setup_windows():
    """Setup for Windows environment"""
    print("Checking system requirements...")
    checker = RequirementsChecker()
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

def start_app():
    """Start the application"""
    if is_docker():
        # In Docker, we use the system Python
        python_cmd = sys.executable
    else:
        # In Windows, we use the virtual environment Python
        python_cmd = os.path.join('venv', 'Scripts', 'python.exe')
    
    print("\nStarting Proxmox NLI...")
    process = subprocess.Popen([python_cmd, 'app.py'])
    
    # Wait a bit for the server to start
    time.sleep(2)
    
    # Open the browser
    webbrowser.open('http://localhost:5000')
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        process.terminate()

if __name__ == "__main__":
    if is_docker():
        if setup_docker():
            start_app()
    else:
        if setup_windows():
            start_app()