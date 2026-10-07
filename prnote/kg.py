"""Knowledge Graph construction module.

Builds a property graph from repository artifacts:
- Changed files (from git diff)
- Test coverage (by naming conventions and imports)
- Code ownership (from CODEOWNERS)
- Dependencies (imports/calls)
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class KGNode:
    """Knowledge Graph node."""
    id: str
    type: str  # PR, File, TestCase, Owner
    props: Dict[str, Any]


@dataclass
class KGEdge:
    """Knowledge Graph edge."""
    src_id: str
    dst_id: str
    rel: str  # touched_file, covers, owns, imports, calls_function_in
    props: Dict[str, Any]


# =============================================================================
# LANGUAGE DETECTION
# =============================================================================

LANGUAGE_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.jsx': 'JavaScript',
    '.java': 'Java',
    '.go': 'Go',
    '.rs': 'Rust',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.cs': 'C#',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.scala': 'Scala',
    '.kt': 'Kotlin',
    '.swift': 'Swift',
    '.m': 'Objective-C',
    '.sh': 'Shell',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.json': 'JSON',
    '.md': 'Markdown',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sql': 'SQL',
}


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_MAP.get(ext, 'unknown')


# =============================================================================
# GIT OPERATIONS
# =============================================================================

def get_changed_files(repo: str, base: str, head: str) -> List[Dict[str, Any]]:
    """Get list of changed files with diff stats."""
    # Get diff with stats
    result = subprocess.run(
        ['git', 'diff', '--numstat', base, head],
        cwd=repo,
        capture_output=True,
        text=True
    )
    
    changed_files = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 3:
            added = int(parts[0]) if parts[0] != '-' else 0
            deleted = int(parts[1]) if parts[1] != '-' else 0
            path = parts[2]
            
            changed_files.append({
                'path': path,
                'language': detect_language(path),
                'added': added,
                'deleted': deleted
            })
    
    return changed_files


def get_diff_hunks(repo: str, base: str, head: str, file_path: str) -> List[Dict[str, int]]:
    """Get hunk line ranges for a specific file."""
    result = subprocess.run(
        ['git', 'diff', '-U0', base, head, '--', file_path],
        cwd=repo,
        capture_output=True,
        text=True
    )
    
    hunks = []
    for line in result.stdout.split('\n'):
        if line.startswith('@@'):
            # Parse hunk header: @@ -start,count +start,count @@
            match = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if match:
                start = int(match.group(1))
                count = int(match.group(2)) if match.group(2) else 1
                hunks.append({
                    'start': start,
                    'end': start + count - 1,
                    'added': count,
                    'deleted': 0  # Simplified
                })
    
    return hunks


# =============================================================================
# TEST DETECTION
# =============================================================================

def find_tests_for_file(repo: str, file_path: str) -> List[Dict[str, Any]]:
    """Find test files that likely cover a given source file."""
    tests = []
    file_name = Path(file_path).stem
    file_dir = Path(file_path).parent
    
    # Common test patterns
    patterns = [
        f'test_{file_name}',
        f'{file_name}_test',
        f'{file_name}Test',
        f'{file_name}.test',
        f'{file_name}.spec',
    ]
    
    # Search in common test directories
    test_dirs = ['test', 'tests', '__tests__', 'spec', 'test_*']
    
    repo_path = Path(repo)
    
    for test_dir in test_dirs:
        for test_path in repo_path.glob(f'**/{test_dir}/**/*'):
            if test_path.is_file():
                test_name = test_path.stem
                for pattern in patterns:
                    if pattern.lower() in test_name.lower():
                        tests.append({
                            'file': str(test_path.relative_to(repo_path)),
                            'name': test_name,
                            'confidence': 0.8
                        })
    
    # Also check same directory for test files
    for sibling in (repo_path / file_dir).glob('*'):
        if sibling.is_file():
            sibling_name = sibling.stem
            for pattern in patterns:
                if pattern.lower() in sibling_name.lower():
                    tests.append({
                        'file': str(sibling.relative_to(repo_path)),
                        'name': sibling_name,
                        'confidence': 0.9
                    })
    
    # Deduplicate
    seen = set()
    unique_tests = []
    for t in tests:
        if t['file'] not in seen:
            seen.add(t['file'])
            unique_tests.append(t)
    
    return unique_tests[:5]  # Limit to 5 most relevant


# =============================================================================
# CODEOWNERS PARSING
# =============================================================================

def parse_codeowners(codeowners_path: str) -> List[Dict[str, str]]:
    """Parse CODEOWNERS file into patterns and owners."""
    owners = []
    
    if not os.path.exists(codeowners_path):
        return owners
    
    with open(codeowners_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                pattern = parts[0]
                handles = [p for p in parts[1:] if p.startswith('@')]
                
                for handle in handles:
                    owners.append({
                        'pattern': pattern,
                        'handle': handle
                    })
    
    return owners


def match_owners(file_path: str, owners: List[Dict[str, str]]) -> List[str]:
    """Find owners that match a file path."""
    matched = []
    
    for owner in owners:
        pattern = owner['pattern']
        # Simple glob matching
        if pattern.endswith('/*'):
            # Directory match
            dir_pattern = pattern[:-2]
            if file_path.startswith(dir_pattern):
                matched.append(owner['handle'])
        elif pattern.endswith('/**'):
            # Recursive directory match
            dir_pattern = pattern[:-3]
            if file_path.startswith(dir_pattern):
                matched.append(owner['handle'])
        elif pattern.startswith('*'):
            # Extension match
            if file_path.endswith(pattern[1:]):
                matched.append(owner['handle'])
        else:
            # Exact match or prefix
            if file_path == pattern or file_path.startswith(pattern):
                matched.append(owner['handle'])
    
    return list(set(matched))


# =============================================================================
# DEPENDENCY DETECTION
# =============================================================================

def find_importers(repo: str, file_path: str, language: str) -> List[str]:
    """Find files that import/include the given file."""
    importers = []
    repo_path = Path(repo)
    file_name = Path(file_path).stem
    
    # Language-specific import patterns
    if language == 'Python':
        patterns = [
            f'import {file_name}',
            f'from {file_name}',
            f'from .{file_name}',
        ]
    elif language in ['JavaScript', 'TypeScript']:
        patterns = [
            f"from '{file_name}'",
            f'from "{file_name}"',
            f"require('{file_name}'",
            f'require("{file_name}"',
        ]
    elif language == 'Go':
        patterns = [f'"{file_name}"']
    elif language == 'Java':
        patterns = [f'import.*{file_name}']
    else:
        patterns = [file_name]
    
    # Search using grep (efficient for large repos)
    for pattern in patterns[:2]:  # Limit patterns
        try:
            result = subprocess.run(
                ['grep', '-rl', pattern, '.'],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=30
            )
            for line in result.stdout.strip().split('\n'):
                if line and line != file_path:
                    importers.append(line.lstrip('./'))
        except (subprocess.TimeoutExpired, Exception):
            pass
    
    return list(set(importers))[:15]  # Limit results


def find_callers(repo: str, file_path: str, language: str) -> List[str]:
    """Find files that call functions from the given file."""
    # For simplicity, use the same logic as importers
    # In production, this would use AST analysis
    return find_importers(repo, file_path, language)


# =============================================================================
# MAIN BUILD FUNCTION
# =============================================================================

def build(
    repo: str,
    base: str,
    head: str,
    out: str,
    pr_title: Optional[str] = None,
    owners_path: Optional[str] = None,
    issues_json: Optional[str] = None
) -> Tuple[List[Dict], List[Dict]]:
    """
    Build Knowledge Graph from repository.
    
    Args:
        repo: Path to repository
        base: Base commit SHA
        head: Head commit SHA
        out: Output directory for KG files
        pr_title: Optional PR title
        owners_path: Path to CODEOWNERS file
        issues_json: Path to issues JSON (optional)
    
    Returns:
        Tuple of (nodes, edges) lists
    """
    print(f"Building Knowledge Graph...")
    print(f"  Repository: {repo}")
    print(f"  Base: {base}")
    print(f"  Head: {head}")
    
    nodes = []
    edges = []
    
    # 1. Create PR node
    pr_id = f"pr:{base[:8]}..{head[:8]}"
    nodes.append(KGNode(
        id=pr_id,
        type='PR',
        props={
            'base': base,
            'head': head,
            'title': pr_title or f"Changes from {base[:8]} to {head[:8]}"
        }
    ))
    
    # 2. Get changed files
    print("  Detecting changed files...")
    changed_files = get_changed_files(repo, base, head)
    print(f"    Found {len(changed_files)} changed files")
    
    # 3. Create File nodes and edges
    for cf in changed_files:
        file_id = f"file:{cf['path']}"
        
        # Get hunks for this file
        hunks = get_diff_hunks(repo, base, head, cf['path'])
        
        nodes.append(KGNode(
            id=file_id,
            type='File',
            props={
                'path': cf['path'],
                'language': cf['language']
            }
        ))
        
        edges.append(KGEdge(
            src_id=pr_id,
            dst_id=file_id,
            rel='touched_file',
            props={
                'added': cf['added'],
                'deleted': cf['deleted'],
                'hunks': hunks
            }
        ))
    
    # 4. Find tests
    print("  Finding related tests...")
    all_tests = set()
    for cf in changed_files:
        tests = find_tests_for_file(repo, cf['path'])
        for test in tests:
            test_id = f"test:{test['file']}"
            
            if test['file'] not in all_tests:
                all_tests.add(test['file'])
                nodes.append(KGNode(
                    id=test_id,
                    type='TestCase',
                    props={
                        'file': test['file'],
                        'name': test['name'],
                        'changed_in_pr': False
                    }
                ))
            
            edges.append(KGEdge(
                src_id=test_id,
                dst_id=f"file:{cf['path']}",
                rel='covers',
                props={'confidence': test['confidence']}
            ))
    
    print(f"    Found {len(all_tests)} related tests")
    
    # 5. Parse CODEOWNERS
    print("  Parsing code ownership...")
    owners = []
    if owners_path:
        owners = parse_codeowners(owners_path)
    else:
        # Try default locations
        for default_path in [
            os.path.join(repo, 'CODEOWNERS'),
            os.path.join(repo, '.github', 'CODEOWNERS'),
            os.path.join(repo, 'docs', 'CODEOWNERS'),
        ]:
            if os.path.exists(default_path):
                owners = parse_codeowners(default_path)
                break
    
    owner_nodes = set()
    for cf in changed_files:
        matched = match_owners(cf['path'], owners)
        for handle in matched:
            owner_id = f"owner:{handle}"
            
            if handle not in owner_nodes:
                owner_nodes.add(handle)
                nodes.append(KGNode(
                    id=owner_id,
                    type='Owner',
                    props={'handle': handle, 'pattern': ''}
                ))
            
            edges.append(KGEdge(
                src_id=owner_id,
                dst_id=f"file:{cf['path']}",
                rel='owns',
                props={}
            ))
    
    print(f"    Found {len(owner_nodes)} code owners")
    
    # 6. Find dependencies (importers/callers)
    print("  Analyzing dependencies...")
    dep_count = 0
    for cf in changed_files[:10]:  # Limit to first 10 files for performance
        language = cf['language']
        importers = find_importers(repo, cf['path'], language)
        
        for importer in importers[:5]:  # Limit importers per file
            importer_id = f"file:{importer}"
            
            # Add importer node if not exists
            if not any(n.id == importer_id for n in nodes if hasattr(n, 'id')):
                if not any(n['id'] == importer_id for n in nodes if isinstance(n, dict)):
                    nodes.append(KGNode(
                        id=importer_id,
                        type='File',
                        props={
                            'path': importer,
                            'language': detect_language(importer)
                        }
                    ))
            
            edges.append(KGEdge(
                src_id=importer_id,
                dst_id=f"file:{cf['path']}",
                rel='imports',
                props={}
            ))
            dep_count += 1
    
    print(f"    Found {dep_count} import relationships")
    
    # 7. Save KG
    os.makedirs(out, exist_ok=True)
    
    # Convert dataclasses to dicts
    nodes_data = [asdict(n) if hasattr(n, '__dataclass_fields__') else n for n in nodes]
    edges_data = [asdict(e) if hasattr(e, '__dataclass_fields__') else e for e in edges]
    
    with open(os.path.join(out, 'nodes.json'), 'w') as f:
        json.dump(nodes_data, f, indent=2)
    
    with open(os.path.join(out, 'edges.json'), 'w') as f:
        json.dump(edges_data, f, indent=2)
    
    print(f"\n✓ Knowledge Graph saved to {out}")
    print(f"  Nodes: {len(nodes_data)}")
    print(f"  Edges: {len(edges_data)}")
    
    return nodes_data, edges_data

