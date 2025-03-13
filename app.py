#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, url_for
from flask_socketio import SocketIO, emit
import os
from proxmox_nli.core import ProxmoxNLI
from proxmox_nli.core.voice_handler import VoiceHandler, VoiceProfile
from proxmox_nli.services.goal_mapper import GoalMapper
from proxmox_nli.core.security.auth_manager import AuthManager
from functools import wraps
from dotenv import load_dotenv
import logging
import threading
import time
import json
import re
import subprocess
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
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize the ProxmoxNLI instance (will be properly configured on app start)
proxmox_nli = None
voice_handler = VoiceHandler()
status_monitor_thread = None
resource_monitor_thread = None
auth_manager = AuthManager()

# Store resource history for optimization analysis
vm_resource_history = defaultdict(lambda: {"cpu": [], "memory": [], "disk_io": [], "network": [], "timestamps": []})
resource_history_window = 24 * 60 * 60  # 24 hours in seconds

# Optimization thresholds
CPU_UNDERUTILIZED_THRESHOLD = 10  # percentage
CPU_OVERUTILIZED_THRESHOLD = 80  # percentage
MEMORY_UNDERUTILIZED_THRESHOLD = 20  # percentage
MEMORY_OVERUTILIZED_THRESHOLD = 85  # percentage

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

def monitor_vm_status():
    """Background task to monitor VM status and emit updates"""
    while True:
        try:
            if proxmox_nli:
                # Get VM list and status
                result = proxmox_nli.commands.list_vms()
                if result['success']:
                    socketio.emit('vm_status_update', {'vms': result['vms']})
                else:
                    logger.error(f"Failed to get VM status: {result.get('message', 'Unknown error')}")
                    socketio.emit('vm_status_update', {'error': result.get('message', 'Failed to get VM status')})
                    
                # Get cluster status
                cluster_status = proxmox_nli.commands.get_cluster_status()
                if cluster_status['success']:
                    socketio.emit('cluster_status_update', {'status': cluster_status['nodes']})
        except Exception as e:
            logger.error(f"Error in status monitor: {str(e)}")
            socketio.emit('vm_status_update', {'error': 'System error occurred'})
            socketio.emit('cluster_status_update', {'error': 'System error occurred'})
        time.sleep(5)  # Update every 5 seconds

def monitor_vm_resources():
    """Background task to monitor VM resource usage and store historical data"""
    while True:
        try:
            if proxmox_nli:
                # Get detailed resource usage for all VMs
                vms = proxmox_nli.commands.list_vms()
                if vms.get('success'):
                    current_time = datetime.now()
                    for vm in vms.get('vms', []):
                        vm_id = vm.get('vmid')
                        if not vm_id:
                            continue
                            
                        # Get detailed resource usage for this VM
                        resource_data = proxmox_nli.commands.get_vm_resources(vm_id)
                        if resource_data.get('success'):
                            # Clean up old data (older than resource_history_window)
                            if vm_resource_history[vm_id]['timestamps']:
                                cutoff_time = current_time - timedelta(seconds=resource_history_window)
                                cutoff_timestamp = cutoff_time.timestamp()
                                
                                # Find the index of the oldest data point to keep
                                idx = 0
                                for ts in vm_resource_history[vm_id]['timestamps']:
                                    if ts >= cutoff_timestamp:
                                        break
                                    idx += 1
                                
                                if idx > 0:
                                    # Remove old data points
                                    vm_resource_history[vm_id]['cpu'] = vm_resource_history[vm_id]['cpu'][idx:]
                                    vm_resource_history[vm_id]['memory'] = vm_resource_history[vm_id]['memory'][idx:]
                                    vm_resource_history[vm_id]['disk_io'] = vm_resource_history[vm_id]['disk_io'][idx:]
                                    vm_resource_history[vm_id]['network'] = vm_resource_history[vm_id]['network'][idx:]
                                    vm_resource_history[vm_id]['timestamps'] = vm_resource_history[vm_id]['timestamps'][idx:]
                            
                            # Store current resource data
                            resources = resource_data.get('resources', {})
                            vm_resource_history[vm_id]['cpu'].append(resources.get('cpu_usage', 0))
                            vm_resource_history[vm_id]['memory'].append(resources.get('memory_usage', 0))
                            vm_resource_history[vm_id]['disk_io'].append(resources.get('disk_io', 0))
                            vm_resource_history[vm_id]['network'].append(resources.get('network_io', 0))
                            vm_resource_history[vm_id]['timestamps'].append(current_time.timestamp())
                            
                # Generate optimization recommendations periodically
                generate_optimization_recommendations()
        except Exception as e:
            logger.error(f"Error in resource monitor: {str(e)}")
        
        time.sleep(60)  # Update every 60 seconds

def generate_optimization_recommendations():
    """Generate VM optimization recommendations based on resource usage patterns"""
    try:
        recommendations = []
        
        for vm_id, resources in vm_resource_history.items():
            if not resources['cpu'] or len(resources['cpu']) < 10:  # Need enough data points
                continue
                
            # Calculate average resource utilization
            avg_cpu = sum(resources['cpu']) / len(resources['cpu'])
            avg_memory = sum(resources['memory']) / len(resources['memory'])
            
            vm_info = None
            # Get VM configuration
            vm_list = proxmox_nli.commands.list_vms().get('vms', [])
            for vm in vm_list:
                if vm.get('vmid') == vm_id:
                    vm_info = vm
                    break
            
            if not vm_info:
                continue
                
            vm_name = vm_info.get('name', f'VM {vm_id}')
            current_cores = vm_info.get('cores', 0)
            current_memory = vm_info.get('memory', 0) / 1024  # Convert to GB
            
            # CPU optimization recommendations
            if avg_cpu < CPU_UNDERUTILIZED_THRESHOLD and current_cores > 1:
                # VM is using less than threshold% CPU on average, can reduce cores
                recommended_cores = max(1, current_cores - 1)
                recommendations.append({
                    'vm_id': vm_id,
                    'vm_name': vm_name,
                    'resource': 'cpu',
                    'current': current_cores,
                    'recommended': recommended_cores,
                    'type': 'reduce',
                    'reason': f'CPU utilization is consistently below {CPU_UNDERUTILIZED_THRESHOLD}% (avg: {avg_cpu:.1f}%)',
                    'savings': 'Reducing CPU cores will free up host resources for other VMs'
                })
            elif avg_cpu > CPU_OVERUTILIZED_THRESHOLD:
                # VM is using more than threshold% CPU on average, might need more cores
                recommended_cores = current_cores + 1
                recommendations.append({
                    'vm_id': vm_id,
                    'vm_name': vm_name,
                    'resource': 'cpu',
                    'current': current_cores,
                    'recommended': recommended_cores,
                    'type': 'increase',
                    'reason': f'CPU utilization is consistently above {CPU_OVERUTILIZED_THRESHOLD}% (avg: {avg_cpu:.1f}%)',
                    'savings': 'Increasing CPU cores will improve VM performance'
                })
            
            # Memory optimization recommendations
            if avg_memory < MEMORY_UNDERUTILIZED_THRESHOLD and current_memory > 1:
                # VM is using less than threshold% memory on average, can reduce memory
                recommended_memory = max(1, int(current_memory * 0.75))  # Reduce by 25%
                recommendations.append({
                    'vm_id': vm_id,
                    'vm_name': vm_name,
                    'resource': 'memory',
                    'current': current_memory,
                    'recommended': recommended_memory,
                    'type': 'reduce',
                    'reason': f'Memory utilization is consistently below {MEMORY_UNDERUTILIZED_THRESHOLD}% (avg: {avg_memory:.1f}%)',
                    'savings': 'Reducing memory will free up host resources for other VMs'
                })
            elif avg_memory > MEMORY_OVERUTILIZED_THRESHOLD:
                # VM is using more than threshold% memory on average, might need more memory
                recommended_memory = int(current_memory * 1.25)  # Increase by 25%
                recommendations.append({
                    'vm_id': vm_id,
                    'vm_name': vm_name,
                    'resource': 'memory',
                    'current': current_memory,
                    'recommended': recommended_memory,
                    'type': 'increase',
                    'reason': f'Memory utilization is consistently above {MEMORY_OVERUTILIZED_THRESHOLD}% (avg: {avg_memory:.1f}%)',
                    'savings': 'Increasing memory will improve VM performance and prevent swapping'
                })
                
        # Store recommendations for API endpoints to access
        app.config['optimization_recommendations'] = recommendations
        
        # Emit new recommendations via websocket
        socketio.emit('optimization_recommendations', {'recommendations': recommendations})
        
    except Exception as e:
        logger.error(f"Error generating optimization recommendations: {str(e)}")

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

@app.route('/initial-status')
def get_initial_status():
    """Get initial VM and cluster status"""
    try:
        vm_result = proxmox_nli.commands.list_vms()
        cluster_result = proxmox_nli.commands.get_cluster_status()
        return jsonify({
            'success': True,
            'vm_status': vm_result.get('vms', []) if vm_result.get('success') else [],
            'cluster_status': {
                'nodes': cluster_result.get('nodes', []) if cluster_result.get('success') else []
            }
        })
    except Exception as e:
        logger.error(f"Error getting initial status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

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
    """Convert text to speech with optional voice profile and personality settings"""
    text = request.json.get('text', '')
    profile_name = request.json.get('profile', 'tessa_default')
    add_personality = request.json.get('add_personality', True)
    personality_level = request.json.get('personality_level', 0.2)
    
    if not text:
        return jsonify({'error': 'No text provided'})
    
    # Set active profile if specified
    if profile_name and profile_name in voice_handler.profiles:
        voice_handler.set_active_profile(profile_name)
    
    # Process text with specified personality settings
    result = voice_handler.text_to_speech(text, add_personality=add_personality)
    
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

# New endpoint: Voice profiles list
@app.route('/voice-profiles', methods=['GET'])
def get_voice_profiles():
    """Get available voice profiles"""
    try:
        profiles = voice_handler.list_profiles()
        active_profile = voice_handler.active_profile_name
        return jsonify({
            'success': True,
            'profiles': profiles,
            'active': active_profile
        })
    except Exception as e:
        logger.error(f'Error getting voice profiles: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# New endpoint: Get specific voice profile
@app.route('/voice-profile/<profile_name>', methods=['GET'])
def get_voice_profile(profile_name):
    """Get details for a specific voice profile"""
    try:
        if profile_name in voice_handler.profiles:
            profile = voice_handler.profiles[profile_name]
            return jsonify({
                'success': True,
                'profile': profile.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Voice profile "{profile_name}" not found'
            }), 404
    except Exception as e:
        logger.error(f'Error getting voice profile: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# New endpoint: Save voice settings
@app.route('/voice-settings', methods=['POST'])
def save_voice_settings():
    """Save voice settings to a profile"""
    try:
        profile_name = request.json.get('profile_name')
        accent = request.json.get('accent')  # TLD value
        slow = request.json.get('slow')  # Boolean
        tone_style = request.json.get('tone_style')
        
        if not profile_name:
            return jsonify({'success': False, 'error': 'Profile name is required'}), 400
        
        # Get existing profile or create new one
        if profile_name in voice_handler.profiles:
            profile = voice_handler.profiles[profile_name]
        else:
            profile = VoiceProfile(
                name=profile_name.replace('_', ' ').title(),
                lang="en"
            )
        
        # Update profile properties with new values if provided
        if accent is not None:
            profile.tld = accent
            
        if slow is not None:
            profile.slow = slow
            
        if tone_style is not None:
            profile.tone_style = tone_style
        
        # Save the profile
        voice_handler.save_profile(profile_name, profile)
        voice_handler.set_active_profile(profile_name)
        
        return jsonify({
            'success': True,
            'profile': profile_name
        })
    except Exception as e:
        logger.error(f'Error saving voice settings: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# New endpoint: Test voice with current settings
@app.route('/test-voice', methods=['POST'])
def test_voice():
    """Test voice with specified settings"""
    try:
        text = request.json.get('text')
        profile_name = request.json.get('profile_name')
        accent = request.json.get('accent')
        slow = request.json.get('slow')
        tone_style = request.json.get('tone_style')
        personality_enabled = request.json.get('personality_enabled', True)
        personality_level = request.json.get('personality_level', 0.2)
        
        if not text:
            return jsonify({'success': False, 'error': 'Text is required'}), 400
            
        # Create a temporary profile for testing
        temp_profile = VoiceProfile(
            name="Test Profile",
            lang="en",
            tld=accent or "com",
            slow=slow if slow is not None else False,
            tone_style=tone_style or "friendly"
        )
        
        # Save temporary profile
        voice_handler.save_profile("_temp_test_profile", temp_profile)
        voice_handler.set_active_profile("_temp_test_profile")
        
        # Generate speech with temporary profile
        result = voice_handler.text_to_speech(text, add_personality=personality_enabled)
        
        # Clean up temporary profile
        if "_temp_test_profile" in voice_handler.profiles:
            del voice_handler.profiles["_temp_test_profile"]
            
        # Restore previous profile
        if profile_name in voice_handler.profiles:
            voice_handler.set_active_profile(profile_name)
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'Error testing voice: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# New endpoint: Adapt voice to user experience level
@app.route('/adapt-voice', methods=['POST'])
def adapt_voice_to_experience():
    """Adapt TESSA's voice to user experience level"""
    try:
        experience_level = request.json.get('experience_level', 0.5)  # 0.0 to 1.0
        
        # Validate experience level
        if not isinstance(experience_level, (int, float)) or experience_level < 0 or experience_level > 1:
            return jsonify({
                'success': False,
                'error': 'Experience level must be a number between 0 and 1'
            }), 400
            
        # Call the voice handler to adapt
        voice_handler.adapt_to_user_experience(experience_level)
        
        # Return the new active profile
        return jsonify({
            'success': True,
            'profile': voice_handler.active_profile_name,
            'profile_details': voice_handler.get_active_profile().to_dict()
        })
        
    except Exception as e:
        logger.error(f'Error adapting voice: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

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

@app.route('/deploy', methods=['POST'])
def deploy_services():
    """Deploy services based on user goals and resources"""
    data = request.json
    goals = data.get('goals', [])
    other_goals = data.get('otherGoals', '')
    resources = data.get('resources', {})
    services = data.get('services', [])

    try:
        # Use the GoalMapper to deploy services based on goals and resources
        goal_mapper = GoalMapper()
        
        # Log the deployment request
        logger.info(f"Deploying services with goals: {goals}, other goals: {other_goals}, resources: {resources}, services: {services}")
        
        # Here we would call proxmox_nli to actually deploy the services
        # For now, we'll just return success
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deploying services: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/recommend-services', methods=['POST'])
def recommend_services():
    """Recommend services based on user goals"""
    data = request.json
    goals = data.get('goals', [])
    cloud_services = data.get('cloudServices', [])
    
    try:
        goal_mapper = GoalMapper()
        
        # Get recommendations based on goals
        goal_recommendations = goal_mapper.get_recommended_services(goals)
        
        # Get recommendations based on cloud services to replace
        cloud_recommendations = {}
        if cloud_services:
            cloud_recommendations = goal_mapper.get_cloud_replacement_services(cloud_services)
            
        # Merge recommendations, prioritizing cloud service replacements
        recommendations = {**goal_recommendations, **cloud_recommendations}
        
        # Convert to list format for the frontend
        result = []
        for service_id, service_info in recommendations.items():
            result.append({
                'id': service_id,
                'name': service_info.get('name', service_id),
                'description': service_info.get('description', ''),
                'goal': service_info.get('goal', ''),
                'goal_description': service_info.get('goal_description', ''),
                'replaces': service_info.get('replaces', ''),
                'replacement_description': service_info.get('replacement_description', ''),
                'resources': service_info.get('resources', {})
            })
            
        # Estimate total resource requirements
        total_resources = goal_mapper.estimate_resource_requirements([r['id'] for r in result])
            
        return jsonify({
            'success': True, 
            'recommendations': result,
            'total_resources': total_resources
        })
    except Exception as e:
        logger.error(f"Error recommending services: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/detect-resources', methods=['GET'])
def detect_resources():
    """
    Detect available system resources for the setup wizard.
    Returns CPU cores, RAM, disk space, and network speed.
    """
    try:
        # Detect CPU cores
        cpu_cores = os.cpu_count() or 4  # Default to 4 if detection fails
        
        # Detect RAM (in GB)
        ram_gb = 8  # Default value
        try:
            if os.name == 'posix':  # Linux/Mac
                mem_info = subprocess.check_output(['free', '-g']).decode('utf-8')
                ram_gb = int(re.search(r'Mem:\s+(\d+)', mem_info).group(1))
            elif os.name == 'nt':  # Windows
                mem_info = subprocess.check_output(['wmic', 'OS', 'get', 'TotalVisibleMemorySize', '/Value']).decode('utf-8')
                ram_kb = int(re.search(r'TotalVisibleMemorySize=(\d+)', mem_info).group(1))
                ram_gb = ram_kb // (1024 * 1024)  # Convert KB to GB
        except Exception as e:
            logging.warning(f"Failed to detect RAM: {e}")
        
        # Detect disk space (in GB)
        disk_gb = 500  # Default value
        try:
            if os.name == 'posix':  # Linux/Mac
                disk_info = subprocess.check_output(['df', '-h', '/']).decode('utf-8')
                disk_gb = int(re.search(r'/\s+\d+[KMGT]\s+\d+[KMGT]\s+\d+[KMGT]\s+\d+%\s+/', disk_info).group(1))
            elif os.name == 'nt':  # Windows
                disk_info = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'size', '/Value']).decode('utf-8')
                # Sum up all disk sizes
                disk_bytes = sum([int(size) for size in re.findall(r'Size=(\d+)', disk_info)])
                disk_gb = disk_bytes // (1024 * 1024 * 1024)  # Convert bytes to GB
        except Exception as e:
            logging.warning(f"Failed to detect disk space: {e}")
        
        # Estimate network speed (in Mbps) - this is just an estimate
        network_speed = 100  # Default to 100 Mbps
        
        return jsonify({
            'success': True,
            'resources': {
                'cpu_cores': cpu_cores,
                'ram_gb': ram_gb,
                'disk_gb': disk_gb,
                'network_speed': network_speed
            }
        })
    except Exception as e:
        logging.error(f"Error detecting system resources: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/vm-resources/<vm_id>', methods=['GET'])
@token_required(['user', 'admin'])
def get_vm_resources(vm_id):
    """Get resource usage data for a specific VM"""
    try:
        if not proxmox_nli:
            return jsonify({'error': 'System not initialized'}), 500
            
        # Get current resource usage
        resource_data = proxmox_nli.commands.get_vm_resources(vm_id)
        
        # Get historical data
        history = vm_resource_history.get(vm_id, {
            'cpu': [], 
            'memory': [], 
            'disk_io': [], 
            'network': [], 
            'timestamps': []
        })
        
        # Format timestamps for frontend
        formatted_timestamps = [datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in history['timestamps']]
        
        return jsonify({
            'success': True,
            'current': resource_data.get('resources', {}),
            'history': {
                'cpu': history['cpu'],
                'memory': history['memory'],
                'disk_io': history['disk_io'],
                'network': history['network'],
                'timestamps': formatted_timestamps
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting VM resources: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/optimization-recommendations', methods=['GET'])
@token_required(['user', 'admin'])
def get_optimization_recommendations():
    """Get optimization recommendations for all VMs"""
    try:
        recommendations = app.config.get('optimization_recommendations', [])
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/apply-optimization/<vm_id>', methods=['POST'])
@token_required(['admin'])
def apply_optimization(vm_id):
    """Apply a recommended optimization to a VM"""
    try:
        if not proxmox_nli:
            return jsonify({'error': 'System not initialized'}), 500
            
        data = request.json
        resource_type = data.get('resource')
        new_value = data.get('value')
        
        if not resource_type or new_value is None:
            return jsonify({'success': False, 'error': 'Resource type and value are required'}), 400
            
        # Apply the optimization
        result = None
        if resource_type == 'cpu':
            result = proxmox_nli.commands.set_vm_cpu(vm_id, new_value)
        elif resource_type == 'memory':
            result = proxmox_nli.commands.set_vm_memory(vm_id, new_value * 1024)  # Convert GB to MB
        
        if result and result.get('success'):
            # Log the optimization
            logger.info(f"Applied {resource_type} optimization to VM {vm_id}: set to {new_value}")
            return jsonify({
                'success': True,
                'message': f'Successfully applied {resource_type} optimization to VM {vm_id}'
            })
        else:
            error = result.get('error', 'Unknown error') if result else 'Failed to apply optimization'
            return jsonify({'success': False, 'error': error}), 500
            
    except Exception as e:
        logger.error(f"Error applying optimization: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/cluster-resources', methods=['GET'])
@token_required(['user', 'admin'])
def get_cluster_resources():
    """Get overall resource usage across the cluster"""
    try:
        if not proxmox_nli:
            return jsonify({'error': 'System not initialized'}), 500
            
        # Get cluster resources
        result = proxmox_nli.commands.get_cluster_resources()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'resources': result.get('resources', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to get cluster resources')
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting cluster resources: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

def start_app(host, user, password, realm='pam', verify_ssl=False, debug=False):
    """Start the Flask application with the given configuration"""
    global proxmox_nli, status_monitor_thread, resource_monitor_thread
    
    # Initialize ProxmoxNLI
    proxmox_nli = ProxmoxNLI(
        host=host,
        user=user,
        password=password,
        realm=realm,
        verify_ssl=verify_ssl
    )
    
    # Initialize app config for storing optimization recommendations
    app.config['optimization_recommendations'] = []
    
    # Start the status monitor in a background thread
    if not status_monitor_thread or not status_monitor_thread.is_alive():
        status_monitor_thread = threading.Thread(target=monitor_vm_status, daemon=True)
        status_monitor_thread.start()
    
    # Start the resource monitor in a background thread
    if not resource_monitor_thread or not resource_monitor_thread.is_alive():
        resource_monitor_thread = threading.Thread(target=monitor_vm_resources, daemon=True)
        resource_monitor_thread.start()
    
    # Start the Flask app
    socketio.run(app, debug=debug, host='0.0.0.0', port=int(os.getenv('API_PORT', 5000)))

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