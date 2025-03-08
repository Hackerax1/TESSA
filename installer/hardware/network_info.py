import socket
import psutil
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NetworkInfoManager:
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """Get information about network interfaces."""
        network_info = {
            "interfaces": [],
            "hostname": socket.gethostname()
        }
        
        # Try to get external IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            network_info["primary_ip"] = s.getsockname()[0]
            s.close()
        except Exception as e:
            logger.debug(f"Could not determine primary IP: {str(e)}")
        
        # Get interface details
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for interface_name, addresses in interfaces.items():
            interface_info = {
                "name": interface_name,
                "addresses": [],
                "is_up": False
            }
            
            # Add status information if available
            if interface_name in stats:
                stat = stats[interface_name]
                interface_info.update({
                    "is_up": stat.isup,
                    "speed": stat.speed,
                    "mtu": stat.mtu,
                    "duplex": stat.duplex if hasattr(stat, 'duplex') else None
                })
            
            # Add address information
            for address in addresses:
                addr_info = {
                    "family": str(address.family),
                    "address": address.address
                }
                
                if hasattr(address, 'netmask') and address.netmask:
                    addr_info["netmask"] = address.netmask
                    
                if hasattr(address, 'broadcast') and address.broadcast:
                    addr_info["broadcast"] = address.broadcast
                    
                interface_info["addresses"].append(addr_info)
                
            network_info["interfaces"].append(interface_info)
            
        return network_info