"""
Voice Authentication Blueprint.
This module provides routes for voice authentication functionality.
"""
from flask import Blueprint

voice_auth_bp = Blueprint('voice_auth', __name__, url_prefix='/api/voice-auth')

from . import routes
