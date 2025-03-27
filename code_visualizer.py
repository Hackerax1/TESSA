#!/usr/bin/env python3
"""
Code Structure Visualizer for TESSA

This script analyzes Python source code and generates visual diagrams
of class hierarchies, dependencies, and relationships using Mermaid syntax.
"""

import os
import re
import ast
import sys
import logging
import argparse
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class CodeVisualizer:
    """
    Analyzes Python code and generates visual diagrams.
    
    This class scans Python source files, extracts class hierarchies
    and dependencies, and generates Mermaid diagrams to visualize them.
    """
    
    def __init__(self, 
                source_dirs: List[str] = None,
                output_dir: str = "docs/diagrams",
                exclude_dirs: List[str] = None,
                include_private: bool = False):
        """
        Initialize the code visualizer.
        
        Args:
            source_dirs: List of directories to scan for Python files
            output_dir: Directory to write diagram files
            exclude_dirs: List of directories to exclude from scanning
            include_private: Whether to include private members (prefixed with _)
        """
        self.source_dirs = source_dirs or ["proxmox_nli"]
        self.output_dir = output_dir
        self.exclude_dirs = exclude_dirs or ["__pycache__"]
        self.include_private = include_private
        
        # Data structures to hold analysis results
        self.classes = {}  # {class_name: {file, docstring, bases, methods}}
        self.modules = {}  # {module_name: {classes, functions, imports}}
        self.dependencies = defaultdict(set)  # {module_name: {imported_modules}}
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def analyze_code(self) -> bool:
        """
        Analyze code in the source directories.
        
        Returns:
            True if analysis was successful
        """
        try:
            logger.info("Analyzing code structure...")
            
            # Process each source directory
            for source_dir in self.source_dirs:
                self._process_directory(source_dir)
            
            logger.info(f"Analysis complete. Found {len(self.classes)} classes in {len(self.modules)} modules.")
            return True
        
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return False
    
    def generate_diagrams(self) -> bool:
        """
        Generate diagrams from the analyzed code.
        
        Returns:
            True if diagram generation was successful
        """
        try:
            logger.info("Generating code structure diagrams...")
            
            # Generate class hierarchy diagram
            self._generate_class_diagram()
            
            # Generate module dependency diagram
            self._generate_dependency_diagram()
            
            # Generate package structure diagram
            self._generate_package_diagram()
            
            logger.info(f"Diagrams generated in {self.output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating diagrams: {str(e)}")
            return False
    
    def _process_directory(self, directory: str, package: str = "") -> None:
        """
        Process a directory to find Python files and subdirectories.
        
        Args:
            directory: Directory to process
            package: Current package name for imports
        """
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return
        
        # Skip excluded directories
        dir_name = os.path.basename(directory)
        if dir_name in self.exclude_dirs:
            logger.debug(f"Skipping excluded directory: {directory}")
            return
        
        # Calculate package name
        current_package = package
        if package and dir_name:
            current_package = f"{package}.{dir_name}"
        elif dir_name:
            current_package = dir_name
        
        logger.debug(f"Processing directory: {directory} (package: {current_package})")
        
        # Process Python files in this directory
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isdir(item_path):
                # Process subdirectories recursively
                self._process_directory(item_path, current_package)
            
            elif item.endswith(".py"):
                # Process Python file
                module_name = item[:-3]  # Remove .py extension
                full_module_name = current_package
                
                if full_module_name and module_name != "__init__":
                    full_module_name = f"{full_module_name}.{module_name}"
                elif module_name != "__init__":
                    full_module_name = module_name
                
                # Skip if it's an __init__.py file in the root
                if full_module_name and module_name != "__init__":
                    self._process_file(item_path, full_module_name)
    
    def _process_file(self, file_path: str, module_name: str) -> None:
        """
        Process a Python file to extract class and import information.
        
        Args:
            file_path: Path to the Python file
            module_name: Full module name for the file
        """
        logger.debug(f"Processing file: {file_path} (module: {module_name})")
        
        try:
            # Parse the Python file
            with open(file_path, "r") as f:
                source_code = f.read()
            
            # Parse AST
            tree = ast.parse(source_code)
            
            # Extract module info
            self.modules[module_name] = {
                "file_path": file_path,
                "docstring": ast.get_docstring(tree) or "",
                "classes": [],
                "functions": [],
                "imports": []
            }
            
            # Process nodes
            for node in ast.iter_child_nodes(tree):
                # Extract classes
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    if not self.include_private and class_name.startswith("_"):
                        continue
                        
                    full_class_name = f"{module_name}.{class_name}"
                    
                    # Extract base classes
                    base_classes = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_classes.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            base_classes.append(f"{base.value.id}.{base.attr}")
                    
                    # Extract methods
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_name = item.name
                            if self.include_private or not method_name.startswith("_") or method_name == "__init__":
                                methods.append(method_name)
                    
                    # Add to classes dictionary
                    self.classes[full_class_name] = {
                        "file_path": file_path,
                        "module": module_name,
                        "name": class_name,
                        "docstring": ast.get_docstring(node) or "",
                        "bases": base_classes,
                        "methods": methods
                    }
                    
                    # Add to module's classes
                    self.modules[module_name]["classes"].append(class_name)
                
                # Extract functions
                elif isinstance(node, ast.FunctionDef):
                    function_name = node.name
                    if not self.include_private and function_name.startswith("_"):
                        continue
                    
                    self.modules[module_name]["functions"].append(function_name)
                
                # Extract imports
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        self.modules[module_name]["imports"].append(name.name)
                        self.dependencies[module_name].add(name.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.modules[module_name]["imports"].append(node.module)
                        self.dependencies[module_name].add(node.module)
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
    
    def _generate_class_diagram(self) -> None:
        """Generate a class hierarchy diagram using Mermaid syntax."""
        output_path = os.path.join(self.output_dir, "class_diagram.md")
        
        with open(output_path, "w") as f:
            f.write("# TESSA Class Hierarchy Diagram\n\n")
            f.write("This diagram shows the class hierarchy of the main classes in TESSA.\n\n")
            
            f.write("```mermaid\nclassDiagram\n")
            
            # Write class definitions and relationships
            for class_name, class_info in self.classes.items():
                short_name = class_info["name"]
                
                # Add class with methods
                if class_info["methods"]:
                    f.write(f"    class {short_name} {{\n")
                    for method in class_info["methods"]:
                        if method == "__init__":
                            f.write(f"        +{method}()\n")
                        elif method.startswith("_"):
                            f.write(f"        -{method}()\n")
                        else:
                            f.write(f"        +{method}()\n")
                    f.write("    }\n")
                else:
                    f.write(f"    class {short_name}\n")
                
                # Add inheritance relationships
                for base in class_info["bases"]:
                    if "." in base:
                        base = base.split(".")[-1]
                    f.write(f"    {base} <|-- {short_name}\n")
            
            f.write("```\n")
            
            # Add legend
            f.write("\n## Legend\n\n")
            f.write("- Classes are shown with their methods\n")
            f.write("- `+` indicates public methods\n")
            f.write("- `-` indicates private/protected methods\n")
            f.write("- Inheritance is shown with arrows pointing from the child to the parent class\n")
    
    def _generate_dependency_diagram(self) -> None:
        """Generate a module dependency diagram using Mermaid syntax."""
        output_path = os.path.join(self.output_dir, "dependency_diagram.md")
        
        # Filter dependencies to include only modules in our codebase
        filtered_deps = {}
        for module, deps in self.dependencies.items():
            filtered_deps[module] = set()
            for dep in deps:
                # Check if it's one of our own modules
                if any(dep.startswith(src_dir) for src_dir in self.source_dirs) or dep in self.modules:
                    filtered_deps[module].add(dep)
        
        with open(output_path, "w") as f:
            f.write("# TESSA Module Dependency Diagram\n\n")
            f.write("This diagram shows the dependencies between modules in TESSA.\n\n")
            
            f.write("```mermaid\nflowchart LR\n")
            
            # Add nodes for all modules
            for module in self.modules:
                safe_name = self._safe_id(module)
                module_short = module.split(".")[-1]
                f.write(f"    {safe_name}[{module_short}]\n")
            
            # Add edges for dependencies
            for module, deps in filtered_deps.items():
                safe_source = self._safe_id(module)
                
                for dep in deps:
                    safe_target = self._safe_id(dep)
                    if safe_source != safe_target and dep in self.modules:
                        f.write(f"    {safe_source} --> {safe_target}\n")
            
            f.write("```\n")
    
    def _generate_package_diagram(self) -> None:
        """Generate a package structure diagram using Mermaid syntax."""
        output_path = os.path.join(self.output_dir, "package_diagram.md")
        
        # Build a tree of packages
        packages = {}
        for module_name in self.modules:
            parts = module_name.split(".")
            
            current = packages
            for part in parts[:-1]:  # Skip the leaf/module name
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        with open(output_path, "w") as f:
            f.write("# TESSA Package Structure\n\n")
            f.write("This diagram shows the package structure of TESSA.\n\n")
            
            f.write("```mermaid\nflowchart TD\n")
            
            # Helper function to build the package diagram
            def build_package_diagram(package_dict, parent=None, level=0):
                for name, subpackages in package_dict.items():
                    safe_name = self._safe_id(name)
                    if parent:
                        safe_parent = self._safe_id(parent)
                        f.write(f"    {safe_parent} --> {safe_name}[{name}]\n")
                    else:
                        f.write(f"    {safe_name}[{name}]\n")
                    
                    if subpackages:
                        build_package_diagram(subpackages, name, level + 1)
            
            # Generate the diagram
            build_package_diagram(packages)
            
            f.write("```\n")
    
    def _safe_id(self, name: str) -> str:
        """
        Convert a name to a safe ID for Mermaid diagrams.
        
        Args:
            name: Name to convert
            
        Returns:
            Safe ID for Mermaid diagrams
        """
        return "id_" + re.sub(r'[^a-zA-Z0-9]', '_', name)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate visual diagrams of code structure")
    parser.add_argument("--source", "-s", action="append", help="Source directories to scan")
    parser.add_argument("--output", "-o", default="docs/diagrams", help="Output directory for diagrams")
    parser.add_argument("--exclude", "-e", action="append", help="Directories to exclude")
    parser.add_argument("--private", "-p", action="store_true", help="Include private members")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    visualizer = CodeVisualizer(
        source_dirs=args.source,
        output_dir=args.output,
        exclude_dirs=args.exclude,
        include_private=args.private
    )
    
    if visualizer.analyze_code():
        return 0 if visualizer.generate_diagrams() else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())