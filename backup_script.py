import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PROXMOX_API_URL = os.getenv('PROXMOX_API_URL')
PROXMOX_USER = os.getenv('PROXMOX_USER')
PROXMOX_PASSWORD = os.getenv('PROXMOX_PASSWORD')
BACKUP_DIR = os.getenv('BACKUP_DIR', '/backups')


def backup_vm(vm_id):
    """Backup a VM"""
    url = f"{PROXMOX_API_URL}/nodes/{PROXMOX_USER}/qemu/{vm_id}/status/start"
    response = requests.post(url, auth=(PROXMOX_USER, PROXMOX_PASSWORD))
    if response.status_code == 200:
        print(f"VM {vm_id} backed up successfully")
    else:
        print(f"Failed to backup VM {vm_id}: {response.text}")


def main():
    # List of VM IDs to backup
    vm_ids = [100, 101, 102]  # Replace with your VM IDs
    for vm_id in vm_ids:
        backup_vm(vm_id)


if __name__ == "__main__":
    main()