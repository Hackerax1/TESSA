import logging
import os
import platform
from typing import List, Dict

logger = logging.getLogger(__name__)

# --- Platform specific configuration ---
if platform.system() == "Windows":
    HOSTS_FILE_PATH = r"C:\Windows\System32\drivers\etc\hosts"
else: # Assume Linux/macOS path
    HOSTS_FILE_PATH = "/etc/hosts"

MANAGEMENT_MARKER = "# Managed by ProxmoxNLI"
# --- End Platform specific configuration ---

def _parse_hosts_file(file_path: str) -> tuple[List[str], Dict[str, str]]:
    """Parses the hosts file, separating managed entries from others."""
    other_lines = []
    managed_entries = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                stripped_line = line.strip()
                if MANAGEMENT_MARKER in line:
                    parts = stripped_line.split()
                    # Expecting format: IP HOSTNAME # Managed by ProxmoxNLI [Optional comments]
                    if len(parts) >= 3 and parts[0] != '#':
                        ip, hostname = parts[0], parts[1]
                        # Simple validation (can be improved)
                        if '.' in ip or ':' in ip: # Basic IP check
                             managed_entries[hostname.lower()] = ip
                        else:
                            logger.warning(f"Skipping potentially malformed managed line: {line.strip()}")
                            other_lines.append(line) # Keep malformed managed lines as is
                    else:
                         other_lines.append(line) # Keep comment lines with the marker
                else:
                    other_lines.append(line)
    except FileNotFoundError:
        logger.warning(f"Hosts file not found at {file_path}. Will attempt to create it.")
    except Exception as e:
        logger.error(f"Error reading hosts file {file_path}: {e}", exc_info=True)
        raise # Re-raise critical errors

    # Ensure the file ends with a newline if it had content
    if other_lines and not other_lines[-1].endswith(os.linesep):
        other_lines[-1] += os.linesep

    return other_lines, managed_entries

def _check_hostname_exists(hostname: str, lines: List[str]) -> bool:
    """Checks if a hostname exists in non-managed lines."""
    hostname_lower = hostname.lower()
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue
        parts = stripped_line.split()
        if len(parts) >= 2:
            # Check all hostnames on the line
            for part in parts[1:]:
                 if part.lower() == hostname_lower:
                     return True
    return False


def update_hosts_file(discovered_hosts: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Updates the system's hosts file with discovered Proxmox instances.

    Args:
        discovered_hosts: A list of dictionaries, each containing at least
                          'server' (hostname) and 'address' (IP).

    Returns:
        A dictionary summarizing the outcome, e.g.,
        {"success": True/False, "message": "...", "added": [], "updated": [], "skipped": []}
    """
    results = {"success": False, "message": "", "added": [], "updated": [], "skipped": []}
    if not os.path.exists(HOSTS_FILE_PATH):
         # Check if directory exists, try to create an empty file if needed. Permissions might still fail.
        dir_name = os.path.dirname(HOSTS_FILE_PATH)
        if not os.path.exists(dir_name):
             results["message"] = f"Hosts file directory does not exist: {dir_name}"
             logger.error(results["message"])
             return results
        try:
            # Create an empty file to parse correctly
            with open(HOSTS_FILE_PATH, 'w') as f:
                pass
            logger.info(f"Created empty hosts file at {HOSTS_FILE_PATH}")
        except PermissionError:
            results["message"] = f"Permission denied to create hosts file at {HOSTS_FILE_PATH}. Please run as administrator."
            logger.error(results["message"])
            return results
        except Exception as e:
             results["message"] = f"Failed to create hosts file at {HOSTS_FILE_PATH}: {e}"
             logger.error(results["message"], exc_info=True)
             return results


    try:
        other_lines, managed_entries = _parse_hosts_file(HOSTS_FILE_PATH)
    except Exception as e:
        results["message"] = f"Failed to parse hosts file: {e}"
        return results

    current_managed = managed_entries.copy() # Hostnames currently managed by us
    seen_hostnames = set()                 # Hostnames from the latest discovery

    new_host_lines = []

    for host in discovered_hosts:
        hostname = host.get('server')
        ip = host.get('address')

        if not hostname or not ip:
            logger.warning(f"Skipping host entry due to missing hostname or IP: {host}")
            continue

        hostname_lower = hostname.lower()
        seen_hostnames.add(hostname_lower)

        if hostname_lower in current_managed:
            if current_managed[hostname_lower] != ip:
                logger.info(f"Updating managed host: {hostname} -> {ip} (was {current_managed[hostname_lower]})")
                new_host_lines.append(f"{ip}\t{hostname}\t{MANAGEMENT_MARKER}\n")
                results["updated"].append(f"{hostname} -> {ip}")
            else:
                # No change needed, add existing entry back
                new_host_lines.append(f"{ip}\t{hostname}\t{MANAGEMENT_MARKER}\n")
                # results["skipped"].append(f"{hostname} (no change)") # Less verbose
        else:
            # Check if hostname exists in *other* (unmanaged) lines
            if _check_hostname_exists(hostname, other_lines):
                 logger.warning(f"Skipping host '{hostname}': Found existing unmanaged entry in hosts file.")
                 results["skipped"].append(f"{hostname} (existing unmanaged entry)")
            else:
                logger.info(f"Adding new managed host: {hostname} -> {ip}")
                new_host_lines.append(f"{ip}\t{hostname}\t{MANAGEMENT_MARKER}\n")
                results["added"].append(f"{hostname} -> {ip}")

    # Optional: Remove old managed entries not present in the current discovery
    # for hostname, ip in current_managed.items():
    #     if hostname not in seen_hostnames:
    #         logger.info(f"Removing stale managed host: {hostname} ({ip})")
    #         results["removed"].append(hostname) # Need to adjust message if implementing removal

    # Combine non-managed lines and new/updated managed lines
    final_content = "".join(other_lines)
    if other_lines and not final_content.endswith(os.linesep): # Ensure separation
        final_content += os.linesep
    final_content += "".join(new_host_lines)

    try:
        # Write back to the hosts file
        with open(HOSTS_FILE_PATH, 'w') as f:
            f.write(final_content)
        logger.info(f"Successfully updated hosts file: {HOSTS_FILE_PATH}")
        results["success"] = True
        message_parts = []
        if results["added"]: message_parts.append(f"Added: {', '.join(results['added'])}")
        if results["updated"]: message_parts.append(f"Updated: {', '.join(results['updated'])}")
        if results["skipped"]: message_parts.append(f"Skipped: {', '.join(results['skipped'])}")
        if not message_parts: message_parts.append("No changes needed.")
        results["message"] = f"Hosts file update complete. {'. '.join(message_parts)}"

    except PermissionError:
        logger.error(f"Permission denied writing to hosts file: {HOSTS_FILE_PATH}. Please run as administrator.")
        results["message"] = f"Permission denied updating hosts file. Please run the application as administrator."
    except Exception as e:
        logger.error(f"Error writing hosts file {HOSTS_FILE_PATH}: {e}", exc_info=True)
        results["message"] = f"An unexpected error occurred while writing to the hosts file: {e}"

    return results

if __name__ == '__main__':
    # Example Usage (requires running as admin on Windows/root on Linux/macOS)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print(f"Attempting to update hosts file: {HOSTS_FILE_PATH}")
    # Dummy data for testing
    test_hosts = [
        {'server': 'pve-node1.lan', 'address': '192.168.1.101'},
        {'server': 'pve-node2', 'address': '192.168.1.102'},
        {'server': 'existing-unmanaged', 'address': '1.1.1.1'}, # Should be skipped if present unmanaged
        {'server': 'old-managed-host', 'address': '10.0.0.5'} # Should be updated/added
    ]
    # Simulate a discovery run
    discovered = [
         {'server': 'pve-node1.lan', 'address': '192.168.1.101'}, # same
         {'server': 'pve-node2', 'address': '192.168.1.199'}, # updated IP
         {'server': 'pve-new', 'address': '192.168.1.105'}, # new
         {'server': 'existing-unmanaged', 'address': '1.1.1.1'} # skipped
    ]

    print("\nRunning update with sample data...")
    result = update_hosts_file(discovered)
    print("\nUpdate Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Message: {result.get('message')}")
    # print(f"  Added: {result.get('added')}")
    # print(f"  Updated: {result.get('updated')}")
    # print(f"  Skipped: {result.get('skipped')}")

    print("\nNote: If the operation failed due to permissions, please re-run this script as administrator/root.")
