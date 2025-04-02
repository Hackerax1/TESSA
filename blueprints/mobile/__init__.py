"""
Mobile Blueprint.
This module provides routes for mobile interface functionality.
"""
from flask import Blueprint

mobile_bp = Blueprint('mobile', __name__, url_prefix='/mobile')

from . import routes
