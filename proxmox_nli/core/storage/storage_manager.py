"""
Storage manager module for Proxmox NLI.
Handles storage operations, including listing, creating, and managing storage resources.
"""
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, api):
        self.api = api
        
    def list_storage(self, node: str = None) -> Dict:
        """List all storage resources on the cluster or a specific node"""
        try:
            endpoint = f'nodes/{node}/storage' if node else 'storage'
            result = self.api.api_request('GET', endpoint)
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to list storage: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": "Storage resources retrieved successfully",
                "storage": result['data']
            }
            
        except Exception as e:
            logger.error(f"Error listing storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error listing storage: {str(e)}"
            }
    
    def get_storage_details(self, storage_id: str, node: str = None) -> Dict:
        """Get detailed information about a specific storage resource"""
        try:
            if node:
                endpoint = f'nodes/{node}/storage/{storage_id}'
                result = self.api.api_request('GET', endpoint)
            else:
                endpoint = 'storage'
                result = self.api.api_request('GET', endpoint)
                if result['success']:
                    # Filter for the specific storage ID
                    storage_data = next((s for s in result['data'] if s['storage'] == storage_id), None)
                    if storage_data:
                        result['data'] = storage_data
                    else:
                        result['success'] = False
                        result['message'] = f"Storage {storage_id} not found"
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to get storage details: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Storage {storage_id} details retrieved successfully",
                "storage": result['data']
            }
            
        except Exception as e:
            logger.error(f"Error getting storage details: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting storage details: {str(e)}"
            }
    
    def create_storage(self, storage_id: str, storage_type: str, config: Dict) -> Dict:
        """Create a new storage resource"""
        try:
            valid_types = ['dir', 'nfs', 'cifs', 'lvm', 'lvmthin', 'zfs', 'iscsi', 'glusterfs', 'cephfs', 'rbd']
            if storage_type not in valid_types:
                return {
                    "success": False,
                    "message": f"Invalid storage type: {storage_type}. Valid types are: {', '.join(valid_types)}"
                }
            
            # Create parameters for the API request
            params = {
                'storage': storage_id,
                'type': storage_type,
            }
            params.update(config)
            
            result = self.api.api_request('POST', 'storage', params)
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to create storage: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Storage {storage_id} created successfully",
                "task_id": result.get('data')
            }
            
        except Exception as e:
            logger.error(f"Error creating storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating storage: {str(e)}"
            }
    
    def delete_storage(self, storage_id: str) -> Dict:
        """Delete a storage resource"""
        try:
            result = self.api.api_request('DELETE', f'storage/{storage_id}')
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to delete storage: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Storage {storage_id} deleted successfully",
                "task_id": result.get('data')
            }
            
        except Exception as e:
            logger.error(f"Error deleting storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error deleting storage: {str(e)}"
            }
    
    def update_storage(self, storage_id: str, config: Dict) -> Dict:
        """Update a storage resource configuration"""
        try:
            result = self.api.api_request('PUT', f'storage/{storage_id}', config)
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to update storage: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Storage {storage_id} updated successfully",
                "task_id": result.get('data')
            }
            
        except Exception as e:
            logger.error(f"Error updating storage: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating storage: {str(e)}"
            }
    
    def get_storage_status(self, node: str) -> Dict:
        """Get storage status information for a node"""
        try:
            result = self.api.api_request('GET', f'nodes/{node}/storage/status')
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to get storage status: {result.get('message', 'Unknown error')}"
                }
                
            # Calculate total and used space
            total_space = 0
            used_space = 0
            
            for storage in result['data']:
                if 'total' in storage and 'used' in storage:
                    total_space += storage['total']
                    used_space += storage['used']
            
            return {
                "success": True,
                "message": f"Storage status for node {node} retrieved successfully",
                "storage": result['data'],
                "summary": {
                    "total": total_space,
                    "used": used_space,
                    "free": total_space - used_space,
                    "usage_percent": (used_space / total_space * 100) if total_space > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting storage status: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting storage status: {str(e)}"
            }
    
    def get_content(self, storage_id: str, content_type: str = None) -> Dict:
        """Get content list of a storage"""
        try:
            params = {}
            if content_type:
                params['content'] = content_type
            
            result = self.api.api_request('GET', f'storage/{storage_id}/content', params)
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to get storage content: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"Content of storage {storage_id} retrieved successfully",
                "content": result['data']
            }
            
        except Exception as e:
            logger.error(f"Error getting storage content: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting storage content: {str(e)}"
            }
    
    def upload_content(self, node: str, storage_id: str, file_path: str, content_type: str) -> Dict:
        """Upload content to storage"""
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"File not found: {file_path}"
                }
            
            filename = os.path.basename(file_path)
            
            # For real implementation, you would use the Proxmox API to upload files
            # This is a placeholder for the actual API call that would use requests or similar
            
            result = self.api.api_request('POST', f'nodes/{node}/storage/{storage_id}/upload', {
                'content': content_type,
                'filename': filename
            }, files={'file': open(file_path, 'rb')})
            
            if not result['success']:
                return {
                    "success": False,
                    "message": f"Failed to upload content: {result.get('message', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "message": f"File {filename} uploaded successfully to {storage_id}",
                "task_id": result.get('data')
            }
            
        except Exception as e:
            logger.error(f"Error uploading content: {str(e)}")
            return {
                "success": False,
                "message": f"Error uploading content: {str(e)}"
            }