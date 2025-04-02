"""
Authentication Blueprint.
This module provides routes for authentication and user management functionality.
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_ui_bp = Blueprint('auth_ui', __name__, url_prefix='/auth')

from . import routes
from . import ui_routes
