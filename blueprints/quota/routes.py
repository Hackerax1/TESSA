"""
Quota Management Routes.
This module contains all API routes for quota management.
"""
from flask import request, jsonify, current_app, g
from proxmox_nli.core.security.auth_manager import token_required
from proxmox_nli.services.quota_management import quota_management_service
from . import quota_bp

@quota_bp.route('/users', methods=['GET'])
@token_required(required_roles=['admin'])
def get_all_user_quotas():
    """Get quotas for all users."""
    try:
        quotas = quota_management_service.get_all_quotas()
        return jsonify({
            "success": True,
            "quotas": quotas
        })
    except Exception as e:
        current_app.logger.error(f"Error getting all user quotas: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting all user quotas: {str(e)}"
        }), 500

@quota_bp.route('/users/<user_id>', methods=['GET'])
@token_required()
def get_user_quota(user_id):
    """Get quota for a specific user."""
    try:
        # Check if user is requesting their own quota or has admin role
        current_user_id = g.user_id
        roles = g.roles
        
        if current_user_id != user_id and 'admin' not in roles:
            return jsonify({
                "success": False,
                "message": "Unauthorized to view this user's quota"
            }), 403
        
        quota = quota_management_service.get_user_quota(user_id)
        return jsonify({
            "success": True,
            "quota": quota
        })
    except Exception as e:
        current_app.logger.error(f"Error getting user quota: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting user quota: {str(e)}"
        }), 500

@quota_bp.route('/users/<user_id>', methods=['PUT'])
@token_required(required_roles=['admin'])
def set_user_quota(user_id):
    """Set quota for a specific user."""
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        success = quota_management_service.set_user_quota(user_id, data)
        if success:
            return jsonify({
                "success": True,
                "message": f"Quota for user {user_id} updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to update user quota"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error setting user quota: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error setting user quota: {str(e)}"
        }), 500

@quota_bp.route('/users/<user_id>', methods=['DELETE'])
@token_required(required_roles=['admin'])
def delete_user_quota(user_id):
    """Delete quota for a specific user."""
    try:
        success = quota_management_service.delete_user_quota(user_id)
        if success:
            return jsonify({
                "success": True,
                "message": f"Quota for user {user_id} deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to delete user quota"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error deleting user quota: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error deleting user quota: {str(e)}"
        }), 500

@quota_bp.route('/groups', methods=['GET'])
@token_required(required_roles=['admin'])
def get_all_group_quotas():
    """Get quotas for all groups."""
    try:
        quotas = quota_management_service.get_all_quotas()
        return jsonify({
            "success": True,
            "group_quotas": quotas.get("groups", {})
        })
    except Exception as e:
        current_app.logger.error(f"Error getting all group quotas: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting all group quotas: {str(e)}"
        }), 500

@quota_bp.route('/groups/<group_id>', methods=['GET'])
@token_required()
def get_group_quota(group_id):
    """Get quota for a specific group."""
    try:
        # Check if user is a member of the group or has admin role
        current_user_id = g.user_id
        roles = g.roles
        
        # In a real implementation, you would check group membership
        # For now, we'll just check if the user is an admin
        if 'admin' not in roles:
            # Check if user is in the group
            from proxmox_nli.core.security.family_manager import family_manager
            user_groups = family_manager.get_member_groups(current_user_id).get("groups", [])
            
            if group_id not in [group.get("id") for group in user_groups]:
                return jsonify({
                    "success": False,
                    "message": "Unauthorized to view this group's quota"
                }), 403
        
        quota = quota_management_service.get_group_quota(group_id)
        return jsonify({
            "success": True,
            "quota": quota
        })
    except Exception as e:
        current_app.logger.error(f"Error getting group quota: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting group quota: {str(e)}"
        }), 500

@quota_bp.route('/groups/<group_id>', methods=['PUT'])
@token_required(required_roles=['admin'])
def set_group_quota(group_id):
    """Set quota for a specific group."""
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        success = quota_management_service.set_group_quota(group_id, data)
        if success:
            return jsonify({
                "success": True,
                "message": f"Quota for group {group_id} updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to update group quota"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error setting group quota: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error setting group quota: {str(e)}"
        }), 500

@quota_bp.route('/groups/<group_id>', methods=['DELETE'])
@token_required(required_roles=['admin'])
def delete_group_quota(group_id):
    """Delete quota for a specific group."""
    try:
        success = quota_management_service.delete_group_quota(group_id)
        if success:
            return jsonify({
                "success": True,
                "message": f"Quota for group {group_id} deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to delete group quota"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error deleting group quota: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error deleting group quota: {str(e)}"
        }), 500

@quota_bp.route('/defaults', methods=['GET'])
@token_required()
def get_default_quotas():
    """Get default quotas."""
    try:
        defaults = quota_management_service.get_default_quotas()
        return jsonify({
            "success": True,
            "defaults": defaults
        })
    except Exception as e:
        current_app.logger.error(f"Error getting default quotas: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting default quotas: {str(e)}"
        }), 500

@quota_bp.route('/defaults', methods=['PUT'])
@token_required(required_roles=['admin'])
def set_default_quotas():
    """Set default quotas."""
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        success = quota_management_service.set_default_quotas(data)
        if success:
            return jsonify({
                "success": True,
                "message": "Default quotas updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to update default quotas"
            }), 500
    except Exception as e:
        current_app.logger.error(f"Error setting default quotas: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error setting default quotas: {str(e)}"
        }), 500

@quota_bp.route('/users/<user_id>/compliance', methods=['GET'])
@token_required()
def check_user_compliance(user_id):
    """Check if a user is compliant with their quotas."""
    try:
        # Check if user is requesting their own compliance or has admin role
        current_user_id = g.user_id
        roles = g.roles
        
        if current_user_id != user_id and 'admin' not in roles:
            return jsonify({
                "success": False,
                "message": "Unauthorized to view this user's compliance"
            }), 403
        
        is_compliant, compliance = quota_management_service.check_quota_compliance(user_id)
        return jsonify({
            "success": True,
            "is_compliant": is_compliant,
            "compliance": compliance
        })
    except Exception as e:
        current_app.logger.error(f"Error checking user compliance: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error checking user compliance: {str(e)}"
        }), 500

@quota_bp.route('/users/<user_id>/enforce', methods=['POST'])
@token_required(required_roles=['admin'])
def enforce_user_quotas(user_id):
    """Enforce quotas for a user."""
    try:
        success, result = quota_management_service.enforce_quotas(user_id)
        return jsonify({
            "success": True,
            "enforcement_success": success,
            "result": result
        })
    except Exception as e:
        current_app.logger.error(f"Error enforcing user quotas: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error enforcing user quotas: {str(e)}"
        }), 500

@quota_bp.route('/report', methods=['GET'])
@token_required(required_roles=['admin'])
def get_quota_report():
    """Get a report of quota usage for all users."""
    try:
        report = quota_management_service.get_quota_usage_report()
        return jsonify({
            "success": True,
            "report": report
        })
    except Exception as e:
        current_app.logger.error(f"Error getting quota report: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting quota report: {str(e)}"
        }), 500

@quota_bp.route('/users/<user_id>/report', methods=['GET'])
@token_required()
def get_user_quota_report(user_id):
    """Get a report of quota usage for a specific user."""
    try:
        # Check if user is requesting their own report or has admin role
        current_user_id = g.user_id
        roles = g.roles
        
        if current_user_id != user_id and 'admin' not in roles:
            return jsonify({
                "success": False,
                "message": "Unauthorized to view this user's quota report"
            }), 403
        
        report = quota_management_service.get_quota_usage_report(user_id)
        return jsonify({
            "success": True,
            "report": report
        })
    except Exception as e:
        current_app.logger.error(f"Error getting user quota report: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error getting user quota report: {str(e)}"
        }), 500
