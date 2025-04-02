"""
Voice Authentication Routes.
This module contains all routes for voice authentication.
"""
from flask import request, jsonify, render_template, current_app
from proxmox_nli.core.voice_handler import voice_handler
from proxmox_nli.core.security.auth_manager import token_required
from . import voice_auth_bp

@voice_auth_bp.route('/register', methods=['POST'])
@token_required
def register_voice():
    """Register a user's voice for authentication."""
    try:
        data = request.json
        if not data or 'user_id' not in data or 'audio_samples' not in data:
            return jsonify({"success": False, "message": "User ID and audio samples are required"}), 400
        
        user_id = data['user_id']
        audio_samples = data['audio_samples']
        phrase = data.get('phrase')
        
        if len(audio_samples) < 3:
            return jsonify({"success": False, "message": "At least 3 audio samples are required"}), 400
        
        success = voice_handler.register_voice(user_id, audio_samples, phrase)
        
        if success:
            return jsonify({"success": True, "message": "Voice registered successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to register voice"}), 500
    except Exception as e:
        current_app.logger.error(f"Error registering voice: {str(e)}")
        return jsonify({"success": False, "message": f"Error registering voice: {str(e)}"}), 500

@voice_auth_bp.route('/authenticate', methods=['POST'])
@token_required
def authenticate_voice():
    """Authenticate a user by their voice."""
    try:
        data = request.json
        if not data or 'audio' not in data:
            return jsonify({"success": False, "message": "Audio data is required"}), 400
        
        audio = data['audio']
        user_id = data.get('user_id')  # Optional: specific user to authenticate against
        threshold = data.get('threshold', 0.7)
        require_passphrase = data.get('require_passphrase', False)
        spoken_text = data.get('text')  # Optional: recognized text for passphrase verification
        
        success, authenticated_user, confidence = voice_handler.authenticate_voice(
            audio, threshold, user_id, require_passphrase, spoken_text
        )
        
        if success:
            return jsonify({
                "success": True, 
                "authenticated": True,
                "user_id": authenticated_user,
                "confidence": confidence
            })
        else:
            return jsonify({
                "success": True,
                "authenticated": False,
                "confidence": confidence,
                "message": "Voice authentication failed"
            })
    except Exception as e:
        current_app.logger.error(f"Error authenticating voice: {str(e)}")
        return jsonify({"success": False, "message": f"Error authenticating voice: {str(e)}"}), 500

@voice_auth_bp.route('/update', methods=['POST'])
@token_required
def update_voice_signature():
    """Update a user's voice signature with a new sample."""
    try:
        data = request.json
        if not data or 'user_id' not in data or 'audio' not in data:
            return jsonify({"success": False, "message": "User ID and audio data are required"}), 400
        
        user_id = data['user_id']
        audio = data['audio']
        
        success = voice_handler.update_voice_signature(user_id, audio)
        
        if success:
            return jsonify({"success": True, "message": "Voice signature updated successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to update voice signature"}), 500
    except Exception as e:
        current_app.logger.error(f"Error updating voice signature: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating voice signature: {str(e)}"}), 500

@voice_auth_bp.route('/delete/<user_id>', methods=['DELETE'])
@token_required
def delete_voice_signature(user_id):
    """Delete a user's voice signature."""
    try:
        success = voice_handler.delete_voice_signature(user_id)
        
        if success:
            return jsonify({"success": True, "message": "Voice signature deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to delete voice signature"}), 500
    except Exception as e:
        current_app.logger.error(f"Error deleting voice signature: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting voice signature: {str(e)}"}), 500

@voice_auth_bp.route('/users', methods=['GET'])
@token_required
def list_voice_users():
    """List all users with registered voice signatures."""
    try:
        users = voice_handler.list_voice_users()
        
        return jsonify({"success": True, "users": users})
    except Exception as e:
        current_app.logger.error(f"Error listing voice users: {str(e)}")
        return jsonify({"success": False, "message": f"Error listing voice users: {str(e)}"}), 500

@voice_auth_bp.route('/passphrase', methods=['POST'])
@token_required
def set_user_passphrase():
    """Set or update a user's authentication passphrase."""
    try:
        data = request.json
        if not data or 'user_id' not in data or 'passphrase' not in data:
            return jsonify({"success": False, "message": "User ID and passphrase are required"}), 400
        
        user_id = data['user_id']
        passphrase = data['passphrase']
        
        success = voice_handler.set_user_passphrase(user_id, passphrase)
        
        if success:
            return jsonify({"success": True, "message": "Passphrase set successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to set passphrase"}), 500
    except Exception as e:
        current_app.logger.error(f"Error setting passphrase: {str(e)}")
        return jsonify({"success": False, "message": f"Error setting passphrase: {str(e)}"}), 500
