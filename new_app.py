#!/usr/bin/env python3
"""
Proxmox NLI Application Entry Point.
This module serves as the entry point for the Proxmox NLI application.
"""
import os
from app_factory import start_app

# Create and configure the application
app, socketio = start_app()

if __name__ == '__main__':
    # Get host and port from environment or use defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # Run the application
    socketio.run(app, host=host, port=port, debug=True, use_reloader=True)
