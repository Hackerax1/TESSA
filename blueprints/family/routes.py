"""
Family Management Routes.
This module contains all API routes for family management.
"""
from flask import request, jsonify, g
from proxmox_nli.core.security.auth_manager import token_required, auth_manager
from proxmox_nli.core.security.family_manager import FamilyManager
from . import family_bp

# Initialize the family manager
family_manager = FamilyManager()

@family_bp.route('/members', methods=['GET'])
@token_required(required_roles=['admin'])
def get_family_members():
    """Get all family members."""
    result = family_manager.get_family_members()
    return jsonify(result)

@family_bp.route('/members/<user_id>', methods=['GET'])
@token_required()
def get_family_member(user_id):
    """Get a specific family member."""
    # Check if user is requesting their own info or has admin role
    current_user_id = g.user_id
    roles = g.roles
    
    if current_user_id != user_id and 'admin' not in roles:
        return jsonify({
            'success': False,
            'message': 'Unauthorized to view this family member'
        }), 403
    
    result = family_manager.get_family_member(user_id)
    return jsonify(result)

@family_bp.route('/members', methods=['POST'])
@token_required(required_roles=['admin'])
def add_family_member():
    """Add a new family member."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    user_id = data.get('user_id')
    name = data.get('name')
    
    if not user_id or not name:
        return jsonify({
            'success': False,
            'message': 'User ID and name are required'
        }), 400
    
    relationship = data.get('relationship')
    age = data.get('age')
    profile_image = data.get('profile_image')
    
    result = family_manager.add_family_member(user_id, name, relationship, age, profile_image)
    
    if result.get('success'):
        # If group is specified, add member to group
        group = data.get('group')
        if group:
            family_manager.add_member_to_group(user_id, group)
        
        # If policy is specified, apply policy
        policy = data.get('policy')
        if policy:
            family_manager.apply_access_policy(user_id, policy)
    
    return jsonify(result)

@family_bp.route('/groups/<group_name>/members/<user_id>', methods=['POST'])
@token_required(required_roles=['admin'])
def add_member_to_group(group_name, user_id):
    """Add a family member to a group."""
    result = family_manager.add_member_to_group(user_id, group_name)
    return jsonify(result)

@family_bp.route('/members/<user_id>/groups', methods=['GET'])
@token_required()
def get_member_groups(user_id):
    """Get groups that a family member belongs to."""
    # Check if user is requesting their own info or has admin role
    current_user_id = g.user_id
    roles = g.roles
    
    if current_user_id != user_id and 'admin' not in roles:
        return jsonify({
            'success': False,
            'message': 'Unauthorized to view this family member\'s groups'
        }), 403
    
    result = family_manager.get_member_groups(user_id)
    return jsonify(result)

@family_bp.route('/policies/<policy_name>/members/<user_id>', methods=['POST'])
@token_required(required_roles=['admin'])
def apply_policy_to_member(policy_name, user_id):
    """Apply an access policy to a family member."""
    result = family_manager.apply_access_policy(user_id, policy_name)
    return jsonify(result)

@family_bp.route('/members/<user_id>/policies', methods=['GET'])
@token_required()
def get_member_policies(user_id):
    """Get access policies applied to a family member."""
    # Check if user is requesting their own info or has admin role
    current_user_id = g.user_id
    roles = g.roles
    
    if current_user_id != user_id and 'admin' not in roles:
        return jsonify({
            'success': False,
            'message': 'Unauthorized to view this family member\'s policies'
        }), 403
    
    result = family_manager.get_member_policies(user_id)
    return jsonify(result)

@family_bp.route('/members/<user_id>', methods=['PUT'])
@token_required(required_roles=['admin'])
def update_family_member(user_id):
    """Update a family member."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    result = family_manager.update_family_member(user_id, data)
    return jsonify(result)

@family_bp.route('/members/<user_id>', methods=['DELETE'])
@token_required(required_roles=['admin'])
def remove_family_member(user_id):
    """Remove a family member."""
    result = family_manager.remove_family_member(user_id)
    return jsonify(result)

@family_bp.route('/groups', methods=['GET'])
@token_required()
def get_family_groups():
    """Get all family groups."""
    result = family_manager.get_family_groups()
    return jsonify(result)

@family_bp.route('/groups', methods=['POST'])
@token_required(required_roles=['admin'])
def create_family_group():
    """Create a new family group."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    name = data.get('name')
    
    if not name:
        return jsonify({
            'success': False,
            'message': 'Group name is required'
        }), 400
    
    description = data.get('description')
    
    result = family_manager.create_family_group(name, description)
    return jsonify(result)

@family_bp.route('/policies', methods=['GET'])
@token_required()
def get_access_policies():
    """Get all access policies."""
    result = family_manager.get_access_policies()
    return jsonify(result)

@family_bp.route('/policies', methods=['POST'])
@token_required(required_roles=['admin'])
def create_access_policy():
    """Create a new access policy."""
    data = request.json
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    name = data.get('name')
    
    if not name:
        return jsonify({
            'success': False,
            'message': 'Policy name is required'
        }), 400
    
    permissions = data.get('permissions')
    
    if not permissions:
        return jsonify({
            'success': False,
            'message': 'Permissions are required'
        }), 400
    
    description = data.get('description')
    
    result = family_manager.create_access_policy(name, permissions, description)
    return jsonify(result)
