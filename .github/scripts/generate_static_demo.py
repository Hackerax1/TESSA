#!/usr/bin/env python3
"""
Script to generate static HTML pages from Flask templates for GitHub Pages demo.
This script converts Jinja2 templates to static HTML pages with mock data.
"""

import os
import re
import json
import shutil
from datetime import datetime
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

# Configure paths
TEMPLATES_DIR = "templates"
OUTPUT_DIR = "demo"
STATIC_DIR = "static"
SCRIPTS_DIR = ".github/scripts"

# Configure Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# Mock data for templates
mock_data = {
    "user": {
        "name": "Demo User",
        "email": "demo@example.com",
        "is_authenticated": True,
        "role": "admin"
    },
    "vms": [
        {
            "id": "101", 
            "name": "Web Server", 
            "status": "running", 
            "vmid": "101",
            "memory": 4096, 
            "cpu": 2, 
            "disk": 50.0,
            "cpu_usage": 25,
            "memory_usage": 60
        },
        {
            "id": "102", 
            "name": "Database Server", 
            "status": "running", 
            "vmid": "102",
            "memory": 8192, 
            "cpu": 4, 
            "disk": 100.0,
            "cpu_usage": 40,
            "memory_usage": 75
        },
        {
            "id": "103", 
            "name": "Test Environment", 
            "status": "stopped", 
            "vmid": "103",
            "memory": 2048, 
            "cpu": 1, 
            "disk": 25.0,
            "cpu_usage": 0,
            "memory_usage": 0
        }
    ],
    "cluster_status": {
        "status": "healthy", 
        "nodes": [
            {"name": "node1", "status": "online"}, 
            {"name": "node2", "status": "online"}
        ]
    },
    "storage": [
        {"name": "local", "type": "dir", "usage": 35, "available": 956.2, "total": 1000.0},
        {"name": "storage1", "type": "lvm", "usage": 65, "available": 350.0, "total": 1000.0}
    ],
    "current_year": datetime.now().year
}

# Common context data for all pages
common_context = {
    "url_for": lambda name, **kwargs: f"#{name.replace('_', '-')}",
    "versioned_asset": lambda path: path
}

# Pages to render with their specific context
pages_to_render = {
    "index.html": {"template": "login.html", "context": {}},
    "dashboard.html": {"template": "dashboard.html", "context": {}},
    "family_profile.html": {"template": "family_profile.html", "context": {}},
    "user_profile.html": {"template": "user_profile.html", "context": {}},
    "vm_access.html": {"template": "vm_access.html", "context": {"vm_id": "101"}},
    "service_access.html": {"template": "service_access.html", "context": {"service_id": "1"}}
}

def fix_relative_paths(html_content, page_name):
    """
    Fix relative paths in the HTML content for GitHub Pages.
    
    Args:
        html_content (str): The HTML content to fix
        page_name (str): The name of the current page
        
    Returns:
        str: The fixed HTML content
    """
    # Replace versioned assets
    html_content = re.sub(r'{{ \'([^\']+)\'\|versioned_asset }}', r'\1', html_content)
    
    # Fix URLs
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Fix CSS and JS references
    for element in soup.find_all(['link', 'script']):
        if element.get('href') and element['href'].startswith('/'):
            element['href'] = '.' + element['href']
        if element.get('src') and element['src'].startswith('/'):
            element['src'] = '.' + element['src']
    
    # Fix image references
    for img in soup.find_all('img'):
        if img.get('src') and img['src'].startswith('/'):
            img['src'] = '.' + img['src']
    
    # Remove Flask-specific elements and scripts
    for element in soup.select('[data-flask]'):
        element.decompose()
    
    # Remove server-side includes
    comments = soup.findAll(string=lambda text: isinstance(text, str) and text.strip().startswith('{% include'))
    for comment in comments:
        comment.extract()
    
    # Add demo banner
    demo_banner = soup.new_tag('div')
    demo_banner['class'] = 'demo-banner'
    demo_banner['style'] = 'position: fixed; top: 0; left: 0; width: 100%; background-color: #f44336; color: white; text-align: center; padding: 10px; z-index: 9999;'
    demo_banner.string = 'TESSA UI Demo - For demonstration purposes only'
    if soup.body:
        soup.body.insert(0, demo_banner)
    
    # Add demo-utils.js script tag just before closing body tag
    demo_utils_script = soup.new_tag('script')
    demo_utils_script['src'] = './demo-utils.js'
    if soup.body:
        soup.body.append(demo_utils_script)
    
    return str(soup)

def create_static_demo():
    """Create static HTML pages for the demo."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create a demo.css file for any custom demo styles
    with open(os.path.join(OUTPUT_DIR, "demo.css"), "w") as f:
        f.write("""
        .demo-banner {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #f44336;
            color: white;
            text-align: center;
            padding: 10px;
            z-index: 9999;
        }
        
        body {
            padding-top: 40px;
        }
        
        /* Toast styling */
        .toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1050;
        }
        
        .toast {
            background-color: white;
            border-radius: 0.25rem;
            box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.1);
            margin-bottom: 0.5rem;
            transition: opacity 0.3s ease-in-out;
            opacity: 0;
            width: 300px;
            display: none;
        }
        
        .toast-header {
            display: flex;
            align-items: center;
            padding: 0.5rem 0.75rem;
            background-color: rgba(255, 255, 255, 0.85);
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        .toast-body {
            padding: 0.75rem;
        }
        
        .me-auto {
            margin-right: auto !important;
        }
        """)
    
    # Copy demo-utils.js to the output directory
    shutil.copy(os.path.join(SCRIPTS_DIR, "demo-utils.js"), os.path.join(OUTPUT_DIR, "demo-utils.js"))
    
    # Create JSON files for API mock data
    os.makedirs(os.path.join(OUTPUT_DIR, "api"), exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "api", "vms-status.json"), "w") as f:
        json.dump({"success": True, "vms": mock_data["vms"]}, f, indent=2)
    
    with open(os.path.join(OUTPUT_DIR, "api", "cluster-resources.json"), "w") as f:
        json.dump({
            "success": True, 
            "resources": {
                "cpu": {"used": 35, "total": 100},
                "memory": {"used": 24576, "total": 65536},
                "storage": {"used": 650, "total": 2000}
            }
        }, f, indent=2)
    
    # Create README for the demo
    with open(os.path.join(OUTPUT_DIR, "README.md"), "w") as f:
        f.write("""# TESSA - Proxmox Natural Language Interface UI Demo

This is a static demo of the TESSA user interface. This demo shows the visual design and layout of the application, but does not include actual functionality.

TESSA is a natural language interface for Proxmox that allows users to control their Proxmox environment using natural language commands either through text or voice.

## Demo Pages

- [Login Page](index.html)
- [Dashboard](dashboard.html)
- [Family Profile](family_profile.html)
- [User Profile](user_profile.html)
- [VM Access](vm_access.html)
- [Service Access](service_access.html)

## Note

This is only a UI demonstration. The actual application requires a Proxmox environment to function properly.
""")
    
    # Render templates to static HTML
    for output_file, page_info in pages_to_render.items():
        template_name = page_info["template"]
        context = {**mock_data, **common_context, **page_info["context"]}
        
        try:
            template = env.get_template(template_name)
            html_content = template.render(**context)
            html_content = fix_relative_paths(html_content, output_file)
            
            with open(os.path.join(OUTPUT_DIR, output_file), "w", encoding="utf-8") as f:
                f.write(html_content)
            
            print(f"Generated {output_file} from template {template_name}")
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")

if __name__ == "__main__":
    create_static_demo()
    print("Static demo generation complete.")