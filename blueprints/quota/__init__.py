"""
Quota Management Blueprint.
This module provides routes for quota management functionality.
"""
from flask import Blueprint

quota_bp = Blueprint('quota', __name__, url_prefix='/api/quota')
quota_ui_bp = Blueprint('quota_ui', __name__, url_prefix='/quota')

from . import routes
from . import ui_routes
