# Contributing to TESSA

First off, thank you for considering contributing to TESSA! It's people like you that make TESSA such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for TESSA.

Before creating bug reports, please check the issue tracker as you might find that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the bug**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots if possible**
- **Include details about your configuration and environment**

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for TESSA, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and explain which behavior you expected to see instead and why**
- **Explain why this enhancement would be useful to most TESSA users**

### Pull Requests

- Fill in the required template
- Do not include issue numbers in the PR title
- Include screenshots and animated GIFs in your pull request whenever possible
- Follow the Python style guide
- Include thoughtfully-worded, well-structured tests
- Document new code based on the Documentation Styleguide
- End all files with a newline

## Development Environment

### Setting Up Your Development Environment

1. Fork the repo
2. Clone your fork
```bash
git clone https://github.com/Hackerax1/proxmox-nli.git
cd proxmox-nli
```

3. Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

4. Run the tests to verify your setup
```bash
pytest
```

## Project Structure

Here's an overview of the project structure to help you find your way around:

- `proxmox_nli/`: Core package
  - `api/`: API integration with Proxmox
  - `commands/`: Implementation of all natural language commands
  - `core/`: Core functionality and interfaces
  - `nlu/`: Natural language understanding components
- `docs/`: Documentation
- `tests/`: Test suite
- `installer/`: Installation scripts and GUI
- `plugins/`: Plugin system for extensions
- `static/`: Static assets for web interface
- `templates/`: HTML templates

## Style Guidelines

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use 4 spaces for indentation
- Use docstrings for all public classes, methods, and functions
- Keep line length to a maximum of 100 characters
- Run your code through pylint and fix any issues before submitting

### Documentation Styleguide

- Use [Markdown](https://guides.github.com/features/mastering-markdown/) for documentation
- Reference classes, methods, and variable names using backticks: \`ClassA\`
- Document all public API methods using docstrings

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Testing

- Write tests for all new features
- Ensure all tests pass before submitting a pull request
- Aim for high test coverage

## Additional Notes

### Issue Labels

Our issue tracker utilizes several labels to help organize and identify issues. 
Here's what they represent:

* `bug`: Something isn't working
* `documentation`: Improvements or additions to documentation
* `duplicate`: This issue already exists
* `enhancement`: New feature or request
* `good first issue`: Good for newcomers
* `help wanted`: Extra attention is needed
* `invalid`: This doesn't seem right
* `question`: Further information is requested
* `wontfix`: This will not be worked on

## Release Process

For maintainers, here's how to make a new release:

1. Update CHANGELOG.md
2. Update version in all necessary files
3. Create a new GitHub release with the appropriate tag
4. Build and publish packages

Thank you again for your interest in contributing to TESSA!