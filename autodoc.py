#!/usr/bin/env python3
"""
Automatic API Documentation Generator for TESSA

This script automatically generates API documentation from
docstrings in the codebase and outputs them in Markdown format.
"""

import os
import re
import ast
import sys
import inspect
import importlib
import importlib.util
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class APIDocGenerator:
    """
    Generates API documentation from Python docstrings.
    
    This class scans Python source files and extracts docstrings,
    types, and other information to generate comprehensive API
    documentation in Markdown format.
    """
    
    def __init__(self, 
                output_dir: str = "docs/api",
                source_dirs: List[str] = None,
                exclude_dirs: List[str] = None,
                include_private: bool = False):
        """
        Initialize the API documentation generator.
        
        Args:
            output_dir: Directory where documentation will be written
            source_dirs: List of directories to scan for Python files
            exclude_dirs: List of directories to exclude from scanning
            include_private: Whether to include private methods/classes (prefixed with _)
        """
        self.output_dir = output_dir
        self.source_dirs = source_dirs or ["proxmox_nli"]
        self.exclude_dirs = exclude_dirs or ["__pycache__"]
        self.include_private = include_private
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_docs(self) -> bool:
        """
        Generate API documentation for the entire codebase.
        
        Returns:
            True if documentation generation was successful
        """
        logger.info(f"Generating API documentation in {self.output_dir}")
        
        try:
            # Create index.md
            with open(os.path.join(self.output_dir, "index.md"), "w") as f:
                f.write("# TESSA API Documentation\n\n")
                f.write("Welcome to the TESSA API documentation, automatically generated from the codebase.\n\n")
                f.write("## Modules\n\n")
            
            # Process each source directory
            for source_dir in self.source_dirs:
                self._process_directory(source_dir)
            
            # Update index with directory structure
            self._update_index()
            
            logger.info("API documentation generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error generating API documentation: {str(e)}")
            return False
    
    def _process_directory(self, directory: str, parent_module: str = "") -> None:
        """
        Process a directory to find Python files and subdirectories.
        
        Args:
            directory: Directory to process
            parent_module: Parent module path for proper import
        """
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return
        
        # Skip excluded directories
        directory_name = os.path.basename(directory)
        if directory_name in self.exclude_dirs:
            logger.debug(f"Skipping excluded directory: {directory}")
            return
        
        # Calculate module name
        current_module = parent_module
        if parent_module and directory_name:
            current_module = f"{parent_module}.{directory_name}"
        elif directory_name:
            current_module = directory_name
        
        logger.debug(f"Processing directory: {directory} (module: {current_module})")
        
        # Process Python files in this directory
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isdir(item_path):
                # Process subdirectories recursively
                self._process_directory(item_path, current_module)
            
            elif item.endswith(".py") and not item.startswith("_"):
                # Process Python files
                module_name = item[:-3]  # Remove .py extension
                full_module_name = current_module
                
                if full_module_name:
                    full_module_name = f"{full_module_name}.{module_name}"
                else:
                    full_module_name = module_name
                
                # Extract documentation
                self._process_file(item_path, full_module_name)
    
    def _process_file(self, file_path: str, module_name: str) -> None:
        """
        Process a Python file to extract documentation.
        
        Args:
            file_path: Path to the Python file
            module_name: Full module path for the file
        """
        logger.debug(f"Processing file: {file_path} (module: {module_name})")
        
        try:
            # Parse the Python file with UTF-8 encoding
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source_code = f.read()
            
            # Parse AST
            tree = ast.parse(source_code)
            
            # Extract module docstring
            module_doc = ast.get_docstring(tree)
            
            # Extract classes and functions
            classes = []
            functions = []
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef) and (self.include_private or not node.name.startswith("_")):
                    classes.append(self._extract_class_info(node))
                elif isinstance(node, ast.FunctionDef) and (self.include_private or not node.name.startswith("_")):
                    functions.append(self._extract_function_info(node))
            
            # Generate documentation file
            module_parts = module_name.split(".")
            output_subdir = os.path.join(self.output_dir, *module_parts[:-1])
            os.makedirs(output_subdir, exist_ok=True)
            
            output_path = os.path.join(output_subdir, f"{module_parts[-1]}.md")
            
            with open(output_path, "w", encoding="utf-8") as f:
                # Write module header
                f.write(f"# {module_parts[-1]}\n\n")
                
                if module_doc:
                    f.write(f"{module_doc.strip()}\n\n")
                
                # Module path
                f.write(f"**Module Path**: `{module_name}`\n\n")
                
                # Write classes
                if classes:
                    f.write("## Classes\n\n")
                    for cls in classes:
                        f.write(f"### {cls['name']}\n\n")
                        
                        if cls['docstring']:
                            f.write(f"{cls['docstring'].strip()}\n\n")
                        
                        # Write methods
                        if cls['methods']:
                            for method in cls['methods']:
                                f.write(f"#### {method['name']}({self._format_params(method['params'])})\n\n")
                                
                                if method['docstring']:
                                    f.write(f"{method['docstring'].strip()}\n\n")
                                
                                # Write return type if available
                                if method['returns']:
                                    f.write(f"**Returns**: `{method['returns']}`\n\n")
                
                # Write functions
                if functions:
                    f.write("## Functions\n\n")
                    for func in functions:
                        f.write(f"### {func['name']}({self._format_params(func['params'])})\n\n")
                        
                        if func['docstring']:
                            f.write(f"{func['docstring'].strip()}\n\n")
                        
                        # Write return type if available
                        if func['returns']:
                            f.write(f"**Returns**: `{func['returns']}`\n\n")
            
            logger.info(f"Generated documentation for module: {module_name}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
    
    def _extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """
        Extract information about a class.
        
        Args:
            node: AST node for the class
            
        Returns:
            Dict with class information
        """
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or "",
            'methods': []
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and (self.include_private or not item.name.startswith("_") or item.name == "__init__"):
                class_info['methods'].append(self._extract_function_info(item))
        
        return class_info
    
    def _extract_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Extract information about a function or method.
        
        Args:
            node: AST node for the function
            
        Returns:
            Dict with function information
        """
        func_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or "",
            'params': self._extract_parameters(node),
            'returns': self._extract_return_type(node)
        }
        
        return func_info
    
    def _extract_parameters(self, node: ast.FunctionDef) -> List[Dict[str, str]]:
        """
        Extract function parameters and their types.
        
        Args:
            node: AST node for the function
            
        Returns:
            List of parameter information dicts
        """
        params = []
        
        for arg in node.args.args:
            if arg.arg == "self":
                continue
                
            param_info = {
                'name': arg.arg,
                'type': "",
                'default': None
            }
            
            # Extract type annotation if available
            if arg.annotation:
                param_info['type'] = self._get_annotation_name(arg.annotation)
            
            params.append(param_info)
        
        # Extract default values
        defaults = []
        if node.args.defaults:
            default_offset = len(node.args.args) - len(node.args.defaults)
            for i, default in enumerate(node.args.defaults):
                if i + default_offset < len(params):
                    params[i + default_offset]['default'] = self._get_default_value(default)
        
        return params
    
    def _extract_return_type(self, node: ast.FunctionDef) -> str:
        """
        Extract function return type.
        
        Args:
            node: AST node for the function
            
        Returns:
            String representation of the return type
        """
        if node.returns:
            return self._get_annotation_name(node.returns)
        
        # Try to extract return type from docstring
        docstring = ast.get_docstring(node) or ""
        match = re.search(r"Returns:\s*(.*?)(?:\n\n|\Z)", docstring, re.DOTALL)
        if match:
            return match.group(1).strip()
            
        return ""
    
    def _get_annotation_name(self, annotation: ast.AST) -> str:
        """
        Get the name of a type annotation.
        
        Args:
            annotation: AST node for the annotation
            
        Returns:
            String representation of the annotation
        """
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_annotation_name(annotation.value)}.{annotation.attr}"
        elif isinstance(annotation, ast.Subscript):
            value = self._get_annotation_name(annotation.value)
            if sys.version_info >= (3, 9):
                # Python 3.9+ handling
                slice_value = annotation.slice
                if isinstance(slice_value, ast.Index):
                    slice_str = self._get_annotation_name(slice_value.value)
                else:
                    slice_str = self._get_annotation_name(slice_value)
            else:
                # Earlier Python versions
                slice_value = annotation.slice
                if isinstance(slice_value, ast.Index):
                    slice_str = self._get_annotation_name(slice_value.value)
                else:
                    slice_str = "..."
            return f"{value}[{slice_str}]"
        elif isinstance(annotation, ast.Tuple):
            elts = [self._get_annotation_name(e) for e in annotation.elts]
            return f"({', '.join(elts)})"
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        else:
            return str(annotation)
    
    def _get_default_value(self, default: ast.AST) -> str:
        """
        Get string representation of a default value.
        
        Args:
            default: AST node for the default value
            
        Returns:
            String representation of the default value
        """
        if isinstance(default, ast.Constant):
            return repr(default.value)
        elif isinstance(default, ast.Name):
            return default.id
        elif isinstance(default, ast.Call):
            return f"{self._get_annotation_name(default.func)}(...)"
        elif isinstance(default, ast.List):
            return "[]"
        elif isinstance(default, ast.Dict):
            return "{}"
        else:
            return "..."
    
    def _format_params(self, params: List[Dict[str, str]]) -> str:
        """
        Format function parameters for display.
        
        Args:
            params: List of parameter information dicts
            
        Returns:
            Formatted parameter string
        """
        param_strs = []
        
        for param in params:
            param_str = param['name']
            
            if param['type']:
                param_str += f": {param['type']}"
            
            if param['default'] is not None:
                param_str += f" = {param['default']}"
            
            param_strs.append(param_str)
            
        return ", ".join(param_strs)
    
    def _update_index(self) -> None:
        """Update the index.md file with the directory structure."""
        index_path = os.path.join(self.output_dir, "index.md")
        structure = self._build_directory_structure()
        
        with open(index_path, "a") as f:
            self._write_directory_structure(f, structure)
            
            # Add additional information
            f.write("\n\n## About\n\n")
            f.write("This documentation was automatically generated from docstrings ")
            f.write("in the codebase using the `autodoc.py` script.\n\n")
            f.write("To regenerate this documentation, run:\n\n")
            f.write("```bash\npython autodoc.py\n```\n")
    
    def _build_directory_structure(self) -> Dict:
        """
        Build a nested dictionary representing the document structure.
        
        Returns:
            Dictionary with the nested structure
        """
        structure = {}
        
        # Traverse the output directory
        for root, dirs, files in os.walk(self.output_dir):
            rel_path = os.path.relpath(root, self.output_dir)
            
            if rel_path == ".":
                # Root directory
                for file in files:
                    if file != "index.md" and file.endswith(".md"):
                        module_name = file[:-3]  # Remove .md extension
                        structure[module_name] = file
                        
                for dir_name in dirs:
                    if dir_name != "__pycache__" and not dir_name.startswith("."):
                        structure[dir_name] = {}
            else:
                # Subdirectories
                parts = rel_path.split(os.sep)
                current = structure
                
                # Navigate to the correct nested dict
                for i, part in enumerate(parts):
                    if part not in current:
                        current[part] = {}
                    
                    if i < len(parts) - 1:
                        current = current[part]
                
                # Add files in this directory
                for file in files:
                    if file.endswith(".md"):
                        module_name = file[:-3]
                        current[parts[-1]][module_name] = os.path.join(rel_path, file)
                
                # Add subdirectories
                for dir_name in dirs:
                    if dir_name != "__pycache__" and not dir_name.startswith("."):
                        if dir_name not in current[parts[-1]]:
                            current[parts[-1]][dir_name] = {}
        
        return structure
    
    def _write_directory_structure(self, f, structure, level=0):
        """
        Write the directory structure as a nested list.
        
        Args:
            f: File handle to write to
            structure: Directory structure dictionary
            level: Current indentation level
        """
        indent = "  " * level
        
        for key, value in sorted(structure.items()):
            if isinstance(value, dict):
                # This is a directory
                f.write(f"{indent}- **{key}**\n")
                self._write_directory_structure(f, value, level + 1)
            else:
                # This is a file
                rel_path = value
                link_text = key
                # Replace backslashes with forward slashes for Markdown links
                rel_path = rel_path.replace('\\', '/')
                f.write(f"{indent}- [{link_text}]({rel_path})\n")


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate API documentation from docstrings.')
    parser.add_argument('--output', '-o', default='docs/api', help='Output directory for documentation')
    parser.add_argument('--source', '-s', action='append', help='Source directories to scan')
    parser.add_argument('--exclude', '-e', action='append', help='Directories to exclude')
    parser.add_argument('--private', '-p', action='store_true', help='Include private methods/classes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    generator = APIDocGenerator(
        output_dir=args.output,
        source_dirs=args.source,
        exclude_dirs=args.exclude,
        include_private=args.private
    )
    
    success = generator.generate_docs()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())