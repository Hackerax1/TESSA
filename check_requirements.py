#!/usr/bin/env python3
import sys
import shutil
import subprocess
import platform
import os

class RequirementsChecker:
    def __init__(self):
        self.issues = []
        self.os_type = platform.system().lower()

    def print_status(self, component, status, details=""):
        mark = "✓" if status else "✗"
        print(f"{mark} {component:<20} {details}")
        if not status:
            self.issues.append(f"{component}: {details}")

    def check_python_version(self):
        version = sys.version_info
        status = version >= (3, 8)
        self.print_status(
            "Python Version",
            status,
            f"{version.major}.{version.minor}.{version.micro} {'(OK)' if status else '(Python 3.8+ required)'}"
        )
        return status

    def check_pip(self):
        try:
            import pip
            self.print_status("pip", True, "Installed")
            return True
        except ImportError:
            self.print_status("pip", False, "Not found")
            return False

    def check_venv(self):
        try:
            import venv
            self.print_status("venv", True, "Available")
            return True
        except ImportError:
            self.print_status("venv", False, "Not available")
            return False

    def check_python_dev(self):
        if self.os_type == 'windows':
            return True
        
        result = shutil.which('python3-config')
        status = result is not None
        self.print_status(
            "Python Dev Headers",
            status,
            "Found" if status else "Not found (install python3-dev)"
        )
        return status

    def check_build_tools(self):
        if self.os_type == 'windows':
            # Check for Visual C++ Build Tools on Windows
            # Instead of directly calling cl.exe, check for the existence of necessary files
            # or if any required packages can be built correctly
            try:
                # Check if Visual C++ compiler is available by building a simple extension
                from setuptools import _distutils
                from setuptools._distutils import ccompiler
                compiler = ccompiler.new_compiler()
                compiler.initialize()
                self.print_status("Build Tools", True, "Visual C++ Build Tools found")
                return True
            except (ImportError, AttributeError, Exception) as e:
                # Next, try checking for common Visual C++ Build Tools paths
                vs_paths = [
                    os.path.expandvars("%ProgramFiles(x86)%\\Microsoft Visual Studio"),
                    os.path.expandvars("%ProgramFiles%\\Microsoft Visual Studio"),
                    os.path.expandvars("%ProgramFiles(x86)%\\Microsoft Visual C++ Build Tools"),
                    os.path.expandvars("%ProgramFiles%\\Microsoft Visual C++ Build Tools"),
                    # VS 2022 path
                    os.path.expandvars("%ProgramFiles%\\Microsoft Visual Studio\\2022"),
                    # VS 2019 path
                    os.path.expandvars("%ProgramFiles%\\Microsoft Visual Studio\\2019"),
                ]
                
                for path in vs_paths:
                    if os.path.exists(path):
                        self.print_status("Build Tools", True, f"Visual C++ Build Tools found at {path}")
                        return True
                
                self.print_status("Build Tools", False, "Visual C++ Build Tools not found")
                return False
        else:
            # Check for gcc/make on Unix-like systems
            gcc = shutil.which('gcc') is not None
            make = shutil.which('make') is not None
            status = gcc and make
            self.print_status(
                "Build Tools",
                status,
                "Found" if status else "Not found (install build-essential)"
            )
            return status

    def check_ssl_dev(self):
        if self.os_type == 'windows':
            return True
        
        result = shutil.which('openssl')
        status = result is not None
        self.print_status(
            "SSL Dev Headers",
            status,
            "Found" if status else "Not found (install libssl-dev)"
        )
        return status

    def print_installation_instructions(self):
        if not self.issues:
            print("\nAll requirements are met! ✓")
            return

        print("\nSome requirements are missing. Here's how to install them:\n")
        
        if self.os_type == 'windows':
            print("Windows instructions:")
            print("1. Python: Download and install from https://www.python.org/downloads/")
            print("2. Visual C++ Build Tools: Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        
        elif self.os_type == 'linux':
            print("Linux instructions (Ubuntu/Debian):")
            print("sudo apt update")
            print("sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential libssl-dev")
            print("\nFor other Linux distributions, use your package manager to install equivalent packages.")
        
        elif self.os_type == 'darwin':
            print("macOS instructions:")
            print("1. Install Homebrew if not already installed:")
            print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            print("2. Install requirements:")
            print("   brew install python openssl")

    def run_checks(self):
        print("Checking system requirements...\n")
        
        python_ok = self.check_python_version()
        pip_ok = self.check_pip()
        venv_ok = self.check_venv()
        dev_ok = self.check_python_dev()
        build_ok = self.check_build_tools()
        ssl_ok = self.check_ssl_dev()
        
        if self.issues:
            print("\n⚠️  Some requirements are missing!")
            self.print_installation_instructions()
            return False
        return True

if __name__ == "__main__":
    checker = RequirementsChecker()
    if checker.run_checks():
        sys.exit(0)
    sys.exit(1)