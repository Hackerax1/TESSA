"""
Command-line interface module for the Proxmox NLI.
"""
from .core_nli import ProxmoxNLI

def cli_mode(args):
    """Run the Proxmox NLI in command line interface mode"""
    proxmox_nli = ProxmoxNLI(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl
    )
    
    print("Proxmox Natural Language Interface")
    print("Type 'exit' or 'quit' to exit")
    print("Type 'help' to see available commands")
    
    while True:
        try:
            query = input("\n> ").strip()
            if query.lower() in ['exit', 'quit']:
                break
            
            # For pending command confirmation
            if proxmox_nli.pending_command:
                if query.lower() in ['y', 'yes']:
                    response = proxmox_nli.confirm_command(True)
                    print(response)
                elif query.lower() in ['n', 'no']:
                    response = proxmox_nli.confirm_command(False)
                    print(response)
                else:
                    print("Please respond with 'yes' or 'no'")
                continue
            
            # Normal command processing
            response = proxmox_nli.process_query(query)
            print(response)
            
        except KeyboardInterrupt:
            print("\nCommand cancelled. Use 'exit' to quit.")
        except Exception as e:
            print(f"Error: {str(e)}")