# proxmox_commands

**Module Path**: `proxmox_nli.commands.proxmox_commands`

## Classes

### ProxmoxCommands

#### __init__(api)

#### list_vms()

Get a list of all VMs with their status

#### get_cluster_status()

Get status of all nodes in the cluster

#### start_vm(vm_id)

Start a VM

#### stop_vm(vm_id)

Stop a VM

#### restart_vm(vm_id)

Restart a VM

#### get_vm_status(vm_id)

Get the status of a VM

#### create_vm(params)

Create a new VM with the given parameters

#### delete_vm(vm_id)

Delete a VM

#### list_containers()

List all containers

#### get_node_status(node)

Get the status of a node

#### get_storage_info()

Get storage information

#### get_vm_location(vm_id)

Get the node where a VM is located

#### get_help()

Get help information

#### create_backup(vm_id: str, mode: str, storage: str = 'snapshot', compression: str = None, notes: str = 'zstd')

Create a backup of a VM.

Args:
    vm_id: VM ID
    mode: Backup mode (snapshot or suspend)
    storage: Storage location
    compression: Compression algorithm
    notes: Backup notes
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### restore_backup(vm_id: str, backup_file: str, target_storage: str, restore_options: Dict = None)

Restore a VM from backup.

Args:
    vm_id: VM ID
    backup_file: Backup file path
    target_storage: Target storage location
    restore_options: Additional restore options
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### list_backups(vm_id: str)

List available backups.

Args:
    vm_id: Optional VM ID to filter backups
    
Returns:
    Dict: List of backups

**Returns**: `Dict`

#### delete_backup(backup_id: str)

Delete a backup.

Args:
    backup_id: Backup ID
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### verify_backup(vm_id: str, backup_file: str)

Verify a backup's integrity.

Args:
    vm_id: VM ID
    backup_file: Optional backup file path
    
Returns:
    Dict: Verification result

**Returns**: `Dict`

#### create_zfs_pool(node: str, name: str, devices: list, raid_level: str)

Create a ZFS storage pool on a node.

Args:
    node: Node name
    name: Pool name
    devices: List of device paths
    raid_level: ZFS raid level (mirror, raidz, raidz2, etc.)

**Returns**: `dict`

#### get_zfs_pools(node: str)

Get ZFS pool information from a node.

**Returns**: `dict`

#### get_zfs_datasets(node: str, pool: str)

Get ZFS dataset information.

**Returns**: `dict`

#### create_zfs_dataset(node: str, name: str, options: dict)

Create a ZFS dataset with options.

**Returns**: `dict`

#### set_zfs_properties(node: str, dataset: str, properties: dict)

Set ZFS dataset properties.

**Returns**: `dict`

#### create_zfs_snapshot(node: str, dataset: str, snapshot_name: str, recursive: bool)

Create a ZFS snapshot.

**Returns**: `dict`

#### setup_auto_snapshots(node: str, dataset: str, schedule: str)

Configure automatic ZFS snapshots.

**Returns**: `dict`

#### configure_cloudflare_domain(domain_name, email, api_key)

Configure a domain with Cloudflare

#### setup_cloudflare_tunnel(domain_name, tunnel_name)

Set up a Cloudflare tunnel for a domain

#### list_cloudflare_domains()

List all configured Cloudflare domains

#### list_cloudflare_tunnels()

List all configured Cloudflare tunnels

#### remove_cloudflare_domain(domain_name)

Remove a domain from Cloudflare configuration

#### analyze_vm_resources(vm_id: str, days: int)

Analyze VM resource usage and provide optimization recommendations

**Returns**: `dict`

#### get_cluster_efficiency()

Get cluster efficiency metrics and recommendations

**Returns**: `dict`

#### configure_backup(vm_id: str, schedule: dict)

Configure automated backups for a VM

**Returns**: `dict`

#### create_backup(vm_id: str)

Create a backup of a VM

**Returns**: `dict`

#### verify_backup(vm_id: str)

Verify a VM's backup integrity

**Returns**: `dict`

#### restore_backup(vm_id: str, backup_file: str)

Restore a VM from backup

**Returns**: `dict`

#### configure_remote_storage(storage_type: str, config: dict)

Configure remote backup storage

**Returns**: `dict`

#### get_backup_status(vm_id: str)

Get backup status for VMs

**Returns**: `dict`

#### setup_network_segmentation()

Set up initial network segmentation with VLANs

**Returns**: `dict`

#### create_network_segment(name: str, vlan_id: int, subnet: str, purpose: str)

Create a new network segment

**Returns**: `dict`

#### get_network_recommendations(service_type: str)

Get network configuration recommendations for a service

**Returns**: `dict`

#### configure_service_network(service_id: str, service_type: str, vm_id: str)

Configure network for a service

**Returns**: `dict`

#### analyze_network_security()

Analyze network security and provide recommendations

**Returns**: `dict`

#### auto_configure_node(node: str)

Automatically configure initial Proxmox network and storage settings

**Returns**: `dict`

#### configure_network(node: str, use_dhcp: bool)

Configure network settings for a node using auto-detection

**Returns**: `dict`

#### set_network_profile(profile_name: str)

Set the default network profile for auto-configuration

**Returns**: `dict`

#### create_network_profile(name: str, subnet: str, gateway: str, dns_servers: list)

Create a new network profile for auto-configuration

**Returns**: `dict`

#### detect_network_interfaces(node: str)

Detect available network interfaces on a node

**Returns**: `dict`

#### scan_network_for_devices(subnet: str)

Scan network for SSH-accessible devices

Args:
    subnet (str, optional): Subnet to scan in CIDR notation. Defaults to local subnet.

Returns:
    dict: Scan results

**Returns**: `dict`

#### discover_ssh_devices(subnet: str, username: str = None, password: str = 'root')

Discover and add SSH devices on the network

Args:
    subnet (str, optional): Subnet to scan in CIDR notation. Defaults to local subnet.
    username (str, optional): Default username for connections. Defaults to "root".
    password (str, optional): Default password for connections. Defaults to None.

Returns:
    dict: Discovery results

**Returns**: `dict`

#### list_ssh_devices(device_type: str)

List all SSH devices or devices of a specific type

Args:
    device_type (str, optional): Filter by device type. Defaults to None.

Returns:
    dict: List of devices

**Returns**: `dict`

#### get_ssh_device_groups()

Get devices grouped by their type

Returns:
    dict: Device groups

**Returns**: `dict`

#### add_ssh_device(hostname: str, name: str, username: str = None, password: str = 'root', port: int = None, description: str = 22, tags: List[str] = '')

Add an SSH device manually

Args:
    hostname (str): IP or hostname of the device
    name (str, optional): User-friendly name. Defaults to hostname.
    username (str, optional): Username for SSH. Defaults to "root".
    password (str, optional): Password for SSH. Defaults to None.
    port (int, optional): SSH port. Defaults to 22.
    description (str, optional): Description of the device. Defaults to "".
    tags (List[str], optional): Tags for the device. Defaults to None.

Returns:
    dict: Result of operation

**Returns**: `dict`

#### remove_ssh_device(hostname: str)

Remove an SSH device

Args:
    hostname (str): IP or hostname of the device

Returns:
    dict: Result of operation

**Returns**: `dict`

#### execute_ssh_command(hostname: str, command: str)

Execute a command on an SSH device

Args:
    hostname (str): IP or hostname of the device
    command (str): Command to execute

Returns:
    dict: Command execution results

**Returns**: `dict`

#### execute_ssh_command_on_multiple(hostnames: List[str], command: str)

Execute a command on multiple SSH devices

Args:
    hostnames (List[str]): List of IPs or hostnames
    command (str): Command to execute

Returns:
    dict: Command execution results for each device

**Returns**: `dict`

#### execute_ssh_command_on_group(group_name: str, command: str)

Execute a command on a group of SSH devices

Args:
    group_name (str): Group name (device type)
    command (str): Command to execute

Returns:
    dict: Command execution results for each device

**Returns**: `dict`

#### setup_ssh_keys(hostnames: List[str], key_path: str)

Set up SSH key authentication for multiple devices

Args:
    hostnames (List[str]): List of IPs or hostnames
    key_path (str, optional): Path to existing SSH key. Defaults to None.

Returns:
    dict: Results of key setup

**Returns**: `dict`

#### setup_ssh_keys_for_group(group_name: str, key_path: str)

Set up SSH key authentication for a group of devices

Args:
    group_name (str): Group name (device type)
    key_path (str, optional): Path to existing SSH key. Defaults to None.

Returns:
    dict: Results of key setup

**Returns**: `dict`

#### create_vlan(name: str, vlan_id: int, subnet: str, purpose: str)

Create a new VLAN

**Returns**: `dict`

#### configure_firewall_rule(rule: dict)

Configure a firewall rule

**Returns**: `dict`

#### ssh_into_device(hostname: str, username: str, port: int = 'root')

SSH into a device on the network

**Returns**: `dict`

#### setup_pxe_service()

Set up PXE service for network booting

**Returns**: `dict`

#### create_vlan(name: str, vlan_id: int, subnet: str, purpose: str)

Create a new VLAN

Args:
    name: Name of the VLAN
    vlan_id: VLAN ID (1-4094)
    subnet: Subnet in CIDR notation (e.g., 192.168.10.0/24)
    purpose: Purpose of the VLAN

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### list_vlans()

List all configured VLANs

Returns:
    dict: List of VLANs

**Returns**: `dict`

#### delete_vlan(vlan_id: int, bridge: str)

Delete a VLAN

Args:
    vlan_id: VLAN ID to delete
    bridge: Bridge interface (default: vmbr0)

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### assign_vm_to_vlan(vm_id: int, vlan_id: int)

Assign a VM to a VLAN

Args:
    vm_id: ID of the VM
    vlan_id: ID of the VLAN

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### add_firewall_rule(rule: dict)

Add a firewall rule

Args:
    rule: Firewall rule definition including:
        - action: ACCEPT, DROP, REJECT
        - type: in, out
        - proto: Protocol (tcp, udp, etc.)
        - dport: Destination port(s)
        - source: Source address (optional)
        - dest: Destination address (optional)
        - comment: Rule description

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### list_firewall_rules()

List all firewall rules

Returns:
    dict: List of firewall rules

**Returns**: `dict`

#### delete_firewall_rule(rule_id: int)

Delete a firewall rule

Args:
    rule_id: ID of the rule to delete

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### add_service_firewall_rules(service_name: str, ports: List[int], sources: List[str])

Add firewall rules for a service

Args:
    service_name: Name of the service (for comments)
    ports: List of ports to allow
    sources: List of source IPs/networks (None for any)

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### get_firewall_status()

Get firewall status

Returns:
    dict: Firewall status information

**Returns**: `dict`

#### ssh_into_device(hostname: str, username: str, port: int = 'root')

SSH into a network device

Args:
    hostname: Hostname or IP address
    username: SSH username
    port: SSH port

Returns:
    dict: SSH connection information

**Returns**: `dict`

#### setup_pxe_service(network_interface: str, subnet: str = 'vmbr0')

Set up PXE service for network booting

Args:
    network_interface: Network interface to serve PXE on
    subnet: Subnet for DHCP (optional)

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### disable_pxe_service()

Disable PXE boot service

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### get_pxe_status()

Get PXE service status

Returns:
    dict: Status of PXE services

**Returns**: `dict`

#### upload_pxe_boot_image(image_type: str, image_path: str)

Upload a boot image for PXE

Args:
    image_type: Type of image (e.g., 'ubuntu', 'centos')
    image_path: Local path to boot image

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### list_pxe_boot_images()

List available PXE boot images

Returns:
    dict: List of boot images

**Returns**: `dict`

#### add_dns_record(hostname: str, ip_address: str, comment: str)

Add a DNS record

Args:
    hostname: Hostname to add
    ip_address: IP address for hostname
    comment: Optional comment

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### list_dns_records()

List all DNS records

Returns:
    dict: List of DNS records

**Returns**: `dict`

#### update_dns_servers(servers: List[str])

Update DNS servers

Args:
    servers: List of DNS server IP addresses

Returns:
    dict: Result of the operation

**Returns**: `dict`

#### merge_existing_proxmox(conflict_resolution: str)

Merge an existing Proxmox environment into TESSA

This detects, analyzes and imports configurations from an existing Proxmox environment.

Args:
    conflict_resolution: How to resolve conflicts - "ask", "tessa_priority", "existing_priority", "merge"
    
Returns:
    dict: Results of the merge operation

**Returns**: `dict`

#### discover_proxmox_environment()

Discover details about the existing Proxmox environment

Returns:
    dict: Discovered environment details

**Returns**: `dict`

#### analyze_proxmox_environment()

Analyze the existing Proxmox environment for potential merge points

Returns:
    dict: Analysis results with recommendations

**Returns**: `dict`

#### set_environment_merge_options(options: dict)

Set options for merging environments

Args:
    options: Dictionary with option flags:
        - storage_pools: Whether to merge storage pools
        - network_config: Whether to merge network configurations
        - virtual_machines: Whether to merge VM inventory
        - containers: Whether to merge container inventory
        - users_and_permissions: Whether to merge users and permissions
        - backups: Whether to merge backup configurations
        - firewall_rules: Whether to merge firewall rules
        - ha_settings: Whether to merge HA settings
        
Returns:
    dict: Updated merge options

**Returns**: `dict`

#### get_merge_history()

Get history of previously merged environments

Returns:
    dict: History of merged environments

**Returns**: `dict`

#### start_backup_scheduler()

Start the backup scheduler service.

Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### stop_backup_scheduler()

Stop the backup scheduler service.

Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### get_scheduler_status()

Get the status of the backup scheduler.

Returns:
    Dict: Scheduler status information

**Returns**: `Dict`

#### schedule_backup(vm_id: str, schedule: Dict)

Configure backup schedule for a VM.

Args:
    vm_id: VM ID
    schedule: Schedule configuration with frequency, time, etc.
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### configure_recovery_testing(config: Dict)

Configure automated recovery testing.

Args:
    config: Recovery testing configuration
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### configure_retention_policy(vm_id: str, policy: Dict)

Configure backup retention policy for a VM.

Args:
    vm_id: VM ID
    policy: Retention policy configuration
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_backup_now(vm_id: str)

Run a backup immediately.

Args:
    vm_id: VM ID
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_recovery_test_now(vm_ids: Optional[List[str]])

Run a recovery test immediately.

Args:
    vm_ids: Optional list of VM IDs to test
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_retention_enforcement_now()

Run retention policy enforcement immediately.

Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_deduplication_now()

Run data deduplication immediately.

Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### configure_notifications(config: Dict)

Configure backup notifications.

Args:
    config: Notification configuration
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### run_security_audit(scope: str)

Run a security audit on the system.

Args:
    scope: Audit scope (full, updates, firewall, permissions, certificates)
    
Returns:
    Dict: Audit results

**Returns**: `Dict`

#### get_audit_history(limit: int)

Get security audit history.

Args:
    limit: Maximum number of audit records to retrieve
    
Returns:
    Dict: Audit history

**Returns**: `Dict`

#### manage_permissions(action: str, user: str, role: str)

Manage user permissions.

Args:
    action: Action to perform (add, remove, list)
    user: Username
    role: Role name (required for add/remove)
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### manage_certificates(action: str, domain: str, email: str = None)

Manage SSL certificates.

Args:
    action: Action to perform (list, generate_self_signed, request_lets_encrypt, check)
    domain: Domain name (required for generate/request)
    email: Email address (required for Let's Encrypt)
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### manage_firewall(action: str, port: str, protocol: str = None, service: str = 'tcp', source: str = None)

Manage firewall rules.

Args:
    action: Action to perform (list, allow, deny, delete)
    port: Port number (required for allow/deny)
    protocol: Protocol (tcp, udp)
    service: Service name (alternative to port)
    source: Source IP/network
    
Returns:
    Dict: Result of the operation

**Returns**: `Dict`

#### assess_security_posture(area: str)

Assess the security posture of the system.

Args:
    area: Specific security area to assess (system_hardening, network_security, 
          authentication, updates_patching, monitoring_logging)
    
Returns:
    Dict: Security posture assessment

**Returns**: `Dict`

#### generate_security_report()

Generate a comprehensive security posture report.

Returns:
    Dict: Security posture report

**Returns**: `Dict`

#### get_security_recommendations(area: str)

Get security improvement recommendations.

Args:
    area: Specific security area for recommendations
    
Returns:
    Dict: Security recommendations

**Returns**: `Dict`

#### diagnose_issue(issue_type: str, context: str)

Run diagnostics for a specific issue type.

Args:
    issue_type: Type of issue to diagnose (vm, container, network, storage, service, security, performance)
    context: Additional context for the diagnostics
    
Returns:
    Dict: Diagnostic results

**Returns**: `Dict`

#### analyze_logs(log_type: str, context: str = None)

Analyze logs for issues and patterns.

Args:
    log_type: Type of logs to analyze (vm, container, node, cluster, service)
    context: Additional context for log analysis
    
Returns:
    Dict: Log analysis results

**Returns**: `Dict`

#### run_network_diagnostics(diagnostic_type: str, context: str)

Run network diagnostics.

Args:
    diagnostic_type: Type of network diagnostic to run (connectivity, dns, ports, visualization)
    context: Additional context for the diagnostics
    
Returns:
    Dict: Network diagnostic results

**Returns**: `Dict`

#### analyze_performance(resource_type: str, context: str = 'all')

Analyze system performance.

Args:
    resource_type: Type of resource to analyze (cpu, memory, disk, network, all)
    context: Additional context for performance analysis
    
Returns:
    Dict: Performance analysis results

**Returns**: `Dict`

#### auto_resolve_issues(issue_type: str, context: str)

Automatically resolve identified issues.

Args:
    issue_type: Type of issue to resolve (vm, container, network, storage, service, security, performance)
    context: Additional context for issue resolution
    
Returns:
    Dict: Resolution results

**Returns**: `Dict`

#### generate_troubleshooting_report(report_format: str, issue_type: str = 'text', context: str = None)

Generate a troubleshooting report.

Args:
    report_format: Format of the report (text, html, json)
    issue_type: Type of issue to include in the report
    context: Additional context for report generation
    
Returns:
    Dict: Report generation results

**Returns**: `Dict`

#### view_troubleshooting_history(issue_type: str, limit: int = None)

View troubleshooting history.

Args:
    issue_type: Type of issue to filter by
    limit: Maximum number of history entries to return
    
Returns:
    Dict: Troubleshooting history

**Returns**: `Dict`

