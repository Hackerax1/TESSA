# Update Management

The update management system allows you to check for and apply updates to your deployed services using natural language commands. This feature helps you keep your services up-to-date with the latest security patches and features.

## Commands

### Check for Updates

Check if there are any updates available for your services.

```
Examples:
"Check for updates"
"Are there any updates available?"
"Check if nextcloud needs updating"
"Check for updates on plex"
```

### List Updates

List details about available updates for your services.

```
Examples:
"List all available updates"
"Show me updates for nextcloud"
"What updates are available for plex?"
"Tell me about pending updates"
```

### Apply Updates

Apply available updates to your services.

```
Examples:
"Update all services"
"Apply updates to nextcloud"
"Update plex server"
"Apply all available updates"
```

### Update Plan

Generate a plan for applying updates, including recommendations based on update priority.

```
Examples:
"Generate an update plan"
"Create update plan for nextcloud"
"Make me an update plan for all services"
"What's the best update strategy?"
```

### Update Status

Check the current status of the update system, including when checks were last performed.

```
Examples:
"What's the update status?"
"Show update system status"
"When was the last update check?"
```

### Schedule Updates

Schedule updates to be applied at a specific time (e.g., during maintenance windows).

```
Examples:
"Schedule updates for tonight"
"Schedule nextcloud update for tomorrow"
"Plan updates for next week"
"Schedule updates during maintenance window"
```

## How Updates Are Checked

The system checks for updates in different ways depending on the service type:

1. **Docker Services**: Pulls the latest image from the registry to check if a newer version is available.

2. **Script-deployed Services**: Uses service-specific update check scripts when available, or falls back to checking for system updates using apt or yum.

## Update Priorities

Updates are categorized by priority:

- **Critical**: Security updates or critical bug fixes that should be applied immediately.
- **Warning**: Important updates that fix significant issues or add valuable features.
- **Normal**: Routine updates that can be applied during regular maintenance.

## Automatic Update Checking

The system automatically checks for updates on a regular schedule (default: every 24 hours). You can check the status of these automatic checks using the "update status" command.

## Confirmation

For safety, the system will always ask for confirmation before applying updates to ensure you're aware of the potential impact on your services.