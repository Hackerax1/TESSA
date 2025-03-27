# certificate_manager

Certificate Manager for Proxmox NLI.
Provides natural language interfaces for SSL certificate management.

**Module Path**: `proxmox_nli.core.security.certificate_manager`

## Classes

### CertificateManager

Manages SSL certificates with natural language interfaces

#### __init__(api, base_nli)

Initialize the certificate manager

Args:
    api: Proxmox API client
    base_nli: Base NLI instance for accessing other components

#### list_certificates()

List all certificates in the system

Returns:
    Dictionary with certificate information

**Returns**: `Dict[(str, Any)]`

#### generate_self_signed_certificate(domain: str, email: Optional[str])

Generate a self-signed certificate

Args:
    domain: Domain name for the certificate
    email: Email address for the certificate
    
Returns:
    Dictionary with generation result

**Returns**: `Dict[(str, Any)]`

#### request_lets_encrypt_certificate(domain: str, email: str)

Request a Let's Encrypt certificate

Args:
    domain: Domain name for the certificate
    email: Email address for Let's Encrypt account
    
Returns:
    Dictionary with request result

**Returns**: `Dict[(str, Any)]`

#### interpret_certificate_command(command: str)

Interpret a natural language certificate command

Args:
    command: Natural language command for certificate management
    
Returns:
    Dictionary with interpreted command and parameters

**Returns**: `Dict[(str, Any)]`

#### generate_certificate_report()

Generate a report on certificate status

Returns:
    Dictionary with certificate report

**Returns**: `Dict[(str, Any)]`

