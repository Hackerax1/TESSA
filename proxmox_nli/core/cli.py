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
        query = input("\n> ")
        if query.lower() in ['exit', 'quit']:
            break
        
        response = proxmox_nli.process_query(query)
        print(response)