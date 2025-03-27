# goal_based_setup

Goal-Based Setup Workflow for TESSA
Guides users through service selection and setup based on their goals

**Module Path**: `proxmox_nli.services.goal_based_setup`

## Classes

### GoalBasedSetupWizard

A wizard to guide users through setting up services based on their goals
or cloud services they want to replace.

#### __init__(goal_based_catalog, dependency_manager = None, service_manager = None)

Initialize the goal-based setup wizard

Args:
    goal_based_catalog: The goal-based catalog instance
    dependency_manager: The dependency manager instance
    service_manager: The service deployment manager instance

#### reset_state()

Reset the wizard state to defaults

#### get_goal_categories()

Get all available goal categories

Returns:
    List of goal dictionaries

**Returns**: `List[Dict]`

#### get_cloud_replacements()

Get all available cloud service replacements

Returns:
    List of cloud replacement dictionaries

**Returns**: `List[Dict]`

#### start_setup()

Begin the setup wizard

Returns:
    State dictionary with welcome message and options

**Returns**: `Dict`

#### select_approach(approach: str)

Select the setup approach (goals or replacements)

Args:
    approach: Either 'goals' or 'replacement'
    
Returns:
    Updated state dictionary

**Returns**: `Dict`

#### select_goals(goal_ids: List[str])

Select user goals

Args:
    goal_ids: List of goal IDs
    
Returns:
    Updated state dictionary

**Returns**: `Dict`

#### select_replacements(replacement_ids: List[str])

Select cloud services to replace

Args:
    replacement_ids: List of cloud service IDs
    
Returns:
    Updated state dictionary

**Returns**: `Dict`

#### select_services(service_ids: List[str])

Select services to install

Args:
    service_ids: List of service IDs to install
    
Returns:
    Updated state dictionary

**Returns**: `Dict`

#### confirm_plan(confirmed: bool)

Confirm the deployment plan and start installation

Args:
    confirmed: Whether the user confirmed the plan
    
Returns:
    Updated state dictionary

**Returns**: `Dict`

#### get_current_state()

Get the current state of the setup wizard

Returns:
    Current state dictionary

**Returns**: `Dict`

#### to_json()

Convert the current state to JSON

Returns:
    JSON string representation of the state

**Returns**: `str`

#### from_json(cls, json_str: str, goal_based_catalog = None, dependency_manager = None, service_manager = None)

Create a wizard instance from a JSON state

Args:
    json_str: JSON string representation of the state
    goal_based_catalog: The goal-based catalog instance
    dependency_manager: The dependency manager instance
    service_manager: The service deployment manager instance
    
Returns:
    GoalBasedSetupWizard instance with restored state

**Returns**: `GoalBasedSetupWizard instance with restored state`

