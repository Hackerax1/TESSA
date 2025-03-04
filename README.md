# Proxmox Natural Language Interface (NLI)

A natural language interface for managing Proxmox VE environments, allowing users to control virtual machines, containers, and more using plain English commands.

## Features

- Control Proxmox VE using natural language commands
- Manage VMs: list, start, stop, restart, status, create, delete
- Execute commands on VMs via QEMU agent
- Manage Docker containers running on VMs
- Pull Docker images, run containers, view logs
- Web interface with chat-like UI
- Command-line interface for terminal use
- AI-powered NLU using Ollama integration

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
            cli.py
            web.py
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

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.