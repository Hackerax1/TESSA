"""
Resource Planning Blueprint.
This module provides routes for resource planning functionality.
"""
from flask import Blueprint

resource_planning_bp = Blueprint('resource_planning', __name__, url_prefix='/api/resource-planning')

from . import routes
from .ui_routes import resource_planning_ui_bp  # Import the UI blueprint
