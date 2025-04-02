"""
Mobile Routes.
This module contains all routes for the mobile interface.
"""
from flask import render_template
from . import mobile_bp

@mobile_bp.route('/', methods=['GET'])
def mobile_interface():
    """
    Render the mobile interface
    
    Returns:
        HTML: Mobile interface
    """
    return render_template('mobile_base.html')

@mobile_bp.route('/vms', methods=['GET'])
def mobile_vms():
    """
    Render the mobile VMs page
    
    Returns:
        HTML: Mobile VMs page
    """
    return render_template('mobile_vms.html')

@mobile_bp.route('/notifications', methods=['GET'])
def mobile_notifications():
    """
    Render the mobile notifications page
    
    Returns:
        HTML: Mobile notifications page
    """
    return render_template('mobile_notifications.html')
