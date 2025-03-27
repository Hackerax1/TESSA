# Changelog

# 1.0.0 (2025-03-27)

## Features

* Enhance login functionality with detailed logging and error handling; add test endpoint for login configuration; update login.html for improved user experience
* Enhance home route to render login page for unauthenticated users; add login.html template for user authentication
* Implement dashboard panel components and profile synchronization module
* Enhance intent identification and voice module functionality

## Bug Fixes

* Update nginx deployment configuration to use Docker Compose format; improve volume mappings and restart policy
* Update cluster status handling and improve error logging; refactor exception imports in profile_sync.py; add backup configuration and schedule JSON files
* Update import path for UserManager to reflect new directory structure

## Other Changes

* Create docker-image.yml
* Add Dashboard Viewer and Editor components with dynamic panel management
* Refactor command execution logic to improve routing and validation in CommandExecutor
* Implement storage management, ZFS management, and diagnostics features for Proxmox NLI
* remove obsolete test files and refactor NLU and API test structure
* add unit tests for VPN and arr stack integration in Proxmox NLI
* more things
* troubleshooting interface
* reqs are recent
* big index refactor... might not even need it anymore
* app.js on ozempic
* Add service handler module for managing services and enhance user preferences initialization
* Add update management functionality with intent handling and confirmation prompts
* Add Hugging Face integration with client implementation and tests
* Enhance query processing with confirmation handling and improved error logging
* Add token management and permission handling modules; refactor authentication structure and update service catalog
* Add Prometheus & Grafana monitoring stack configuration and event dispatcher implementation
* Add Environment Merger functionality and update todo list
* Add firewall management module and update networking management tasks in todo list
* Refactor authentication module and restructure project directories; add monitoring, network, automation, and security modules
* Update todo list to mark comprehensive documentation as complete and enhance service catalog recommendations
* Add goal-based setup wizard and service dependency management
* Mark VM resource monitoring and optimization recommendations as complete in todo list
* Implement token-based authentication for protected routes
* Update .gitignore to exclude .pytest_cache directory
* Update .gitignore and enhance todo list; add auto-configuration methods for Proxmox
* Update .gitignore to exclude additional files
* Add hardware detection and compatibility tests; implement Proxmox API test suite
* Update todo list: mark fallback options and driver auto-installation system as complete for hardware detection and compatibility
* Implement unit tests for NLU engine; add service validation for dependencies and user goals; introduce MariaDB and Mealie service catalog entries with deployment configurations
* Add test suites for Proxmox NLI and NLU; update requirements for Docker and testing libraries
* Enhance TESSA voice settings UI with profile selection, accent options, speaking speed, conversation style, and personality level controls; mark related tasks as complete in todo list
* Add Hello World plugin demonstrating Proxmox NLI plugin system; update todo list
* Add Proxmox NLI installer with GUI wizard and hardware detection functionality; update todo list
* Add service deployment endpoint and enhance UI for deployment goals; update requirements and todo list
* Add hardware detection functionality and update installation scripts; remove old setup scripts and enhance requirements
* Remove webrtcvad from requirements and update todo list with detailed security, management, and feature enhancement tasks
* Add service deployment validators and enhance service catalog with validation logic; update requirements and .gitignore
* Refactor NLU engine to integrate logging, enhance query processing with conversation history, and add context management methods for saving and loading context
* Refactor main function to simplify web mode argument handling
* Add environment variable support for Proxmox API in backup script and import shutil in run script
* Add Windows startup script, enhance security configuration, and implement JWT authentication module
* Refactor service handler, command executor, and user manager to remove dependency on BaseNLI; add Cloudflare service setup and removal methods with detailed configuration instructions in service manager and catalog
* ``` Add new service catalog entries for additional applications and enhance deployment documentation ```
* Add service catalog entries for PFSense, Home Assistant OS, Home Assistant Docker, and VPN Service with deployment instructions and access information
* Add ZFS storage intent patterns and entity extraction for pool, dataset, and snapshot management; introduce NGINX, TrueNAS, and NextCloud service catalog entries
* Add user manager and service handler modules for user preferences, activity tracking, and service management
* Add user preferences and statistics endpoints, enhance context management with user favorites and inference capabilities
* Add setup wizard script to streamline Proxmox NLI installation and check for Python availability
* Add services module for self-hosted deployments, enhance query processing with command confirmation, and update requirements
* Add voice handler module for speech recognition and synthesis, enhance ProxmoxNLI with audit logging, and update requirements
* Add Docker support, backup and restore functionality, and enhance setup scripts
* Add Ollama integration for enhanced NLU and response generation
* Refactor project structure and enhance CLI and web interface functionality
* move from spacy to ntlk
* Implement Proxmox NLI structure with core modules, API integration, and command handling
* Add initial project setup with Flask app, Proxmox API integration, and dependencies
