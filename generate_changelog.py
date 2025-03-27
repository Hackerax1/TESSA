#!/usr/bin/env python3
"""
Changelog Generator for TESSA

This script automatically generates a changelog from git commit history,
organizing commits by type and generating formatted Markdown output.
"""

import os
import re
import sys
import logging
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ChangelogGenerator:
    """
    Generates a changelog from git commit history.
    
    This class extracts commits from git history, parses them by type,
    and generates a formatted Markdown changelog.
    """
    
    # Commit types and their display labels
    COMMIT_TYPES = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "docs": "Documentation",
        "style": "Code Style",
        "refactor": "Code Refactoring",
        "perf": "Performance Improvements",
        "test": "Tests",
        "build": "Build System",
        "ci": "CI/CD",
        "chore": "Chores",
        "revert": "Reverts"
    }
    
    def __init__(self, 
                 repo_path: str = ".", 
                 output_file: str = "CHANGELOG.md", 
                 from_tag: Optional[str] = None,
                 to_tag: Optional[str] = "HEAD",
                 version: Optional[str] = None):
        """
        Initialize the changelog generator.
        
        Args:
            repo_path: Path to the git repository
            output_file: Path to the output changelog file
            from_tag: Starting tag or commit hash (defaults to beginning of repo)
            to_tag: Ending tag or commit hash (defaults to HEAD)
            version: Version name for this changelog section
        """
        self.repo_path = repo_path
        self.output_file = output_file
        self.from_tag = from_tag
        self.to_tag = to_tag
        self.version = version or self._get_suggested_version()
        
        # Ensure repo path is valid
        if not os.path.exists(os.path.join(repo_path, ".git")):
            raise ValueError(f"Not a git repository: {repo_path}")
    
    def generate(self) -> bool:
        """
        Generate the changelog.
        
        Returns:
            True if changelog generation was successful
        """
        try:
            logger.info(f"Generating changelog for version {self.version}")
            
            # Get commits
            commits = self._get_commits()
            if not commits:
                logger.warning("No commits found in the specified range")
                return False
            
            # Parse commits
            parsed_commits = self._parse_commits(commits)
            
            # Generate changelog content
            content = self._generate_content(parsed_commits)
            
            # Write to file
            self._write_changelog(content)
            
            logger.info(f"Changelog generated successfully: {self.output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating changelog: {str(e)}")
            return False
    
    def _get_suggested_version(self) -> str:
        """
        Get a suggested version based on the latest tag.
        
        Returns:
            Suggested version string
        """
        try:
            # Try to get the latest tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                latest_tag = result.stdout.strip()
                # Parse version components
                match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", latest_tag)
                if match:
                    major, minor, patch = map(int, match.groups())
                    # Increment minor version
                    return f"{major}.{minor + 1}.0"
            
            # Default to 1.0.0 if no tags found
            return "1.0.0"
            
        except Exception as e:
            logger.warning(f"Error determining version: {str(e)}")
            return "1.0.0"
    
    def _get_commits(self) -> List[str]:
        """
        Get commits from git history.
        
        Returns:
            List of commit messages
        """
        # Build git command
        git_cmd = ["git", "log", "--no-merges", "--pretty=format:%s"]
        
        if self.from_tag and self.to_tag:
            git_cmd.append(f"{self.from_tag}..{self.to_tag}")
        elif self.from_tag:
            git_cmd.append(f"{self.from_tag}..HEAD")
        elif self.to_tag and self.to_tag != "HEAD":
            git_cmd.append(f"{self.to_tag}")
        
        # Run git command
        result = subprocess.run(
            git_cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output
        commits = [line for line in result.stdout.split("\n") if line.strip()]
        return commits
    
    def _parse_commits(self, commits: List[str]) -> Dict[str, List[str]]:
        """
        Parse commits by type.
        
        Args:
            commits: List of commit messages
            
        Returns:
            Dictionary mapping commit types to lists of commit messages
        """
        parsed = {commit_type: [] for commit_type in self.COMMIT_TYPES}
        parsed["other"] = []
        
        # Regular expression to parse conventional commits
        # Format: type(scope): description
        pattern = r"^(\w+)(?:\(([^)]+)\))?: (.+)$"
        
        for commit in commits:
            match = re.match(pattern, commit)
            if match:
                commit_type, scope, description = match.groups()
                
                # Clean up description
                description = description.strip()
                if description.endswith("."):
                    description = description[:-1]
                
                # Format commit message
                if scope:
                    formatted_message = f"**{scope}**: {description}"
                else:
                    formatted_message = description
                
                # Add to appropriate category
                if commit_type in parsed:
                    parsed[commit_type].append(formatted_message)
                else:
                    parsed["other"].append(formatted_message)
            else:
                # Non-conventional commit
                parsed["other"].append(commit)
        
        return parsed
    
    def _generate_content(self, parsed_commits: Dict[str, List[str]]) -> str:
        """
        Generate changelog content.
        
        Args:
            parsed_commits: Parsed commit dictionary
            
        Returns:
            Formatted changelog content
        """
        # Get the current date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Start with header
        lines = [
            f"# {self.version} ({today})\n",
        ]
        
        # Add each section
        for commit_type, label in self.COMMIT_TYPES.items():
            commits = parsed_commits.get(commit_type, [])
            if commits:
                lines.append(f"## {label}\n")
                for commit in commits:
                    lines.append(f"* {commit}")
                lines.append("")  # Empty line between sections
        
        # Add other commits
        other_commits = parsed_commits.get("other", [])
        if other_commits:
            lines.append("## Other Changes\n")
            for commit in other_commits:
                lines.append(f"* {commit}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _write_changelog(self, content: str) -> None:
        """
        Write changelog to file.
        
        Args:
            content: Changelog content to write
        """
        # Check if file exists
        file_exists = os.path.exists(self.output_file)
        
        if file_exists:
            # Read existing content
            with open(self.output_file, "r") as f:
                existing_content = f.read()
            
            # Insert new content after the header
            header_match = re.search(r"^# Changelog", existing_content)
            if header_match:
                # Insert after the header
                insert_pos = header_match.end() + 1
                while insert_pos < len(existing_content) and existing_content[insert_pos] in ["\r", "\n"]:
                    insert_pos += 1
                
                new_content = existing_content[:insert_pos] + "\n" + content + existing_content[insert_pos:]
            else:
                # No header found, prepend content
                new_content = content + "\n" + existing_content
            
            # Write updated content
            with open(self.output_file, "w") as f:
                f.write(new_content)
        else:
            # Create new file with header
            with open(self.output_file, "w") as f:
                f.write("# Changelog\n\n")
                f.write(content)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate a changelog from git commit history")
    parser.add_argument("--repo", "-r", default=".", help="Path to the git repository")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file")
    parser.add_argument("--from", dest="from_tag", help="Starting tag or commit")
    parser.add_argument("--to", dest="to_tag", default="HEAD", help="Ending tag or commit")
    parser.add_argument("--version", "-v", help="Version name for this release")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    generator = ChangelogGenerator(
        repo_path=args.repo,
        output_file=args.output,
        from_tag=args.from_tag,
        to_tag=args.to_tag,
        version=args.version
    )
    
    success = generator.generate()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())