"""
Hardware Compatibility Database module.

This module maintains a database of known hardware compatibility information,
with community contribution features.
"""

import json
import os
import logging
import hashlib
import platform
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class HardwareCompatibilityDB:
    """
    Database for hardware compatibility information with community contribution support.
    """
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the hardware compatibility database.
        
        Args:
            db_path: Optional path to the database file. If None, uses the default path.
        """
        if db_path is None:
            # Default to a directory inside the user's home directory
            self.db_path = os.path.join(
                os.path.expanduser("~"),
                ".proxmox-nli",
                "hardware_compatibility.json"
            )
        else:
            self.db_path = db_path
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database or load existing one
        self.db = self._load_database()
        
    def _load_database(self) -> Dict[str, Any]:
        """Load the hardware compatibility database from disk or initialize a new one."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading hardware compatibility database: {str(e)}")
                # Return an empty database if loading fails
                return self._create_empty_db()
        else:
            # Initialize new database
            return self._create_empty_db()
    
    def _create_empty_db(self) -> Dict[str, Any]:
        """Create an empty hardware compatibility database structure."""
        return {
            "version": 1,
            "last_updated": time.time(),
            "entries_count": 0,
            "hardware": {
                "cpu": {},
                "gpu": {},
                "motherboard": {},
                "network_interface": {},
                "storage_controller": {},
                "usb_device": {},
                "other": {}
            },
            "community_contributions": []
        }
    
    def save(self) -> bool:
        """Save the database to disk."""
        try:
            # Update metadata
            self.db["last_updated"] = time.time()
            self.db["entries_count"] = self._count_entries()
            
            with open(self.db_path, 'w') as f:
                json.dump(self.db, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving hardware compatibility database: {str(e)}")
            return False
    
    def _count_entries(self) -> int:
        """Count the total number of hardware entries in the database."""
        count = 0
        for category in self.db["hardware"]:
            count += len(self.db["hardware"][category])
        return count
    
    def get_hardware_compatibility(self, hardware_type: str, hardware_id: str) -> Optional[Dict[str, Any]]:
        """
        Get compatibility information for specific hardware.
        
        Args:
            hardware_type: Type of hardware (cpu, gpu, etc.)
            hardware_id: Identifier for the hardware
            
        Returns:
            Compatibility information or None if not found
        """
        if hardware_type in self.db["hardware"] and hardware_id in self.db["hardware"][hardware_type]:
            return self.db["hardware"][hardware_type][hardware_id]
        return None
    
    def add_hardware_entry(self, hardware_type: str, hardware_id: str, 
                           compatibility_info: Dict[str, Any], 
                           contributor: Optional[str] = None) -> bool:
        """
        Add or update a hardware compatibility entry.
        
        Args:
            hardware_type: Type of hardware (cpu, gpu, etc.)
            hardware_id: Identifier for the hardware
            compatibility_info: Compatibility information
            contributor: Name of contributor (optional)
            
        Returns:
            Boolean indicating success
        """
        if hardware_type not in self.db["hardware"]:
            logger.warning(f"Invalid hardware type: {hardware_type}")
            return False
            
        # Add entry to database
        self.db["hardware"][hardware_type][hardware_id] = compatibility_info
        
        # Add to community contributions if a contributor is provided
        if contributor:
            contribution = {
                "timestamp": time.time(),
                "contributor": contributor,
                "hardware_type": hardware_type,
                "hardware_id": hardware_id,
                "status": "pending_review"
            }
            self.db["community_contributions"].append(contribution)
            
        return self.save()
    
    def submit_community_contribution(self, hardware_info: Dict[str, Any], 
                                     compatibility_notes: str,
                                     contributor_name: Optional[str] = None,
                                     contact_info: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a community contribution for hardware compatibility.
        
        Args:
            hardware_info: Information about the hardware
            compatibility_notes: Notes about compatibility with Proxmox
            contributor_name: Name of contributor (optional)
            contact_info: Contact information (optional)
            
        Returns:
            Dictionary with submission result
        """
        try:
            # Generate a unique ID for the hardware based on its details
            hw_type = hardware_info.get("type", "other")
            hw_id = self._generate_hardware_id(hardware_info)
            
            # Create contribution record
            contribution = {
                "timestamp": time.time(),
                "hardware_type": hw_type,
                "hardware_id": hw_id,
                "hardware_info": hardware_info,
                "compatibility_notes": compatibility_notes,
                "status": "pending_review"
            }
            
            if contributor_name:
                contribution["contributor_name"] = contributor_name
            
            if contact_info:
                # Store hash of contact info for privacy
                contribution["contact_hash"] = hashlib.sha256(contact_info.encode()).hexdigest()
            
            # Add to community contributions list
            self.db["community_contributions"].append(contribution)
            
            # Save database
            self.save()
            
            return {
                "success": True,
                "message": "Thank you for your contribution!",
                "contribution_id": f"{hw_type}:{hw_id}"
            }
            
        except Exception as e:
            logger.error(f"Error processing community contribution: {str(e)}")
            return {
                "success": False,
                "message": f"Error submitting contribution: {str(e)}",
                "error": str(e)
            }
    
    def _generate_hardware_id(self, hardware_info: Dict[str, Any]) -> str:
        """Generate a unique identifier for hardware based on its information."""
        # Create a string representation to hash
        hw_str = ""
        
        # Use model/name/vendor information if available
        for key in ["model", "name", "vendor", "manufacturer", "device_id"]:
            if key in hardware_info and hardware_info[key]:
                hw_str += str(hardware_info[key])
        
        # If we couldn't generate anything from standard fields, use the full dict
        if not hw_str:
            hw_str = str(sorted(hardware_info.items()))
            
        # Generate hash
        return hashlib.md5(hw_str.encode()).hexdigest()[:12]
    
    def search_compatible_hardware(self, hardware_type: str, query: str = "") -> List[Dict[str, Any]]:
        """
        Search for compatible hardware in the database.
        
        Args:
            hardware_type: Type of hardware to search for
            query: Optional search query
            
        Returns:
            List of matching hardware entries
        """
        results = []
        
        if hardware_type not in self.db["hardware"]:
            return results
            
        for hw_id, hw_info in self.db["hardware"][hardware_type].items():
            # Skip hardware marked as incompatible
            if not hw_info.get("is_compatible", False):
                continue
                
            # If there's a search query, filter by it
            if query:
                matched = False
                # Search in common fields
                for field in ["name", "model", "vendor", "manufacturer", "description"]:
                    if field in hw_info and query.lower() in str(hw_info[field]).lower():
                        matched = True
                        break
                        
                if not matched:
                    continue
            
            # Add to results
            results.append({
                "id": hw_id,
                "type": hardware_type,
                **hw_info
            })
            
        return results