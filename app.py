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

# ... (rest of the code remains the same)

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