"""
Configuration file for pytest.
Adds the project root directory to Python's path so that tests can import
modules from the proxmox_nli package.
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)