"""
Export Routes.
This module contains all API routes for infrastructure as code export functionality.
"""
from flask import request, jsonify, send_file, current_app
from proxmox_nli.core.security.auth_manager import token_required
from proxmox_nli.services.export.export_manager import ExportManager
import os
import io
import zipfile
from . import export_bp

@export_bp.route('/terraform', methods=['POST'])
@token_required
def export_terraform():
    """Export Proxmox configuration to Terraform format"""
    data = request.get_json()
    output_dir = data.get('output_dir')
    resource_types = data.get('resource_types')
    
    # Initialize export manager
    from proxmox_nli.core import proxmox_nli
    export_manager = ExportManager(proxmox_nli.proxmox_api)
    
    # Export to Terraform
    result = export_manager.export_terraform(output_dir, resource_types)
    
    return jsonify(result)

@export_bp.route('/ansible', methods=['POST'])
@token_required
def export_ansible():
    """Export Proxmox configuration to Ansible playbook format"""
    data = request.get_json()
    output_dir = data.get('output_dir')
    resource_types = data.get('resource_types')
    
    # Initialize export manager
    from proxmox_nli.core import proxmox_nli
    export_manager = ExportManager(proxmox_nli.proxmox_api)
    
    # Export to Ansible
    result = export_manager.export_ansible(output_dir, resource_types)
    
    return jsonify(result)

@export_bp.route('/config', methods=['GET'])
@token_required
def get_export_config():
    """Get export configuration"""
    # Initialize export manager
    from proxmox_nli.core import proxmox_nli
    export_manager = ExportManager(proxmox_nli.proxmox_api)
    
    return jsonify({
        "success": True,
        "config": export_manager.config
    })

@export_bp.route('/config', methods=['PUT'])
@token_required
def update_export_config():
    """Update export configuration"""
    data = request.get_json()
    
    # Initialize export manager
    from proxmox_nli.core import proxmox_nli
    export_manager = ExportManager(proxmox_nli.proxmox_api)
    
    # Update configuration
    result = export_manager.update_config(data)
    
    return jsonify(result)

@export_bp.route('/download/<path:filename>', methods=['GET'])
@token_required
def download_export(filename):
    """Download exported file"""
    # For security, ensure the filename is within the allowed export directories
    if not filename.startswith(('tessa_terraform_', 'tessa_ansible_')):
        return jsonify({"error": "Invalid export filename"}), 403
        
    # Get the full path
    full_path = os.path.join('/tmp', filename)
    
    # Check if the file exists
    if not os.path.exists(full_path):
        return jsonify({"error": "Export file not found"}), 404
        
    # If it's a directory, create a zip file
    if os.path.isdir(full_path):
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, full_path)
                    zipf.write(file_path, arcname)
                    
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{os.path.basename(full_path)}.zip"
        )
    else:
        # It's a single file
        return send_file(
            full_path,
            as_attachment=True,
            download_name=os.path.basename(full_path)
        )
