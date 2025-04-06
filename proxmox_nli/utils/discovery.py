import logging
import socket
import time
from typing import Dict, List, Optional, Set, Tuple
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, ServiceInfo

logger = logging.getLogger(__name__)

# --- Default Service Definitions ---
# Structure: { 'service_name': (service_type, port) }
DEFAULT_SERVICE_DEFINITIONS = {
    "proxmox": ("_https._tcp.local.", 8006),
    "jellyfin_http": ("_http._tcp.local.", 8096), # Common Jellyfin setup
    # Add other potential Jellyfin types if needed, e.g.:
    # "jellyfin_mdns": ("_jellyfin._tcp.local.", 8096),
    # Immich might be _http or _https on 2283, but lacks standard mDNS
    # "immich_http": ("_http._tcp.local.", 2283)
}
# --- End Service Definitions ---


class ServiceDiscoveryListener(ServiceListener):
    """Listens for multiple mDNS service types and ports."""
    def __init__(self, target_services: Dict[str, Tuple[str, int]]):
        """Initializes the listener with target services.
        
        Args:
            target_services: Dict mapping internal service names to (mdns_type, port).
                             e.g., {'proxmox': ('_https._tcp.local.', 8006)}
        """
        self.found_services: Dict[str, Dict[str, ServiceInfo]] = {name: {} for name in target_services}
        self.target_definitions: Dict[str, Tuple[str, int]] = target_services
        # Create a reverse lookup: (mdns_type, port) -> internal_service_name
        self.type_port_to_name: Dict[Tuple[str, int], str] = {v: k for k, v in target_services.items()}
        self.target_types: Set[str] = {svc_type for svc_type, port in target_services.values()}
        logger.debug(f"Listener initialized for targets: {self.target_definitions}")

    def remove_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        logger.debug(f"Service {name} ({type}) removed")
        # Remove from any category it might be in (though unlikely to match multiple)
        for service_name, service_infos in self.found_services.items():
            if name in service_infos:
                mdns_type, port = self.target_definitions[service_name]
                if mdns_type == type: # Ensure it's the correct type being removed
                     del service_infos[name]
                     logger.info(f"Removed {service_name} instance: {name}")
                     break

    def add_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        if type not in self.target_types:
            # logger.debug(f"Ignoring service type {type} for {name}")
            return
            
        info = zeroconf.get_service_info(type, name)
        # logger.debug(f"Service {name} ({type}) added, service info: {info}")
        if not info or not info.port:
             logger.debug(f"Ignoring service {name} ({type}) due to missing info or port.")
             return

        # Check if this service matches any of our target definitions
        lookup_key = (type, info.port)
        internal_service_name = self.type_port_to_name.get(lookup_key)

        if internal_service_name:
            self.found_services[internal_service_name][name] = info
            addresses = info.parsed_addresses()
            address_str = ', '.join(addresses) if addresses else 'N/A'
            logger.info(f"Found potential {internal_service_name} instance: {name} at {info.server} ({address_str}:{info.port})")
        else:
             logger.debug(f"Service {name} ({type}:{info.port}) did not match any target port/type definition.")


    def update_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        # Often gets called alongside add_service, handle similarly
        self.add_service(zeroconf, type, name)


def discover_network_services(
    service_names: Optional[List[str]] = None,
    timeout: int = 5,
    definitions: Dict[str, Tuple[str, int]] = DEFAULT_SERVICE_DEFINITIONS
) -> Dict[str, List[Dict[str, str]]]:
    """
    Discovers specified services on the local network using mDNS (Zeroconf).

    Args:
        service_names: A list of internal service names to discover (e.g., ["proxmox", "jellyfin_http"]).
                       If None or empty, discovers all services defined in 'definitions'.
        timeout: Time in seconds to wait for responses.
        definitions: A dictionary defining the services to look for.
                     Format: { 'internal_name': (mdns_type, port) }

    Returns:
        A dictionary where keys are the internal service names and values are lists
        of discovered host details for that service.
        e.g., {
            "proxmox": [ { "name": ..., "server": ..., "address": ..., "port": ... } ],
            "jellyfin_http": [ { ... } ]
        }
    """
    zeroconf = None
    browser = None
    results: Dict[str, List[Dict[str, str]]] = {}

    # Determine which services to target
    target_definitions: Dict[str, Tuple[str, int]]
    if not service_names:
        target_definitions = definitions
        logger.info(f"Discovering all defined services: {list(definitions.keys())}")
    else:
        target_definitions = {name: definitions[name] for name in service_names if name in definitions}
        if not target_definitions:
            logger.warning("No valid service names provided for discovery.")
            return {}
        logger.info(f"Discovering specific services: {list(target_definitions.keys())}")

    # Initialize results structure
    for name in target_definitions:
        results[name] = []

    # Get the set of mDNS types to browse for
    types_to_browse = list({svc_type for svc_type, port in target_definitions.values()})
    if not types_to_browse:
         logger.warning("No mDNS types to browse based on selected services.")
         return {}

    try:
        zeroconf = Zeroconf()
        listener = ServiceDiscoveryListener(target_definitions)
        # Browse for all relevant types at once
        browser = ServiceBrowser(zeroconf, types_to_browse, listener)
        logger.info(f"Browsing for {types_to_browse} services for {timeout} seconds...")
        time.sleep(timeout) # Wait for responses
        logger.info("Finished browsing.")

        # Process results gathered by the listener
        for service_name, service_infos in listener.found_services.items():
            for mdns_name, info in service_infos.items():
                if info and info.server: # Ensure server name exists
                    addresses = info.parsed_addresses()
                    if not addresses:
                        logger.warning(f"Skipping service {mdns_name} ({info.server}) as it has no resolved address.")
                        continue

                    # Prefer IPv4 addresses if available
                    ipv4_addresses = [addr for addr in addresses if ':' not in addr] # Simple IPv4 check
                    address = ipv4_addresses[0] if ipv4_addresses else addresses[0] # Fallback to first available

                    host_info = {
                        "name": mdns_name, # Usually like 'hostname._<type>._tcp.local.'
                        "server": info.server.rstrip('.'), # The actual hostname
                        "address": address,
                        "port": info.port,
                        "service_type": service_name # Our internal name (e.g., "proxmox")
                    }
                    
                    # Avoid duplicates based on server/address/port within the same service type list
                    if not any(d['server'] == host_info['server'] and d['address'] == host_info['address'] and d['port'] == host_info['port'] for d in results[service_name]):
                        results[service_name].append(host_info)
                        logger.info(f"Confirmed {service_name} instance: {host_info['server']} ({host_info['address']}:{host_info['port']})")
                    else:
                        logger.debug(f"Skipping duplicate discovery for {service_name}: {host_info}")

    except OSError as e:
         if "Network is unreachable" in str(e) or "socket.gaierror" in str(e):
             logger.error(f"Network error during mDNS discovery: {e}. Ensure network is configured and accessible.")
         else:
             logger.error(f"OS error during mDNS discovery: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error during mDNS discovery: {e}", exc_info=True)
    finally:
        if browser:
            try:
                browser.cancel()
            except Exception as e:
                 logger.error(f"Error cancelling service browser: {e}", exc_info=True)
        if zeroconf:
            try:
                zeroconf.close()
            except Exception as e:
                 logger.error(f"Error closing zeroconf: {e}", exc_info=True)

    total_found = sum(len(hosts) for hosts in results.values())
    logger.info(f"Discovery found {total_found} total service instances across requested types.")
    return results

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("\nStarting discovery for ALL defined services...")
    all_hosts = discover_network_services(timeout=5)
    if all_hosts:
        print("\nDiscovered Services:")
        for service_name, hosts in all_hosts.items():
            if hosts:
                print(f"  {service_name.upper()}:")
                for host in hosts:
                     print(f"    - Server: {host['server']} ({host['address']}:{host['port']})")
            else:
                 print(f"  {service_name.upper()}: None found")
    else:
        print("No services found on the network via mDNS.")

    print("\nStarting discovery specifically for Proxmox...")
    proxmox_only = discover_network_services(service_names=["proxmox"], timeout=3)
    if proxmox_only.get("proxmox"):
        print("\nDiscovered Proxmox Instances:")
        for host in proxmox_only["proxmox"]:
            print(f"  - Server: {host['server']} ({host['address']}:{host['port']})")
    else:
        print("No Proxmox instances found.")
