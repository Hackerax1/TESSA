# report_generator

Report Generator for Proxmox NLI.
Generates detailed reports from troubleshooting data.

**Module Path**: `proxmox_nli.core.troubleshooting.report_generator`

## Classes

### ReportGenerator

Generates detailed reports from troubleshooting data.

#### __init__(report_dir: str)

Initialize the report generator.

Args:
    report_dir: Directory to store reports

#### generate_report(troubleshooting_data: Dict, report_type: str)

Generate a report from troubleshooting data.

Args:
    troubleshooting_data: Data from troubleshooting session
    report_type: Type of report to generate (text, html, json)
    
Returns:
    Dict with report information

**Returns**: `Dict`

#### generate_text_report(troubleshooting_data: Dict)

Generate a text report from troubleshooting data.

Args:
    troubleshooting_data: Data from troubleshooting session
    
Returns:
    Dict with report information

**Returns**: `Dict`

#### generate_html_report(troubleshooting_data: Dict)

Generate an HTML report from troubleshooting data.

Args:
    troubleshooting_data: Data from troubleshooting session
    
Returns:
    Dict with report information

**Returns**: `Dict`

#### generate_json_report(troubleshooting_data: Dict)

Generate a JSON report from troubleshooting data.

Args:
    troubleshooting_data: Data from troubleshooting session
    
Returns:
    Dict with report information

**Returns**: `Dict`

#### get_report_history()

Get history of generated reports.

Returns:
    Dict with report history

**Returns**: `Dict`

#### delete_report(report_path: str)

Delete a report.

Args:
    report_path: Path to report to delete
    
Returns:
    Dict with deletion result

**Returns**: `Dict`

