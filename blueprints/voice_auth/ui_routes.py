"""
Voice Authentication UI Routes.
This module contains all UI routes for voice authentication.
"""
from flask import render_template
from proxmox_nli.core.security.auth_manager import token_required
from . import voice_auth_bp

@voice_auth_bp.route('/ui', methods=['GET'])
@token_required
def voice_auth_page():
    """Render the voice authentication page."""
    return render_template('voice_auth.html')

@voice_auth_bp.route('/ui/register', methods=['GET'])
@token_required
def voice_auth_register_page():
    """Render the voice registration page."""
    return render_template('voice_auth_register.html')

@voice_auth_bp.route('/ui/manage', methods=['GET'])
@token_required
def voice_auth_manage_page():
    """Render the voice authentication management page."""
    return render_template('voice_auth_manage.html')
