#!/usr/bin/env python3
"""
Proxmox NLI Application Factory.
This module creates and configures the Flask application.
"""
from flask import Flask, render_template, g, jsonify
from flask_socketio import SocketIO
import os
import sys
import logging
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, 
               static_folder='static',
               static_url_path='/static')
    
    # Load default configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
    
    # Override default configuration with test config if provided
    if test_config:
        app.config.update(test_config)
    
    # Initialize extensions
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize core components
    from proxmox_nli.core import ProxmoxNLI
    from proxmox_nli.core.voice_handler import VoiceHandler
    from proxmox_nli.core.security.auth_manager import AuthManager
    from proxmox_nli.core.user_preferences import UserManager, UserPreferencesManager
    from proxmox_nli.core.profile_sync import ProfileSyncManager
    from proxmox_nli.core.dashboard_manager import DashboardManager
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # Add asset versioning support
    app.config['ASSET_MANIFEST'] = {}
    manifest_path = os.path.join(app.static_folder, 'dist', 'manifest.json')
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                app.config['ASSET_MANIFEST'] = json.load(f)
        except Exception as e:
            logger.error(f"Error loading asset manifest: {str(e)}")
    
    # Register template context processors
    @app.context_processor
    def inject_globals():
        return {
            'versioned_asset': lambda filename: versioned_asset(app, filename)
        }
    
    # Register blueprints
    register_blueprints(app)
    
    # Run asset optimization in production mode
    if not app.debug:
        try:
            from scripts.optimize_js import main as optimize_js
            optimize_js()
        except Exception as e:
            logger.error(f"Error running asset optimization: {str(e)}")
    
    return app, socketio

def register_blueprints(app):
    """Register all application blueprints."""
    # Import blueprints
    from blueprints.voice_auth import voice_auth_bp
    from blueprints.voice_auth.ui_routes import voice_auth_bp as voice_auth_ui_bp
    from blueprints.resource_planning import resource_planning_bp
    from blueprints.resource_planning.ui_routes import resource_planning_ui_bp
    from blueprints.notifications import notifications_bp
    from blueprints.mobile import mobile_bp
    from blueprints.auth import auth_bp, auth_ui_bp
    from blueprints.family import family_bp, family_ui_bp
    from blueprints.export import export_bp, export_ui_bp
    from blueprints.quota import quota_bp, quota_ui_bp
    
    # Register blueprints
    app.register_blueprint(voice_auth_bp)
    app.register_blueprint(voice_auth_ui_bp)
    app.register_blueprint(resource_planning_bp)
    app.register_blueprint(resource_planning_ui_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(mobile_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(auth_ui_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(family_ui_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(export_ui_bp)
    app.register_blueprint(quota_bp)
    app.register_blueprint(quota_ui_bp)
    
    # TODO: Register additional blueprints as they are created

def versioned_asset(app, filename):
    """Get the versioned path for an asset."""
    if app.debug:
        return filename
    
    manifest = app.config.get('ASSET_MANIFEST', {})
    if filename in manifest:
        return manifest[filename]
    
    return filename

def start_app():
    """Initialize and start the application."""
    app, socketio = create_app()
    
    # Initialize global services and components
    from proxmox_nli.core import ProxmoxNLI
    from proxmox_nli.core.voice_handler import VoiceHandler
    from proxmox_nli.core.security.auth_manager import AuthManager
    from proxmox_nli.core.user_preferences import UserManager, UserPreferencesManager
    from proxmox_nli.core.profile_sync import ProfileSyncManager
    from proxmox_nli.core.dashboard_manager import DashboardManager
    
    global proxmox_nli, voice_handler, auth_manager, user_manager, user_preferences
    global profile_sync_manager, dashboard_manager
    
    proxmox_nli = ProxmoxNLI()
    voice_handler = VoiceHandler()
    auth_manager = AuthManager()
    user_manager = UserManager()
    user_preferences = UserPreferencesManager()
    profile_sync_manager = ProfileSyncManager(proxmox_nli)
    dashboard_manager = DashboardManager(proxmox_nli)
    
    # Start monitoring threads
    start_monitoring_threads()
    
    return app, socketio

def start_monitoring_threads():
    """Start background monitoring threads."""
    # TODO: Implement monitoring thread initialization
    pass

if __name__ == '__main__':
    app, socketio = start_app()
    
    # Get host and port from environment or use defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # Run the application
    socketio.run(app, host=host, port=port, debug=True, use_reloader=True)
