#!/usr/bin/env python3
import argparse
from proxmox_nli.core.proxmox_nli import ProxmoxNLI, cli_mode, web_mode

def main():
    """Main entry point for Proxmox Natural Language Interface"""
    parser = argparse.ArgumentParser(description='Proxmox Natural Language Interface')
    parser.add_argument('--host', required=True, help='Proxmox host')
    parser.add_argument('--user', required=True, help='Proxmox user')
    parser.add_argument('--password', required=True, help='Proxmox password')
    parser.add_argument('--realm', default='pam', help='Proxmox realm')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificate')
    parser.add_argument('--web', action='store_true', help='Start as web server with voice recognition')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (web server only)')
    
    args = parser.parse_args()
    
    try:
        if args.web:
            web_mode(args)
        else:
            cli_mode(args)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()