"""
Report Generator for Proxmox NLI.
Generates detailed reports from troubleshooting data.
"""
import logging
import json
import os
import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates detailed reports from troubleshooting data."""
    
    def __init__(self, report_dir: str = None):
        """Initialize the report generator.
        
        Args:
            report_dir: Directory to store reports
        """
        self.report_dir = report_dir or os.path.expanduser("~/proxmox_reports")
        
        # Create report directory if it doesn't exist
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_report(self, troubleshooting_data: Dict, report_type: str = "text") -> Dict:
        """Generate a report from troubleshooting data.
        
        Args:
            troubleshooting_data: Data from troubleshooting session
            report_type: Type of report to generate (text, html, json)
            
        Returns:
            Dict with report information
        """
        if report_type == "text":
            return self.generate_text_report(troubleshooting_data)
        elif report_type == "html":
            return self.generate_html_report(troubleshooting_data)
        elif report_type == "json":
            return self.generate_json_report(troubleshooting_data)
        else:
            return {
                "success": False,
                "message": f"Unknown report type: {report_type}",
                "recommendations": ["Please specify a valid report type: text, html, json"]
            }
    
    def generate_text_report(self, troubleshooting_data: Dict) -> Dict:
        """Generate a text report from troubleshooting data.
        
        Args:
            troubleshooting_data: Data from troubleshooting session
            
        Returns:
            Dict with report information
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"proxmox_report_{timestamp}.txt"
        report_path = os.path.join(self.report_dir, report_filename)
        
        try:
            with open(report_path, "w") as f:
                f.write("=== PROXMOX TROUBLESHOOTING REPORT ===\n")
                f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write summary
                f.write("=== SUMMARY ===\n")
                if "summary" in troubleshooting_data:
                    f.write(troubleshooting_data["summary"])
                else:
                    f.write("No summary provided.\n")
                f.write("\n\n")
                
                # Write issues
                f.write("=== ISSUES DETECTED ===\n")
                if "issues" in troubleshooting_data and troubleshooting_data["issues"]:
                    for i, issue in enumerate(troubleshooting_data["issues"], 1):
                        f.write(f"{i}. {issue}\n")
                else:
                    f.write("No issues detected.\n")
                f.write("\n\n")
                
                # Write actions taken
                f.write("=== ACTIONS TAKEN ===\n")
                if "actions_taken" in troubleshooting_data and troubleshooting_data["actions_taken"]:
                    for i, action in enumerate(troubleshooting_data["actions_taken"], 1):
                        f.write(f"{i}. {action}\n")
                else:
                    f.write("No actions taken.\n")
                f.write("\n\n")
                
                # Write recommendations
                f.write("=== RECOMMENDATIONS ===\n")
                if "recommendations" in troubleshooting_data and troubleshooting_data["recommendations"]:
                    for i, recommendation in enumerate(troubleshooting_data["recommendations"], 1):
                        f.write(f"{i}. {recommendation}\n")
                else:
                    f.write("No recommendations provided.\n")
                f.write("\n\n")
                
                # Write diagnostic details
                f.write("=== DIAGNOSTIC DETAILS ===\n")
                if "diagnostics" in troubleshooting_data:
                    for diagnostic_type, diagnostic_data in troubleshooting_data["diagnostics"].items():
                        f.write(f"\n--- {diagnostic_type.upper()} ---\n")
                        
                        if isinstance(diagnostic_data, dict):
                            # Write diagnostic summary
                            if "summary" in diagnostic_data:
                                f.write(f"Summary: {diagnostic_data['summary']}\n")
                            
                            # Write diagnostic success status
                            if "success" in diagnostic_data:
                                status = "Success" if diagnostic_data["success"] else "Failed"
                                f.write(f"Status: {status}\n")
                            
                            # Write diagnostic message
                            if "message" in diagnostic_data:
                                f.write(f"Message: {diagnostic_data['message']}\n")
                            
                            # Write diagnostic output
                            if "output" in diagnostic_data:
                                f.write("\nOutput:\n")
                                f.write("```\n")
                                f.write(diagnostic_data["output"])
                                f.write("\n```\n")
                        else:
                            # Write diagnostic data directly
                            f.write(str(diagnostic_data))
                else:
                    f.write("No diagnostic details provided.\n")
                
                # Write footer
                f.write("\n\n=== END OF REPORT ===\n")
            
            return {
                "success": True,
                "message": f"Report generated successfully: {report_path}",
                "report_path": report_path,
                "report_type": "text"
            }
        
        except Exception as e:
            logger.error(f"Error generating text report: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating text report: {str(e)}"
            }
    
    def generate_html_report(self, troubleshooting_data: Dict) -> Dict:
        """Generate an HTML report from troubleshooting data.
        
        Args:
            troubleshooting_data: Data from troubleshooting session
            
        Returns:
            Dict with report information
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"proxmox_report_{timestamp}.html"
        report_path = os.path.join(self.report_dir, report_filename)
        
        try:
            with open(report_path, "w") as f:
                # Write HTML header
                f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Proxmox Troubleshooting Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1, h2, h3 {
            color: #2b2f3a;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background-color: #37474f;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .issue {
            background-color: #ffebee;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #f44336;
        }
        .action {
            background-color: #e8f5e9;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #4caf50;
        }
        .recommendation {
            background-color: #e3f2fd;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #2196f3;
        }
        .diagnostic {
            background-color: #ffffff;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        .diagnostic-header {
            font-weight: bold;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 1px solid #eee;
        }
        .output {
            background-color: #f8f9fa;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-family: monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        .success {
            color: #4caf50;
        }
        .failure {
            color: #f44336;
        }
        .footer {
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            text-align: center;
            font-size: 0.8em;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="container">
                """)
                
                # Write header
                f.write("""
        <div class="header">
            <h1>Proxmox Troubleshooting Report</h1>
            <p>Generated: {}</p>
        </div>
                """.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
                # Write summary
                f.write("""
        <div class="section">
            <h2>Summary</h2>
                """)
                
                if "summary" in troubleshooting_data:
                    f.write(f"<p>{troubleshooting_data['summary']}</p>")
                else:
                    f.write("<p>No summary provided.</p>")
                
                f.write("</div>")
                
                # Write issues
                f.write("""
        <div class="section">
            <h2>Issues Detected</h2>
                """)
                
                if "issues" in troubleshooting_data and troubleshooting_data["issues"]:
                    for issue in troubleshooting_data["issues"]:
                        f.write(f'<div class="issue">{issue}</div>')
                else:
                    f.write("<p>No issues detected.</p>")
                
                f.write("</div>")
                
                # Write actions taken
                f.write("""
        <div class="section">
            <h2>Actions Taken</h2>
                """)
                
                if "actions_taken" in troubleshooting_data and troubleshooting_data["actions_taken"]:
                    for action in troubleshooting_data["actions_taken"]:
                        f.write(f'<div class="action">{action}</div>')
                else:
                    f.write("<p>No actions taken.</p>")
                
                f.write("</div>")
                
                # Write recommendations
                f.write("""
        <div class="section">
            <h2>Recommendations</h2>
                """)
                
                if "recommendations" in troubleshooting_data and troubleshooting_data["recommendations"]:
                    for recommendation in troubleshooting_data["recommendations"]:
                        f.write(f'<div class="recommendation">{recommendation}</div>')
                else:
                    f.write("<p>No recommendations provided.</p>")
                
                f.write("</div>")
                
                # Write diagnostic details
                f.write("""
        <div class="section">
            <h2>Diagnostic Details</h2>
                """)
                
                if "diagnostics" in troubleshooting_data:
                    for diagnostic_type, diagnostic_data in troubleshooting_data["diagnostics"].items():
                        f.write(f'<div class="diagnostic">')
                        f.write(f'<div class="diagnostic-header">{diagnostic_type.upper()}</div>')
                        
                        if isinstance(diagnostic_data, dict):
                            # Write diagnostic summary
                            if "summary" in diagnostic_data:
                                f.write(f"<p><strong>Summary:</strong> {diagnostic_data['summary']}</p>")
                            
                            # Write diagnostic success status
                            if "success" in diagnostic_data:
                                status_class = "success" if diagnostic_data["success"] else "failure"
                                status_text = "Success" if diagnostic_data["success"] else "Failed"
                                f.write(f'<p><strong>Status:</strong> <span class="{status_class}">{status_text}</span></p>')
                            
                            # Write diagnostic message
                            if "message" in diagnostic_data:
                                f.write(f"<p><strong>Message:</strong> {diagnostic_data['message']}</p>")
                            
                            # Write diagnostic output
                            if "output" in diagnostic_data:
                                f.write('<p><strong>Output:</strong></p>')
                                f.write(f'<div class="output">{diagnostic_data["output"]}</div>')
                        else:
                            # Write diagnostic data directly
                            f.write(f"<p>{str(diagnostic_data)}</p>")
                        
                        f.write('</div>')
                else:
                    f.write("<p>No diagnostic details provided.</p>")
                
                f.write("</div>")
                
                # Write footer
                f.write("""
        <div class="footer">
            <p>Proxmox NLI Troubleshooting Assistant</p>
        </div>
    </div>
</body>
</html>
                """)
            
            return {
                "success": True,
                "message": f"HTML report generated successfully: {report_path}",
                "report_path": report_path,
                "report_type": "html"
            }
        
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating HTML report: {str(e)}"
            }
    
    def generate_json_report(self, troubleshooting_data: Dict) -> Dict:
        """Generate a JSON report from troubleshooting data.
        
        Args:
            troubleshooting_data: Data from troubleshooting session
            
        Returns:
            Dict with report information
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"proxmox_report_{timestamp}.json"
        report_path = os.path.join(self.report_dir, report_filename)
        
        try:
            # Add metadata to report
            report_data = {
                "metadata": {
                    "generated_at": datetime.datetime.now().isoformat(),
                    "report_type": "json"
                },
                "troubleshooting_data": troubleshooting_data
            }
            
            with open(report_path, "w") as f:
                json.dump(report_data, f, indent=2)
            
            return {
                "success": True,
                "message": f"JSON report generated successfully: {report_path}",
                "report_path": report_path,
                "report_type": "json"
            }
        
        except Exception as e:
            logger.error(f"Error generating JSON report: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating JSON report: {str(e)}"
            }
    
    def get_report_history(self) -> Dict:
        """Get history of generated reports.
        
        Returns:
            Dict with report history
        """
        try:
            reports = []
            
            # List all files in report directory
            for filename in os.listdir(self.report_dir):
                file_path = os.path.join(self.report_dir, filename)
                
                # Check if file is a report
                if os.path.isfile(file_path) and filename.startswith("proxmox_report_"):
                    # Get report type
                    if filename.endswith(".txt"):
                        report_type = "text"
                    elif filename.endswith(".html"):
                        report_type = "html"
                    elif filename.endswith(".json"):
                        report_type = "json"
                    else:
                        report_type = "unknown"
                    
                    # Get file stats
                    stats = os.stat(file_path)
                    
                    # Extract timestamp from filename
                    timestamp_str = filename.replace("proxmox_report_", "").split(".")[0]
                    try:
                        timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        timestamp = datetime.datetime.fromtimestamp(stats.st_mtime)
                    
                    reports.append({
                        "filename": filename,
                        "path": file_path,
                        "type": report_type,
                        "size": stats.st_size,
                        "created": timestamp.isoformat(),
                        "modified": datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
                    })
            
            # Sort reports by creation time (newest first)
            reports.sort(key=lambda x: x["created"], reverse=True)
            
            return {
                "success": True,
                "message": f"Found {len(reports)} reports",
                "reports": reports
            }
        
        except Exception as e:
            logger.error(f"Error getting report history: {str(e)}")
            return {
                "success": False,
                "message": f"Error getting report history: {str(e)}"
            }
    
    def delete_report(self, report_path: str) -> Dict:
        """Delete a report.
        
        Args:
            report_path: Path to report to delete
            
        Returns:
            Dict with deletion result
        """
        try:
            # Check if file exists
            if not os.path.isfile(report_path):
                return {
                    "success": False,
                    "message": f"Report not found: {report_path}"
                }
            
            # Check if file is in report directory
            if not report_path.startswith(self.report_dir):
                return {
                    "success": False,
                    "message": f"Report is not in report directory: {report_path}"
                }
            
            # Delete file
            os.remove(report_path)
            
            return {
                "success": True,
                "message": f"Report deleted: {report_path}"
            }
        
        except Exception as e:
            logger.error(f"Error deleting report: {str(e)}")
            return {
                "success": False,
                "message": f"Error deleting report: {str(e)}"
            }
