#!/usr/bin/env python3
"""Generate changelog from conventional commits."""

import re
import subprocess
import sys
from typing import Dict, List, Tuple


def run_command(cmd: List[str]) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}", file=sys.stderr)
        return ""


def get_commits_since_tag(tag: str) -> List[str]:
    """Get commits since a specific tag."""
    if tag:
        cmd = ["git", "log", "--pretty=format:%H %s", f"{tag}..HEAD"]
    else:
        cmd = ["git", "log", "--pretty=format:%H %s"]
    
    output = run_command(cmd)
    return [line.strip() for line in output.split('\n') if line.strip()]


def parse_conventional_commit(commit_line: str) -> Tuple[str, str, str]:
    """Parse a conventional commit message."""
    # Extract hash and message
    parts = commit_line.split(' ', 1)
    if len(parts) != 2:
        return "other", "other", commit_line
    
    commit_hash, message = parts
    
    # Conventional commit pattern: type(scope): description
    pattern = r'^(\w+)(?:\(([\w\-]+)\))?:\s*(.+)$'
    match = re.match(pattern, message)
    
    if match:
        commit_type = match.group(1).lower()
        scope = match.group(2) or "general"
        description = match.group(3)
        return commit_type, scope, f"{description} ({commit_hash[:8]})"
    else:
        return "other", "other", f"{message} ({commit_hash[:8]})"


def categorize_commits(commits: List[str]) -> Dict[str, List[str]]:
    """Categorize commits by type."""
    categories = {
        "feat": [],
        "fix": [],
        "docs": [],
        "style": [],
        "refactor": [],
        "perf": [],
        "test": [],
        "chore": [],
        "other": []
    }
    
    for commit in commits:
        commit_type, scope, description = parse_conventional_commit(commit)
        if commit_type in categories:
            categories[commit_type].append(description)
        else:
            categories["other"].append(description)
    
    return categories


def format_changelog(categories: Dict[str, List[str]], version: str) -> str:
    """Format the changelog."""
    changelog = f"# Changelog for WiseRate {version}\n\n"
    
    # Define category headers
    headers = {
        "feat": "🚀 New Features",
        "fix": "🐛 Bug Fixes", 
        "docs": "📚 Documentation",
        "style": "💄 Code Style",
        "refactor": "♻️ Refactoring",
        "perf": "⚡ Performance",
        "test": "🧪 Tests",
        "chore": "🔧 Maintenance",
        "other": "📝 Other Changes"
    }
    
    for category, commits in categories.items():
        if commits:
            changelog += f"## {headers[category]}\n\n"
            for commit in commits:
                changelog += f"- {commit}\n"
            changelog += "\n"
    
    return changelog


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python generate_changelog.py <version> [previous_tag] [--stdout]")
        sys.exit(1)
    
    version = sys.argv[1]
    previous_tag = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    output_stdout = '--stdout' in sys.argv
    
    if not output_stdout:
        print(f"Generating changelog for version {version}...")
    
    # Get commits since last tag
    commits = get_commits_since_tag(previous_tag)
    
    if not commits:
        if not output_stdout:
            print("No commits found.")
        sys.exit(1)
    
    # Categorize commits
    categories = categorize_commits(commits)
    
    # Generate changelog
    changelog = format_changelog(categories, version)
    
    if output_stdout:
        # Output to stdout for GitHub Actions
        print(changelog)
    else:
        # Write to file for local use
        with open("CHANGELOG.md", "w", encoding="utf-8") as f:
            f.write(changelog)
        
        print(f"Changelog generated: CHANGELOG.md")
        print(f"Found {len(commits)} commits")
        
        # Print summary
        for category, commit_list in categories.items():
            if commit_list:
                print(f"  {category}: {len(commit_list)} commits")


if __name__ == "__main__":
    main()
