"""
Authentication UI Routes.
This module contains all UI routes for authentication and user management.
"""
from flask import render_template
from proxmox_nli.core.security.auth_manager import token_required, auth_manager
from . import auth_ui_bp

@auth_ui_bp.route('/settings/oauth', methods=['GET'])
@token_required(required_roles=['admin'])
def oauth_settings():
    """Render the OAuth settings page."""
    providers = auth_manager.get_oauth_providers()
    return render_template('oauth_settings.html', providers=providers.get('providers', {}))

@auth_ui_bp.route('/login', methods=['GET'])
def login_page():
    """Render the login page with OAuth options."""
    providers = auth_manager.get_oauth_providers()
    return render_template('login.html', providers=providers.get('providers', {}))

@auth_ui_bp.route('/profile', methods=['GET'])
@token_required()
def account_profile():
    """Render the user profile page."""
    return render_template('user_profile.html')
