#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, url_for, g, send_file, redirect, session
from flask_socketio import SocketIO, emit
import os
import sys
from proxmox_nli.core import ProxmoxNLI
from proxmox_nli.core.voice_handler import VoiceHandler, VoiceProfile
from proxmox_nli.services.goal_mapper import GoalMapper
from proxmox_nli.core.security.auth_manager import AuthManager
from proxmox_nli.core.user_preferences import UserManager, UserPreferencesManager
from proxmox_nli.core.profile_sync import ProfileSyncManager
from proxmox_nli.core.dashboard_manager import DashboardManager
from functools import wraps
from dotenv import load_dotenv
import logging
import threading
import time
import json
import re
import subprocess
import qrcode
from io import BytesIO
import base64
from pywebpush import webpush, WebPushException
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize the ProxmoxNLI instance (will be properly configured on app start)
proxmox_nli = None
voice_handler = VoiceHandler()
status_monitor_thread = None
resource_monitor_thread = None
auth_manager = AuthManager()
user_manager = UserManager()
user_preferences = UserPreferencesManager()
profile_sync_manager = None  # Will be initialized in start_app
dashboard_manager = None  # Will be initialized in start_app

# Store resource history for optimization analysis
vm_resource_history = defaultdict(lambda: {"cpu": [], "memory": [], "disk_io": [], "network": [], "timestamps": []})
resource_history_window = 24 * 60 * 60  # 24 hours in seconds

# Optimization thresholds
CPU_UNDERUTILIZED_THRESHOLD = 10  # percentage
CPU_OVERUTILIZED_THRESHOLD = 80  # percentage
MEMORY_UNDERUTILIZED_THRESHOLD = 20  # percentage
MEMORY_OVERUTILIZED_THRESHOLD = 85  # percentage

# Push notification settings
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_CLAIMS = {
    "sub": "mailto:" + os.getenv('VAPID_CONTACT_EMAIL', 'admin@example.com')
}

# Store push subscriptions in memory (in production, use a database)
push_subscriptions = {}

# Event notification settings
notification_preferences = defaultdict(lambda: defaultdict(dict))

# Initialize default notification preferences
def initialize_default_notification_preferences(user_id):
    """Initialize default notification preferences for a user"""
    user_prefs = {}
    
    # VM events
    for event_type in ['vm_state_change', 'vm_creation', 'vm_deletion', 'vm_error']:
        user_prefs[event_type] = {
            'email': {'enabled': True},
            'push': {'enabled': True},
            'sms': {'enabled': False},
            'webhook': {'enabled': False}
        }
    
    # Backup events
    for event_type in ['backup_start', 'backup_complete', 'backup_error']:
        user_prefs[event_type] = {
            'email': {'enabled': True},
            'push': {'enabled': True},
            'sms': {'enabled': False},
            'webhook': {'enabled': False}
        }
    
    # Security events
    for event_type in ['security_alert', 'login_failure', 'login_success']:
        user_prefs[event_type] = {
            'email': {'enabled': True},
            'push': {'enabled': True},
            'sms': {'enabled': event_type == 'security_alert'},
            'webhook': {'enabled': False}
        }
    
    # System events
    for event_type in ['system_update', 'resource_warning', 'disk_space_low']:
        user_prefs[event_type] = {
            'email': {'enabled': True},
            'push': {'enabled': True},
            'sms': {'enabled': event_type == 'disk_space_low'},
            'webhook': {'enabled': False}
        }
    
    # Service events
    for event_type in ['service_start', 'service_stop', 'service_error']:
        user_prefs[event_type] = {
            'email': {'enabled': True},
            'push': {'enabled': True},
            'sms': {'enabled': event_type == 'service_error'},
            'webhook': {'enabled': False}
        }
    
    notification_preferences[user_id] = user_prefs
    return user_prefs

# Function to send push notification
def send_push_notification(subscription_info, title, message, data=None, tag=None, url=None):
    """
    Send a push notification to a subscribed client
    
    Args:
        subscription_info: Push subscription info
        title: Notification title
        message: Notification message
        data: Additional data to send
        tag: Notification tag for grouping
        url: URL to open when notification is clicked
    
    Returns:
        bool: True if notification was sent successfully
    """
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        logger.error("VAPID keys not configured. Push notifications disabled.")
        return False
    
    if not subscription_info:
        logger.error("No subscription info provided")
        return False
    
    try:
        # Prepare notification payload
        payload = {
            "title": title,
            "message": message,
            "icon": "/static/TessaLogo.webp",
            "badge": "/static/TessaLogo.webp",
            "tag": tag or str(uuid.uuid4()),
            "requireInteraction": True,
            "renotify": True
        }
        
        # Add optional data
        if data:
            payload["data"] = data
        
        # Add URL to open when clicked
        if url:
            if not payload.get("data"):
                payload["data"] = {}
            payload["data"]["url"] = url
        
        # Send the notification
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        
        return True
    except WebPushException as e:
        logger.error(f"Push notification error: {e}")
        # If the subscription is expired, remove it
        if e.response and e.response.status_code == 410:
            logger.info("Subscription expired, removing")
            # Find and remove the expired subscription
            for user_id, subscriptions in push_subscriptions.items():
                for i, sub in enumerate(subscriptions):
                    if sub == subscription_info:
                        push_subscriptions[user_id].pop(i)
                        break
        return False
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return False

# Function to send notification for an event
def send_event_notification(event_type, title, message, data=None, user_id=None):
    """
    Send notification for an event based on user preferences
    
    Args:
        event_type: Type of event (vm_state_change, backup_error, etc.)
        title: Notification title
        message: Notification message
        data: Additional data for the notification
        user_id: User ID to send notification to (None for all users)
    
    Returns:
        dict: Results of notification attempts
    """
    results = {
        'email': False,
        'push': False,
        'sms': False,
        'webhook': False
    }
    
    # If user_id is specified, only send to that user
    if user_id:
        user_ids = [user_id]
    else:
        # Otherwise send to all users
        user_ids = list(notification_preferences.keys())
    
    for uid in user_ids:
        # Skip if user has no preferences
        if uid not in notification_preferences:
            continue
        
        user_prefs = notification_preferences[uid]
        
        # Skip if event type not in preferences
        if event_type not in user_prefs:
            continue
        
        event_prefs = user_prefs[event_type]
        
        # Check each notification method
        for method, prefs in event_prefs.items():
            if prefs.get('enabled', False):
                if method == 'push':
                    # Send push notification
                    if uid in push_subscriptions:
                        for subscription in push_subscriptions[uid]:
                            success = send_push_notification(
                                subscription,
                                title,
                                message,
                                data=data,
                                tag=event_type
                            )
                            if success:
                                results['push'] = True
                
                elif method == 'email':
                    # TODO: Implement email notifications
                    pass
                
                elif method == 'sms':
                    # TODO: Implement SMS notifications
                    pass
                
                elif method == 'webhook':
                    # TODO: Implement webhook notifications
                    pass
    
    return results

# Create the token_required decorator for protected routes
def token_required(required_roles=['user']):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if Authorization header is present
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid authentication token'}), 401
            
            # Extract token
            token = auth_header.split('Bearer ')[1]
            
            # Check permissions
            if not auth_manager.check_permission(token, required_roles):
                return jsonify({'error': 'Unauthorized access'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Import the new modules
from proxmox_nli.core.security.resource_manager import ResourceManager
from proxmox_nli.core.security.family_manager import FamilyManager

# Initialize resource and family managers
resource_manager = ResourceManager()
family_manager = FamilyManager()

# Add multi-tenancy and family management endpoints

@app.route('/api/family/members', methods=['GET'])
@token_required(required_roles=['admin'])
def get_family_members():
    """Get all family members."""
    result = family_manager.get_family_members()
    return jsonify(result)

@app.route('/api/family/members/<user_id>', methods=['GET'])
@token_required()
def get_family_member(user_id):
    """Get a specific family member."""
    # Check if user is requesting their own info or has admin role
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    
    current_user_id = payload.get('user_id')
    roles = payload.get('roles', [])
    
    if current_user_id != user_id and 'admin' not in roles:
        return jsonify({
            'success': False,
            'message': 'Unauthorized to view this family member'
        }), 403
    
    result = family_manager.get_family_member(user_id)
    return jsonify(result)

@app.route('/api/family/members', methods=['POST'])
@token_required(required_roles=['admin'])
def add_family_member():
    """Add a new family member."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    user_id = data.get('user_id')
    name = data.get('name')
    
    if not user_id or not name:
        return jsonify({
            'success': False,
            'message': 'User ID and name are required'
        }), 400
    
    relationship = data.get('relationship')
    age = data.get('age')
    profile_image = data.get('profile_image')
    
    result = family_manager.add_family_member(user_id, name, relationship, age, profile_image)
    
    if result.get('success'):
        # If group is specified, add member to group
        group = data.get('group')
        if group:
            family_manager.add_member_to_group(user_id, group)
        
        # If policy is specified, apply policy
        policy = data.get('policy')
        if policy:
            family_manager.apply_access_policy(user_id, policy)
    
    return jsonify(result)

@app.route('/api/family/groups/<group_name>/members/<user_id>', methods=['POST'])
@token_required(required_roles=['admin'])
def add_member_to_group(group_name, user_id):
    """Add a family member to a group."""
    result = family_manager.add_member_to_group(user_id, group_name)
    return jsonify(result)

@app.route('/api/family/members/<user_id>/groups', methods=['GET'])
@token_required()
def get_member_groups(user_id):
    """Get groups that a family member belongs to."""
    # Check if user is requesting their own info or has admin role
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    
    current_user_id = payload.get('user_id')
    roles = payload.get('roles', [])
    
    if current_user_id != user_id and 'admin' not in roles:
        return jsonify({
            'success': False,
            'message': 'Unauthorized to view this family member\'s groups'
        }), 403
    
    result = family_manager.get_member_groups(user_id)
    return jsonify(result)

@app.route('/api/family/policies/<policy_name>/members/<user_id>', methods=['POST'])
@token_required(required_roles=['admin'])
def apply_policy_to_member(policy_name, user_id):
    """Apply an access policy to a family member."""
    result = family_manager.apply_access_policy(user_id, policy_name)
    return jsonify(result)

@app.route('/api/family/members/<user_id>/policies', methods=['GET'])
@token_required()
def get_member_policies(user_id):
    """Get access policies applied to a family member."""
    # Check if user is requesting their own info or has admin role
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    
    current_user_id = payload.get('user_id')
    roles = payload.get('roles', [])
    
    if current_user_id != user_id and 'admin' not in roles:
        return jsonify({
            'success': False,
            'message': 'Unauthorized to view this family member\'s policies'
        }), 403
    
    result = family_manager.get_member_policies(user_id)
    return jsonify(result)

@app.route('/api/resources', methods=['GET'])
@token_required()
def get_user_resources():
    """Get resources allocated to the current user."""
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    
    user_id = payload.get('user_id')
    resource_type = request.args.get('type')
    
    result = resource_manager.get_user_resources(user_id, resource_type)
    return jsonify(result)

@app.route('/api/resources/<resource_type>/<resource_id>/allocate', methods=['POST'])
@token_required(required_roles=['admin'])
def allocate_resource(resource_type, resource_id):
    """Allocate a resource to a user."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    user_id = data.get('user_id')
    permissions = data.get('permissions', [])
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': 'User ID is required'
        }), 400
    
    result = resource_manager.allocate_resource(user_id, resource_type, resource_id, permissions)
    return jsonify(result)

@app.route('/api/resources/groups', methods=['POST'])
@token_required(required_roles=['admin'])
def create_resource_group():
    """Create a resource group."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    name = data.get('name')
    description = data.get('description')
    
    if not name:
        return jsonify({
            'success': False,
            'message': 'Group name is required'
        }), 400
    
    result = resource_manager.create_resource_group(name, description)
    return jsonify(result)

@app.route('/api/resources/groups/<group_id>/resources', methods=['POST'])
@token_required(required_roles=['admin'])
def add_resource_to_group(group_id):
    """Add a resource to a group."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    resource_type = data.get('resource_type')
    resource_id = data.get('resource_id')
    
    if not resource_type or not resource_id:
        return jsonify({
            'success': False,
            'message': 'Resource type and ID are required'
        }), 400
    
    result = resource_manager.add_resource_to_group(int(group_id), resource_type, resource_id)
    return jsonify(result)

@app.route('/api/resources/groups/<group_id>/users', methods=['POST'])
@token_required(required_roles=['admin'])
def add_user_to_resource_group(group_id):
    """Add a user to a resource group."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    user_id = data.get('user_id')
    role = data.get('role', 'user')
    
    if not user_id:
        return jsonify({
            'success': False,
            'message': 'User ID is required'
        }), 400
    
    result = resource_manager.add_user_to_group(user_id, int(group_id), role)
    return jsonify(result)

@app.route('/api/users/<user_id>/roles/<role_name>', methods=['POST'])
@token_required(required_roles=['admin'])
def assign_role_to_user(user_id, role_name):
    """Assign a role to a user."""
    result = resource_manager.assign_role_to_user(user_id, role_name)
    return jsonify(result)

@app.route('/api/users/<user_id>/roles', methods=['GET'])
@token_required()
def get_user_roles(user_id):
    """Get roles assigned to a user."""
    # Check if user is requesting their own info or has admin role
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    
    current_user_id = payload.get('user_id')
    roles = payload.get('roles', [])
    
    if current_user_id != user_id and 'admin' not in roles:
        return jsonify({
            'success': False,
            'message': 'Unauthorized to view this user\'s roles'
        }), 403
    
    result = resource_manager.get_user_roles(user_id)
    return jsonify(result)

@app.route('/api/users/<user_id>/quotas', methods=['POST'])
@token_required(required_roles=['admin'])
def set_user_quota(user_id):
    """Set a quota limit for a user."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    resource_type = data.get('resource_type')
    limit_value = data.get('limit_value')
    
    if not resource_type or limit_value is None:
        return jsonify({
            'success': False,
            'message': 'Resource type and limit value are required'
        }), 400
    
    result = resource_manager.set_user_quota(user_id, resource_type, limit_value)
    return jsonify(result)

@app.route('/api/users/<user_id>/quotas', methods=['GET'])
@token_required()
def get_user_quotas(user_id):
    """Get quotas for a user."""
    # Check if user is requesting their own info or has admin role
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    
    current_user_id = payload.get('user_id')
    roles = payload.get('roles', [])
    
    if current_user_id != user_id and 'admin' not in roles:
        return jsonify({
            'success': False,
            'message': 'Unauthorized to view this user\'s quotas'
        }), 403
    
    result = resource_manager.get_user_quotas(user_id)
    return jsonify(result)

# Add family management page routes

@app.route('/family/management', methods=['GET'])
@token_required(required_roles=['admin'])
def family_management_page():
    """Render the family management page."""
    return render_template('family_management.html')

@app.route('/family/profile', methods=['GET'])
@token_required()
def family_profile_page():
    """Render the family profile page."""
    return render_template('family_profile.html')

@app.route('/resources/management', methods=['GET'])
@token_required(required_roles=['admin'])
def resource_management_page():
    """Render the resource management page."""
    return render_template('resource_management.html')

# Add notification API endpoints

@app.route('/api/notifications/<user_id>', methods=['GET'])
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
        logger.error(f"Error getting notifications: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/notifications/<user_id>', methods=['POST'])
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
        logger.error(f"Error adding notification: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/notifications/<user_id>/<notification_id>', methods=['PUT'])
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
        logger.error(f"Error updating notification: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/notifications/<user_id>/<notification_id>', methods=['DELETE'])
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
        logger.error(f"Error deleting notification: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/notifications/<user_id>/read-all', methods=['POST'])
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
        logger.error(f"Error marking all notifications as read: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/notifications/<user_id>/clear-all', methods=['POST'])
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
        logger.error(f"Error clearing all notifications: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ... (rest of the code remains the same)

# Import the new modules
from proxmox_nli.controllers.user_experience_controller import UserExperienceController
from proxmox_nli.core.knowledge_system import KnowledgeSystem
from proxmox_nli.core.config_validation import ConfigValidator
from proxmox_nli.services.personalized_setup import PersonalizedSetupJourney

# Initialize the user experience controller
user_experience_controller = UserExperienceController()

# User Experience API Routes
@app.route('/api/user-experience/journey/start', methods=['POST'])
@token_required
def start_personalized_journey():
    """Start a personalized setup journey for the current user"""
    data = request.get_json()
    user_id = g.user_id
    expertise_level = data.get('expertise_level')
    
    journey = user_experience_controller.start_personalized_journey(user_id, expertise_level)
    
    return jsonify(journey)

@app.route('/api/user-experience/journey/current-step', methods=['GET'])
@token_required
def get_current_journey_step():
    """Get the current step in the user's journey"""
    user_id = g.user_id
    
    step = user_experience_controller.get_current_journey_step(user_id)
    
    if not step:
        return jsonify({"error": "No active journey or step found"}), 404
        
    return jsonify(step)

@app.route('/api/user-experience/journey/advance', methods=['POST'])
@token_required
def advance_journey():
    """Advance to the next step in the user's journey"""
    user_id = g.user_id
    
    journey = user_experience_controller.advance_journey(user_id)
    
    if not journey:
        return jsonify({"error": "No active journey found"}), 404
        
    return jsonify(journey)

@app.route('/api/user-experience/journey/progress', methods=['GET'])
@token_required
def get_journey_progress():
    """Get the progress of the user's journey"""
    user_id = g.user_id
    
    progress = user_experience_controller.get_journey_progress(user_id)
    
    if not progress:
        return jsonify({"error": "No active journey found"}), 404
        
    return jsonify(progress)

@app.route('/api/user-experience/journey/customize', methods=['POST'])
@token_required
def customize_journey():
    """Customize the user's journey"""
    data = request.get_json()
    user_id = g.user_id
    
    journey = user_experience_controller.customize_journey(user_id, data)
    
    if not journey:
        return jsonify({"error": "No active journey found"}), 404
        
    return jsonify(journey)

@app.route('/api/user-experience/config/validate', methods=['POST'])
@token_required
def validate_configuration():
    """Validate a configuration and create a backup if valid"""
    data = request.get_json()
    config_type = data.get('config_type')
    config_id = data.get('config_id')
    config_data = data.get('config_data')
    
    if not all([config_type, config_id, config_data]):
        return jsonify({"error": "Missing required fields"}), 400
        
    result = user_experience_controller.validate_configuration(config_type, config_id, config_data)
    
    return jsonify(result)

@app.route('/api/user-experience/config/rollback', methods=['POST'])
@token_required
def rollback_configuration():
    """Rollback to a previous configuration"""
    data = request.get_json()
    user_id = g.user_id
    backup_id = data.get('backup_id')
    
    if not backup_id:
        return jsonify({"error": "Missing backup_id"}), 400
        
    result = user_experience_controller.rollback_configuration(user_id, backup_id)
    
    return jsonify(result)

@app.route('/api/user-experience/config/backups', methods=['GET'])
@token_required
def get_configuration_backups():
    """Get available configuration backups"""
    config_type = request.args.get('config_type')
    config_id = request.args.get('config_id')
    
    backups = user_experience_controller.get_configuration_backups(config_type, config_id)
    
    return jsonify(backups)

@app.route('/api/user-experience/config/compare', methods=['POST'])
@token_required
def compare_configurations():
    """Compare current configuration with a backup"""
    data = request.get_json()
    current_config = data.get('current_config')
    backup_id = data.get('backup_id')
    
    if not all([current_config, backup_id]):
        return jsonify({"error": "Missing required fields"}), 400
        
    differences = user_experience_controller.compare_configurations(current_config, backup_id)
    
    return jsonify(differences)

@app.route('/api/user-experience/ui/preferences', methods=['PUT'])
@token_required
def update_ui_preferences():
    """Update UI preferences for a user"""
    data = request.get_json()
    user_id = g.user_id
    
    preferences = user_experience_controller.update_ui_preferences(user_id, data)
    
    return jsonify(preferences)

@app.route('/api/user-experience/ui/adaptations', methods=['GET'])
@token_required
def get_ui_adaptations():
    """Get UI adaptation recommendations for a user"""
    user_id = g.user_id
    
    adaptations = user_experience_controller.get_ui_adaptations(user_id)
    
    return jsonify(adaptations)

@app.route('/api/user-experience/knowledge/record', methods=['POST'])
@token_required
def record_learning_activity():
    """Record a learning activity for a user"""
    data = request.get_json()
    user_id = g.user_id
    knowledge_area = data.get('knowledge_area')
    activity_type = data.get('activity_type')
    details = data.get('details', {})
    
    if not all([knowledge_area, activity_type]):
        return jsonify({"error": "Missing required fields"}), 400
        
    result = user_experience_controller.record_learning_activity(user_id, knowledge_area, activity_type, details)
    
    return jsonify(result)

@app.route('/api/user-experience/knowledge/recommendations', methods=['GET'])
@token_required
def get_learning_recommendations():
    """Get learning recommendations for a user"""
    user_id = g.user_id
    
    recommendations = user_experience_controller.get_learning_recommendations(user_id)
    
    return jsonify(recommendations)

@app.route('/api/user-experience/knowledge/expertise', methods=['GET'])
@token_required
def get_expertise_summary():
    """Get a summary of the user's expertise"""
    user_id = g.user_id
    
    summary = user_experience_controller.get_expertise_summary(user_id)
    
    return jsonify(summary)

@app.route('/api/user-experience/setup/start', methods=['POST'])
@token_required
def start_goal_based_setup():
    """Start a goal-based setup for a user"""
    user_id = g.user_id
    
    setup_state = user_experience_controller.start_goal_based_setup(user_id)
    
    return jsonify(setup_state)

@app.route('/api/user-experience/setup/goals', methods=['POST'])
@token_required
def process_goal_selection():
    """Process goal selection for a user"""
    data = request.get_json()
    user_id = g.user_id
    goals = data.get('goals', [])
    
    setup_state = user_experience_controller.process_goal_selection(user_id, goals)
    
    return jsonify(setup_state)

@app.route('/api/user-experience/setup/recommendations', methods=['GET'])
@token_required
def get_goal_based_recommendations():
    """Get service recommendations based on user goals"""
    user_id = g.user_id
    
    recommendations = user_experience_controller.get_goal_based_recommendations(user_id)
    
    return jsonify(recommendations)

# Add asset versioning support
app.config['ASSET_MANIFEST'] = {}
manifest_path = os.path.join(app.static_folder, 'dist', 'manifest.json')
if os.path.exists(manifest_path):
    with open(manifest_path, 'r') as f:
        app.config['ASSET_MANIFEST'] = json.load(f)

# Create a template function to get versioned assets
@app.template_filter('versioned_asset')
def versioned_asset(filename):
    """Get the versioned path for an asset."""
    if app.debug:
        # In debug mode, use the original file to avoid caching issues
        return url_for('static', filename=filename)
    
    # In production, use the versioned file from the manifest
    manifest = app.config['ASSET_MANIFEST']
    if filename in manifest:
        return manifest[filename]['path']
    
    # Fallback to the original file
    return url_for('static', filename=filename)

# Run asset optimization in production mode
if not app.debug:
    try:
        from scripts.optimize_js import main as optimize_js
        print("Optimizing JavaScript and CSS files...")
        optimize_js()
        
        # Reload the manifest
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                app.config['ASSET_MANIFEST'] = json.load(f)
    except Exception as e:
        print(f"Error optimizing assets: {e}")

@app.route('/api/push-public-key', methods=['GET'])
def get_push_public_key():
    """
    Get the public key for push notifications
    
    Returns:
        JSON: Public key for push notifications
    """
    if not VAPID_PUBLIC_KEY:
        return jsonify({"success": False, "message": "Push notifications not configured"}), 500
    
    return jsonify({
        "success": True,
        "publicKey": VAPID_PUBLIC_KEY
    })

@app.route('/api/push-subscription', methods=['POST'])
def save_push_subscription():
    """
    Save a push subscription
    
    Returns:
        JSON: Success status
    """
    try:
        data = request.json
        if not data or not data.get('subscription'):
            return jsonify({"success": False, "message": "No subscription data provided"}), 400
        
        subscription = data.get('subscription')
        user_id = data.get('user_id', 'default_user')
        
        # Initialize user's subscriptions list if it doesn't exist
        if user_id not in push_subscriptions:
            push_subscriptions[user_id] = []
        
        # Check if subscription already exists
        for existing_sub in push_subscriptions[user_id]:
            if existing_sub.get('endpoint') == subscription.get('endpoint'):
                # Update existing subscription
                existing_sub.update(subscription)
                break
        else:
            # Add new subscription
            push_subscriptions[user_id].append(subscription)
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error saving push subscription: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/notification-preferences/<user_id>', methods=['GET'])
@token_required()
def get_notification_preferences(user_id):
    """
    Get notification preferences for a user
    
    Args:
        user_id: User ID
        
    Returns:
        JSON: Notification preferences
    """
    try:
        # Check if user has preferences
        if user_id not in notification_preferences:
            return jsonify({
                "success": True,
                "preferences": [],
                "grouped_preferences": {}
            })
        
        # Return preferences
        return jsonify({
            "success": True,
            "preferences": notification_preferences[user_id],
            "grouped_preferences": notification_preferences[user_id]
        })
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/initialize-notification-preferences/<user_id>', methods=['POST'])
@token_required()
def initialize_notification_preferences(user_id):
    """
    Initialize notification preferences for a user
    
    Args:
        user_id: User ID
        
    Returns:
        JSON: Success status
    """
    try:
        # Initialize default preferences
        prefs = initialize_default_notification_preferences(user_id)
        
        return jsonify({
            "success": True,
            "message": "Notification preferences initialized",
            "preferences": prefs,
            "grouped_preferences": prefs
        })
    except Exception as e:
        logger.error(f"Error initializing notification preferences: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/notification-preference/<user_id>', methods=['POST'])
@token_required()
def set_notification_preference(user_id):
    """
    Set a notification preference
    
    Args:
        user_id: User ID
        
    Returns:
        JSON: Success status
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        event_type = data.get('event_type')
        method = data.get('method')
        enabled = data.get('enabled', False)
        
        if not event_type or not method:
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        # Initialize user's preferences if they don't exist
        if user_id not in notification_preferences:
            notification_preferences[user_id] = {}
        
        # Initialize event type if it doesn't exist
        if event_type not in notification_preferences[user_id]:
            notification_preferences[user_id][event_type] = {}
        
        # Initialize method if it doesn't exist
        if method not in notification_preferences[user_id][event_type]:
            notification_preferences[user_id][event_type][method] = {}
        
        # Set enabled status
        notification_preferences[user_id][event_type][method]['enabled'] = enabled
        
        # If this is a push subscription, store the subscription
        if method == 'push' and enabled and data.get('subscription'):
            subscription = data.get('subscription')
            
            # Initialize user's subscriptions list if it doesn't exist
            if user_id not in push_subscriptions:
                push_subscriptions[user_id] = []
            
            # Check if subscription already exists
            for existing_sub in push_subscriptions[user_id]:
                if existing_sub.get('endpoint') == subscription.get('endpoint'):
                    # Update existing subscription
                    existing_sub.update(subscription)
                    break
            else:
                # Add new subscription
                push_subscriptions[user_id].append(subscription)
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error setting notification preference: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/test-notification/<user_id>', methods=['POST'])
@token_required()
def test_notification(user_id):
    """
    Send a test notification
    
    Args:
        user_id: User ID
        
    Returns:
        JSON: Success status
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        notification_type = data.get('type')
        
        if not notification_type:
            return jsonify({"success": False, "message": "Missing notification type"}), 400
        
        if notification_type == 'push':
            # Send test push notification
            subscription = data.get('subscription')
            if not subscription:
                return jsonify({"success": False, "message": "No push subscription provided"}), 400
            
            success = send_push_notification(
                subscription,
                "Test Notification",
                "This is a test push notification from Proxmox NLI",
                data={"test": True},
                tag="test_notification"
            )
            
            if success:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "message": "Failed to send push notification"}), 500
        
        elif notification_type == 'email':
            # TODO: Implement email test notification
            return jsonify({"success": False, "message": "Email notifications not implemented yet"}), 501
        
        elif notification_type == 'sms':
            # TODO: Implement SMS test notification
            return jsonify({"success": False, "message": "SMS notifications not implemented yet"}), 501
        
        elif notification_type == 'webhook':
            # TODO: Implement webhook test notification
            return jsonify({"success": False, "message": "Webhook notifications not implemented yet"}), 501
        
        else:
            return jsonify({"success": False, "message": f"Unknown notification type: {notification_type}"}), 400
    
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/mobile', methods=['GET'])
def mobile_interface():
    """
    Render the mobile interface
    
    Returns:
        HTML: Mobile interface
    """
    return render_template('mobile_base.html')

@app.route('/mobile/vms', methods=['GET'])
def mobile_vms():
    """
    Render the mobile VMs page
    
    Returns:
        HTML: Mobile VMs page
    """
    return render_template('mobile_vms.html')

@app.route('/mobile/notifications', methods=['GET'])
def mobile_notifications():
    """
    Render the mobile notifications page
    
    Returns:
        HTML: Mobile notifications page
    """
    return render_template('mobile_notifications.html')

@app.route('/auth/oauth/providers', methods=['GET'])
def oauth_providers():
    """Get all configured OAuth providers."""
    providers = auth_manager.get_oauth_providers()
    return jsonify(providers)

@app.route('/auth/oauth/login/<provider_id>', methods=['GET'])
def oauth_login(provider_id):
    """Initiate OAuth login flow."""
    # Generate the redirect URI
    redirect_uri = url_for('oauth_callback', provider_id=provider_id, _external=True)
    
    # Generate the authorization URL
    result = auth_manager.generate_oauth_authorization_url(provider_id, redirect_uri)
    
    if not result.get('success', False):
        return jsonify(result), 400
        
    # Redirect to the authorization URL
    return redirect(result['auth_url'])

@app.route('/auth/oauth/callback/<provider_id>', methods=['GET'])
def oauth_callback(provider_id):
    """Handle OAuth callback."""
    # Get the authorization code and state from the request
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return jsonify({
            'success': False,
            'message': 'Missing code or state parameter'
        }), 400
        
    # Handle the callback
    result = auth_manager.handle_oauth_callback(code, state)
    
    if not result.get('success', False):
        return jsonify(result), 400
        
    # Set the token in a cookie or session
    token = result.get('token')
    if token:
        session['token'] = token
        
        # Redirect to the dashboard or a success page
        return redirect(url_for('dashboard'))
    else:
        return jsonify({
            'success': False,
            'message': 'Authentication successful but no token was generated'
        }), 500

@app.route('/auth/oauth/link/<provider_id>', methods=['GET'])
@token_required()
def oauth_link(provider_id):
    """Link an OAuth account to the current user."""
    # Get the current user ID from the token
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
        
    user_id = payload.get('user_id')
    
    # Generate the redirect URI
    redirect_uri = url_for('oauth_link_callback', provider_id=provider_id, _external=True)
    
    # Generate the authorization URL
    result = auth_manager.generate_oauth_authorization_url(provider_id, redirect_uri)
    
    if not result.get('success', False):
        return jsonify(result), 400
        
    # Store the user ID in the session for the callback
    session['linking_user_id'] = user_id
    
    # Redirect to the authorization URL
    return redirect(result['auth_url'])

@app.route('/auth/oauth/link-callback/<provider_id>', methods=['GET'])
def oauth_link_callback(provider_id):
    """Handle OAuth account linking callback."""
    # Get the authorization code and state from the request
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return jsonify({
            'success': False,
            'message': 'Missing code or state parameter'
        }), 400
        
    # Get the user ID from the session
    user_id = session.get('linking_user_id')
    if not user_id:
        return jsonify({
            'success': False,
            'message': 'No user ID found in session'
        }), 400
        
    # Handle the callback
    result = auth_manager.handle_oauth_callback(code, state)
    
    if not result.get('success', False):
        return jsonify(result), 400
        
    # Link the OAuth account to the user
    link_result = auth_manager.link_oauth_account(
        user_id, 
        provider_id, 
        result.get('userinfo', {}).get('provider_user_id', ''),
        result.get('userinfo', {})
    )
    
    # Redirect to the account settings page
    return redirect(url_for('account_settings'))

@app.route('/auth/oauth/unlink/<provider_id>/<provider_user_id>', methods=['POST'])
@token_required()
def oauth_unlink(provider_id, provider_user_id):
    """Unlink an OAuth account from the current user."""
    # Get the current user ID from the token
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
        
    user_id = payload.get('user_id')
    
    # Unlink the OAuth account
    result = auth_manager.unlink_oauth_account(user_id, provider_id, provider_user_id)
    
    return jsonify(result)

@app.route('/auth/oauth/accounts', methods=['GET'])
@token_required()
def oauth_accounts():
    """Get all OAuth accounts linked to the current user."""
    # Get the current user ID from the token
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
        
    user_id = payload.get('user_id')
    
    # Get the user's OAuth accounts
    result = auth_manager.get_user_oauth_accounts(user_id)
    
    return jsonify(result)

@app.route('/auth/oauth/configure/<provider_id>', methods=['POST'])
@token_required(required_roles=['admin'])
def oauth_configure(provider_id):
    """Configure an OAuth provider."""
    # Only administrators can configure OAuth providers
    config = request.json
    
    if not config:
        return jsonify({
            'success': False,
            'message': 'No configuration provided'
        }), 400
        
    # Configure the provider
    result = auth_manager.configure_oauth_provider(provider_id, config)
    
    return jsonify(result)

@app.route('/settings/oauth', methods=['GET'])
@token_required(required_roles=['admin'])
def oauth_settings():
    """Render the OAuth settings page."""
    providers = auth_manager.get_oauth_providers()
    return render_template('oauth_settings.html', providers=providers.get('providers', {}))

@app.route('/login', methods=['GET'])
def login_page():
    """Render the login page with OAuth options."""
    providers = auth_manager.get_oauth_providers()
    return render_template('login.html', providers=providers.get('providers', {}))

@app.route('/api/user/profile', methods=['GET'])
@token_required()
def get_user_profile():
    """Get the current user's profile."""
    # Get the current user ID from the token
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
        
    user_id = payload.get('user_id')
    
    # Get the user's profile from the database
    user = user_manager.get_user(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Return the user's profile
    return jsonify({
        'success': True,
        'user_id': user_id,
        'username': user.get('username', ''),
        'email': user.get('email', ''),
        'display_name': user.get('display_name', ''),
        'roles': payload.get('roles', [])
    })

@app.route('/api/user/profile', methods=['PUT'])
@token_required()
def update_user_profile():
    """Update the current user's profile."""
    # Get the current user ID from the token
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
        
    user_id = payload.get('user_id')
    
    # Get the profile data from the request
    profile_data = request.json
    
    if not profile_data:
        return jsonify({
            'success': False,
            'message': 'No profile data provided'
        }), 400
    
    # Update the user's profile in the database
    result = user_manager.update_user(user_id, profile_data)
    
    if not result.get('success', False):
        return jsonify(result), 400
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully'
    })

@app.route('/api/user/password', methods=['PUT'])
@token_required()
def change_password():
    """Change the current user's password."""
    # Get the current user ID from the token
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    if not payload:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
        
    user_id = payload.get('user_id')
    
    # Get the password data from the request
    password_data = request.json
    
    if not password_data:
        return jsonify({
            'success': False,
            'message': 'No password data provided'
        }), 400
    
    current_password = password_data.get('current_password')
    new_password = password_data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({
            'success': False,
            'message': 'Current password and new password are required'
        }), 400
    
    # Verify the current password
    if not user_manager.verify_password(user_id, current_password):
        return jsonify({
            'success': False,
            'message': 'Current password is incorrect'
        }), 401
    
    # Update the user's password in the database
    result = user_manager.update_password(user_id, new_password)
    
    if not result.get('success', False):
        return jsonify(result), 400
    
    return jsonify({
        'success': True,
        'message': 'Password changed successfully'
    })

@app.route('/account/profile', methods=['GET'])
@token_required()
def account_profile():
    """Render the user profile page."""
    return render_template('user_profile.html')

@app.route('/auth/oauth/configure/mapping', methods=['POST'])
@token_required(required_roles=['admin'])
def oauth_configure_mapping():
    """Configure OAuth user mapping settings."""
    # Only administrators can configure OAuth mapping
    config = request.json
    
    if not config:
        return jsonify({
            'success': False,
            'message': 'No configuration provided'
        }), 400
        
    # Configure the mapping
    result = auth_manager.oauth_provider.configure_mapping(config)
    
    return jsonify(result)

# Add error logging endpoint

@app.route('/api/log/error', methods=['POST'])
@token_required()
def log_client_error():
    """Log client-side errors for monitoring and debugging."""
    error_data = request.json
    
    if not error_data:
        return jsonify({
            'success': False,
            'message': 'No error data provided'
        }), 400
    
    # Get user information
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = auth_manager.verify_token(token)
    user_id = payload.get('user_id', 'anonymous') if payload else 'anonymous'
    
    # Add timestamp and user info
    error_data.update({
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    })
    
    # Log the error
    app.logger.error(f"Client Error: {error_data.get('code', 'UNKNOWN')} - {error_data.get('message', 'No message')}")
    
    # Store error in database for analysis
    try:
        # Create errors collection if it doesn't exist
        if 'errors' not in db.list_collection_names():
            db.create_collection('errors', capped=True, size=10485760)  # 10MB capped collection
        
        # Insert error into database
        db.errors.insert_one(error_data)
        
        return jsonify({
            'success': True,
            'message': 'Error logged successfully'
        })
    except Exception as e:
        app.logger.error(f"Failed to log client error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to log error'
        }), 500

# Import export manager
from proxmox_nli.services.export.export_manager import ExportManager

# Infrastructure as Code Export Routes
@app.route('/api/export/terraform', methods=['POST'])
@token_required
def export_terraform():
    """Export Proxmox configuration to Terraform format"""
    data = request.get_json()
    output_dir = data.get('output_dir')
    resource_types = data.get('resource_types')
    
    # Initialize export manager
    export_manager = ExportManager(proxmox_api)
    
    # Export to Terraform
    result = export_manager.export_terraform(output_dir, resource_types)
    
    return jsonify(result)

@app.route('/api/export/ansible', methods=['POST'])
@token_required
def export_ansible():
    """Export Proxmox configuration to Ansible playbook format"""
    data = request.get_json()
    output_dir = data.get('output_dir')
    resource_types = data.get('resource_types')
    
    # Initialize export manager
    export_manager = ExportManager(proxmox_api)
    
    # Export to Ansible
    result = export_manager.export_ansible(output_dir, resource_types)
    
    return jsonify(result)

@app.route('/api/export/config', methods=['GET'])
@token_required
def get_export_config():
    """Get export configuration"""
    # Initialize export manager
    export_manager = ExportManager(proxmox_api)
    
    return jsonify({
        "success": True,
        "config": export_manager.config
    })

@app.route('/api/export/config', methods=['PUT'])
@token_required
def update_export_config():
    """Update export configuration"""
    data = request.get_json()
    
    # Initialize export manager
    export_manager = ExportManager(proxmox_api)
    
    # Update configuration
    result = export_manager.update_config(data)
    
    return jsonify(result)

@app.route('/api/export/download/<path:filename>', methods=['GET'])
@token_required
def download_export(filename):
    """Download exported file"""
    # For security, ensure the filename is within the allowed export directories
    if not filename.startswith(('tessa_terraform_', 'tessa_ansible_')):
        return jsonify({"error": "Invalid export filename"}), 403
        
    # Get the full path
    full_path = os.path.join('/tmp', filename)
    
    # Check if the file exists
    if not os.path.exists(full_path):
        return jsonify({"error": "Export file not found"}), 404
        
    # If it's a directory, create a zip file
    if os.path.isdir(full_path):
        import zipfile
        import io
        
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, full_path)
                    zipf.write(file_path, arcname)
                    
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{os.path.basename(full_path)}.zip"
        )
    else:
        # It's a single file
        return send_file(
            full_path,
            as_attachment=True,
            download_name=os.path.basename(full_path)
        )

# Version Control Integration Routes
@app.route('/api/export/vcs/setup', methods=['POST'])
@token_required
def setup_vcs_repository():
    """Set up a version control repository for configuration management"""
    data = request.get_json()
    vcs_type = data.get('vcs_type', 'git')
    repository_url = data.get('repository_url')
    branch = data.get('branch', 'main')
    username = data.get('username')
    password = data.get('password')
    
    if not repository_url:
        return jsonify({"success": False, "message": "Repository URL is required"}), 400
    
    # Initialize VCS integration
    from proxmox_nli.services.export.vcs_integration import VersionControlIntegration
    vcs = VersionControlIntegration()
    
    # Set up repository
    result = vcs.setup_repository(
        vcs_type=vcs_type,
        repository_url=repository_url,
        branch=branch,
        username=username,
        password=password
    )
    
    return jsonify(result)

@app.route('/api/export/vcs/repositories', methods=['GET'])
@token_required
def list_vcs_repositories():
    """List available version control repositories"""
    # Initialize VCS integration
    from proxmox_nli.services.export.vcs_integration import VersionControlIntegration
    vcs = VersionControlIntegration()
    
    # List repositories
    result = vcs.list_repositories()
    
    return jsonify(result)

@app.route('/api/export/vcs/sync', methods=['POST'])
@token_required
def sync_vcs_repository():
    """Sync a version control repository with remote"""
    data = request.get_json()
    repo_name = data.get('repo_name')
    
    # Initialize VCS integration
    from proxmox_nli.services.export.vcs_integration import VersionControlIntegration
    vcs = VersionControlIntegration()
    
    # Sync repository
    result = vcs.sync_repository(repo_name)
    
    return jsonify(result)

@app.route('/api/export/vcs/commit', methods=['POST'])
@token_required
def commit_to_vcs_repository():
    """Commit exported files to a version control repository"""
    data = request.get_json()
    directory = data.get('directory')
    message = data.get('message', 'Update configuration via TESSA export')
    repo_name = data.get('repo_name')
    branch = data.get('branch')
    
    if not directory:
        return jsonify({"success": False, "message": "Directory is required"}), 400
    
    # Initialize VCS integration
    from proxmox_nli.services.export.vcs_integration import VersionControlIntegration
    vcs = VersionControlIntegration()
    
    # Add to repository
    result = vcs.add_to_repository(
        directory=directory,
        message=message,
        repo_name=repo_name,
        branch=branch
    )
    
    return jsonify(result)

@app.route('/export', methods=['GET'])
@token_required
def export_page():
    """Render the Infrastructure as Code export page"""
    return render_template('export_vcs.html')

# Import GPU passthrough assistant
from proxmox_nli.services.gpu_passthrough import GPUPassthroughAssistant

# GPU Passthrough Optimization Routes
@app.route('/api/gpu/detect', methods=['GET'])
@token_required
def detect_gpus():
    """Detect available GPUs on the node"""
    node_name = request.args.get('node')
    
    # Initialize GPU passthrough assistant
    gpu_assistant = GPUPassthroughAssistant(proxmox_api)
    
    # Detect GPUs
    result = gpu_assistant.detect_gpus(node_name)
    
    return jsonify(result)

@app.route('/api/gpu/compatibility', methods=['GET'])
@token_required
def check_gpu_compatibility():
    """Check if the system is compatible with GPU passthrough"""
    node_name = request.args.get('node')
    
    # Initialize GPU passthrough assistant
    gpu_assistant = GPUPassthroughAssistant(proxmox_api)
    
    # Check compatibility
    result = gpu_assistant.check_passthrough_compatibility(node_name)
    
    return jsonify(result)

@app.route('/api/gpu/recommendations', methods=['GET'])
@token_required
def get_gpu_recommendations():
    """Get optimization recommendations for GPU passthrough"""
    node_name = request.args.get('node')
    vm_id = request.args.get('vmid')
    
    # Initialize GPU passthrough assistant
    gpu_assistant = GPUPassthroughAssistant(proxmox_api)
    
    # Get recommendations
    result = gpu_assistant.get_optimization_recommendations(node_name, vm_id)
    
    return jsonify(result)

@app.route('/api/gpu/optimize', methods=['POST'])
@token_required
def apply_gpu_optimizations():
    """Apply selected optimizations to a VM"""
    data = request.get_json()
    node_name = data.get('node')
    vm_id = data.get('vmid')
    optimizations = data.get('optimizations', [])
    
    if not node_name or not vm_id:
        return jsonify({"success": False, "message": "Node name and VM ID are required"}), 400
    
    # Initialize GPU passthrough assistant
    gpu_assistant = GPUPassthroughAssistant(proxmox_api)
    
    # Apply optimizations
    result = gpu_assistant.apply_optimizations(node_name, vm_id, optimizations)
    
    return jsonify(result)

@app.route('/api/gpu/configure', methods=['POST'])
@token_required
def configure_gpu_passthrough():
    """Configure GPU passthrough for a VM"""
    data = request.get_json()
    node_name = data.get('node')
    vm_id = data.get('vmid')
    gpu_pci_id = data.get('gpu_pci_id')
    
    if not node_name or not vm_id or not gpu_pci_id:
        return jsonify({"success": False, "message": "Node name, VM ID, and GPU PCI ID are required"}), 400
    
    # Initialize GPU passthrough assistant
    gpu_assistant = GPUPassthroughAssistant(proxmox_api)
    
    # Configure GPU passthrough
    result = gpu_assistant.configure_gpu_passthrough(node_name, vm_id, gpu_pci_id)
    
    return jsonify(result)

@app.route('/api/gpu/status', methods=['GET'])
@token_required
def get_gpu_passthrough_status():
    """Get the current status of GPU passthrough on the node"""
    node_name = request.args.get('node')
    
    # Initialize GPU passthrough assistant
    gpu_assistant = GPUPassthroughAssistant(proxmox_api)
    
    # Get passthrough status
    result = gpu_assistant.get_passthrough_status(node_name)
    
    return jsonify(result)

@app.route('/gpu-passthrough', methods=['GET'])
@token_required
def gpu_passthrough_page():
    """Render the GPU passthrough optimization assistant page"""
    return render_template('gpu_passthrough.html')

# Import migration manager
from proxmox_nli.services.migration.migration_manager import MigrationManager

# Cross-Platform Migration Routes
@app.route('/api/migration/platforms', methods=['GET'])
@token_required
def get_migration_platforms():
    """Get supported migration platforms"""
    migration_manager = MigrationManager(proxmox_api)
    platforms = migration_manager.get_available_platforms()
    
    return jsonify({
        "success": True,
        "platforms": platforms
    })

@app.route('/api/migration/<platform>/validate', methods=['POST'])
@token_required
def validate_migration_source(platform):
    """Validate source platform credentials"""
    data = request.get_json()
    
    if not data or not data.get('credentials'):
        return jsonify({"success": False, "message": "Credentials required"}), 400
    
    migration_manager = MigrationManager(proxmox_api)
    result = migration_manager.validate_source_credentials(platform, data.get('credentials'))
    
    return jsonify(result)

@app.route('/api/migration/<platform>/analyze', methods=['POST'])
@token_required
def analyze_migration_source(platform):
    """Analyze source environment"""
    data = request.get_json()
    
    if not data or not data.get('credentials'):
        return jsonify({"success": False, "message": "Credentials required"}), 400
    
    migration_manager = MigrationManager(proxmox_api)
    result = migration_manager.analyze_source_environment(platform, data.get('credentials'))
    
    return jsonify(result)

@app.route('/api/migration/plan', methods=['POST'])
@token_required
def create_migration_plan():
    """Create migration plan"""
    data = request.get_json()
    
    if not data or not data.get('migration_id') or not data.get('source_resources') or not data.get('target_node'):
        return jsonify({"success": False, "message": "Migration ID, source resources, and target node required"}), 400
    
    migration_manager = MigrationManager(proxmox_api)
    result = migration_manager.create_migration_plan(
        data.get('migration_id'),
        data.get('source_resources'),
        data.get('target_node')
    )
    
    return jsonify(result)

@app.route('/api/migration/execute', methods=['POST'])
@token_required
def execute_migration():
    """Execute migration"""
    data = request.get_json()
    
    if not data or not data.get('migration_id') or not data.get('migration_plan'):
        return jsonify({"success": False, "message": "Migration ID and plan required"}), 400
    
    migration_manager = MigrationManager(proxmox_api)
    result = migration_manager.execute_migration(
        data.get('migration_id'),
        data.get('migration_plan')
    )
    
    return jsonify(result)

@app.route('/api/migration/status/<migration_id>', methods=['GET'])
@token_required
def get_migration_status(migration_id):
    """Get migration status"""
    migration_manager = MigrationManager(proxmox_api)
    result = migration_manager.get_migration_status(migration_id)
    
    return jsonify(result)

@app.route('/api/migration/list', methods=['GET'])
@token_required
def list_migrations():
    """List all migrations"""
    migration_manager = MigrationManager(proxmox_api)
    migrations = migration_manager.list_migrations()
    
    return jsonify({
        "success": True,
        "migrations": migrations
    })

@app.route('/api/migration/report/<migration_id>', methods=['GET'])
@token_required
def get_migration_report(migration_id):
    """Get migration report"""
    migration_manager = MigrationManager(proxmox_api)
    result = migration_manager.get_migration_report(migration_id)
    
    return jsonify(result)

@app.route('/api/migration/cancel/<migration_id>', methods=['POST'])
@token_required
def cancel_migration(migration_id):
    """Cancel migration"""
    migration_manager = MigrationManager(proxmox_api)
    result = migration_manager.cancel_migration(migration_id)
    
    return jsonify(result)

@app.route('/migration', methods=['GET'])
@token_required
def migration_page():
    """Render the cross-platform migration wizard page"""
    return render_template('migration.html')

# Network Planning Wizard API
@app.route('/api/network-planning/plans', methods=['GET'])
@token_required
def get_network_plans():
    """Get all network plans."""
    try:
        from proxmox_nli.services.network_planning import network_planning_service
        plans = network_planning_service.get_plans()
        return jsonify({"success": True, "plans": plans})
    except Exception as e:
        app.logger.error(f"Error getting network plans: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting network plans: {str(e)}"}), 500

@app.route('/api/network-planning/plans/<plan_id>', methods=['GET'])
@token_required
def get_network_plan(plan_id):
    """Get a network plan by ID."""
    try:
        from proxmox_nli.services.network_planning import network_planning_service
        plan = network_planning_service.get_plan(plan_id)
        if not plan:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        return jsonify({"success": True, "plan": plan})
    except Exception as e:
        app.logger.error(f"Error getting network plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting network plan: {str(e)}"}), 500

@app.route('/api/network-planning/plans', methods=['POST'])
@token_required
def create_network_plan():
    """Create a new network plan."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "message": f"Missing required field: {field}"
                }), 400
        
        name = data.get('name')
        
        from proxmox_nli.services.network_planning import network_planning_service
        plan = network_planning_service.create_plan(name)
        return jsonify({"success": True, "plan": plan})
    except Exception as e:
        app.logger.error(f"Error creating network plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error creating network plan: {str(e)}"}), 500

@app.route('/api/network-planning/plans/<plan_id>', methods=['PUT'])
@token_required
def update_network_plan(plan_id):
    """Update a network plan."""
    try:
        data = request.json
        
        from proxmox_nli.services.network_planning import network_planning_service
        plan = network_planning_service.update_plan(plan_id, data)
        if not plan:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        return jsonify({"success": True, "plan": plan})
    except Exception as e:
        app.logger.error(f"Error updating network plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating network plan: {str(e)}"}), 500

@app.route('/api/network-planning/plans/<plan_id>', methods=['DELETE'])
@token_required
def delete_network_plan(plan_id):
    """Delete a network plan."""
    try:
        from proxmox_nli.services.network_planning import network_planning_service
        success = network_planning_service.delete_plan(plan_id)
        if not success:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Error deleting network plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting network plan: {str(e)}"}), 500

@app.route('/api/network-planning/plans/<plan_id>/validate', methods=['POST'])
@token_required
def validate_network_plan(plan_id):
    """Validate a network plan."""
    try:
        from proxmox_nli.services.network_planning import network_planning_service
        plan = network_planning_service.get_plan(plan_id)
        if not plan:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        
        is_valid, errors = network_planning_service.validate_plan(plan)
        return jsonify({
            "success": True,
            "is_valid": is_valid,
            "errors": errors
        })
    except Exception as e:
        app.logger.error(f"Error validating network plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error validating network plan: {str(e)}"}), 500

@app.route('/api/network-planning/plans/<plan_id>/generate-config', methods=['POST'])
@token_required
def generate_network_config(plan_id):
    """Generate Proxmox network configuration from a network plan."""
    try:
        from proxmox_nli.services.network_planning import network_planning_service
        plan = network_planning_service.get_plan(plan_id)
        if not plan:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        
        config = network_planning_service.generate_proxmox_network_config(plan)
        return jsonify({
            "success": True,
            "config": config
        })
    except Exception as e:
        app.logger.error(f"Error generating network configuration: {str(e)}")
        return jsonify({"success": False, "message": f"Error generating network configuration: {str(e)}"}), 500

# VLAN and Subnet Templates API
@app.route('/api/network-planning/vlan-templates', methods=['GET'])
@token_required
def get_vlan_templates():
    """Get all available VLAN templates."""
    try:
        from proxmox_nli.services.network_planning import network_planning_service
        templates = network_planning_service.get_vlan_templates()
        return jsonify({"success": True, "templates": templates})
    except Exception as e:
        app.logger.error(f"Error getting VLAN templates: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting VLAN templates: {str(e)}"}), 500

@app.route('/api/network-planning/subnet-templates', methods=['GET'])
@token_required
def get_subnet_templates():
    """Get all available subnet templates."""
    try:
        from proxmox_nli.services.network_planning import network_planning_service
        templates = network_planning_service.get_subnet_templates()
        return jsonify({"success": True, "templates": templates})
    except Exception as e:
        app.logger.error(f"Error getting subnet templates: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting subnet templates: {str(e)}"}), 500

@app.route('/api/network-planning/plans/<plan_id>/apply-vlan-template', methods=['POST'])
@token_required
def apply_vlan_template(plan_id):
    """Apply a VLAN template to a network plan."""
    try:
        data = request.json
        if not data or 'template_id' not in data:
            return jsonify({"success": False, "message": "Template ID is required"}), 400
        
        template_id = data['template_id']
        
        from proxmox_nli.services.network_planning import network_planning_service
        plan = network_planning_service.apply_vlan_template(plan_id, template_id)
        if not plan:
            return jsonify({"success": False, "message": f"Failed to apply VLAN template to plan: {plan_id}"}), 404
        
        return jsonify({"success": True, "plan": plan})
    except Exception as e:
        app.logger.error(f"Error applying VLAN template: {str(e)}")
        return jsonify({"success": False, "message": f"Error applying VLAN template: {str(e)}"}), 500

@app.route('/api/network-planning/plans/<plan_id>/apply-subnet-template', methods=['POST'])
@token_required
def apply_subnet_template(plan_id):
    """Apply a subnet template to a network plan."""
    try:
        data = request.json
        if not data or 'template_id' not in data:
            return jsonify({"success": False, "message": "Template ID is required"}), 400
        
        template_id = data['template_id']
        
        from proxmox_nli.services.network_planning import network_planning_service
        plan = network_planning_service.apply_subnet_template(plan_id, template_id)
        if not plan:
            return jsonify({"success": False, "message": f"Failed to apply subnet template to plan: {plan_id}"}), 404
        
        return jsonify({"success": True, "plan": plan})
    except Exception as e:
        app.logger.error(f"Error applying subnet template: {str(e)}")
        return jsonify({"success": False, "message": f"Error applying subnet template: {str(e)}"}), 500

# Network Planning Wizard UI routes
@app.route('/network-planning', methods=['GET'])
@token_required
def network_planning_page():
    """Render the network planning page."""
    return render_template('network_planning.html')

@app.route('/network-planning/designer/<plan_id>', methods=['GET'])
@token_required
def network_designer_page(plan_id):
    """Render the network designer page for a specific plan."""
    return render_template('network_designer.html', plan_id=plan_id)

# Resource Planning API
@app.route('/api/resource-planning/calculate', methods=['POST'])
@token_required
def calculate_resources():
    """Calculate required resources based on a VM plan."""
    try:
        data = request.json
        if not data or 'vm_plan' not in data:
            return jsonify({"success": False, "message": "VM plan is required"}), 400
        
        vm_plan = data['vm_plan']
        
        from proxmox_nli.services.resource_planning import resource_planning_service
        result = resource_planning_service.calculate_resources(vm_plan)
        
        return jsonify({
            "success": True,
            "resources": result
        })
    except Exception as e:
        app.logger.error(f"Error calculating resources: {str(e)}")
        return jsonify({"success": False, "message": f"Error calculating resources: {str(e)}"}), 500

@app.route('/api/resource-planning/forecast', methods=['POST'])
@token_required
def forecast_disk_usage():
    """Forecast disk usage over time based on VM plan."""
    try:
        data = request.json
        if not data or 'vm_plan' not in data:
            return jsonify({"success": False, "message": "VM plan is required"}), 400
        
        vm_plan = data['vm_plan']
        months = data.get('months', 12)
        
        from proxmox_nli.services.resource_planning import resource_planning_service
        result = resource_planning_service.forecast_disk_usage(vm_plan, months)
        
        return jsonify({
            "success": True,
            "forecast": result
        })
    except Exception as e:
        app.logger.error(f"Error forecasting disk usage: {str(e)}")
        return jsonify({"success": False, "message": f"Error forecasting disk usage: {str(e)}"}), 500

@app.route('/api/resource-planning/recommend', methods=['POST'])
@token_required
def recommend_hardware():
    """Recommend hardware based on calculated resource requirements."""
    try:
        data = request.json
        if not data or 'requirements' not in data:
            return jsonify({"success": False, "message": "Resource requirements are required"}), 400
        
        requirements = data['requirements']
        
        from proxmox_nli.services.resource_planning import resource_planning_service
        result = resource_planning_service.recommend_hardware(requirements)
        
        return jsonify({
            "success": True,
            "recommendations": result
        })
    except Exception as e:
        app.logger.error(f"Error recommending hardware: {str(e)}")
        return jsonify({"success": False, "message": f"Error recommending hardware: {str(e)}"}), 500

@app.route('/api/resource-planning/plans', methods=['GET'])
@token_required
def get_resource_plans():
    """Get all resource plans."""
    try:
        from proxmox_nli.services.resource_planning import resource_planning_service
        plans = resource_planning_service.get_resource_plans()
        
        return jsonify({
            "success": True,
            "plans": plans
        })
    except Exception as e:
        app.logger.error(f"Error getting resource plans: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting resource plans: {str(e)}"}), 500

@app.route('/api/resource-planning/plans/<plan_id>', methods=['GET'])
@token_required
def get_resource_plan(plan_id):
    """Get a resource plan by ID."""
    try:
        from proxmox_nli.services.resource_planning import resource_planning_service
        plan = resource_planning_service.get_resource_plan(plan_id)
        
        if not plan:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        
        return jsonify({
            "success": True,
            "plan": plan
        })
    except Exception as e:
        app.logger.error(f"Error getting resource plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting resource plan: {str(e)}"}), 500

@app.route('/api/resource-planning/plans', methods=['POST'])
@token_required
def create_resource_plan():
    """Create a new resource plan."""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Plan data is required"}), 400
        
        from proxmox_nli.services.resource_planning import resource_planning_service
        plan_id = resource_planning_service.save_resource_plan(data)
        
        return jsonify({
            "success": True,
            "plan_id": plan_id
        })
    except Exception as e:
        app.logger.error(f"Error creating resource plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error creating resource plan: {str(e)}"}), 500

@app.route('/api/resource-planning/plans/<plan_id>', methods=['PUT'])
@token_required
def update_resource_plan(plan_id):
    """Update a resource plan."""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Plan data is required"}), 400
        
        # Ensure plan ID matches
        data['id'] = plan_id
        
        from proxmox_nli.services.resource_planning import resource_planning_service
        plan_id = resource_planning_service.save_resource_plan(data)
        
        return jsonify({
            "success": True,
            "plan_id": plan_id
        })
    except Exception as e:
        app.logger.error(f"Error updating resource plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating resource plan: {str(e)}"}), 500

@app.route('/api/resource-planning/plans/<plan_id>', methods=['DELETE'])
@token_required
def delete_resource_plan(plan_id):
    """Delete a resource plan."""
    try:
        from proxmox_nli.services.resource_planning import resource_planning_service
        success = resource_planning_service.delete_resource_plan(plan_id)
        
        if not success:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        
        return jsonify({
            "success": True
        })
    except Exception as e:
        app.logger.error(f"Error deleting resource plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting resource plan: {str(e)}"}), 500

@app.route('/api/resource-planning/vm-profiles', methods=['GET'])
@token_required
def get_vm_profiles():
    """Get all VM profiles."""
    try:
        from proxmox_nli.services.resource_planning import resource_planning_service
        profiles = resource_planning_service.get_vm_profiles()
        
        return jsonify({
            "success": True,
            "profiles": profiles
        })
    except Exception as e:
        app.logger.error(f"Error getting VM profiles: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting VM profiles: {str(e)}"}), 500

@app.route('/api/resource-planning/hardware', methods=['GET'])
@token_required
def get_hardware_database():
    """Get the hardware database."""
    try:
        from proxmox_nli.services.resource_planning import resource_planning_service
        hardware = resource_planning_service.get_hardware_database()
        
        return jsonify({
            "success": True,
            "hardware": hardware
        })
    except Exception as e:
        app.logger.error(f"Error getting hardware database: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting hardware database: {str(e)}"}), 500

# Resource Planning UI routes
@app.route('/resource-planning', methods=['GET'])
@token_required
def resource_planning_page():
    """Render the resource planning page."""
    return render_template('resource_planning.html')

@app.route('/resource-planning/calculator', methods=['GET'])
@token_required
def resource_calculator_page():
    """Render the resource calculator page."""
    return render_template('resource_calculator.html')

@app.route('/resource-planning/forecasting', methods=['GET'])
@token_required
def disk_forecasting_page():
    """Render the disk space forecasting page."""
    return render_template('disk_forecasting.html')

@app.route('/resource-planning/recommendations', methods=['GET'])
@token_required
def hardware_recommendations_page():
    """Render the hardware recommendations page."""
    return render_template('hardware_recommendations.html')

# Voice Authentication API
@app.route('/api/voice-auth/register', methods=['POST'])
@token_required
def register_voice():
    """Register a user's voice for authentication."""
    try:
        data = request.json
        if not data or 'user_id' not in data or 'audio_samples' not in data:
            return jsonify({"success": False, "message": "User ID and audio samples are required"}), 400
        
        user_id = data['user_id']
        audio_samples = data['audio_samples']
        phrase = data.get('phrase')
        
        if len(audio_samples) < 3:
            return jsonify({"success": False, "message": "At least 3 audio samples are required"}), 400
        
        from proxmox_nli.core.voice_handler import voice_handler
        success = voice_handler.register_voice(user_id, audio_samples, phrase)
        
        if success:
            return jsonify({"success": True, "message": "Voice registered successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to register voice"}), 500
    except Exception as e:
        app.logger.error(f"Error registering voice: {str(e)}")
        return jsonify({"success": False, "message": f"Error registering voice: {str(e)}"}), 500

@app.route('/api/voice-auth/authenticate', methods=['POST'])
@token_required
def authenticate_voice():
    """Authenticate a user by their voice."""
    try:
        data = request.json
        if not data or 'audio' not in data:
            return jsonify({"success": False, "message": "Audio data is required"}), 400
        
        audio = data['audio']
        user_id = data.get('user_id')  # Optional: specific user to authenticate against
        threshold = data.get('threshold', 0.7)
        require_passphrase = data.get('require_passphrase', False)
        spoken_text = data.get('text')  # Optional: recognized text for passphrase verification
        
        from proxmox_nli.core.voice_handler import voice_handler
        success, authenticated_user, confidence = voice_handler.authenticate_voice(
            audio, threshold, user_id, require_passphrase, spoken_text
        )
        
        if success:
            return jsonify({
                "success": True, 
                "authenticated": True,
                "user_id": authenticated_user,
                "confidence": confidence
            })
        else:
            return jsonify({
                "success": True,
                "authenticated": False,
                "confidence": confidence,
                "message": "Voice authentication failed"
            })
    except Exception as e:
        app.logger.error(f"Error authenticating voice: {str(e)}")
        return jsonify({"success": False, "message": f"Error authenticating voice: {str(e)}"}), 500

@app.route('/api/voice-auth/update', methods=['POST'])
@token_required
def update_voice_signature():
    """Update a user's voice signature with a new sample."""
    try:
        data = request.json
        if not data or 'user_id' not in data or 'audio' not in data:
            return jsonify({"success": False, "message": "User ID and audio data are required"}), 400
        
        user_id = data['user_id']
        audio = data['audio']
        
        from proxmox_nli.core.voice_handler import voice_handler
        success = voice_handler.update_voice_signature(user_id, audio)
        
        if success:
            return jsonify({"success": True, "message": "Voice signature updated successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to update voice signature"}), 500
    except Exception as e:
        app.logger.error(f"Error updating voice signature: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating voice signature: {str(e)}"}), 500

@app.route('/api/voice-auth/delete/<user_id>', methods=['DELETE'])
@token_required
def delete_voice_signature(user_id):
    """Delete a user's voice signature."""
    try:
        from proxmox_nli.core.voice_handler import voice_handler
        success = voice_handler.delete_voice_signature(user_id)
        
        if success:
            return jsonify({"success": True, "message": "Voice signature deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to delete voice signature"}), 500
    except Exception as e:
        app.logger.error(f"Error deleting voice signature: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting voice signature: {str(e)}"}), 500

@app.route('/api/voice-auth/users', methods=['GET'])
@token_required
def list_voice_users():
    """List all users with registered voice signatures."""
    try:
        from proxmox_nli.core.voice_handler import voice_handler
        users = voice_handler.list_voice_users()
        
        return jsonify({"success": True, "users": users})
    except Exception as e:
        app.logger.error(f"Error listing voice users: {str(e)}")
        return jsonify({"success": False, "message": f"Error listing voice users: {str(e)}"}), 500

@app.route('/api/voice-auth/passphrase', methods=['POST'])
@token_required
def set_user_passphrase():
    """Set or update a user's authentication passphrase."""
    try:
        data = request.json
        if not data or 'user_id' not in data or 'passphrase' not in data:
            return jsonify({"success": False, "message": "User ID and passphrase are required"}), 400
        
        user_id = data['user_id']
        passphrase = data['passphrase']
        
        from proxmox_nli.core.voice_handler import voice_handler
        success = voice_handler.set_user_passphrase(user_id, passphrase)
        
        if success:
            return jsonify({"success": True, "message": "Passphrase set successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to set passphrase"}), 500
    except Exception as e:
        app.logger.error(f"Error setting passphrase: {str(e)}")
        return jsonify({"success": False, "message": f"Error setting passphrase: {str(e)}"}), 500

# Voice Authentication UI routes
@app.route('/voice-auth', methods=['GET'])
@token_required
def voice_auth_page():
    """Render the voice authentication page."""
    return render_template('voice_auth.html')

@app.route('/voice-auth/register', methods=['GET'])
@token_required
def voice_auth_register_page():
    """Render the voice registration page."""
    return render_template('voice_auth_register.html')

@app.route('/voice-auth/manage', methods=['GET'])
@token_required
def voice_auth_manage_page():
    """Render the voice authentication management page."""
    return render_template('voice_auth_manage.html')