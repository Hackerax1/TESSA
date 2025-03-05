# Proxmox Natural Language Interface (NLI)

A natural language interface for managing your Proxmox VE environment using plain English commands.

## Quick Start

### Windows Users
1. Download and extract the project
2. Double-click `start.bat`
3. Follow the setup prompts (requirements check, dependencies installation)
4. Edit the created `.env` file with your Proxmox configuration
5. Run `start.bat` again to launch the application

### Docker Users
1. Download and extract the project
2. Copy `.env.example` to `.env` and edit with your configuration
3. Build and run with Docker:
   ```sh
   docker-compose up --build
   ```

The application will automatically:
- Check system requirements (Windows only)
- Create a Python virtual environment (Windows only)
- Install all required dependencies
- Configure your connection with the provided settings
- Start the web interface
- Open your browser to the interface

## Features

- Control Proxmox VE using natural language commands
- Manage VMs: list, start, stop, restart, status, create, delete
- Execute commands on VMs via QEMU agent
- Manage Docker containers running on VMs
- Pull Docker images, run containers, view logs
- Web interface with chat-like UI
- Command-line interface for terminal use
- AI-powered NLU using Ollama integration
- ZFS storage management and snapshots
- Domain management with Cloudflare integration
- Automatic SSL certificate management
- Secure tunnel configuration for remote access
- Zero Trust security features

## Project Structure

The project uses a modular architecture:

```
proxmox-nli/
    proxmox_nli/               # Main package
        __init__.py
        api/                   # API communication module
            __init__.py
            proxmox_api.py
        nlu/                   # Natural Language Understanding module
            __init__.py
            nlu_engine.py
            ollama_client.py   # Ollama integration
            preprocessing.py
            entity_extraction.py
            intent_identification.py
            context_management.py
        commands/              # Command implementations
            __init__.py
            proxmox_commands.py
            docker_commands.py
            vm_command.py
        core/                  # Core functionality
            __init__.py
            core_nli.py
            response_generator.py
            cloudflare_manager.py  # Cloudflare integration
            cli.py
            web.py
        services/             # Service management
            catalog/          # Service definitions
                nginx.yml
                cloudflared.yml
            service_manager.py
            service_catalog.py
    templates/                 # Web interface templates
        index.html
    app.py                     # Web server
    main.py                    # CLI entry point
    setup.py                   # Package installation
    requirements.txt           # Dependencies
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/username/proxmox-nli.git
   cd proxmox-nli
   ```

2. Install the package and dependencies:
   ```
   pip install -r requirements.txt
   pip install -e .
   ```

3. Install the NLTK resources (automatically downloaded during runtime):
   ```
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

4. (Optional) Install Ollama for enhanced NLU capabilities:
   ```
   # On Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # On macOS
   brew install ollama
   
   # On Windows
   # Download and install from https://ollama.com/download
   ```

## Configuration

Create a `.env` file in the project root with your configuration:

```
# Proxmox NLI Configuration
PROXMOX_API_URL=https://your-proxmox-host:8006/api2/json
PROXMOX_USER=your-username@pam
PROXMOX_PASSWORD=your-password
PROXMOX_NODE=node-name
API_PORT=5000

# Interface Configuration
START_WEB_INTERFACE=false
DEBUG_MODE=false

# Ollama Integration
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama3
DISABLE_OLLAMA=false
DISABLE_OLLAMA_RESPONSE=false

# Cloudflare Configuration
CLOUDFLARE_API_TOKEN=your-api-token  # Optional: For automated DNS management
CLOUDFLARE_EMAIL=your-email
CLOUDFLARE_ZONE_ID=your-zone-id      # Optional: For automated DNS management

# Backup Configuration
BACKUP_DIR=/backups
```

## Usage

### Command Line Interface

```
python main.py --host <proxmox-host> --user <username> --password <password>
```

Optional arguments:
- `--realm`: Proxmox realm (default: pam)
- `--verify-ssl`: Enable SSL verification

### Web Interface

```
python main.py --host <proxmox-host> --user <username> --password <password> --web
```

Additional options for web mode:
- `--debug`: Enable debug mode for the Flask server

Or run directly with app.py:
```
python app.py --host <proxmox-host> --user <username> --password <password>
```

## Docker Deployment

### Build and Run with Docker

1. Build the Docker image:
   ```sh
   docker build -t proxmox-nli .
   ```

2. Run the Docker container:
   ```sh
   docker run -d -p 5000:5000 --env-file .env proxmox-nli
   ```

### Using Docker Compose

1. Build and start the services:
   ```sh
   docker-compose up --build
   ```

2. Stop the services:
   ```sh
   docker-compose down
   ```

### Environment Configuration

Ensure you have a `.env` file in the root directory with the necessary configuration. You can use the provided `.env.example` as a template.

## Example Commands

- `list vms` - Show all virtual machines
- `start vm 100` - Start virtual machine with ID 100
- `stop vm 100` - Stop virtual machine with ID 100
- `restart vm 100` - Restart virtual machine with ID 100
- `status of vm 100` - Get status of a virtual machine
- `create a new vm with 2GB RAM, 2 CPUs and 20GB disk using ubuntu` - Create a new VM
- `list docker containers on vm 100` - List Docker containers on VM 100
- `start docker container myapp on vm 100` - Start a Docker container
- `run command "uptime" on vm 100` - Execute a command on VM 100
- `help` - Show all available commands

### Domain Management Commands
- `configure cloudflare domain example.com with email user@example.com` - Configure a domain with Cloudflare
- `setup cloudflare tunnel for domain example.com` - Create a Cloudflare tunnel
- `list cloudflare domains` - Show all configured Cloudflare domains
- `list cloudflare tunnels` - Show all configured Cloudflare tunnels
- `remove cloudflare domain example.com` - Remove a domain from Cloudflare configuration

## Ollama Integration

The system can use Ollama's AI models to improve natural language understanding and response generation:

### Features
- More accurate intent recognition
- Better entity extraction from complex queries
- Enhanced natural language responses
- Improved handling of ambiguous requests

### Configuration
1. Ensure Ollama is installed and running (see Installation section)
2. Pull a compatible model:
   ```
   ollama pull llama3
   ```
3. Configure Ollama settings in `.env`:
   ```
   OLLAMA_API_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   DISABLE_OLLAMA=false
   DISABLE_OLLAMA_RESPONSE=false
   ```

### Available Models
Any Ollama-compatible model can be used, but these are recommended:
- llama3 (default)
- mistral
- mixtral
- gemma:7b

### Fallback Mechanism
If Ollama is unavailable or encounters an error, the system will automatically fall back to traditional pattern-based NLU methods.

## Domain Management and SSL

The system supports seamless domain management and SSL certificate configuration through Cloudflare integration:

### Features
- Automatic SSL certificate management via Cloudflare
- Zero Trust access control
- DDoS protection
- Secure tunnel configuration
- No port forwarding required

### Setting up a Domain

1. Register a domain (e.g., from Namecheap, GoDaddy, etc.)
2. Configure the domain with Cloudflare:
   ```
   configure cloudflare domain your-domain.com with email your-email@example.com
   ```
3. Follow the provided instructions to update nameservers
4. Create a secure tunnel:
   ```
   setup cloudflare tunnel for domain your-domain.com
   ```

### Security Features

The Cloudflare integration provides several security features:
- End-to-end encryption
- Zero Trust access control
- DDoS protection
- Web Application Firewall (WAF)
- Bot protection
- Rate limiting

### Tunnel Configuration

Cloudflare Tunnels provide secure access to your homelab without exposing ports:

1. **Install cloudflared:**
   ```bash
   # Windows (using scoop):
   scoop install cloudflared

   # Linux:
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared.deb

   # Mac:
   brew install cloudflare/cloudflare/cloudflared
   ```

2. **Configure the tunnel:**
   - Run `cloudflared tunnel login`
   - Follow the browser authentication process
   - The system will automatically configure the tunnel for your domain

3. **Access your services:**
   - Proxmox web interface: `https://proxmox.your-domain.com`
   - Other services can be added to the tunnel configuration

### Best Practices

1. **Security:**
   - Enable Cloudflare Access for sensitive services
   - Use strong authentication methods
   - Regularly update SSL/TLS settings
   - Monitor access logs

2. **Performance:**
   - Use Cloudflare's CDN features
   - Enable caching where appropriate
   - Configure proper DNS records

3. **Maintenance:**
   - Regularly update cloudflared
   - Monitor tunnel status
   - Keep DNS records current

## Custom Commands and Plugin System

### Adding Custom Commands

1. Create a new Python file in the `custom_commands` directory.
2. Define your custom commands in the file and register them with the `ProxmoxNLI` instance.

Example:

```python
# custom_commands/my_custom_command.py

def register_commands(proxmox_nli):
    def my_custom_command():
        return {"success": True, "message": "This is a custom command"}
    
    proxmox_nli.custom_commands['my_custom_command'] = my_custom_command
```

### Using Custom Commands

You can use custom commands just like any other command in the NLI.

Example:

```
my_custom_command
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.