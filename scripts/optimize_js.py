#!/usr/bin/env python3
"""
JavaScript optimization script for Proxmox NLI
This script minifies JavaScript files and combines modules where appropriate.
"""
import os
import re
import json
import shutil
import argparse
from pathlib import Path

try:
    import jsmin
    import cssmin
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "jsmin", "cssmin"])
    import jsmin
    import cssmin

def minify_js_file(input_path, output_path):
    """Minify a JavaScript file"""
    with open(input_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    # Minify the content
    minified = jsmin.jsmin(js_content)
    
    # Write the minified content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(minified)
    
    # Calculate size reduction
    original_size = os.path.getsize(input_path)
    minified_size = os.path.getsize(output_path)
    reduction = (1 - (minified_size / original_size)) * 100
    
    print(f"Minified {input_path} -> {output_path}")
    print(f"  Original size: {original_size / 1024:.2f} KB")
    print(f"  Minified size: {minified_size / 1024:.2f} KB")
    print(f"  Reduction: {reduction:.2f}%")

def minify_css_file(input_path, output_path):
    """Minify a CSS file"""
    with open(input_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Minify the content
    minified = cssmin.cssmin(css_content)
    
    # Write the minified content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(minified)
    
    # Calculate size reduction
    original_size = os.path.getsize(input_path)
    minified_size = os.path.getsize(output_path)
    reduction = (1 - (minified_size / original_size)) * 100
    
    print(f"Minified {input_path} -> {output_path}")
    print(f"  Original size: {original_size / 1024:.2f} KB")
    print(f"  Minified size: {minified_size / 1024:.2f} KB")
    print(f"  Reduction: {reduction:.2f}%")

def process_directory(input_dir, output_dir, file_type='.js'):
    """Process all files in a directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process all files
    for file in input_path.glob(f'**/*{file_type}'):
        # Get the relative path
        rel_path = file.relative_to(input_path)
        
        # Create the output path
        out_file = output_path / rel_path
        
        # Create parent directories if they don't exist
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Minify the file
        if file_type == '.js':
            minify_js_file(file, out_file)
        elif file_type == '.css':
            minify_css_file(file, out_file)

def create_manifest(output_dir):
    """Create a manifest file with file paths and sizes"""
    output_path = Path(output_dir)
    manifest = {}
    
    # Get all JS and CSS files
    for file_type in ['.js', '.css']:
        for file in output_path.glob(f'**/*{file_type}'):
            rel_path = file.relative_to(output_path)
            manifest[str(rel_path)] = {
                'size': os.path.getsize(file),
                'path': f'/static/dist/{rel_path}'
            }
    
    # Write the manifest file
    with open(output_path / 'manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Created manifest file: {output_path / 'manifest.json'}")

def main():
    parser = argparse.ArgumentParser(description='Optimize JavaScript and CSS files')
    parser.add_argument('--input', default='static', help='Input directory')
    parser.add_argument('--output', default='static/dist', help='Output directory')
    parser.add_argument('--clean', action='store_true', help='Clean output directory before processing')
    
    args = parser.parse_args()
    
    # Clean output directory if requested
    if args.clean and os.path.exists(args.output):
        shutil.rmtree(args.output)
        print(f"Cleaned output directory: {args.output}")
    
    # Process JavaScript files
    process_directory(f"{args.input}/js", f"{args.output}/js", '.js')
    
    # Process CSS files
    process_directory(f"{args.input}/css", f"{args.output}/css", '.css')
    
    # Create manifest file
    create_manifest(args.output)
    
    print("Optimization complete!")

if __name__ == '__main__':
    main()
