# environment_merger

Environment Merger module for integrating existing Proxmox environments into TESSA.
Handles discovery, analysis, and merging of existing Proxmox configurations.

**Module Path**: `proxmox_nli.core.integration.environment_merger`

## Classes

### EnvironmentMerger

Class for detecting and merging existing Proxmox environments into TESSA

#### __init__(api: ProxmoxAPI, base_dir: str)

Initialize with Proxmox API connection

#### discover_environment()

Discover details about the existing Proxmox environment

**Returns**: `Dict`

#### analyze_environment(environment: Dict)

Analyze the discovered environment and identify merge points

**Returns**: `Dict`

#### generate_merge_plan(environment: Dict, analysis: Dict)

Generate a plan for merging the environment

**Returns**: `Dict`

#### execute_merge(plan: Dict)

Execute the merge plan to integrate an existing environment

**Returns**: `Dict`

#### merge_existing_environment(conflict_resolution: str)

Main function to discover, analyze, plan, and execute a merge

**Returns**: `Dict`

#### set_merge_options(options: Dict)

Update the merge options

**Returns**: `Dict`

#### get_merge_history()

Get history of merged environments

**Returns**: `Dict`

