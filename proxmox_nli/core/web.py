"""
Web interface module for the Proxmox NLI.
"""

def web_mode(args):
    """Run the Proxmox NLI as a web server with voice recognition"""
    from app import start_app
    
    print("Starting web interface on http://0.0.0.0:5000")
    print("Press Ctrl+C to stop the server")
    
    start_app(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl,
        debug=args.debug
    )