#!/usr/bin/env python3
"""
Automatic Documentation Tools for TESSA

This package provides tools for automatically generating documentation,
visualizing code structure, and creating changelogs for the TESSA project.
"""

from .autodoc import APIDocGenerator
from .code_visualizer import CodeVisualizer
from .generate_changelog import ChangelogGenerator
import logging

__all__ = [
    'APIDocGenerator',
    'CodeVisualizer',
    'ChangelogGenerator',
    'generate_api_docs',
    'generate_code_diagrams',
    'generate_changelog',
    'generate_all'
]

def generate_api_docs(
    output_dir="docs/api",
    source_dirs=None,
    exclude_dirs=None,
    include_private=False
):
    """
    Generate API documentation from docstrings.
    
    Args:
        output_dir: Directory where documentation will be written
        source_dirs: List of directories to scan for Python files
        exclude_dirs: List of directories to exclude from scanning
        include_private: Whether to include private methods/classes
        
    Returns:
        True if documentation was generated successfully
    """
    from .autodoc import APIDocGenerator
    
    generator = APIDocGenerator(
        output_dir=output_dir,
        source_dirs=source_dirs,
        exclude_dirs=exclude_dirs,
        include_private=include_private
    )
    
    return generator.generate_docs()

def generate_code_diagrams(
    source_dirs=None,
    output_dir="docs/diagrams",
    exclude_dirs=None,
    include_private=False
):
    """
    Generate code structure diagrams.
    
    Args:
        source_dirs: List of directories to scan for Python files
        output_dir: Directory to write diagram files
        exclude_dirs: List of directories to exclude from scanning
        include_private: Whether to include private members
        
    Returns:
        True if diagrams were generated successfully
    """
    from .code_visualizer import CodeVisualizer
    
    visualizer = CodeVisualizer(
        source_dirs=source_dirs,
        output_dir=output_dir,
        exclude_dirs=exclude_dirs,
        include_private=include_private
    )
    
    if visualizer.analyze_code():
        return visualizer.generate_diagrams()
    return False

def generate_changelog(
    repo_path=".",
    output_file="CHANGELOG.md",
    from_tag=None,
    to_tag="HEAD",
    version=None
):
    """
    Generate a changelog from git commit history.
    
    Args:
        repo_path: Path to the git repository
        output_file: Path to the output changelog file
        from_tag: Starting tag or commit hash
        to_tag: Ending tag or commit hash (defaults to HEAD)
        version: Version name for this changelog section
        
    Returns:
        True if changelog was generated successfully
    """
    from .generate_changelog import ChangelogGenerator
    
    generator = ChangelogGenerator(
        repo_path=repo_path,
        output_file=output_file,
        from_tag=from_tag,
        to_tag=to_tag,
        version=version
    )
    
    return generator.generate()

def generate_all(
    source_dirs=None,
    exclude_dirs=None,
    include_private=False,
    repo_path=".",
    changelog_file="CHANGELOG.md",
    from_tag=None,
    version=None
):
    """
    Generate all documentation: API docs, code diagrams, and changelog.
    
    Args:
        source_dirs: List of directories to scan for Python files
        exclude_dirs: List of directories to exclude from scanning
        include_private: Whether to include private members
        repo_path: Path to the git repository
        changelog_file: Path to the output changelog file
        from_tag: Starting tag or commit hash
        version: Version name for this changelog section
        
    Returns:
        Dictionary with results of each generation step
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Generating all documentation")
    
    results = {
        "api_docs": False,
        "diagrams": False,
        "changelog": False
    }
    
    # Generate API docs
    logger.info("Generating API documentation")
    results["api_docs"] = generate_api_docs(
        source_dirs=source_dirs,
        exclude_dirs=exclude_dirs,
        include_private=include_private
    )
    
    # Generate code diagrams
    logger.info("Generating code structure diagrams")
    results["diagrams"] = generate_code_diagrams(
        source_dirs=source_dirs,
        exclude_dirs=exclude_dirs,
        include_private=include_private
    )
    
    # Generate changelog
    logger.info("Generating changelog")
    results["changelog"] = generate_changelog(
        repo_path=repo_path,
        output_file=changelog_file,
        from_tag=from_tag,
        version=version
    )
    
    return results

# Enable script execution
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate documentation for TESSA")
    parser.add_argument("--api", action="store_true", help="Generate API documentation")
    parser.add_argument("--diagrams", action="store_true", help="Generate code structure diagrams")
    parser.add_argument("--changelog", action="store_true", help="Generate changelog")
    parser.add_argument("--all", action="store_true", help="Generate all documentation")
    parser.add_argument("--source", "-s", action="append", help="Source directories to scan")
    parser.add_argument("--exclude", "-e", action="append", help="Directories to exclude")
    parser.add_argument("--private", "-p", action="store_true", help="Include private members")
    parser.add_argument("--repo", "-r", default=".", help="Path to the git repository")
    parser.add_argument("--output-changelog", default="CHANGELOG.md", help="Output changelog file")
    parser.add_argument("--from-tag", help="Starting tag or commit for changelog")
    parser.add_argument("--version", "-v", help="Version for changelog")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    # Default to --all if no specific action provided
    if not (args.api or args.diagrams or args.changelog or args.all):
        args.all = True
    
    # Set up common args
    success = True
    source_dirs = args.source
    exclude_dirs = args.exclude
    include_private = args.private
    
    # Generate specified documentation
    if args.all:
        results = generate_all(
            source_dirs=source_dirs,
            exclude_dirs=exclude_dirs,
            include_private=include_private,
            repo_path=args.repo,
            changelog_file=args.output_changelog,
            from_tag=args.from_tag,
            version=args.version
        )
        success = all(results.values())
    else:
        if args.api:
            success &= generate_api_docs(
                source_dirs=source_dirs,
                exclude_dirs=exclude_dirs,
                include_private=include_private
            )
        
        if args.diagrams:
            success &= generate_code_diagrams(
                source_dirs=source_dirs,
                exclude_dirs=exclude_dirs,
                include_private=include_private
            )
        
        if args.changelog:
            success &= generate_changelog(
                repo_path=args.repo,
                output_file=args.output_changelog,
                from_tag=args.from_tag,
                version=args.version
            )
    
    sys.exit(0 if success else 1)