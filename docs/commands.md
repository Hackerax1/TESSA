# Commands

## Overview

This document provides detailed information about the commands available in TESSA. All commands can be entered in natural language through the TESSA interface. The commands are designed to be intuitive and can be phrased in multiple ways.

## Command Categories

### Virtual Machine Management

| Command | Description | Example | Response |
|---------|-------------|---------|----------|
| **list vms** | Lists all virtual machines in the Proxmox environment. Shows ID, name, status, and resource usage. | "Show me all my virtual machines" | TESSA will display a table with all VMs and their current status. |
| **start vm \<id\>** | Starts a virtual machine with the specified ID. | "Start virtual machine 100" or "Power on VM 100" | "Starting VM 100. This will take a few moments..." |
| **stop vm \<id\>** | Stops a virtual machine with the specified ID. Can specify graceful shutdown or force stop. | "Shutdown VM 100" or "Force stop virtual machine 100" | "Shutting down VM 100 gracefully. This may take up to 60 seconds." |
| **restart vm \<id\>** | Restarts a virtual machine with the specified ID. | "Reboot VM 100" or "Restart virtual machine 100" | "Restarting VM 100. This will take a moment..." |
| **status of vm \<id\>** | Gets detailed status of a VM including uptime, resource usage, and network info. | "What's the status of VM 100?" or "Tell me about virtual machine 100" | TESSA will show detailed information about the VM's current state. |
| **create a new vm** | Creates a new virtual machine with specified resources and OS template. | "Create a new VM with 2GB RAM, 2 CPUs and 20GB disk using Ubuntu" | "I'll create that VM for you. Would you like me to name it automatically or do you have a name in mind?" |
| **delete vm \<id\>** | Deletes a virtual machine with the specified ID. | "Delete VM 100" or "Remove virtual machine 100" | "Are you sure you want to delete VM 100? This action cannot be undone." |

### Container Management

| Command | Description | Example | Response |
|---------|-------------|---------|----------|
| **list containers** | Lists all containers in the Proxmox environment. | "Show all my containers" or "List LXC containers" | TESSA will display all containers with their status and basic information. |
| **start container \<id\>** | Starts a container with the specified ID. | "Start container 200" | "Starting container 200..." |
| **stop container \<id\>** | Stops a container with the specified ID. | "Stop container 200" | "Stopping container 200..." |

### Cluster Management

| Command | Description | Example | Response |
|---------|-------------|---------|----------|
| **get cluster status** | Shows overall cluster health, nodes, and quorum status. | "How is my cluster doing?" or "Check cluster health" | TESSA will display a summary of cluster status and any issues detected. |
| **get status of node \<n\>** | Gets detailed information about a specific node. | "Show me node pve1 status" or "What's happening with node pve2?" | TESSA will show CPU, memory, storage usage and running VMs on that node. |
| **get storage info** | Shows storage pools, usage, and health information. | "How much storage do I have left?" or "Show storage status" | TESSA will display available storage pools and their current usage. |

### Resource Management

| Command | Description | Example | Response |
|---------|-------------|---------|----------|
| **show resource usage** | Displays CPU, memory, and storage usage across the cluster. | "What's my resource usage like?" | TESSA will show graphs and data about current resource utilization. |
| **optimize resources** | Suggests VM placement and resource allocation improvements. | "Help me optimize my resources" | "I've analyzed your environment. Here are my recommendations..." |

## Advanced Command Syntax

For advanced users, TESSA supports more detailed command parameters:

```bash
# VM creation with advanced options
create vm template=ubuntu-22.04 cpu=4 memory=8192 disk=50 name=webserver net=vmbr0 ip=dhcp

# Storage management
add storage type=zfs name=tank path=/tank

# Backup commands
backup vm 100 to storage=backup retention=3
```

## Using Variables and References

TESSA can remember context from previous commands:

1. "Show me VM 100" 
2. "Increase its memory to 4GB"

TESSA will understand that "its" refers to VM 100 from the previous command.

## Getting Help

At any time, you can ask for help with specific commands:

- "How do I create a VM?"
- "What parameters can I use with the backup command?"
- "Show me examples of container commands"

TESSA will provide detailed guidance for your specific question.
