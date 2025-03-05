#!/usr/bin/env python3
import os
import sys
import argparse
from dotenv import load_dotenv
from proxmox_nli.core import ProxmoxNLI, cli_mode, web_mode

def main():
    """Main entry point for Proxmox Natural Language Interface"""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get default values from environment variables
    default_host = os.getenv('PROXMOX_API_URL', '').replace('https://', '').split(':')[0]
    default_user = os.getenv('PROXMOX_USER', '').split('@')[0]
    default_password = os.getenv('PROXMOX_PASSWORD', '')
    default_realm = os.getenv('PROXMOX_USER', 'root@pam').split('@')[1] if '@' in os.getenv('PROXMOX_USER', 'root@pam') else 'pam'
    default_web_mode = os.getenv('START_WEB_INTERFACE', 'false').lower() == 'true'
    default_debug = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    parser = argparse.ArgumentParser(description='Proxmox Natural Language Interface')
    parser.add_argument('--host', default=default_host, help='Proxmox host')
    parser.add_argument('--user', default=default_user, help='Proxmox user')
    parser.add_argument('--password', default=default_password, help='Proxmox password')
    parser.add_argument('--realm', default=default_realm, help='Proxmox realm')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificate')
    parser.add_argument('--web', action='store_true', default=default_web_mode, help='Start web interface')
    parser.add_argument('--debug', action='store_true', default=default_debug, help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Validate required settings
    if not all([args.host, args.user, args.password]):
        print("Error: Missing required configuration.")
        print("Please ensure PROXMOX_API_URL, PROXMOX_USER, and PROXMOX_PASSWORD are set in .env")
        print("Or provide them as command line arguments: --host, --user, --password")
        sys.exit(1)
    
    if args.web:
        web_mode(args)
    else:
        cli_mode(args.host, args.user, args.password, args.realm, args.verify_ssl)

if __name__ == "__main__":
    main()