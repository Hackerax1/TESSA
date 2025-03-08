#!/usr/bin/env python3
"""
Pre-Installation Compatibility Checker for Proxmox NLI

This standalone tool checks system hardware compatibility before installation
and provides recommendations based on the hardware compatibility database.
"""

import sys
import os
import json
import argparse
import logging
import platform
import time
from typing import Dict, List, Any, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("preinstall-checker")

# Add the project directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from installer.hardware_detector import HardwareDetector
from installer.hardware.types import HardwareCompatibility
from installer.hardware.hardware_compatibility_db import HardwareCompatibilityDB

class PreinstallChecker:
    """Pre-installation compatibility checker for Proxmox NLI."""
    
    def __init__(self, args):
        """Initialize the pre-installation checker with command line arguments."""
        self.args = args
        self.hardware_detector = HardwareDetector()
        self.compatibility_db = HardwareCompatibilityDB()
        self.detailed_output = args.verbose
        self.compatibility_results = []
        self.hardware_summary = {}
        
    def run(self) -> int:
        """Run the compatibility checker and return exit code (0 = success)."""
        try:
            print("\n===== Proxmox NLI Pre-Installation Compatibility Checker =====\n")
            
            # Detect hardware
            print("Detecting hardware...", end="", flush=True)
            self.hardware_summary = self.hardware_detector.get_hardware_summary()
            print(" Done")
            
            # Check compatibility
            print("Checking compatibility...", end="", flush=True)
            self.compatibility_results = self.hardware_detector.check_hardware_compatibility()
            print(" Done")
            
            # Display results
            self._display_results()
            
            # Check against community hardware database
            self._check_against_database()
            
            # Handle community contribution if requested
            if self.args.contribute:
                self._contribute_hardware_data()
            
            # Save detailed report if requested
            if self.args.output:
                self._save_report(self.args.output)
            
            # Return appropriate exit code
            issues = [r for r in self.compatibility_results if not r.is_compatible]
            critical_issues = [r for r in issues if r.severity == "critical" and not r.fallback_available]
            
            if critical_issues:
                return 2  # Critical issues, installation not recommended
            elif issues:
                return 1  # Issues, but installation possible with workarounds
            else:
                return 0  # No issues
                
        except KeyboardInterrupt:
            print("\nCancelled by user")
            return 130
        except Exception as e:
            logger.error(f"Error during compatibility check: {str(e)}", exc_info=True)
            print(f"\nError: {str(e)}")
            return 1
    
    def _display_results(self):
        """Display the compatibility check results."""
        print("\n===== Hardware Compatibility Results =====\n")
        
        # Count issues
        issues = [r for r in self.compatibility_results if not r.is_compatible]
        critical_issues = [r for r in issues if r.severity == "critical"]
        warning_issues = [r for r in issues if r.severity == "warning"]
        
        # Display summary
        if not issues:
            print("✅ All hardware checks passed! Your system is compatible with Proxmox NLI.\n")
        else:
            if critical_issues:
                print(f"❌ Found {len(critical_issues)} critical compatibility issues.")
            if warning_issues:
                print(f"⚠️  Found {len(warning_issues)} minor compatibility issues.\n")
                
        # Display system information
        self._print_system_info()
        
        # Display detailed results
        if self.detailed_output or issues:
            self._print_detailed_results()
            
        # Print overall recommendation
        self._print_recommendation(critical_issues, warning_issues)
    
    def _print_system_info(self):
        """Print basic system information."""
        cpu_info = self.hardware_summary.get("cpu_info", {})
        memory_info = self.hardware_summary.get("memory_info", {})
        
        print(f"System:    {self.hardware_summary.get('system_info', {}).get('system', 'Unknown')}")
        print(f"CPU:       {cpu_info.get('model', 'Unknown')}")
        print(f"Cores:     {cpu_info.get('physical_cores', 'Unknown')} physical, {cpu_info.get('total_cores', 'Unknown')} logical")
        print(f"Memory:    {memory_info.get('total', 0) / (1024**3):.1f} GB")
        print(f"Disks:     {len(self.hardware_summary.get('disk_info', []))} detected")
        print(f"Network:   {len(self.hardware_summary.get('network_info', {}).get('interfaces', []))} interfaces\n")
    
    def _print_detailed_results(self):
        """Print detailed compatibility results."""
        print("\n----- Detailed Compatibility Results -----\n")
        
        for result in self.compatibility_results:
            status = "✅" if result.is_compatible else "❌" if result.severity == "critical" else "⚠️"
            print(f"{status} {result.component}: {result.message}")
            
            if not result.is_compatible and result.fallback_available:
                print(f"   → Fallback: {result.fallback_description}")
                
        print("")  # Empty line for spacing
    
    def _print_recommendation(self, critical_issues, warning_issues):
        """Print an overall recommendation based on compatibility results."""
        print("\n----- Recommendation -----\n")
        
        critical_without_fallback = [i for i in critical_issues if not i.fallback_available]
        
        if critical_without_fallback:
            print("❌ NOT RECOMMENDED: Your system has critical compatibility issues without fallback options.")
            print("   Installation may fail or the system may not function correctly.")
        elif critical_issues:
            print("⚠️  PROCEED WITH CAUTION: Your system has critical issues but fallback options are available.")
            print("   Installation is possible but some features may have limited functionality.")
        elif warning_issues:
            print("✅ RECOMMENDED WITH MINOR ADJUSTMENTS: Your system is generally compatible but has some")
            print("   minor issues that may affect performance or functionality.")
        else:
            print("✅ HIGHLY RECOMMENDED: Your system is fully compatible with Proxmox NLI.")
            
        print("")  # Empty line for spacing
    
    def _check_against_database(self):
        """Check hardware against the community compatibility database."""
        print("\n----- Community Hardware Database Check -----\n")
        
        cpu_info = self.hardware_summary.get("cpu_info", {})
        gpu_info = self.hardware_summary.get("gpu_info", [])
        
        # Check CPU compatibility in database
        if "model" in cpu_info:
            cpu_hw_id = self.compatibility_db._generate_hardware_id({"model": cpu_info["model"]})
            cpu_compat = self.compatibility_db.get_hardware_compatibility("cpu", cpu_hw_id)
            
            if cpu_compat:
                status = "Compatible" if cpu_compat.get("is_compatible", False) else "Issues reported"
                print(f"CPU: {cpu_info['model']} - {status}")
                if "notes" in cpu_compat:
                    print(f"   → {cpu_compat['notes']}")
            else:
                print(f"CPU: {cpu_info['model']} - No community data available")
        
        # Check GPU compatibility in database
        for gpu in gpu_info:
            if "name" in gpu:
                gpu_hw_id = self.compatibility_db._generate_hardware_id({"name": gpu["name"]})
                gpu_compat = self.compatibility_db.get_hardware_compatibility("gpu", gpu_hw_id)
                
                if gpu_compat:
                    status = "Compatible" if gpu_compat.get("is_compatible", False) else "Issues reported"
                    print(f"GPU: {gpu['name']} - {status}")
                    if "notes" in gpu_compat:
                        print(f"   → {gpu_compat['notes']}")
                else:
                    print(f"GPU: {gpu['name']} - No community data available")
        
        print("\nNote: This data is community-contributed and may not be comprehensive.")
        print("Consider contributing your hardware compatibility results to help others.")
        
        print("")  # Empty line for spacing
    
    def _contribute_hardware_data(self):
        """Contribute hardware compatibility data to the community database."""
        print("\n----- Contribute Hardware Compatibility Data -----\n")
        print("Your hardware information and compatibility results can help other users.")
        print("This data will be anonymized and shared with the community database.\n")
        
        try:
            contributor_name = input("Your name (optional, leave blank to remain anonymous): ").strip()
            contact = input("Contact email (optional, only used if we need to follow up): ").strip()
            notes = input("Additional notes about your experience: ").strip()
            
            # CPU contribution
            cpu_info = self.hardware_summary.get("cpu_info", {})
            if "model" in cpu_info:
                # Find CPU compatibility result
                cpu_result = next((r for r in self.compatibility_results 
                                 if r.component in ["CPU Virtualization", "CPU Cores"]), None)
                
                cpu_notes = f"User notes: {notes}" if notes else ""
                if cpu_result:
                    cpu_notes += f" Compatibility: {cpu_result.message}"
                
                cpu_data = {
                    "type": "cpu",
                    "model": cpu_info["model"],
                    "cores": cpu_info.get("physical_cores", 0),
                    "threads": cpu_info.get("total_cores", 0),
                    "virtualization_support": cpu_info.get("virtualization_support", {})
                }
                
                self.compatibility_db.submit_community_contribution(
                    hardware_info=cpu_data,
                    compatibility_notes=cpu_notes,
                    contributor_name=contributor_name if contributor_name else None,
                    contact_info=contact if contact else None
                )
            
            # GPU contribution (if any)
            for gpu in self.hardware_summary.get("gpu_info", []):
                if "name" in gpu:
                    gpu_data = {
                        "type": "gpu",
                        **gpu
                    }
                    
                    gpu_notes = f"User notes: {notes}" if notes else ""
                    
                    self.compatibility_db.submit_community_contribution(
                        hardware_info=gpu_data,
                        compatibility_notes=gpu_notes,
                        contributor_name=contributor_name if contributor_name else None,
                        contact_info=contact if contact else None
                    )
            
            print("\nThank you for your contribution! Your hardware compatibility data")
            print("has been submitted to help improve the community database.")
            
        except KeyboardInterrupt:
            print("\nContribution cancelled.")
        except Exception as e:
            logger.error(f"Error submitting contribution: {str(e)}", exc_info=True)
            print(f"\nError submitting contribution: {str(e)}")
    
    def _save_report(self, output_path: str):
        """Save a detailed compatibility report to a file."""
        try:
            # Create report data structure
            report = {
                "timestamp": time.time(),
                "system_info": self.hardware_summary.get("system_info", {}),
                "hardware_summary": {
                    "cpu": self.hardware_summary.get("cpu_info", {}),
                    "memory": self.hardware_summary.get("memory_info", {}),
                    "disk": self.hardware_summary.get("disk_info", []),
                    "network": self.hardware_summary.get("network_info", {}),
                    "gpu": self.hardware_summary.get("gpu_info", []),
                    "virtualization": self.hardware_summary.get("virtualization_info", {})
                },
                "compatibility_results": [
                    {
                        "component": r.component,
                        "is_compatible": r.is_compatible,
                        "message": r.message,
                        "severity": r.severity,
                        "fallback_available": r.fallback_available,
                        "fallback_option": r.fallback_option,
                        "fallback_description": r.fallback_description
                    } for r in self.compatibility_results
                ]
            }
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            print(f"\nDetailed compatibility report saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}", exc_info=True)
            print(f"\nError saving report: {str(e)}")


def main():
    """Main entry point for the pre-installation compatibility checker."""
    parser = argparse.ArgumentParser(
        description="Pre-Installation Compatibility Checker for Proxmox NLI"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        help="Save detailed compatibility report to the specified file"
    )
    parser.add_argument(
        "-c", "--contribute", 
        action="store_true", 
        help="Contribute your hardware compatibility data to the community database"
    )
    
    args = parser.parse_args()
    checker = PreinstallChecker(args)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())