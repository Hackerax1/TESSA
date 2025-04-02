"""
Resource Planning UI Routes.
This module contains all UI routes for resource planning.
"""
from flask import Blueprint, render_template
from proxmox_nli.core.security.auth_manager import token_required

# Create a separate blueprint for UI routes with a different URL prefix
resource_planning_ui_bp = Blueprint('resource_planning_ui', __name__, url_prefix='/resource-planning')

@resource_planning_ui_bp.route('/', methods=['GET'])
@token_required
def resource_planning_page():
    """Render the resource planning page."""
    return render_template('resource_planning.html')

@resource_planning_ui_bp.route('/calculator', methods=['GET'])
@token_required
def resource_calculator_page():
    """Render the resource calculator page."""
    return render_template('resource_calculator.html')

@resource_planning_ui_bp.route('/forecasting', methods=['GET'])
@token_required
def disk_forecasting_page():
    """Render the disk space forecasting page."""
    return render_template('disk_forecasting.html')

@resource_planning_ui_bp.route('/hardware', methods=['GET'])
@token_required
def hardware_recommendations_page():
    """Render the hardware recommendations page."""
    return render_template('hardware_recommendations.html')
