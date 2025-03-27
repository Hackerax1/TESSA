# self_healing_tools

Self-Healing Tools for Proxmox NLI.
Provides automated remediation capabilities for common issues in Proxmox environments.

**Module Path**: `proxmox_nli.core.troubleshooting.self_healing_tools`

## Classes

### SelfHealingTools

Provides automated remediation capabilities for common Proxmox issues.

#### __init__(api)

Initialize the self-healing tools.

Args:
    api: Proxmox API client

#### apply_remediation(issue_type: str, context: Dict)

Apply automated remediation for a specific issue type.

Args:
    issue_type: Type of issue to remediate
    context: Additional context for remediation
    
Returns:
    Dict with remediation results

**Returns**: `Dict`

#### fix_service_issue(service: str, node: str)

Fix issues with a service.

Args:
    service: Service to fix
    node: Node to fix service on
    
Returns:
    Dict with service remediation results

**Returns**: `Dict`

#### fix_network_connectivity(context: Dict)

Fix network connectivity issues.

Args:
    context: Additional context for network remediation
    
Returns:
    Dict with network remediation results

**Returns**: `Dict`

#### fix_storage_issue(context: Dict)

Fix storage issues.

Args:
    context: Additional context for storage remediation
    
Returns:
    Dict with storage remediation results

**Returns**: `Dict`

#### fix_high_load(node: str)

Fix high system load issues.

Args:
    node: Node to fix high load on
    
Returns:
    Dict with high load remediation results

**Returns**: `Dict`

#### fix_cluster_issue(node: str)

Fix Proxmox cluster issues.

Args:
    node: Node to fix cluster issues on
    
Returns:
    Dict with cluster remediation results

**Returns**: `Dict`

