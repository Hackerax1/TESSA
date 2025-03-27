# pxe_manager

PXE boot service management operations for Proxmox NLI.

**Module Path**: `proxmox_nli.commands.network.pxe_manager`

## Classes

### PXEManager

#### __init__(api)

#### enable_pxe_service(network_interface: str, subnet: Optional[str] = 'vmbr0')

Set up PXE service for network booting

Args:
    network_interface: Network interface to serve PXE on
    subnet: Optional subnet for DHCP
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### disable_pxe_service()

Disable PXE boot service

Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### get_pxe_status()

Get PXE service status

Returns:
    Dict with service status

**Returns**: `Dict[(str, Any)]`

#### upload_boot_image(image_type: str, image_path: str)

Upload a boot image for PXE

Args:
    image_type: Type of image (e.g., 'ubuntu', 'centos')
    image_path: Local path to boot image
    
Returns:
    Dict with operation result

**Returns**: `Dict[(str, Any)]`

#### list_boot_images()

List available PXE boot images

Returns:
    Dict with list of boot images

**Returns**: `Dict[(str, Any)]`

