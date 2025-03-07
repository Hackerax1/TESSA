#!/usr/bin/env python3
"""
Proxmox NLI Installer
Launch script for the installer wizard.
"""
from installer import create_installer

def main():
    """Start the installer wizard"""
    installer = create_installer()
    installer.run()

if __name__ == "__main__":
    main()