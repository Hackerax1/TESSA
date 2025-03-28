"""
Main implementation of the Proxmox VE Helper-Scripts plugin.
"""

import os
import json
import requests
import logging
from pathlib import Path
import subprocess
from typing import Dict, List, Optional, Union, Any

from ..base_plugin import BasePlugin
from ..utils import (
    register_command,
    register_intent_handler,
    register_entity_extractor
)

logger = logging.getLogger(__name__)

class ProxmoxHelperScriptsPlugin(BasePlugin):
    """
    Plugin for integrating Proxmox VE Helper-Scripts community repository.
    Allows browsing, downloading, and executing scripts from the community repository.
    """
    
    REPO_API_URL = "https://api.github.com/repos/community-scripts/ProxmoxVE/contents"
    REPO_RAW_URL = "https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main"
    SCRIPTS_WEB_URL = "https://community-scripts.github.io/ProxmoxVE/scripts"
    
    def __init__(self):
        """Initialize the Proxmox Helper Scripts plugin."""
        self._scripts_cache = {}
        self._categories = {}
        self._script_details = {}
        self._scripts_dir = None
        self._last_update = None
    
    @property
    def name(self) -> str:
        """Return the name of the plugin."""
        return "Proxmox VE Helper-Scripts"
    
    @property
    def version(self) -> str:
        """Return the version of the plugin."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Return the description of the plugin."""
        return "Integrates with the community-maintained Proxmox VE Helper-Scripts repository"
    
    @property
    def author(self) -> str:
        """Return the author of the plugin."""
        return "Proxmox NLI Team"
    
    @property
    def dependencies(self) -> List[str]:
        """Return the dependencies of the plugin."""
        return ["requests"]
    
    def initialize(self, base_nli) -> bool:
        """Initialize the plugin with the base NLI instance."""
        self.nli = base_nli
        
        # Create storage directory for downloaded scripts
        plugin_data_path = Path(os.path.expanduser("~/.proxmox_nli/plugins/helper_scripts"))
        self._scripts_dir = plugin_data_path / "scripts"
        os.makedirs(self._scripts_dir, exist_ok=True)
        
        # Register commands and intent handlers
        register_command(
            self.nli,
            "list_helper_scripts",
            self.list_helper_scripts,
            "List available helper scripts from the community repository"
        )
        register_command(
            self.nli,
            "search_helper_scripts",
            self.search_helper_scripts,
            "Search for helper scripts by keyword"
        )
        register_command(
            self.nli,
            "get_helper_script",
            self.get_helper_script,
            "Get details about a specific helper script"
        )
        register_command(
            self.nli,
            "download_helper_script",
            self.download_helper_script,
            "Download a specific helper script"
        )
        register_command(
            self.nli,
            "execute_helper_script",
            self.execute_helper_script,
            "Execute a downloaded helper script"
        )
        register_command(
            self.nli,
            "update_helper_scripts",
            self.update_scripts_cache,
            "Update the helper scripts cache from the repository"
        )
        
        # Register intent handlers
        register_intent_handler(
            self.nli,
            "list_helper_scripts",
            self._handle_list_scripts_intent
        )
        register_intent_handler(
            self.nli,
            "search_helper_scripts",
            self._handle_search_scripts_intent
        )
        register_intent_handler(
            self.nli,
            "get_helper_script",
            self._handle_get_script_intent
        )
        register_intent_handler(
            self.nli,
            "download_helper_script",
            self._handle_download_script_intent
        )
        register_intent_handler(
            self.nli,
            "execute_helper_script",
            self._handle_execute_script_intent
        )
        
        # Register entity extractors
        register_entity_extractor(
            self.nli,
            "helper_script",
            [
                "backup script",
                "storage script",
                "network script",
                "security script",
                "cluster script",
                "VM script",
                "container script",
                "helper script",
                "script for",
                "script that"
            ]
        )
        
        # Update script cache on initialization
        try:
            self.update_scripts_cache()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Helper Scripts plugin: {str(e)}")
            return False
    
    def update_scripts_cache(self) -> Dict[str, Any]:
        """Update the cache of available scripts from the repository."""
        try:
            # Fetch categories from repository
            response = requests.get(f"{self.REPO_API_URL}/scripts")
            if response.status_code != 200:
                return {"status": "error", "message": f"Failed to fetch scripts: HTTP {response.status_code}"}
            
            categories = []
            for item in response.json():
                if item["type"] == "dir":
                    categories.append(item["name"])
            
            # Fetch scripts for each category
            self._scripts_cache = {}
            self._categories = {}
            
            for category in categories:
                category_response = requests.get(f"{self.REPO_API_URL}/scripts/{category}")
                if category_response.status_code == 200:
                    scripts = []
                    for script_item in category_response.json():
                        if script_item["type"] == "file" and script_item["name"].endswith(('.sh', '.py', '.pl')):
                            script_name = script_item["name"]
                            script_path = f"scripts/{category}/{script_name}"
                            script_url = f"{self.REPO_RAW_URL}/{script_path}"
                            
                            scripts.append({
                                "name": script_name,
                                "path": script_path,
                                "url": script_url,
                                "category": category
                            })
                    
                    self._categories[category] = scripts
                    for script in scripts:
                        self._scripts_cache[script["name"]] = script
            
            self._last_update = "Success"
            return {
                "status": "success", 
                "categories": len(self._categories),
                "scripts": len(self._scripts_cache)
            }
            
        except Exception as e:
            logger.error(f"Failed to update scripts cache: {str(e)}")
            self._last_update = f"Failed: {str(e)}"
            return {"status": "error", "message": str(e)}
    
    def list_helper_scripts(self, category: Optional[str] = None) -> Dict[str, Any]:
        """List available helper scripts, optionally filtered by category."""
        if not self._categories:
            self.update_scripts_cache()
        
        if category and category in self._categories:
            return {
                "category": category,
                "scripts": self._categories[category]
            }
        else:
            return {
                "categories": list(self._categories.keys()),
                "script_count": len(self._scripts_cache),
                "scripts_by_category": self._categories
            }
    
    def search_helper_scripts(self, query: str) -> Dict[str, Any]:
        """Search for helper scripts by keyword."""
        if not self._scripts_cache:
            self.update_scripts_cache()
        
        query = query.lower()
        results = []
        
        for script_name, script_info in self._scripts_cache.items():
            if (
                query in script_name.lower() or
                query in script_info["category"].lower()
            ):
                results.append(script_info)
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
    
    def get_helper_script(self, script_name: str) -> Dict[str, Any]:
        """Get details about a specific helper script."""
        if not self._scripts_cache:
            self.update_scripts_cache()
        
        # Try exact match first
        if script_name in self._scripts_cache:
            script_info = self._scripts_cache[script_name]
            
            # If we haven't fetched the detail yet, fetch it
            if script_name not in self._script_details:
                try:
                    content_response = requests.get(script_info["url"])
                    if content_response.status_code == 200:
                        content = content_response.text
                        self._script_details[script_name] = {
                            **script_info,
                            "content": content[:1000] + ("..." if len(content) > 1000 else ""),
                            "full_content": content
                        }
                except Exception as e:
                    logger.error(f"Failed to fetch script content: {str(e)}")
                    return {"status": "error", "message": f"Failed to fetch script content: {str(e)}"}
            
            return {
                "status": "success",
                "script": self._script_details.get(script_name, script_info)
            }
        
        # Try fuzzy match
        closest_matches = []
        for name in self._scripts_cache.keys():
            if script_name.lower() in name.lower():
                closest_matches.append(self._scripts_cache[name])
        
        if closest_matches:
            return {
                "status": "not_found_exact",
                "message": f"No exact match for '{script_name}', but found similar scripts:",
                "suggestions": closest_matches
            }
        
        return {"status": "not_found", "message": f"No script found matching '{script_name}'"}
    
    def download_helper_script(self, script_name: str) -> Dict[str, Any]:
        """Download a specific helper script."""
        script_info = self.get_helper_script(script_name)
        
        if script_info["status"] == "success":
            script = script_info["script"]
            script_path = os.path.join(self._scripts_dir, script["name"])
            
            try:
                # Get full content if needed
                if "full_content" not in script:
                    content_response = requests.get(script["url"])
                    if content_response.status_code == 200:
                        script["full_content"] = content_response.text
                
                # Write the script to file
                with open(script_path, "w") as f:
                    f.write(script["full_content"])
                
                # Make it executable
                os.chmod(script_path, 0o755)
                
                return {
                    "status": "success",
                    "message": f"Script downloaded to {script_path}",
                    "local_path": script_path
                }
            except Exception as e:
                logger.error(f"Failed to download script: {str(e)}")
                return {"status": "error", "message": f"Failed to download script: {str(e)}"}
        
        return script_info  # Return the error or not found message
    
    def execute_helper_script(self, script_name: str, args: str = "") -> Dict[str, Any]:
        """Execute a downloaded helper script."""
        # First make sure the script is downloaded
        download_result = self.download_helper_script(script_name)
        
        if download_result["status"] == "success":
            script_path = download_result["local_path"]
            
            try:
                # Execute the script
                command = f"{script_path} {args}"
                result = subprocess.run(
                    command, 
                    shell=True, 
                    check=False,
                    capture_output=True, 
                    text=True
                )
                
                return {
                    "status": "success" if result.returncode == 0 else "error",
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": command
                }
            except Exception as e:
                logger.error(f"Failed to execute script: {str(e)}")
                return {"status": "error", "message": f"Failed to execute script: {str(e)}"}
        
        return download_result  # Return the download error
    
    def _handle_list_scripts_intent(self, intent, args, entities):
        """Handle the list_helper_scripts intent."""
        category = entities.get("category", None)
        result = self.list_helper_scripts(category)
        
        if category and category in self._categories:
            scripts = result["scripts"]
            response = f"Found {len(scripts)} scripts in the '{category}' category:\n\n"
            for i, script in enumerate(scripts[:10], 1):
                response += f"{i}. {script['name']}\n"
            
            if len(scripts) > 10:
                response += f"\nAnd {len(scripts) - 10} more scripts. Use 'search helper scripts' for more specific results."
        else:
            categories = result["categories"]
            script_count = result["script_count"]
            response = f"Found {script_count} helper scripts across {len(categories)} categories:\n\n"
            for category in categories:
                cat_scripts = self._categories[category]
                response += f"- {category}: {len(cat_scripts)} scripts\n"
            
            response += "\nUse 'list helper scripts [category]' to see scripts in a specific category."
        
        return response
    
    def _handle_search_scripts_intent(self, intent, args, entities):
        """Handle the search_helper_scripts intent."""
        query = args.get("query", "") or entities.get("query", "")
        if not query:
            return "Please provide a search term. For example: 'search helper scripts backup'"
        
        result = self.search_helper_scripts(query)
        scripts = result["results"]
        
        if scripts:
            response = f"Found {len(scripts)} scripts matching '{query}':\n\n"
            for i, script in enumerate(scripts[:15], 1):
                response += f"{i}. {script['name']} (Category: {script['category']})\n"
            
            if len(scripts) > 15:
                response += f"\nAnd {len(scripts) - 15} more results. Please refine your search to see more specific results."
            
            response += "\n\nTo get details about a specific script, use: 'get helper script [name]'"
        else:
            response = f"No helper scripts found matching '{query}'. Try a different search term or use 'list helper scripts' to see all available scripts."
        
        return response
    
    def _handle_get_script_intent(self, intent, args, entities):
        """Handle the get_helper_script intent."""
        script_name = args.get("script_name", "") or entities.get("script_name", "")
        if not script_name:
            return "Please provide a script name. For example: 'get helper script backup-vm.sh'"
        
        result = self.get_helper_script(script_name)
        
        if result["status"] == "success":
            script = result["script"]
            response = f"Script: {script['name']}\n"
            response += f"Category: {script['category']}\n"
            response += f"Path: {script['path']}\n\n"
            
            if "content" in script:
                response += "Script Content (first 1000 characters):\n```\n"
                response += script["content"]
                response += "\n```\n"
            
            response += f"\nTo download this script, use: 'download helper script {script['name']}'"
            response += f"\nTo execute this script, use: 'execute helper script {script['name']}'"
        elif result["status"] == "not_found_exact":
            suggestions = result["suggestions"]
            response = f"{result['message']}\n\n"
            for i, script in enumerate(suggestions[:5], 1):
                response += f"{i}. {script['name']} (Category: {script['category']})\n"
        else:
            response = result["message"]
        
        return response
    
    def _handle_download_script_intent(self, intent, args, entities):
        """Handle the download_helper_script intent."""
        script_name = args.get("script_name", "") or entities.get("script_name", "")
        if not script_name:
            return "Please provide a script name to download. For example: 'download helper script backup-vm.sh'"
        
        result = self.download_helper_script(script_name)
        
        if result["status"] == "success":
            response = f"{result['message']}\n\n"
            response += f"To execute this script, use: 'execute helper script {script_name}'"
        else:
            response = result.get("message", "Failed to download script.")
            
            if result.get("suggestions"):
                response += "\n\nDid you mean one of these scripts?\n"
                for i, script in enumerate(result["suggestions"][:5], 1):
                    response += f"{i}. {script['name']}\n"
        
        return response
    
    def _handle_execute_script_intent(self, intent, args, entities):
        """Handle the execute_helper_script intent."""
        script_name = args.get("script_name", "") or entities.get("script_name", "")
        script_args = args.get("args", "") or entities.get("args", "")
        
        if not script_name:
            return "Please provide a script name to execute. For example: 'execute helper script backup-vm.sh'"
        
        result = self.execute_helper_script(script_name, script_args)
        
        if result["status"] == "success":
            response = f"Successfully executed {script_name}"
            if script_args:
                response += f" with arguments: {script_args}"
            response += "\n\nOutput:\n```\n"
            response += result["stdout"] if result["stdout"] else "(No output)"
            response += "\n```"
            return response
        elif result.get("returncode") is not None:
            response = f"Script {script_name} executed with return code {result['returncode']}"
            if result["stderr"]:
                response += f"\n\nError output:\n```\n{result['stderr']}\n```"
            if result["stdout"]:
                response += f"\n\nStandard output:\n```\n{result['stdout']}\n```"
            return response
        else:
            response = result.get("message", "Failed to execute script.")
            
            if result.get("suggestions"):
                response += "\n\nDid you mean one of these scripts?\n"
                for i, script in enumerate(result["suggestions"][:5], 1):
                    response += f"{i}. {script['name']}\n"
            
            return response
    
    def on_shutdown(self) -> None:
        """Clean up resources when the plugin is shutting down."""
        pass