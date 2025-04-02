"""
Family Management Blueprint.
This module provides routes for family management functionality.
"""
from flask import Blueprint

family_bp = Blueprint('family', __name__, url_prefix='/api/family')
family_ui_bp = Blueprint('family_ui', __name__, url_prefix='/family')

from . import routes
from . import ui_routes
