"""
Version Control System Integration for TESSA.

This module provides functionality to integrate exported configurations with version control systems
like Git, supporting repository setup, commits, and synchronization.
"""
import logging
import os
import subprocess
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class VersionControlIntegration:
    """Integration with version control systems for configuration management."""
    
    def __init__(self):
        """Initialize the VCS integration."""
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.vcs_config_path = os.path.join(self.config_dir, 'vcs_config.json')
        self.repos_dir = os.path.join(self.config_dir, 'repos')
        os.makedirs(self.repos_dir, exist_ok=True)
        
    def setup_repository(self, vcs_type: str, repository_url: str, branch: str = "main", 
                        username: Optional[str] = None, password: Optional[str] = None) -> Dict:
        """
        Set up a version control repository for configuration management.
        
        Args:
            vcs_type: Type of VCS (git, svn, etc.)
            repository_url: URL of the repository
            branch: Branch to use
            username: Optional username for authentication
            password: Optional password for authentication
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            if vcs_type.lower() != "git":
                return {
                    "success": False,
                    "message": f"Unsupported VCS type: {vcs_type}. Only 'git' is currently supported."
                }
                
            # Create repository directory
            repo_name = repository_url.split('/')[-1].replace('.git', '')
            repo_dir = os.path.join(self.repos_dir, repo_name)
            
            # Check if repository already exists
            if os.path.exists(repo_dir):
                # Pull latest changes
                return self._update_git_repository(repo_dir, branch)
            else:
                # Clone repository
                return self._clone_git_repository(repository_url, repo_dir, branch, username, password)
        except Exception as e:
            logger.error(f"Error setting up repository: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to set up repository: {str(e)}"
            }
            
    def _clone_git_repository(self, repository_url: str, repo_dir: str, branch: str,
                             username: Optional[str] = None, password: Optional[str] = None) -> Dict:
        """Clone a Git repository."""
        try:
            # Construct clone command
            clone_cmd = ["git", "clone"]
            
            # Add branch if specified
            if branch:
                clone_cmd.extend(["-b", branch])
                
            # Add authentication if provided
            if username and password:
                # Format: https://username:password@github.com/user/repo.git
                url_parts = repository_url.split('://')
                if len(url_parts) > 1:
                    auth_url = f"{url_parts[0]}://{username}:{password}@{url_parts[1]}"
                    clone_cmd.append(auth_url)
                else:
                    clone_cmd.append(repository_url)
            else:
                clone_cmd.append(repository_url)
                
            clone_cmd.append(repo_dir)
            
            # Execute clone command
            result = subprocess.run(clone_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to clone repository: {result.stderr}"
                }
                
            logger.info(f"Successfully cloned repository to {repo_dir}")
            return {
                "success": True,
                "message": f"Successfully cloned repository to {repo_dir}",
                "repo_dir": repo_dir
            }
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to clone repository: {str(e)}"
            }
            
    def _update_git_repository(self, repo_dir: str, branch: str) -> Dict:
        """Update an existing Git repository."""
        try:
            # Change to repository directory
            cwd = os.getcwd()
            os.chdir(repo_dir)
            
            try:
                # Fetch latest changes
                fetch_cmd = ["git", "fetch", "origin"]
                fetch_result = subprocess.run(fetch_cmd, capture_output=True, text=True)
                
                if fetch_result.returncode != 0:
                    logger.error(f"Git fetch failed: {fetch_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to fetch latest changes: {fetch_result.stderr}"
                    }
                    
                # Checkout specified branch
                checkout_cmd = ["git", "checkout", branch]
                checkout_result = subprocess.run(checkout_cmd, capture_output=True, text=True)
                
                if checkout_result.returncode != 0:
                    logger.error(f"Git checkout failed: {checkout_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to checkout branch {branch}: {checkout_result.stderr}"
                    }
                    
                # Pull latest changes
                pull_cmd = ["git", "pull", "origin", branch]
                pull_result = subprocess.run(pull_cmd, capture_output=True, text=True)
                
                if pull_result.returncode != 0:
                    logger.error(f"Git pull failed: {pull_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to pull latest changes: {pull_result.stderr}"
                    }
                    
                logger.info(f"Successfully updated repository in {repo_dir}")
                return {
                    "success": True,
                    "message": f"Successfully updated repository in {repo_dir}",
                    "repo_dir": repo_dir
                }
            finally:
                # Change back to original directory
                os.chdir(cwd)
        except Exception as e:
            logger.error(f"Error updating repository: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to update repository: {str(e)}"
            }
            
    def add_to_repository(self, directory: str, message: str, repo_name: Optional[str] = None,
                         branch: Optional[str] = None) -> Dict:
        """
        Add exported files to a version control repository.
        
        Args:
            directory: Directory containing files to add
            message: Commit message
            repo_name: Optional repository name (defaults to last repository used)
            branch: Optional branch to commit to
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            # Find repository directory
            if repo_name:
                repo_dir = os.path.join(self.repos_dir, repo_name)
            else:
                # Use the first repository found
                repos = os.listdir(self.repos_dir)
                if not repos:
                    return {
                        "success": False,
                        "message": "No repositories found. Please set up a repository first."
                    }
                repo_dir = os.path.join(self.repos_dir, repos[0])
                
            # Check if repository exists
            if not os.path.exists(repo_dir):
                return {
                    "success": False,
                    "message": f"Repository directory {repo_dir} not found."
                }
                
            # Copy files to repository
            export_dir = os.path.join(repo_dir, "exports", os.path.basename(directory))
            os.makedirs(export_dir, exist_ok=True)
            
            # Clear existing files in export directory
            for item in os.listdir(export_dir):
                item_path = os.path.join(export_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                    
            # Copy new files
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    shutil.copytree(item_path, os.path.join(export_dir, item))
                else:
                    shutil.copy2(item_path, export_dir)
                    
            # Commit changes
            return self._commit_changes(repo_dir, export_dir, message, branch)
        except Exception as e:
            logger.error(f"Error adding to repository: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to add to repository: {str(e)}"
            }
            
    def _commit_changes(self, repo_dir: str, changed_dir: str, message: str, branch: Optional[str] = None) -> Dict:
        """Commit changes to a Git repository."""
        try:
            # Change to repository directory
            cwd = os.getcwd()
            os.chdir(repo_dir)
            
            try:
                # Checkout branch if specified
                if branch:
                    checkout_cmd = ["git", "checkout", branch]
                    checkout_result = subprocess.run(checkout_cmd, capture_output=True, text=True)
                    
                    if checkout_result.returncode != 0:
                        logger.error(f"Git checkout failed: {checkout_result.stderr}")
                        return {
                            "success": False,
                            "message": f"Failed to checkout branch {branch}: {checkout_result.stderr}"
                        }
                        
                # Get relative path to changed directory
                rel_path = os.path.relpath(changed_dir, repo_dir)
                
                # Add changes
                add_cmd = ["git", "add", rel_path]
                add_result = subprocess.run(add_cmd, capture_output=True, text=True)
                
                if add_result.returncode != 0:
                    logger.error(f"Git add failed: {add_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to add changes: {add_result.stderr}"
                    }
                    
                # Commit changes
                commit_cmd = ["git", "commit", "-m", message]
                commit_result = subprocess.run(commit_cmd, capture_output=True, text=True)
                
                # Check if there were changes to commit
                if commit_result.returncode != 0:
                    if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
                        logger.info("No changes to commit")
                        return {
                            "success": True,
                            "message": "No changes to commit",
                            "repo_dir": repo_dir
                        }
                    else:
                        logger.error(f"Git commit failed: {commit_result.stderr}")
                        return {
                            "success": False,
                            "message": f"Failed to commit changes: {commit_result.stderr}"
                        }
                        
                # Push changes
                push_cmd = ["git", "push", "origin"]
                if branch:
                    push_cmd.append(branch)
                    
                push_result = subprocess.run(push_cmd, capture_output=True, text=True)
                
                if push_result.returncode != 0:
                    logger.error(f"Git push failed: {push_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to push changes: {push_result.stderr}"
                    }
                    
                logger.info(f"Successfully committed and pushed changes")
                return {
                    "success": True,
                    "message": f"Successfully committed and pushed changes",
                    "repo_dir": repo_dir
                }
            finally:
                # Change back to original directory
                os.chdir(cwd)
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to commit changes: {str(e)}"
            }
            
    def list_repositories(self) -> Dict:
        """
        List available repositories.
        
        Returns:
            Result dictionary with success status and repositories
        """
        try:
            repos = []
            
            for repo_name in os.listdir(self.repos_dir):
                repo_dir = os.path.join(self.repos_dir, repo_name)
                if os.path.isdir(repo_dir) and os.path.exists(os.path.join(repo_dir, ".git")):
                    # Get repository details
                    repo_info = self._get_git_repo_info(repo_dir)
                    repos.append({
                        "name": repo_name,
                        "path": repo_dir,
                        **repo_info
                    })
                    
            return {
                "success": True,
                "repositories": repos
            }
        except Exception as e:
            logger.error(f"Error listing repositories: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to list repositories: {str(e)}"
            }
            
    def _get_git_repo_info(self, repo_dir: str) -> Dict:
        """Get information about a Git repository."""
        try:
            info = {}
            
            # Change to repository directory
            cwd = os.getcwd()
            os.chdir(repo_dir)
            
            try:
                # Get current branch
                branch_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
                branch_result = subprocess.run(branch_cmd, capture_output=True, text=True)
                
                if branch_result.returncode == 0:
                    info["current_branch"] = branch_result.stdout.strip()
                    
                # Get remote URL
                remote_cmd = ["git", "config", "--get", "remote.origin.url"]
                remote_result = subprocess.run(remote_cmd, capture_output=True, text=True)
                
                if remote_result.returncode == 0:
                    info["remote_url"] = remote_result.stdout.strip()
                    
                # Get last commit
                commit_cmd = ["git", "log", "-1", "--pretty=format:%h|%an|%ad|%s"]
                commit_result = subprocess.run(commit_cmd, capture_output=True, text=True)
                
                if commit_result.returncode == 0 and commit_result.stdout:
                    parts = commit_result.stdout.strip().split("|")
                    if len(parts) >= 4:
                        info["last_commit"] = {
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        }
                        
                return info
            finally:
                # Change back to original directory
                os.chdir(cwd)
        except Exception as e:
            logger.error(f"Error getting repository info: {str(e)}")
            return {}
            
    def sync_repository(self, repo_name: Optional[str] = None) -> Dict:
        """
        Sync a repository with remote.
        
        Args:
            repo_name: Optional repository name (defaults to last repository used)
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            # Find repository directory
            if repo_name:
                repo_dir = os.path.join(self.repos_dir, repo_name)
            else:
                # Use the first repository found
                repos = os.listdir(self.repos_dir)
                if not repos:
                    return {
                        "success": False,
                        "message": "No repositories found. Please set up a repository first."
                    }
                repo_dir = os.path.join(self.repos_dir, repos[0])
                
            # Check if repository exists
            if not os.path.exists(repo_dir):
                return {
                    "success": False,
                    "message": f"Repository directory {repo_dir} not found."
                }
                
            # Get current branch
            branch = self._get_git_repo_info(repo_dir).get("current_branch", "main")
            
            # Update repository
            return self._update_git_repository(repo_dir, branch)
        except Exception as e:
            logger.error(f"Error syncing repository: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to sync repository: {str(e)}"
            }
