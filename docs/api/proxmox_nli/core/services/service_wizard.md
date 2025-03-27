# service_wizard

Service deployment wizard for Proxmox NLI.
Provides interactive guidance for deploying services with best practices.

**Module Path**: `proxmox_nli.core.services.service_wizard`

## Classes

### ServiceWizard

#### __init__(api, service_catalog)

#### start_wizard(service_type: str)

Start the service deployment wizard

**Returns**: `Dict`

#### start_goal_based_wizard()

Start the goal-based setup wizard to help users select services
based on their goals or cloud services they want to replace.

Returns:
    Dictionary with wizard state and initial options

**Returns**: `Dict`

#### process_goal_wizard_step(action: str, data: Dict)

Process a step in the goal-based wizard flow

Args:
    action: The action to perform (e.g., 'select_approach', 'select_goals')
    data: The data for the action
    
Returns:
    Dictionary with updated wizard state

**Returns**: `Dict`

#### get_available_goals()

Get all available user goals for the goal-based wizard

Returns:
    Dictionary with available goals

**Returns**: `Dict`

#### get_available_cloud_replacements()

Get all available cloud service replacements for the goal-based wizard

Returns:
    Dictionary with available cloud service replacements

**Returns**: `Dict`

#### deploy_service(service_id: str, config: Dict)

Deploy a service using the provided configuration

Args:
    service_id: ID of the service to deploy
    config: Optional configuration for the service
    
Returns:
    Dictionary with deployment result

**Returns**: `Dict`

#### process_answers(service_def: Dict, answers: Dict)

Process wizard answers and generate deployment configuration

**Returns**: `Dict`

