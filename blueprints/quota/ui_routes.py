"""
Quota Management UI Routes.
This module contains all UI routes for quota management.
"""
from flask import render_template
from proxmox_nli.core.security.auth_manager import token_required
from . import quota_ui_bp

@quota_ui_bp.route('/', methods=['GET'])
@token_required()
def quota_dashboard():
    """Render the quota management dashboard."""
    return render_template('quota_dashboard.html')

@quota_ui_bp.route('/users', methods=['GET'])
@token_required(required_roles=['admin'])
def manage_user_quotas():
    """Render the user quota management page."""
    return render_template('quota_users.html')

@quota_ui_bp.route('/groups', methods=['GET'])
@token_required(required_roles=['admin'])
def manage_group_quotas():
    """Render the group quota management page."""
    return render_template('quota_groups.html')

@quota_ui_bp.route('/report', methods=['GET'])
@token_required(required_roles=['admin'])
def quota_report():
    """Render the quota usage report page."""
    return render_template('quota_report.html')

@quota_ui_bp.route('/settings', methods=['GET'])
@token_required(required_roles=['admin'])
def quota_settings():
    """Render the quota settings page."""
    return render_template('quota_settings.html')
