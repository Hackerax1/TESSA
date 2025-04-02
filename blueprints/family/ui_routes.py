"""
Family Management UI Routes.
This module contains all UI routes for family management.
"""
from flask import render_template
from proxmox_nli.core.security.auth_manager import token_required
from . import family_ui_bp

@family_ui_bp.route('/management', methods=['GET'])
@token_required(required_roles=['admin'])
def family_management_page():
    """Render the family management page."""
    return render_template('family_management.html')

@family_ui_bp.route('/profile', methods=['GET'])
@token_required()
def family_profile_page():
    """Render the family profile page."""
    return render_template('family_profile.html')

@family_ui_bp.route('/resources/management', methods=['GET'])
@token_required(required_roles=['admin'])
def resource_management_page():
    """Render the resource management page."""
    return render_template('resource_management.html')
