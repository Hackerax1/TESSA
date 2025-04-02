"""
Notifications Blueprint.
This module provides routes for notification functionality.
"""
from flask import Blueprint

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

from . import routes
