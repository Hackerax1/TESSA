"""
SSH Client Utility for Migration Services

This module provides a secure SSH client for connecting to remote servers
during migration operations. It handles authentication, command execution,
file transfers, and connection management.
"""

import os
import logging
import paramiko
from typing import Dict, List, Optional, Tuple, Union, BinaryIO
from io import BytesIO

logger = logging.getLogger(__name__)

class SSHClient:
    """SSH client for remote server operations"""
    
    def __init__(self, hostname: str, port: int = 22, username: str = None, 
                 password: str = None, key_file: str = None, timeout: int = 30):
        """
        Initialize SSH client
        
        Args:
            hostname: Remote server hostname or IP address
            port: SSH port (default: 22)
            username: SSH username
            password: SSH password (optional if key_file is provided)
            key_file: Path to private key file (optional if password is provided)
            timeout: Connection timeout in seconds
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.timeout = timeout
        self.client = None
        self.sftp = None
        
    def connect(self) -> bool:
        """
        Establish SSH connection to remote server
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.hostname,
                'port': self.port,
                'username': self.username,
                'timeout': self.timeout
            }
            
            if self.password:
                connect_kwargs['password'] = self.password
            
            if self.key_file:
                if os.path.exists(self.key_file):
                    key = paramiko.RSAKey.from_private_key_file(self.key_file)
                    connect_kwargs['pkey'] = key
                else:
                    logger.error(f"Key file not found: {self.key_file}")
                    return False
            
            self.client.connect(**connect_kwargs)
            return True
            
        except paramiko.AuthenticationException:
            logger.error(f"Authentication failed for {self.username}@{self.hostname}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH connection error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.sftp:
            self.sftp.close()
            self.sftp = None
            
        if self.client:
            self.client.close()
            self.client = None
    
    def execute_command(self, command: str, timeout: int = 60) -> Tuple[int, str, str]:
        """
        Execute command on remote server
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.client:
            logger.error("Not connected to SSH server")
            return -1, "", "Not connected to SSH server"
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            
            stdout_str = stdout.read().decode('utf-8', errors='replace')
            stderr_str = stderr.read().decode('utf-8', errors='replace')
            
            return exit_code, stdout_str, stderr_str
            
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return -1, "", str(e)
    
    def execute_sudo_command(self, command: str, sudo_password: str = None, 
                           timeout: int = 60) -> Tuple[int, str, str]:
        """
        Execute sudo command on remote server
        
        Args:
            command: Command to execute with sudo
            sudo_password: Sudo password (uses self.password if None)
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.client:
            logger.error("Not connected to SSH server")
            return -1, "", "Not connected to SSH server"
        
        password = sudo_password if sudo_password else self.password
        
        if not password:
            logger.error("No password provided for sudo command")
            return -1, "", "No password provided for sudo command"
        
        sudo_command = f"sudo -S {command}"
        
        try:
            stdin, stdout, stderr = self.client.exec_command(sudo_command, timeout=timeout)
            stdin.write(f"{password}\n")
            stdin.flush()
            
            exit_code = stdout.channel.recv_exit_status()
            
            stdout_str = stdout.read().decode('utf-8', errors='replace')
            stderr_str = stderr.read().decode('utf-8', errors='replace')
            
            # Remove password prompt from stderr
            if "password for" in stderr_str:
                stderr_str = "\n".join(line for line in stderr_str.splitlines() 
                                     if "password for" not in line)
            
            return exit_code, stdout_str, stderr_str
            
        except Exception as e:
            logger.error(f"Sudo command execution error: {str(e)}")
            return -1, "", str(e)
    
    def get_sftp_client(self):
        """
        Get SFTP client for file transfers
        
        Returns:
            SFTP client
        """
        if not self.client:
            logger.error("Not connected to SSH server")
            return None
        
        if not self.sftp:
            try:
                self.sftp = self.client.open_sftp()
            except Exception as e:
                logger.error(f"SFTP client error: {str(e)}")
                return None
        
        return self.sftp
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download file from remote server
        
        Args:
            remote_path: Path to file on remote server
            local_path: Local path to save file
            
        Returns:
            True if download successful, False otherwise
        """
        sftp = self.get_sftp_client()
        if not sftp:
            return False
        
        try:
            sftp.get(remote_path, local_path)
            return True
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return False
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file to remote server
        
        Args:
            local_path: Local path to file
            remote_path: Path to save file on remote server
            
        Returns:
            True if upload successful, False otherwise
        """
        sftp = self.get_sftp_client()
        if not sftp:
            return False
        
        try:
            sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return False
    
    def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists on remote server
        
        Args:
            remote_path: Path to file on remote server
            
        Returns:
            True if file exists, False otherwise
        """
        sftp = self.get_sftp_client()
        if not sftp:
            return False
        
        try:
            sftp.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"File check error: {str(e)}")
            return False
    
    def list_directory(self, remote_path: str) -> List[Dict]:
        """
        List directory contents on remote server
        
        Args:
            remote_path: Path to directory on remote server
            
        Returns:
            List of file/directory attributes
        """
        sftp = self.get_sftp_client()
        if not sftp:
            return []
        
        try:
            items = []
            for item in sftp.listdir_attr(remote_path):
                items.append({
                    'filename': item.filename,
                    'size': item.st_size,
                    'mtime': item.st_mtime,
                    'mode': item.st_mode,
                    'is_dir': bool(item.st_mode & 0o40000)  # Check if it's a directory
                })
            return items
        except Exception as e:
            logger.error(f"Directory listing error: {str(e)}")
            return []
    
    def create_directory(self, remote_path: str, mode: int = 0o755) -> bool:
        """
        Create directory on remote server
        
        Args:
            remote_path: Path to create on remote server
            mode: Directory permissions (default: 0o755)
            
        Returns:
            True if creation successful, False otherwise
        """
        sftp = self.get_sftp_client()
        if not sftp:
            return False
        
        try:
            sftp.mkdir(remote_path, mode)
            return True
        except Exception as e:
            logger.error(f"Directory creation error: {str(e)}")
            return False
    
    def get_file_content(self, remote_path: str) -> Optional[str]:
        """
        Get file content as string
        
        Args:
            remote_path: Path to file on remote server
            
        Returns:
            File content as string, or None if error
        """
        sftp = self.get_sftp_client()
        if not sftp:
            return None
        
        try:
            with sftp.file(remote_path, 'r') as f:
                return f.read().decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"File read error: {str(e)}")
            return None
    
    def write_file_content(self, remote_path: str, content: str) -> bool:
        """
        Write string content to remote file
        
        Args:
            remote_path: Path to file on remote server
            content: String content to write
            
        Returns:
            True if write successful, False otherwise
        """
        sftp = self.get_sftp_client()
        if not sftp:
            return False
        
        try:
            with sftp.file(remote_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"File write error: {str(e)}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
