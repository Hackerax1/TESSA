# proxmox_api

Proxmox API interface module.

**Module Path**: `proxmox_nli.api.proxmox_api`

## Classes

### ProxmoxAPI

#### __init__(host, user, password, realm, verify_ssl = 'pam')

#### authenticate()

Authenticate with Proxmox API and get ticket and CSRF token

#### api_request(method, endpoint, data)

Make a request to the Proxmox API

