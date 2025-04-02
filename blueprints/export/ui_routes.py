"""
Export UI Routes.
This module contains all UI routes for infrastructure as code export functionality.
"""
from flask import render_template
from proxmox_nli.core.security.auth_manager import token_required
from . import export_ui_bp

@export_ui_bp.route('/', methods=['GET'])
@token_required
def export_page():
    """Render the Infrastructure as Code export page"""
    return render_template('export_vcs.html')
