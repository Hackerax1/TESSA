#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, url_for
from flask_socketio import SocketIO, emit
import os
from proxmox_nli.core import ProxmoxNLI
from proxmox_nli.core.voice_handler import VoiceHandler
from proxmox_nli.core.auth import AuthManager
from dotenv import load_dotenv
import logging
import threading
import time
from functools import wraps
import ssl

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static')
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize the ProxmoxNLI instance (will be properly configured on app start)
proxmox_nli = None
voice_handler = VoiceHandler()
auth_manager = AuthManager()

def token_required(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token or not token.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid token'}), 401
            
            token = token.split('Bearer ')[1]
            if not auth_manager.verify_token(token):
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            if roles and not auth_manager.check_permission(token, roles):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def monitor_vm_status():
    """Background task to monitor VM status and emit updates"""
    while True:
        try:
            if proxmox_nli and proxmox_nli.api.authenticate():
                # Get VM status
                result = proxmox_nli.commands.list_vms()
                if result['success']:
                    socketio.emit('vm_status_update', {'vms': result['vms']})
                else:
                    logger.error(f"Failed to get VM status: {result.get('message', 'Unknown error')}")
                    socketio.emit('vm_status_update', {'error': result.get('message', 'Failed to get VM status')})
                    
                # Get cluster status
                cluster_status = proxmox_nli.commands.get_cluster_status()
                if cluster_status['success']:
                    socketio.emit('cluster_status_update', cluster_status)
                else:
                    logger.error(f"Failed to get cluster status: {cluster_status.get('message', 'Unknown error')}")
                    socketio.emit('cluster_status_update', {'error': cluster_status.get('message', 'Failed to get cluster status')})
            else:
                logger.error("ProxmoxNLI not initialized or authentication failed")
                socketio.emit('vm_status_update', {'error': 'System not ready'})
                socketio.emit('cluster_status_update', {'error': 'System not ready'})
        except Exception as e:
            logger.error(f"Error in status monitor: {str(e)}")
            socketio.emit('vm_status_update', {'error': 'System error occurred'})
            socketio.emit('cluster_status_update', {'error': 'System error occurred'})
        time.sleep(5)  # Update every 5 seconds

@app.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400
        
    # Here you would validate credentials against your user database
    # For now, we'll use a simple check against environment variables
    if username == os.getenv('ADMIN_USER') and password == os.getenv('ADMIN_PASSWORD'):
        token = auth_manager.create_token(username, ['admin'])
        return jsonify({'token': token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/auth/refresh', methods=['POST'])
@token_required()
def refresh_token():
    """Refresh an existing valid token"""
    token = request.headers.get('Authorization').split('Bearer ')[1]
    new_token = auth_manager.refresh_token(token)
    if new_token:
        return jsonify({'token': new_token})
    return jsonify({'error': 'Could not refresh token'}), 401

@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
@token_required(['user', 'admin'])
def process_query():
    """Process a natural language query"""
    query = request.json.get('query', '').strip()
    if not query:
        logger.error('No query provided')
        return jsonify({'error': 'No query provided'})
    
    # Get user information from request
    user = request.json.get('user', 'anonymous')
    ip_address = request.remote_addr
    
    # Handle command confirmation
    if proxmox_nli.pending_command:
        if query.lower() in ['y', 'yes']:
            response = proxmox_nli.confirm_command(True)
        elif query.lower() in ['n', 'no']:
            response = proxmox_nli.confirm_command(False)
        else:
            return jsonify({'response': "Please respond with 'yes' or 'no'"})
        return jsonify({'response': response})
    
    # Normal command processing
    response = proxmox_nli.process_query(query, user=user, source='web', ip_address=ip_address)
    return jsonify({'response': response})

# User preferences endpoints
@app.route('/user-preferences/<user_id>', methods=['GET'])
@token_required(['user', 'admin'])
def get_user_preferences(user_id):
    """Get all preferences for a user"""
    if not proxmox_nli:
        return jsonify({'error': 'System not initialized'}), 500
    
    result = proxmox_nli.get_user_preferences(user_id)
    return jsonify(result)

@app.route('/user-preferences/<user_id>', methods=['POST'])
@token_required(['user', 'admin'])
def set_user_preference(user_id):
    """Set a user preference"""
    if not proxmox_nli:
        return jsonify({'error': 'System not initialized'}), 500
        
    key = request.json.get('key')
    value = request.json.get('value')
    
    if not key:
        return jsonify({'error': 'Preference key is required'}), 400
        
    result = proxmox_nli.set_user_preference(user_id, key, value)
    return jsonify(result)

@app.route('/user-statistics/<user_id>', methods=['GET'])
def get_user_statistics(user_id):
    """Get usage statistics for a user"""
    if not proxmox_nli:
        return jsonify({'error': 'System not initialized'}), 500
        
    result = proxmox_nli.get_user_statistics(user_id)
    return jsonify(result)

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    text = request.json.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'})
    
    result = voice_handler.text_to_speech(text)
    if result['success']:
        return jsonify(result)
    else:
        return jsonify({'error': result['error']}), 400

@app.route('/stt', methods=['POST'])
def speech_to_text():
    """Convert speech to text"""
    audio_data = request.json.get('audio')
    if not audio_data:
        return jsonify({'error': 'No audio data provided'})
    
    result = voice_handler.speech_to_text(audio_data)
    if result['success']:
        return jsonify(result)
    else:
        return jsonify({'error': result['error']}), 400

@app.route('/backup', methods=['POST'])
def backup_vm():
    """Backup a VM"""
    vm_id = request.json.get('vm_id')
    backup_dir = request.json.get('backup_dir')
    if not vm_id or not backup_dir:
        return jsonify({'error': 'VM ID and backup directory are required'}), 400
    try:
        backup_file = proxmox_nli.backup_vm(vm_id, backup_dir)
        return jsonify({'backup_file': backup_file})
    except Exception as e:
        logger.error(f'Error backing up VM: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/restore', methods=['POST'])
def restore_vm():
    """Restore a VM"""
    backup_file = request.json.get('backup_file')
    vm_id = request.json.get('vm_id')
    if not backup_file or not vm_id:
        return jsonify({'error': 'Backup file and VM ID are required'}), 400
    try:
        proxmox_nli.restore_vm(backup_file, vm_id)
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f'Error restoring VM: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    """Get recent audit logs"""
    limit = request.args.get('limit', 100, type=int)
    logs = proxmox_nli.get_recent_activity(limit)
    return jsonify({'logs': logs})

@app.route('/user-activity/<user>', methods=['GET'])
def get_user_activity(user):
    """Get activity for a specific user"""
    limit = request.args.get('limit', 100, type=int)
    logs = proxmox_nli.get_user_activity(user, limit)
    return jsonify({'logs': logs})

@app.route('/failed-commands', methods=['GET'])
def get_failed_commands():
    """Get recent failed commands"""
    limit = request.args.get('limit', 100, type=int)
    logs = proxmox_nli.get_failed_commands(limit)
    return jsonify({'logs': logs})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

def start_app(host, user, password, realm='pam', verify_ssl=False, debug=False):
    """Start the Flask application with the given Proxmox credentials"""
    global proxmox_nli
    
    # Initialize ProxmoxNLI with the provided credentials
    proxmox_nli = ProxmoxNLI(host, user, password, realm, verify_ssl)
    
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Start the background monitoring thread
    monitor_thread = threading.Thread(target=monitor_vm_status, daemon=True)
    monitor_thread.start()
    
    # Configure SSL if enabled
    ssl_context = None
    if os.getenv('ENABLE_SSL', 'false').lower() == 'true':
        cert_path = os.getenv('SSL_CERT_PATH')
        key_path = os.getenv('SSL_KEY_PATH')
        
        if not cert_path or not key_path:
            # Generate self-signed certificate if paths not provided
            from scripts.generate_cert import generate_self_signed_cert
            cert_path, key_path = generate_self_signed_cert()
        
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(cert_path, key_path)
        logger.info("SSL/TLS encryption enabled")
    
    # Start the Flask application with SocketIO
    port = int(os.getenv('API_PORT', 5000))
    socketio.run(app, 
                host='0.0.0.0', 
                port=port, 
                debug=debug,
                ssl_context=ssl_context)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Proxmox NLI Web Server')
    parser.add_argument('--host', required=True, help='Proxmox host')
    parser.add_argument('--user', required=True, help='Proxmox user')
    parser.add_argument('--password', required=True, help='Proxmox password')
    parser.add_argument('--realm', default='pam', help='Proxmox realm')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificate')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    start_app(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl,
        debug=args.debug
    )