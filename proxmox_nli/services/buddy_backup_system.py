"""
Buddy Backup System for Proxmox NLI.
Allows users to securely back up their data to trusted peers.
"""
import logging
import json
import os
import time
import uuid
import shutil
import socket
import threading
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import ipaddress
import yaml

logger = logging.getLogger(__name__)

class BuddyBackupSystem:
    """System for managing peer-to-peer backups between trusted users."""
    
    def __init__(self, backup_handler=None):
        """Initialize the buddy backup system.
        
        Args:
            backup_handler: Optional ServiceBackupHandler instance
        """
        self.backup_handler = backup_handler
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'buddy_backups')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Directory for storing buddy information
        self.buddies_dir = os.path.join(self.data_dir, 'buddies')
        os.makedirs(self.buddies_dir, exist_ok=True)
        
        # Directory for storing backup shares
        self.shares_dir = os.path.join(self.data_dir, 'shares')
        os.makedirs(self.shares_dir, exist_ok=True)
        
        # Directory for storing received backups
        self.received_dir = os.path.join(self.data_dir, 'received')
        os.makedirs(self.received_dir, exist_ok=True)
        
        # Load buddy information
        self.buddies = {}
        self.load_buddies()
        
        # Load backup shares
        self.shares = {}
        self.load_shares()
        
        # Default port for buddy backup service
        self.default_port = 8765
        
        # Background thread for backup service
        self.service_thread = None
        self.service_running = False
        
    def load_buddies(self):
        """Load buddy information from disk."""
        try:
            buddies_file = os.path.join(self.data_dir, 'buddies.json')
            if os.path.exists(buddies_file):
                with open(buddies_file, 'r') as f:
                    self.buddies = json.load(f)
                logger.info(f"Loaded {len(self.buddies)} buddies")
        except Exception as e:
            logger.error(f"Error loading buddies: {str(e)}")
            self.buddies = {}
            
    def save_buddies(self):
        """Save buddy information to disk."""
        try:
            buddies_file = os.path.join(self.data_dir, 'buddies.json')
            with open(buddies_file, 'w') as f:
                json.dump(self.buddies, f)
            logger.debug("Buddies saved to disk")
        except Exception as e:
            logger.error(f"Error saving buddies: {str(e)}")
            
    def load_shares(self):
        """Load backup shares from disk."""
        try:
            shares_file = os.path.join(self.data_dir, 'shares.json')
            if os.path.exists(shares_file):
                with open(shares_file, 'r') as f:
                    self.shares = json.load(f)
                logger.info(f"Loaded {len(self.shares)} backup shares")
        except Exception as e:
            logger.error(f"Error loading backup shares: {str(e)}")
            self.shares = {}
            
    def save_shares(self):
        """Save backup shares to disk."""
        try:
            shares_file = os.path.join(self.data_dir, 'shares.json')
            with open(shares_file, 'w') as f:
                json.dump(self.shares, f)
            logger.debug("Backup shares saved to disk")
        except Exception as e:
            logger.error(f"Error saving backup shares: {str(e)}")
    
    def add_buddy(self, name: str, hostname: str, port: int = None, 
                encryption_key: str = None) -> Dict:
        """Add a new backup buddy.
        
        Args:
            name: Name of the buddy
            hostname: Hostname or IP address of the buddy
            port: Port number for buddy backup service
            encryption_key: Optional encryption key for secure backups
            
        Returns:
            Dictionary with buddy addition result
        """
        # Validate hostname
        try:
            # Check if it's a valid IP address
            ipaddress.ip_address(hostname)
        except ValueError:
            # Not an IP address, check if it's a valid hostname
            try:
                socket.gethostbyname(hostname)
            except socket.gaierror:
                return {
                    'success': False,
                    'message': f'Invalid hostname or IP address: {hostname}'
                }
        
        # Generate a unique buddy ID
        buddy_id = str(uuid.uuid4())
        
        # Generate an encryption key if not provided
        if not encryption_key:
            encryption_key = self._generate_encryption_key()
            
        # Create buddy record
        buddy = {
            'id': buddy_id,
            'name': name,
            'hostname': hostname,
            'port': port or self.default_port,
            'encryption_key': encryption_key,
            'created_at': datetime.now().isoformat(),
            'last_backup': None,
            'status': 'active',
            'backups': []
        }
        
        # Add to buddies dictionary
        self.buddies[buddy_id] = buddy
        self.save_buddies()
        
        return {
            'success': True,
            'message': f'Buddy {name} added successfully',
            'buddy': buddy
        }
    
    def remove_buddy(self, buddy_id: str) -> Dict:
        """Remove a backup buddy.
        
        Args:
            buddy_id: ID of the buddy to remove
            
        Returns:
            Dictionary with buddy removal result
        """
        if buddy_id not in self.buddies:
            return {
                'success': False,
                'message': f'Buddy with ID {buddy_id} not found'
            }
            
        buddy = self.buddies.pop(buddy_id)
        self.save_buddies()
        
        # Remove any shares associated with this buddy
        for share_id in list(self.shares.keys()):
            if self.shares[share_id]['buddy_id'] == buddy_id:
                self.shares.pop(share_id)
                
        self.save_shares()
        
        return {
            'success': True,
            'message': f'Buddy {buddy["name"]} removed successfully',
            'buddy': buddy
        }
    
    def list_buddies(self) -> Dict:
        """List all backup buddies.
        
        Returns:
            Dictionary with list of buddies
        """
        return {
            'success': True,
            'message': f'Found {len(self.buddies)} buddies',
            'buddies': self.buddies
        }
    
    def create_backup_share(self, buddy_id: str, service_ids: List[str] = None,
                          include_data: bool = True, encryption: bool = True) -> Dict:
        """Create a backup share for a buddy.
        
        Args:
            buddy_id: ID of the buddy to share with
            service_ids: List of service IDs to include in the backup
            include_data: Whether to include service data in the backup
            encryption: Whether to encrypt the backup
            
        Returns:
            Dictionary with backup share creation result
        """
        if buddy_id not in self.buddies:
            return {
                'success': False,
                'message': f'Buddy with ID {buddy_id} not found'
            }
            
        if not self.backup_handler:
            return {
                'success': False,
                'message': 'Backup handler not available'
            }
            
        buddy = self.buddies[buddy_id]
        
        # Generate a unique share ID
        share_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create a directory for this share
        share_dir = os.path.join(self.shares_dir, share_id)
        os.makedirs(share_dir, exist_ok=True)
        
        # Create backup for each service
        backup_results = []
        
        if service_ids:
            for service_id in service_ids:
                # Get service definition
                service_def = self._get_service_definition(service_id)
                if not service_def:
                    backup_results.append({
                        'service_id': service_id,
                        'success': False,
                        'message': f'Service {service_id} not found'
                    })
                    continue
                    
                # Create backup
                vm_id = service_def.get('vm_id', 'unknown')
                backup_result = self.backup_handler.backup_service(service_def, vm_id, include_data)
                
                if backup_result.get('success', False):
                    # Copy backup to share directory
                    backup_id = backup_result.get('backup_id')
                    config_path = backup_result.get('config_path')
                    data_path = backup_result.get('data_path')
                    
                    service_backup_dir = os.path.join(share_dir, service_id)
                    os.makedirs(service_backup_dir, exist_ok=True)
                    
                    # Copy configuration
                    if config_path and os.path.exists(config_path):
                        shutil.copytree(config_path, os.path.join(service_backup_dir, 'config'))
                        
                    # Copy data if included
                    if include_data and data_path and os.path.exists(data_path):
                        shutil.copytree(data_path, os.path.join(service_backup_dir, 'data'))
                        
                    backup_results.append({
                        'service_id': service_id,
                        'success': True,
                        'backup_id': backup_id
                    })
                else:
                    backup_results.append({
                        'service_id': service_id,
                        'success': False,
                        'message': backup_result.get('message', 'Unknown error')
                    })
        
        # Create share metadata
        share = {
            'id': share_id,
            'buddy_id': buddy_id,
            'buddy_name': buddy['name'],
            'created_at': timestamp,
            'service_ids': service_ids,
            'include_data': include_data,
            'encryption': encryption,
            'status': 'pending',
            'results': backup_results
        }
        
        # Add to shares dictionary
        self.shares[share_id] = share
        self.save_shares()
        
        # Create share manifest
        manifest = {
            'share_id': share_id,
            'created_at': timestamp,
            'services': service_ids,
            'include_data': include_data,
            'encryption': encryption
        }
        
        with open(os.path.join(share_dir, 'manifest.json'), 'w') as f:
            json.dump(manifest, f)
            
        # Encrypt the share if requested
        if encryption:
            self._encrypt_share(share_id, buddy['encryption_key'])
            
        # Update buddy record
        buddy['last_backup'] = timestamp
        buddy['backups'].append({
            'share_id': share_id,
            'timestamp': timestamp,
            'services': service_ids,
            'status': 'pending'
        })
        
        # Keep only the last 10 backups in the list
        if len(buddy['backups']) > 10:
            buddy['backups'] = buddy['backups'][-10:]
            
        self.save_buddies()
        
        return {
            'success': True,
            'message': f'Backup share created for buddy {buddy["name"]}',
            'share_id': share_id,
            'share': share
        }
    
    def send_backup_to_buddy(self, share_id: str) -> Dict:
        """Send a backup share to a buddy.
        
        Args:
            share_id: ID of the share to send
            
        Returns:
            Dictionary with backup sending result
        """
        if share_id not in self.shares:
            return {
                'success': False,
                'message': f'Backup share {share_id} not found'
            }
            
        share = self.shares[share_id]
        buddy_id = share['buddy_id']
        
        if buddy_id not in self.buddies:
            return {
                'success': False,
                'message': f'Buddy {buddy_id} not found'
            }
            
        buddy = self.buddies[buddy_id]
        
        # Check if the share directory exists
        share_dir = os.path.join(self.shares_dir, share_id)
        if not os.path.exists(share_dir):
            return {
                'success': False,
                'message': f'Backup share directory not found: {share_dir}'
            }
            
        try:
            # Create a zip archive of the share
            zip_path = os.path.join(self.data_dir, f"{share_id}.zip")
            self._create_zip_archive(share_dir, zip_path)
            
            # Send the backup to the buddy
            url = f"http://{buddy['hostname']}:{buddy['port']}/api/buddy-backup/receive"
            
            with open(zip_path, 'rb') as f:
                files = {'backup': f}
                data = {'share_id': share_id}
                
                response = requests.post(url, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Update share status
                    share['status'] = 'sent'
                    share['sent_at'] = datetime.now().isoformat()
                    self.save_shares()
                    
                    # Update buddy record
                    for backup in buddy['backups']:
                        if backup['share_id'] == share_id:
                            backup['status'] = 'sent'
                            break
                            
                    self.save_buddies()
                    
                    # Clean up the zip file
                    os.remove(zip_path)
                    
                    return {
                        'success': True,
                        'message': f'Backup sent to buddy {buddy["name"]}',
                        'result': result
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Failed to send backup: HTTP {response.status_code}',
                        'response': response.text
                    }
        except Exception as e:
            logger.error(f"Error sending backup to buddy: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending backup: {str(e)}'
            }
            
    def receive_backup(self, share_id: str, backup_file_path: str) -> Dict:
        """Receive a backup from a buddy.
        
        Args:
            share_id: ID of the share being received
            backup_file_path: Path to the backup zip file
            
        Returns:
            Dictionary with backup receiving result
        """
        try:
            # Create a directory for this received backup
            received_dir = os.path.join(self.received_dir, share_id)
            os.makedirs(received_dir, exist_ok=True)
            
            # Extract the backup
            self._extract_zip_archive(backup_file_path, received_dir)
            
            # Load the manifest
            manifest_path = os.path.join(received_dir, 'manifest.json')
            if not os.path.exists(manifest_path):
                return {
                    'success': False,
                    'message': 'Invalid backup: manifest not found'
                }
                
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            # Check if the backup is encrypted
            if manifest.get('encryption', False):
                # Find the buddy who sent this backup
                buddy_id = None
                for bid, buddy in self.buddies.items():
                    for backup in buddy.get('backups', []):
                        if backup.get('share_id') == share_id:
                            buddy_id = bid
                            break
                    if buddy_id:
                        break
                        
                if buddy_id:
                    # Decrypt the backup
                    self._decrypt_share(received_dir, self.buddies[buddy_id]['encryption_key'])
                else:
                    return {
                        'success': False,
                        'message': 'Cannot decrypt backup: buddy not found'
                    }
            
            # Record the received backup
            received = {
                'share_id': share_id,
                'received_at': datetime.now().isoformat(),
                'manifest': manifest,
                'path': received_dir
            }
            
            # Save to received backups list
            received_file = os.path.join(self.data_dir, 'received_backups.json')
            received_backups = []
            
            if os.path.exists(received_file):
                with open(received_file, 'r') as f:
                    received_backups = json.load(f)
                    
            received_backups.append(received)
            
            with open(received_file, 'w') as f:
                json.dump(received_backups, f)
                
            return {
                'success': True,
                'message': f'Backup {share_id} received successfully',
                'manifest': manifest
            }
        except Exception as e:
            logger.error(f"Error receiving backup: {str(e)}")
            return {
                'success': False,
                'message': f'Error receiving backup: {str(e)}'
            }
            
    def list_received_backups(self) -> Dict:
        """List all received backups.
        
        Returns:
            Dictionary with list of received backups
        """
        received_file = os.path.join(self.data_dir, 'received_backups.json')
        received_backups = []
        
        if os.path.exists(received_file):
            try:
                with open(received_file, 'r') as f:
                    received_backups = json.load(f)
            except Exception as e:
                logger.error(f"Error loading received backups: {str(e)}")
                
        return {
            'success': True,
            'message': f'Found {len(received_backups)} received backups',
            'backups': received_backups
        }
    
    def restore_from_buddy_backup(self, share_id: str, service_id: str = None, 
                                target_vm_id: str = None) -> Dict:
        """Restore a service from a buddy backup.
        
        Args:
            share_id: ID of the backup share to restore from
            service_id: Optional specific service ID to restore
            target_vm_id: Optional target VM ID to restore to
            
        Returns:
            Dictionary with restoration result
        """
        if not self.backup_handler:
            return {
                'success': False,
                'message': 'Backup handler not available'
            }
            
        # Find the received backup
        received_dir = os.path.join(self.received_dir, share_id)
        if not os.path.exists(received_dir):
            return {
                'success': False,
                'message': f'Backup share {share_id} not found'
            }
            
        # Load the manifest
        manifest_path = os.path.join(received_dir, 'manifest.json')
        if not os.path.exists(manifest_path):
            return {
                'success': False,
                'message': 'Invalid backup: manifest not found'
            }
            
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        # If no specific service ID is provided, restore all services
        if not service_id:
            results = []
            for sid in manifest.get('services', []):
                result = self._restore_service_from_buddy_backup(
                    share_id, sid, received_dir, target_vm_id)
                results.append(result)
                
            success_count = sum(1 for r in results if r.get('success', False))
            
            return {
                'success': success_count > 0,
                'message': f'Restored {success_count}/{len(results)} services',
                'results': results
            }
        else:
            # Restore a specific service
            return self._restore_service_from_buddy_backup(
                share_id, service_id, received_dir, target_vm_id)
    
    def _restore_service_from_buddy_backup(self, share_id: str, service_id: str, 
                                         received_dir: str, target_vm_id: str = None) -> Dict:
        """Restore a specific service from a buddy backup.
        
        Args:
            share_id: ID of the backup share
            service_id: ID of the service to restore
            received_dir: Path to the received backup directory
            target_vm_id: Optional target VM ID to restore to
            
        Returns:
            Dictionary with restoration result
        """
        service_dir = os.path.join(received_dir, service_id)
        if not os.path.exists(service_dir):
            return {
                'success': False,
                'message': f'Service {service_id} not found in backup'
            }
            
        config_dir = os.path.join(service_dir, 'config')
        data_dir = os.path.join(service_dir, 'data')
        
        if not os.path.exists(config_dir):
            return {
                'success': False,
                'message': f'Service configuration not found in backup'
            }
            
        # Load service definition
        service_file = os.path.join(config_dir, 'service.yml')
        if not os.path.exists(service_file):
            return {
                'success': False,
                'message': f'Service definition file not found in backup'
            }
            
        with open(service_file, 'r') as f:
            service_def = yaml.safe_load(f)
            
        # Load deployment configuration
        deployment_file = os.path.join(config_dir, 'deployment.json')
        if os.path.exists(deployment_file):
            with open(deployment_file, 'r') as f:
                deployment = json.load(f)
                service_def['deployment'] = deployment
                
        # Create a temporary backup directory structure for restoration
        temp_backup_id = f"buddy_{share_id}_{service_id}"
        temp_config_dir = os.path.join(self.backup_handler.config_dir, temp_backup_id)
        os.makedirs(temp_config_dir, exist_ok=True)
        
        # Copy configuration files
        shutil.copy(service_file, os.path.join(temp_config_dir, 'service.yml'))
        if os.path.exists(deployment_file):
            shutil.copy(deployment_file, os.path.join(temp_config_dir, 'deployment.json'))
            
        # Copy data files if they exist
        has_data = False
        if os.path.exists(data_dir):
            temp_data_dir = os.path.join(self.backup_handler.data_dir, temp_backup_id)
            os.makedirs(temp_data_dir, exist_ok=True)
            shutil.copytree(data_dir, temp_data_dir, dirs_exist_ok=True)
            has_data = True
            
        # Use the backup handler to restore the service
        restore_result = self.backup_handler.restore_service(temp_backup_id, target_vm_id)
        
        # Clean up temporary files
        try:
            shutil.rmtree(temp_config_dir)
            if has_data:
                shutil.rmtree(temp_data_dir)
        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {str(e)}")
            
        return restore_result
    
    def start_backup_service(self, port: int = None) -> Dict:
        """Start the buddy backup service to receive backups.
        
        Args:
            port: Port number to listen on
            
        Returns:
            Dictionary with service start result
        """
        if self.service_running:
            return {
                'success': False,
                'message': 'Backup service is already running'
            }
            
        port = port or self.default_port
        
        # Start the service in a background thread
        self.service_running = True
        self.service_thread = threading.Thread(
            target=self._run_backup_service, args=(port,), daemon=True)
        self.service_thread.start()
        
        return {
            'success': True,
            'message': f'Backup service started on port {port}'
        }
    
    def stop_backup_service(self) -> Dict:
        """Stop the buddy backup service.
        
        Returns:
            Dictionary with service stop result
        """
        if not self.service_running:
            return {
                'success': False,
                'message': 'Backup service is not running'
            }
            
        self.service_running = False
        
        if self.service_thread:
            self.service_thread.join(timeout=5)
            
        return {
            'success': True,
            'message': 'Backup service stopped'
        }
    
    def _run_backup_service(self, port: int):
        """Run the buddy backup service.
        
        Args:
            port: Port number to listen on
        """
        # This would typically be implemented with a web server like Flask
        # For now, we'll just log that it would be running
        logger.info(f"Buddy backup service would be running on port {port}")
        
        # In a real implementation, this would start a web server
        # that listens for backup uploads from buddies
        
        # Simulate running until stopped
        while self.service_running:
            time.sleep(1)
            
        logger.info("Buddy backup service stopped")
    
    def _get_service_definition(self, service_id: str) -> Dict:
        """Get a service definition.
        
        Args:
            service_id: ID of the service
            
        Returns:
            Service definition dictionary or None if not found
        """
        # This would typically query the service catalog
        # For now, return a placeholder
        return {
            'id': service_id,
            'name': f'Service {service_id}',
            'vm_id': '100'
        }
    
    def _generate_encryption_key(self) -> str:
        """Generate a random encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')
    
    def _encrypt_share(self, share_id: str, encryption_key: str):
        """Encrypt a backup share.
        
        Args:
            share_id: ID of the share to encrypt
            encryption_key: Encryption key to use
        """
        share_dir = os.path.join(self.shares_dir, share_id)
        if not os.path.exists(share_dir):
            logger.error(f"Share directory not found: {share_dir}")
            return
            
        # Create a Fernet cipher
        key_bytes = encryption_key.encode('utf-8')
        cipher = Fernet(key_bytes)
        
        # Encrypt all files in the share directory
        for root, dirs, files in os.walk(share_dir):
            for file in files:
                # Skip the manifest file
                if file == 'manifest.json':
                    continue
                    
                file_path = os.path.join(root, file)
                
                try:
                    # Read the file
                    with open(file_path, 'rb') as f:
                        data = f.read()
                        
                    # Encrypt the data
                    encrypted_data = cipher.encrypt(data)
                    
                    # Write the encrypted data
                    with open(file_path, 'wb') as f:
                        f.write(encrypted_data)
                        
                except Exception as e:
                    logger.error(f"Error encrypting file {file_path}: {str(e)}")
    
    def _decrypt_share(self, share_dir: str, encryption_key: str):
        """Decrypt a backup share.
        
        Args:
            share_dir: Path to the share directory
            encryption_key: Encryption key to use
        """
        if not os.path.exists(share_dir):
            logger.error(f"Share directory not found: {share_dir}")
            return
            
        # Create a Fernet cipher
        key_bytes = encryption_key.encode('utf-8')
        cipher = Fernet(key_bytes)
        
        # Decrypt all files in the share directory
        for root, dirs, files in os.walk(share_dir):
            for file in files:
                # Skip the manifest file
                if file == 'manifest.json':
                    continue
                    
                file_path = os.path.join(root, file)
                
                try:
                    # Read the file
                    with open(file_path, 'rb') as f:
                        data = f.read()
                        
                    # Decrypt the data
                    decrypted_data = cipher.decrypt(data)
                    
                    # Write the decrypted data
                    with open(file_path, 'wb') as f:
                        f.write(decrypted_data)
                        
                except Exception as e:
                    logger.error(f"Error decrypting file {file_path}: {str(e)}")
    
    def _create_zip_archive(self, source_dir: str, output_path: str):
        """Create a zip archive of a directory.
        
        Args:
            source_dir: Directory to archive
            output_path: Path to the output zip file
        """
        shutil.make_archive(output_path.replace('.zip', ''), 'zip', source_dir)
    
    def _extract_zip_archive(self, zip_path: str, output_dir: str):
        """Extract a zip archive to a directory.
        
        Args:
            zip_path: Path to the zip file
            output_dir: Directory to extract to
        """
        shutil.unpack_archive(zip_path, output_dir, 'zip')
