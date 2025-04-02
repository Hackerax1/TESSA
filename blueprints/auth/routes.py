"""
Authentication API Routes.
This module contains all API routes for authentication and user management.
"""
from flask import request, jsonify, url_for, redirect, session, current_app
from proxmox_nli.core.security.auth_manager import token_required, auth_manager
from . import auth_bp

@auth_bp.route('/oauth/providers', methods=['GET'])
def oauth_providers():
    """Get all configured OAuth providers."""
    providers = auth_manager.get_oauth_providers()
    return jsonify(providers)

@auth_bp.route('/oauth/login/<provider_id>', methods=['GET'])
def oauth_login(provider_id):
    """Initiate OAuth login flow."""
    # Generate the redirect URI
    redirect_uri = url_for('auth.oauth_callback', provider_id=provider_id, _external=True)
    
    # Generate the authorization URL
    result = auth_manager.generate_oauth_authorization_url(provider_id, redirect_uri)
    
    if not result.get('success', False):
        return jsonify(result), 400
        
    # Redirect to the authorization URL
    return redirect(result['auth_url'])

@auth_bp.route('/oauth/callback/<provider_id>', methods=['GET'])
def oauth_callback(provider_id):
    """Handle OAuth callback."""
    # Get the authorization code and state from the request
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return jsonify({
            'success': False,
            'message': 'Missing code or state parameter'
        }), 400
        
    # Handle the callback
    result = auth_manager.handle_oauth_callback(code, state)
    
    if not result.get('success', False):
        return jsonify(result), 400
        
    # Set the token in a cookie or session
    token = result.get('token')
    if token:
        session['token'] = token
        
        # Redirect to the dashboard or a success page
        return redirect(url_for('dashboard'))
    else:
        return jsonify({
            'success': False,
            'message': 'Authentication successful but no token was generated'
        }), 500

@auth_bp.route('/oauth/link/<provider_id>', methods=['GET'])
@token_required()
def oauth_link(provider_id):
    """Link an OAuth account to the current user."""
    # Get the user ID from the session
    user_id = g.user_id
    
    # Generate the redirect URI
    redirect_uri = url_for('auth.oauth_link_callback', provider_id=provider_id, _external=True)
    
    # Generate the authorization URL
    result = auth_manager.generate_oauth_authorization_url(provider_id, redirect_uri, user_id)
    
    if not result.get('success', False):
        return jsonify(result), 400
        
    # Redirect to the authorization URL
    return redirect(result['auth_url'])

@auth_bp.route('/oauth/link/callback/<provider_id>', methods=['GET'])
@token_required()
def oauth_link_callback(provider_id):
    """Handle OAuth account linking callback."""
    # Get the user ID from the session
    user_id = g.user_id
    
    # Get the authorization code and state from the request
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return jsonify({
            'success': False,
            'message': 'Missing code or state parameter'
        }), 400
        
    # Handle the callback
    result = auth_manager.handle_oauth_link_callback(code, state, user_id)
    
    if not result.get('success', False):
        return jsonify(result), 400
        
    # Redirect to the account settings page
    return redirect(url_for('auth_ui.account_profile'))

@auth_bp.route('/oauth/unlink/<provider_id>/<provider_user_id>', methods=['POST'])
@token_required()
def oauth_unlink(provider_id, provider_user_id):
    """Unlink an OAuth account from the current user."""
    # Get the user ID from the session
    user_id = g.user_id
    
    # Unlink the account
    result = auth_manager.unlink_oauth_account(user_id, provider_id, provider_user_id)
    
    return jsonify(result)

@auth_bp.route('/oauth/accounts', methods=['GET'])
@token_required()
def oauth_accounts():
    """Get all OAuth accounts linked to the current user."""
    # Get the user ID from the session
    user_id = g.user_id
    
    # Get the linked accounts
    result = auth_manager.get_linked_oauth_accounts(user_id)
    
    return jsonify(result)

@auth_bp.route('/oauth/configure/<provider_id>', methods=['POST'])
@token_required(required_roles=['admin'])
def oauth_configure(provider_id):
    """Configure an OAuth provider."""
    # Get the configuration from the request
    config = request.json
    
    if not config:
        return jsonify({
            'success': False,
            'message': 'Missing configuration'
        }), 400
        
    # Configure the provider
    result = auth_manager.configure_oauth_provider(provider_id, config)
    
    return jsonify(result)

@auth_bp.route('/profile', methods=['GET'])
@token_required()
def get_user_profile():
    """Get the current user's profile."""
    # Get the user ID from the session
    user_id = g.user_id
    
    # Get the user profile
    result = auth_manager.get_user_profile(user_id)
    
    if not result.get('success', False):
        return jsonify(result), 404
        
    return jsonify(result)

@auth_bp.route('/profile', methods=['PUT'])
@token_required()
def update_user_profile():
    """Update the current user's profile."""
    # Get the user ID from the session
    user_id = g.user_id
    
    # Get the profile data from the request
    profile_data = request.json
    
    if not profile_data:
        return jsonify({
            'success': False,
            'message': 'Missing profile data'
        }), 400
        
    # Update the user profile
    result = auth_manager.update_user_profile(user_id, profile_data)
    
    return jsonify(result)

@auth_bp.route('/password', methods=['PUT'])
@token_required()
def change_password():
    """Change the current user's password."""
    # Get the user ID from the session
    user_id = g.user_id
    
    # Get the password data from the request
    password_data = request.json
    
    if not password_data:
        return jsonify({
            'success': False,
            'message': 'Missing password data'
        }), 400
        
    # Validate required fields
    required_fields = ['current_password', 'new_password']
    for field in required_fields:
        if field not in password_data:
            return jsonify({
                'success': False,
                'message': f'Missing required field: {field}'
            }), 400
            
    # Change the password
    result = auth_manager.change_user_password(
        user_id,
        password_data['current_password'],
        password_data['new_password']
    )
    
    return jsonify(result)

@auth_bp.route('/oauth/mapping', methods=['POST'])
@token_required(required_roles=['admin'])
def oauth_configure_mapping():
    """Configure OAuth user mapping settings."""
    # Get the mapping configuration from the request
    config = request.json
    
    if not config:
        return jsonify({
            'success': False,
            'message': 'Missing configuration'
        }), 400
        
    # Configure the mapping
    result = auth_manager.configure_oauth_mapping(config)
    
    return jsonify(result)
