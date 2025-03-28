# Security Policy

## Supported Versions

| Version | Supported          |
|---------|-------------------|
| 1.0.x   | :white_check_mark: |
| 0.9.x   | :white_check_mark: |
| < 0.9   | :x:                |

## Reporting a Vulnerability

TESSA takes security seriously. If you believe you've found a security vulnerability in our project, please follow these steps:

1. **Do not disclose the vulnerability publicly**
2. **Email us** at [security@tessa-project.org](mailto:security@tessa-project.org) with details about the vulnerability
3. Include the following information:
   - Type of vulnerability
   - Steps to reproduce
   - Affected versions
   - Potential impact

## Security Features

TESSA implements several security features to protect your Proxmox environment:

### Authentication & Authorization
- Support for secure login methods
- Role-based access control
- User relationship model for personalized access

### Network Security
- Natural language firewall rule management
- Security audit commands and reporting
- Encrypted communications

### Data Protection
- Sophisticated backup retention policies
- Backup verification and integrity checking
- Encryption for backups

### Service Security
- Container isolation
- Health monitoring
- Secure service deployment via Docker Compose

## Security Best Practices

When using TESSA, we recommend following these security best practices:

1. **Keep TESSA updated** to the latest version
2. **Use strong passwords** for all accounts
3. **Enable two-factor authentication** where available
4. **Regularly review** security audit reports
5. **Maintain regular backups** and test recovery processes
6. **Follow the principle of least privilege** when granting permissions

## Security Roadmap

Our security roadmap includes:

- Implementation of buddy backup system with encryption
- Voice authentication for different users
- Enhanced intrusion detection capabilities
- Integration with external identity providers
- Comprehensive error handling and security logging

## Compliance

TESSA is designed with privacy and security in mind. While we strive to follow security best practices, specific compliance certifications are in development.

---

This security policy was last updated: March 28, 2025