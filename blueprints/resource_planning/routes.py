"""
Resource Planning Routes.
This module contains all API routes for resource planning.
"""
from flask import request, jsonify, current_app
from proxmox_nli.core.security.auth_manager import token_required
from proxmox_nli.services.resource_planning import resource_planning_service
from . import resource_planning_bp

@resource_planning_bp.route('/calculate', methods=['POST'])
@token_required
def calculate_resources():
    """Calculate required resources based on a VM plan."""
    try:
        data = request.json
        if not data or 'vm_plan' not in data:
            return jsonify({"success": False, "message": "VM plan is required"}), 400
        
        vm_plan = data['vm_plan']
        
        result = resource_planning_service.calculate_resources(vm_plan)
        
        return jsonify({
            "success": True,
            "resources": result
        })
    except Exception as e:
        current_app.logger.error(f"Error calculating resources: {str(e)}")
        return jsonify({"success": False, "message": f"Error calculating resources: {str(e)}"}), 500

@resource_planning_bp.route('/forecast', methods=['POST'])
@token_required
def forecast_disk_usage():
    """Forecast disk usage over time based on VM plan."""
    try:
        data = request.json
        if not data or 'vm_plan' not in data:
            return jsonify({"success": False, "message": "VM plan is required"}), 400
        
        vm_plan = data['vm_plan']
        months = data.get('months', 12)
        
        result = resource_planning_service.forecast_disk_usage(vm_plan, months)
        
        return jsonify({
            "success": True,
            "forecast": result
        })
    except Exception as e:
        current_app.logger.error(f"Error forecasting disk usage: {str(e)}")
        return jsonify({"success": False, "message": f"Error forecasting disk usage: {str(e)}"}), 500

@resource_planning_bp.route('/recommend', methods=['POST'])
@token_required
def recommend_hardware():
    """Recommend hardware based on calculated resource requirements."""
    try:
        data = request.json
        if not data or 'requirements' not in data:
            return jsonify({"success": False, "message": "Resource requirements are required"}), 400
        
        requirements = data['requirements']
        
        result = resource_planning_service.recommend_hardware(requirements)
        
        return jsonify({
            "success": True,
            "recommendations": result
        })
    except Exception as e:
        current_app.logger.error(f"Error recommending hardware: {str(e)}")
        return jsonify({"success": False, "message": f"Error recommending hardware: {str(e)}"}), 500

@resource_planning_bp.route('/plans', methods=['GET'])
@token_required
def get_resource_plans():
    """Get all resource plans."""
    try:
        plans = resource_planning_service.get_resource_plans()
        
        return jsonify({
            "success": True,
            "plans": plans
        })
    except Exception as e:
        current_app.logger.error(f"Error getting resource plans: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting resource plans: {str(e)}"}), 500

@resource_planning_bp.route('/plans/<plan_id>', methods=['GET'])
@token_required
def get_resource_plan(plan_id):
    """Get a resource plan by ID."""
    try:
        plan = resource_planning_service.get_resource_plan(plan_id)
        
        if not plan:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        
        return jsonify({
            "success": True,
            "plan": plan
        })
    except Exception as e:
        current_app.logger.error(f"Error getting resource plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting resource plan: {str(e)}"}), 500

@resource_planning_bp.route('/plans', methods=['POST'])
@token_required
def create_resource_plan():
    """Create a new resource plan."""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Plan data is required"}), 400
        
        plan_id = resource_planning_service.save_resource_plan(data)
        
        return jsonify({
            "success": True,
            "plan_id": plan_id
        })
    except Exception as e:
        current_app.logger.error(f"Error creating resource plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error creating resource plan: {str(e)}"}), 500

@resource_planning_bp.route('/plans/<plan_id>', methods=['PUT'])
@token_required
def update_resource_plan(plan_id):
    """Update a resource plan."""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Plan data is required"}), 400
        
        # Ensure plan ID matches
        data['id'] = plan_id
        
        plan_id = resource_planning_service.save_resource_plan(data)
        
        return jsonify({
            "success": True,
            "plan_id": plan_id
        })
    except Exception as e:
        current_app.logger.error(f"Error updating resource plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating resource plan: {str(e)}"}), 500

@resource_planning_bp.route('/plans/<plan_id>', methods=['DELETE'])
@token_required
def delete_resource_plan(plan_id):
    """Delete a resource plan."""
    try:
        success = resource_planning_service.delete_resource_plan(plan_id)
        
        if not success:
            return jsonify({"success": False, "message": f"Plan not found: {plan_id}"}), 404
        
        return jsonify({
            "success": True
        })
    except Exception as e:
        current_app.logger.error(f"Error deleting resource plan: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting resource plan: {str(e)}"}), 500

@resource_planning_bp.route('/vm-profiles', methods=['GET'])
@token_required
def get_vm_profiles():
    """Get all VM profiles."""
    try:
        profiles = resource_planning_service.get_vm_profiles()
        
        return jsonify({
            "success": True,
            "profiles": profiles
        })
    except Exception as e:
        current_app.logger.error(f"Error getting VM profiles: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting VM profiles: {str(e)}"}), 500

@resource_planning_bp.route('/hardware', methods=['GET'])
@token_required
def get_hardware_database():
    """Get hardware database for recommendations."""
    try:
        hardware = resource_planning_service.get_hardware_database()
        
        return jsonify({
            "success": True,
            "hardware": hardware
        })
    except Exception as e:
        current_app.logger.error(f"Error getting hardware database: {str(e)}")
        return jsonify({"success": False, "message": f"Error getting hardware database: {str(e)}"}), 500
