# docker_commands

**Module Path**: `proxmox_nli.commands.docker_commands`

## Classes

### DockerCommands

#### __init__(api)

#### list_docker_containers(vm_id, node = None)

List Docker containers on a VM or across the cluster

#### start_docker_container(container_name, vm_id, node = None)

Start a Docker container on a VM

#### stop_docker_container(container_name, vm_id, node = None)

Stop a Docker container on a VM

#### docker_container_logs(container_name, vm_id, node = None, lines = None)

Get logs from a Docker container

#### docker_container_info(container_name, vm_id, node = None)

Get detailed information about a Docker container

#### pull_docker_image(image_name, vm_id, node = None)

Pull a Docker image on a VM

#### run_docker_container(image_name, container_name, ports = None, volumes = None, environment = None, vm_id = None, node = None)

Run a Docker container on a VM

#### list_docker_images(vm_id, node = None)

List Docker images on a VM

