# security_posture

Security Posture Assessment for Proxmox NLI.
Provides security posture assessment and recommendations.

**Module Path**: `proxmox_nli.core.security.security_posture`

## Classes

### SecurityPostureAssessor

Assesses security posture and provides recommendations

#### __init__(api, base_nli)

Initialize the security posture assessor

Args:
    api: Proxmox API client
    base_nli: Base NLI instance for accessing other components

#### assess_security_posture()

Assess the overall security posture of the system

Returns:
    Dictionary with assessment results

**Returns**: `Dict[(str, Any)]`

#### generate_posture_report()

Generate a natural language report of the security posture

Returns:
    String with natural language report

**Returns**: `str`

#### interpret_posture_command(command: str)

Interpret a natural language posture command

Args:
    command: Natural language command for security posture
    
Returns:
    Dictionary with interpreted command and parameters

**Returns**: `Dict[(str, Any)]`

