"""
Notifications Routes.
This module contains all API routes for notifications.
"""
from flask import request, jsonify, current_app
from proxmox_nli.core.security.auth_manager import token_required
import time
from . import notifications_bp

# In-memory storage for notifications (would be replaced with database in production)
push_subscriptions = {}
notification_preferences = {}

@notifications_bp.route('/<user_id>', methods=['GET'])
@token_required()
def get_notifications(user_id):
    """
    Get notifications for a user
    
    Args:
        user_id: User ID
        
    Returns:
        JSON: Notifications for the user
    """
    try:
        # In a real implementation, this would fetch from a database
        # For now, we'll return some sample notifications
        sample_notifications = [
            {
                "id": "notification_" + str(int(time.time())) + "_1",
                "title": "VM Status Change",
                "message": "VM 'web-server' has been started successfully.",
                "timestamp": int(time.time() - 3600) * 1000,  # 1 hour ago
                "read": False,
                "type": "vm_state_change",
                "data": {
                    "vm_id": "100",
                    "vm_name": "web-server",
                    "state": "running"
                },
                "actionUrl": "/vms/100"
            },
            {
                "id": "notification_" + str(int(time.time())) + "_2",
                "title": "Backup Completed",
                "message": "Weekly backup completed successfully. 3 VMs backed up.",
                "timestamp": int(time.time() - 86400) * 1000,  # 1 day ago
                "read": True,
                "type": "backup_complete",
                "data": {
                    "backup_id": "weekly_" + str(int(time.time() - 86400)),
                    "vms": ["web-server", "database", "mail-server"],
                    "size": "4.2 GB"
                },
                "actionUrl": "/backups"
            },
            {
                "id": "notification_" + str(int(time.time())) + "_3",
                "title": "System Update Available",
                "message": "A new system update is available for your Proxmox server.",
                "timestamp": int(time.time() - 172800) * 1000,  # 2 days ago
                "read": False,
                "type": "system_update",
                "data": {
                    "version": "7.4-15",
                    "release_notes": "https://pve.proxmox.com/wiki/Roadmap"
                },
                "actionUrl": "/settings/updates"
            }
        ]
        
        return jsonify({
            "success": True,
            "notifications": sample_notifications
        })
    except Exception as e:
        current_app.logger.error(f"Error getting notifications: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@notifications_bp.route('/<user_id>', methods=['POST'])
@token_required()
def add_notification(user_id):
    """
    Add a new notification for a user
    
    Args:
        user_id: User ID
        
    Returns:
        JSON: Success status
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['title', 'message', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        # In a real implementation, this would save to a database
        # For now, we'll just return success
        
        # Send push notification if enabled
        notification_prefs = notification_preferences.get(user_id, {}).get(data['type'], {})
        if notification_prefs.get('push', {}).get('enabled', False):
            # Get user's push subscriptions
            subscriptions = push_subscriptions.get(user_id, [])
            
            # Send push notification to all subscriptions
            for subscription in subscriptions:
                from proxmox_nli.services.notifications import send_push_notification
                send_push_notification(
                    subscription_info=subscription,
                    title=data['title'],
                    message=data['message'],
                    data=data.get('data'),
                    tag=data.get('id'),
                    url=data.get('actionUrl')
                )
        
        return jsonify({
            "success": True,
            "message": "Notification added successfully",
            "notification_id": "notification_" + str(int(time.time()))
        })
    except Exception as e:
        current_app.logger.error(f"Error adding notification: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@notifications_bp.route('/<user_id>/<notification_id>', methods=['PUT'])
@token_required()
def update_notification(user_id, notification_id):
    """
    Update a notification for a user
    
    Args:
        user_id: User ID
        notification_id: Notification ID
        
    Returns:
        JSON: Success status
    """
    try:
        data = request.json
        
        # In a real implementation, this would update in a database
        # For now, we'll just return success
        
        return jsonify({
            "success": True,
            "message": "Notification updated successfully"
        })
    except Exception as e:
        current_app.logger.error(f"Error updating notification: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@notifications_bp.route('/<user_id>/<notification_id>', methods=['DELETE'])
@token_required()
def delete_notification(user_id, notification_id):
    """
    Delete a notification for a user
    
    Args:
        user_id: User ID
        notification_id: Notification ID
        
    Returns:
        JSON: Success status
    """
    try:
        # In a real implementation, this would delete from a database
        # For now, we'll just return success
        
        return jsonify({
            "success": True,
            "message": "Notification deleted successfully"
        })
    except Exception as e:
        current_app.logger.error(f"Error deleting notification: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@notifications_bp.route('/<user_id>/read-all', methods=['POST'])
@token_required()
def mark_all_notifications_read(user_id):
    """
    Mark all notifications as read for a user
    
    Args:
        user_id: User ID
        
    Returns:
        JSON: Success status
    """
    try:
        # In a real implementation, this would update in a database
        # For now, we'll just return success
        
        return jsonify({
            "success": True,
            "message": "All notifications marked as read"
        })
    except Exception as e:
        current_app.logger.error(f"Error marking notifications as read: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@notifications_bp.route('/<user_id>/clear-all', methods=['POST'])
@token_required()
def clear_all_notifications(user_id):
    """
    Clear all notifications for a user
    
    Args:
        user_id: User ID
        
    Returns:
        JSON: Success status
    """
    try:
        # In a real implementation, this would delete from a database
        # For now, we'll just return success
        
        return jsonify({
            "success": True,
            "message": "All notifications cleared"
        })
    except Exception as e:
        current_app.logger.error(f"Error clearing notifications: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
