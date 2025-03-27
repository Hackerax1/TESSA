# dns_provider

DNS Provider integration module for managing DNS configurations across different providers.

**Module Path**: `proxmox_nli.core.integration.dns_provider`

## Classes

### DNSProviderBase

Abstract base class for DNS provider implementations

#### authenticate()

Authenticate with the DNS provider

**Returns**: `Dict[(str, Any)]`

#### list_records(domain: str)

List DNS records for a domain

**Returns**: `Dict[(str, Any)]`

#### add_record(domain: str, record_type: str, name: str, content: str, ttl: int)

Add a new DNS record

**Returns**: `Dict[(str, Any)]`

#### update_record(record_id: str, updates: Dict[(str, Any)])

Update an existing DNS record

**Returns**: `Dict[(str, Any)]`

#### delete_record(record_id: str)

Delete a DNS record

**Returns**: `Dict[(str, Any)]`

### DNSProvider

Main class for managing DNS provider integrations

#### __init__(config_dir: str)

Initialize with optional config directory path

#### configure_provider(provider: str, credentials: Dict[(str, Any)])

Configure a DNS provider with credentials

**Returns**: `Dict[(str, Any)]`

#### add_zone(domain: str, provider: str)

Add a new DNS zone configuration

**Returns**: `Dict[(str, Any)]`

#### sync_records(domain: str)

Sync DNS records for specified domain or all configured zones

**Returns**: `Dict[(str, Any)]`

#### update_record(domain: str, record_id: str, updates: Dict[(str, Any)])

Update a DNS record

**Returns**: `Dict[(str, Any)]`

#### add_record(domain: str, record_type: str, name: str, content: str, ttl: int)

Add a new DNS record

**Returns**: `Dict[(str, Any)]`

#### delete_record(domain: str, record_id: str)

Delete a DNS record

**Returns**: `Dict[(str, Any)]`

