#!/usr/bin/env python3
import os
import shutil
import json
import datetime
import sqlite3
from pathlib import Path
import argparse
import requests
from dotenv import load_dotenv

class BackupManager:
    def __init__(self, backup_dir="backups"):
        self.backup_dir = backup_dir
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def create_backup_dir(self):
        """Create backup directory with timestamp"""
        backup_path = os.path.join(self.backup_dir, self.timestamp)
        os.makedirs(backup_path, exist_ok=True)
        return backup_path
        
    def backup_env(self, backup_path):
        """Backup .env file"""
        if os.path.exists(".env"):
            shutil.copy2(".env", os.path.join(backup_path, ".env"))
            return True
        return False
        
    def backup_ssl(self, backup_path):
        """Backup SSL certificates"""
        cert_dir = "certs"
        if os.path.exists(cert_dir):
            shutil.copytree(cert_dir, os.path.join(backup_path, "certs"))
            return True
        return False
        
    def backup_databases(self, backup_path):
        """Backup SQLite databases"""
        dbs = {
            "user_preferences": "data/user_preferences.db",
            "audit": "logs/audit.db"
        }
        
        backed_up = []
        for name, path in dbs.items():
            if os.path.exists(path):
                # Create a copy of the database
                backup_db = os.path.join(backup_path, f"{name}.db")
                try:
                    # Connect to source database
                    source = sqlite3.connect(path)
                    # Create backup database
                    backup = sqlite3.connect(backup_db)
                    # Copy content
                    source.backup(backup)
                    backed_up.append(name)
                except Exception as e:
                    print(f"Error backing up {name} database: {e}")
                finally:
                    source.close()
                    backup.close()
        return backed_up
        
    def create_backup(self):
        """Create a complete backup of configuration and data"""
        try:
            # Create backup directory
            backup_path = self.create_backup_dir()
            print(f"Creating backup in: {backup_path}")
            
            # Backup .env file
            if self.backup_env(backup_path):
                print("✓ Backed up .env configuration")
            
            # Backup SSL certificates
            if self.backup_ssl(backup_path):
                print("✓ Backed up SSL certificates")
                
            # Backup databases
            backed_up_dbs = self.backup_databases(backup_path)
            if backed_up_dbs:
                print(f"✓ Backed up databases: {', '.join(backed_up_dbs)}")
                
            print(f"\nBackup completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
            
    def restore_backup(self, backup_dir):
        """Restore configuration from a backup"""
        try:
            if not os.path.exists(backup_dir):
                print(f"Backup directory not found: {backup_dir}")
                return False
                
            print(f"Restoring from backup: {backup_dir}")
            
            # Restore .env
            env_backup = os.path.join(backup_dir, ".env")
            if os.path.exists(env_backup):
                shutil.copy2(env_backup, ".env")
                print("✓ Restored .env configuration")
                
            # Restore SSL certificates
            certs_backup = os.path.join(backup_dir, "certs")
            if os.path.exists(certs_backup):
                if os.path.exists("certs"):
                    shutil.rmtree("certs")
                shutil.copytree(certs_backup, "certs")
                print("✓ Restored SSL certificates")
                
            # Restore databases
            os.makedirs("data", exist_ok=True)
            os.makedirs("logs", exist_ok=True)
            
            db_mappings = {
                "user_preferences.db": "data/user_preferences.db",
                "audit.db": "logs/audit.db"
            }
            
            for backup_name, restore_path in db_mappings.items():
                backup_db = os.path.join(backup_dir, backup_name)
                if os.path.exists(backup_db):
                    os.makedirs(os.path.dirname(restore_path), exist_ok=True)
                    shutil.copy2(backup_db, restore_path)
                    print(f"✓ Restored {backup_name}")
                    
            print(f"\nRestore completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False

def backup_vm(vm_id):
    """Backup a VM"""
    url = f"{PROXMOX_API_URL}/nodes/{PROXMOX_USER}/qemu/{vm_id}/status/start"
    response = requests.post(url, auth=(PROXMOX_USER, PROXMOX_PASSWORD))
    if response.status_code == 200:
        print(f"VM {vm_id} backed up successfully")
    else:
        print(f"Failed to backup VM {vm_id}: {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Backup and restore Proxmox NLI configuration")
    parser.add_argument("action", choices=["backup", "restore"], help="Action to perform")
    parser.add_argument("--backup-dir", help="Backup directory (for restore)")
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.action == "backup":
        manager.create_backup()
    else:  # restore
        if not args.backup_dir:
            print("Error: --backup-dir is required for restore")
            sys.exit(1)
        manager.restore_backup(args.backup_dir)

if __name__ == "__main__":
    main()