# pxe_manager

PXE Manager module for Proxmox NLI.
Handles PXE boot service configuration and management.

**Module Path**: `proxmox_nli.core.network.pxe_manager`

## Classes

### PXEManager

#### __init__(api)

#### enable_pxe_service(network_interface: str, subnet: str = 'vmbr0')

Enable PXE boot service

Args:
    network_interface: Network interface to serve PXE on
    subnet: Subnet to serve DHCP on (optional)
    
Returns:
    dict: Result of operation

**Returns**: `dict`

#### disable_pxe_service()

Disable PXE boot service

Returns:
    dict: Result of operation

**Returns**: `dict`

#### upload_boot_image(image_type: str, image_path: str)

Upload a boot image for PXE

Args:
    image_type: Type of image (e.g., 'ubuntu', 'centos')
    image_path: Local path to boot image
    
Returns:
    dict: Result of operation

**Returns**: `dict`

#### list_boot_images()

List available boot images

Returns:
    dict: List of available boot images

**Returns**: `dict`

#### get_pxe_status()

Get PXE service status

Returns:
    dict: Status of PXE services

**Returns**: `dict`

