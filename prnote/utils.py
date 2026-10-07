"""Utility functions for prnote."""

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def validate_file_line(anchor: str, repo: str, head: Optional[str] = None) -> bool:
    """
    Validate that a file:line anchor actually exists.
    
    Args:
        anchor: Anchor string like "path/to/file.py:42" or "path/to/file.py:10-20"
        repo: Path to repository
        head: Optional commit SHA to check against
    
    Returns:
        True if the file exists and line is valid
    """
    # Parse anchor
    match = re.match(r'^([^:]+):(\d+)(?:-(\d+))?', anchor)
    if not match:
        return False
    
    file_path = match.group(1)
    start_line = int(match.group(2))
    end_line = int(match.group(3)) if match.group(3) else start_line
    
    full_path = Path(repo) / file_path
    
    # Check if file exists
    if not full_path.exists():
        return False
    
    # Check if lines are valid
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Line numbers are 1-indexed
        if start_line < 1 or end_line > len(lines):
            return False
        
        return True
    
    except Exception:
        return False


def parse_anchor(text: str) -> Optional[Tuple[str, int, int]]:
    """
    Parse file:line anchor from text.
    
    Args:
        text: Text potentially containing an anchor
    
    Returns:
        Tuple of (file_path, start_line, end_line) or None
    """
    # Pattern: file.ext:line or file.ext:start-end
    match = re.search(r'([a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+):(\d+)(?:-(\d+))?', text)
    if match:
        file_path = match.group(1)
        start_line = int(match.group(2))
        end_line = int(match.group(3)) if match.group(3) else start_line
        return (file_path, start_line, end_line)
    
    return None


def get_file_at_commit(repo: str, file_path: str, commit: str) -> Optional[str]:
    """
    Get file content at a specific commit.
    
    Args:
        repo: Path to repository
        file_path: Relative path to file
        commit: Commit SHA
    
    Returns:
        File content or None if not found
    """
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit}:{file_path}'],
            cwd=repo,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return result.stdout
        return None
    
    except Exception:
        return None


def truncate_diff(diff: str, max_lines: int = 200) -> str:
    """
    Truncate diff to reasonable size for LLM prompts.
    
    Args:
        diff: Full diff text
        max_lines: Maximum lines to keep
    
    Returns:
        Truncated diff with note if truncated
    """
    lines = diff.split('\n')
    
    if len(lines) <= max_lines:
        return diff
    
    truncated = '\n'.join(lines[:max_lines])
    return truncated + f"\n\n... [truncated {len(lines) - max_lines} lines]"


def detect_pr_type(files: list) -> str:
    """
    Detect PR type based on changed files.
    
    Args:
        files: List of changed file paths
    
    Returns:
        PR type string (e.g., "feature", "bugfix", "refactor", "test", "docs")
    """
    # Count file types
    test_files = sum(1 for f in files if 'test' in f.lower() or 'spec' in f.lower())
    doc_files = sum(1 for f in files if f.endswith('.md') or 'doc' in f.lower())
    config_files = sum(1 for f in files if f.endswith(('.yml', '.yaml', '.json', '.toml')))
    
    total = len(files)
    if total == 0:
        return "unknown"
    
    # Heuristics
    if test_files / total > 0.7:
        return "test"
    elif doc_files / total > 0.7:
        return "docs"
    elif config_files / total > 0.7:
        return "config"
    elif total == 1:
        return "patch"
    elif total > 20:
        return "refactor"
    else:
        return "feature"


def format_file_list(files: list, max_files: int = 10) -> str:
    """
    Format list of files for display.
    
    Args:
        files: List of file paths
        max_files: Maximum files to show
    
    Returns:
        Formatted string
    """
    if len(files) <= max_files:
        return '\n'.join(f'  - {f}' for f in files)
    
    shown = '\n'.join(f'  - {f}' for f in files[:max_files])
    return f"{shown}\n  ... and {len(files) - max_files} more"


def safe_read_file(path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read a file, handling encoding errors.
    
    Args:
        path: File path
        encoding: Encoding to try
    
    Returns:
        File content or None if failed
    """
    try:
        with open(path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    except Exception:
        return None

