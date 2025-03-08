# TESSA: Technical Environment Self-Service Assistant

![TESSA Logo](static/TessaLogo.webp)

## What is TESSA?

TESSA (Technical Environment Self-Service Assistant) is an open-source project that puts the power of a professional homelab into the hands of everyday users. No more cloud dependence, no more technical barriers—just simple, natural language interaction with your own private infrastructure.

TESSA transforms Proxmox virtualization into an accessible platform through natural language interaction, allowing anyone to self-host applications and services with minimal technical knowledge.

## Key Features

- **Natural Language Interface**: Talk to TESSA like you would a human assistant. Ask for what you want in plain language, and let TESSA handle the technical details.

- **Automated Hardware Detection**: TESSA automatically detects your hardware and configures your environment optimally, with fallback options for partially compatible components.

- **Simple Installation**: Boot from USB, scan a QR code, and you're ready to start. No complex configuration or command-line knowledge required.

- **Goal-Based Setup**: Tell TESSA what cloud services you want to replace (e.g., "I want to replace Google Photos"), and she'll handle the rest.

- **Visual Management**: Understand your homelab at a glance with intuitive visualizations of your services, network, and resources.

- **Progressive Learning Curve**: Start with the basics and gradually unlock more advanced features as you become comfortable.

- **Comprehensive Security**: Robust security measures come pre-configured, with regular updates to keep your homelab safe.

## Getting Started

### Hardware Requirements

- CPU with virtualization support (Intel VT-x/AMD-V)
- Minimum 8GB RAM (16GB+ recommended)
- 120GB+ storage (SSD recommended)
- Network connection

### Installation

1. Download the TESSA installer image
2. Create a bootable USB drive using the image
3. Boot your target system from the USB drive
4. Follow the on-screen instructions
5. Scan the QR code with your phone when prompted to access the web interface

### First Steps

Once TESSA is installed, you can:

1. Tell TESSA what cloud services you'd like to replace
2. Explore the available applications in the service catalog
3. Monitor your system resources and performance
4. Set up automated backups of your environment
5. Invite family members to use your services

## For Developers

TESSA is built on Python and integrates deeply with Proxmox's API. Developers can:

- Extend functionality through the plugin system
- Contribute to the hardware compatibility database
- Add new services to the catalog
- Improve natural language understanding capabilities
- Enhance visualization and reporting features

Check out our [Developer Documentation](https://github.com/tessa-project/docs) for more information.

## Community

- **Forum**: [TESSA Community](https://community.tessa-project.org)
- **Chat**: [Discord Server](https://discord.gg/tessa-project)
- **Bug Reports**: [GitHub Issues](https://github.com/tessa-project/tessa/issues)

## License

TESSA is released under the [MIT License](LICENSE).

## Acknowledgements

TESSA builds upon the excellent work of:
- The Proxmox team
- Various open-source self-hosted applications
- Contributors to the hardware compatibility database
- Everyone who has tested and provided feedback

---

**TESSA** — Your homelab, simplified.