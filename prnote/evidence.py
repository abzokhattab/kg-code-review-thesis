"""Evidence pack assembly module.

Loads Knowledge Graph and assembles evidence packs for LLM prompting.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


# =============================================================================
# KG LOADING
# =============================================================================

def load_kg(kg_dir: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Load Knowledge Graph from directory.
    
    Args:
        kg_dir: Path to KG directory containing nodes.json and edges.json
    
    Returns:
        Tuple of (nodes, edges) lists
    """
    kg_path = Path(kg_dir)
    
    nodes_path = kg_path / 'nodes.json'
    edges_path = kg_path / 'edges.json'
    
    if not nodes_path.exists():
        raise FileNotFoundError(f"KG nodes not found at {nodes_path}")
    if not edges_path.exists():
        raise FileNotFoundError(f"KG edges not found at {edges_path}")
    
    with open(nodes_path, 'r') as f:
        nodes = json.load(f)
    
    with open(edges_path, 'r') as f:
        edges = json.load(f)
    
    return nodes, edges


# =============================================================================
# EVIDENCE EXTRACTION
# =============================================================================

def extract_changed_files(nodes: List[Dict], edges: List[Dict], pr_id: str) -> List[Dict]:
    """Extract changed files from KG."""
    changed_files = []
    
    # Build lookup
    nodes_by_id = {n['id']: n for n in nodes}
    
    for edge in edges:
        if edge['src_id'] == pr_id and edge['rel'] == 'touched_file':
            file_node = nodes_by_id.get(edge['dst_id'])
            if file_node:
                changed_files.append({
                    'path': file_node['props'].get('path', ''),
                    'language': file_node['props'].get('language', 'unknown'),
                    'hunks': edge['props'].get('hunks', []),
                    'added': edge['props'].get('added', 0),
                    'deleted': edge['props'].get('deleted', 0)
                })
    
    return changed_files


def extract_tests(nodes: List[Dict], edges: List[Dict], changed_file_ids: List[str]) -> List[Dict]:
    """Extract tests that cover changed files."""
    tests = []
    
    # Build lookup
    nodes_by_id = {n['id']: n for n in nodes}
    edges_by_rel = {}
    for edge in edges:
        if edge['rel'] not in edges_by_rel:
            edges_by_rel[edge['rel']] = []
        edges_by_rel[edge['rel']].append(edge)
    
    # Find test nodes that cover changed files
    for edge in edges_by_rel.get('covers', []):
        if edge['dst_id'] in changed_file_ids:
            test_node = nodes_by_id.get(edge['src_id'])
            if test_node and test_node['type'] == 'TestCase':
                tests.append({
                    'path': test_node['props'].get('file', ''),
                    'name': test_node['props'].get('name', ''),
                    'confidence': edge['props'].get('confidence', 0.5),
                    'covers': edge['dst_id'].replace('file:', '')
                })
    
    # Sort by confidence and deduplicate
    tests.sort(key=lambda t: t['confidence'], reverse=True)
    seen = set()
    unique_tests = []
    for t in tests:
        if t['path'] not in seen:
            seen.add(t['path'])
            unique_tests.append(t)
    
    return unique_tests


def extract_owners(nodes: List[Dict], edges: List[Dict], changed_file_ids: List[str]) -> List[Dict]:
    """Extract owners for changed files."""
    owners = []
    
    # Build lookup
    nodes_by_id = {n['id']: n for n in nodes}
    
    for edge in edges:
        if edge['rel'] == 'owns' and edge['dst_id'] in changed_file_ids:
            owner_node = nodes_by_id.get(edge['src_id'])
            if owner_node and owner_node['type'] == 'Owner':
                owners.append({
                    'handle': owner_node['props'].get('handle', ''),
                    'pattern': owner_node['props'].get('pattern', ''),
                    'owns': edge['dst_id'].replace('file:', '')
                })
    
    # Deduplicate by handle
    seen = set()
    unique_owners = []
    for o in owners:
        if o['handle'] not in seen:
            seen.add(o['handle'])
            unique_owners.append(o)
    
    return unique_owners


def extract_dependents(nodes: List[Dict], edges: List[Dict], changed_file_ids: List[str]) -> List[Dict]:
    """Extract files that depend on (import/call) changed files."""
    dependents = []
    
    # Build lookup
    nodes_by_id = {n['id']: n for n in nodes}
    
    for edge in edges:
        if edge['rel'] in ['imports', 'calls_function_in'] and edge['dst_id'] in changed_file_ids:
            dep_node = nodes_by_id.get(edge['src_id'])
            if dep_node:
                dependents.append({
                    'path': dep_node['props'].get('path', ''),
                    'language': dep_node['props'].get('language', 'unknown'),
                    'relationship': edge['rel'],
                    'depends_on': edge['dst_id'].replace('file:', '')
                })
    
    # Deduplicate by path
    seen = set()
    unique_deps = []
    for d in dependents:
        if d['path'] not in seen:
            seen.add(d['path'])
            unique_deps.append(d)
    
    return unique_deps


# =============================================================================
# ISSUES LOADING
# =============================================================================

def load_related_issues(issues_json: Optional[str], pr_title: str) -> List[Dict]:
    """Load and filter related issues (if available)."""
    if not issues_json or not os.path.exists(issues_json):
        return []
    
    try:
        with open(issues_json, 'r') as f:
            issues = json.load(f)
        
        # Simple keyword matching (in production, use semantic similarity)
        keywords = set(pr_title.lower().split())
        related = []
        
        for issue in issues[:100]:  # Limit search
            issue_title = issue.get('title', '').lower()
            issue_words = set(issue_title.split())
            
            overlap = len(keywords & issue_words)
            if overlap >= 2:  # At least 2 words in common
                related.append({
                    'number': issue.get('number', 0),
                    'title': issue.get('title', ''),
                    'state': issue.get('state', 'unknown'),
                    'relevance': overlap / len(keywords) if keywords else 0
                })
        
        # Sort by relevance
        related.sort(key=lambda i: i['relevance'], reverse=True)
        return related[:5]
    
    except Exception:
        return []


# =============================================================================
# MAIN PACK FUNCTION
# =============================================================================

def pack(
    repo: str,
    kg: str,
    base: str,
    head: str,
    out: str,
    max_tests: int = 3,
    max_issues: int = 2,
    issues_json: Optional[str] = None
) -> Dict[str, Any]:
    """
    Assemble evidence pack from Knowledge Graph.
    
    Args:
        repo: Path to repository
        kg: Path to KG directory
        base: Base commit SHA
        head: Head commit SHA
        out: Output path for evidence pack JSON
        max_tests: Maximum tests to include
        max_issues: Maximum issues to include
        issues_json: Optional path to issues JSON
    
    Returns:
        Evidence pack dictionary
    """
    print("Assembling evidence pack from KG...")
    
    # Load KG
    nodes, edges = load_kg(kg)
    
    # Find PR node
    pr_node = None
    for node in nodes:
        if node['type'] == 'PR':
            pr_node = node
            break
    
    if not pr_node:
        raise ValueError("No PR node found in KG")
    
    pr_id = pr_node['id']
    pr_props = pr_node['props']
    
    # Extract evidence
    changed_files = extract_changed_files(nodes, edges, pr_id)
    changed_file_ids = [f"file:{f['path']}" for f in changed_files]
    
    nearest_tests = extract_tests(nodes, edges, changed_file_ids)[:max_tests]
    owners = extract_owners(nodes, edges, changed_file_ids)
    dependent_files = extract_dependents(nodes, edges, changed_file_ids)
    
    # Load related issues if available
    related_issues = load_related_issues(issues_json, pr_props.get('title', ''))[:max_issues]
    
    # Assemble evidence pack
    evidence = {
        'pr': {
            'base': pr_props.get('base', base),
            'head': pr_props.get('head', head),
            'title': pr_props.get('title', '')
        },
        'changed_files': changed_files,
        'nearest_tests': nearest_tests,
        'owners': owners,
        'dependent_files': dependent_files,
        'related_issues': related_issues,
        'summary': {
            'files_changed': len(changed_files),
            'tests_found': len(nearest_tests),
            'owners_found': len(owners),
            'dependents_found': len(dependent_files),
            'issues_found': len(related_issues)
        }
    }
    
    # Save evidence pack
    os.makedirs(Path(out).parent, exist_ok=True)
    with open(out, 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print(f"\n✓ Evidence pack saved to {out}")
    print(f"  Changed files: {len(changed_files)}")
    print(f"  Tests: {len(nearest_tests)}")
    print(f"  Owners: {len(owners)}")
    print(f"  Dependents: {len(dependent_files)}")
    print(f"  Related issues: {len(related_issues)}")
    
    return evidence


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def summarize_evidence(evidence_path: str) -> str:
    """Generate a human-readable summary of evidence pack."""
    with open(evidence_path, 'r') as f:
        evidence = json.load(f)
    
    summary = []
    summary.append(f"PR: {evidence.get('pr', {}).get('title', 'Unknown')}")
    summary.append(f"Files: {len(evidence.get('changed_files', []))}")
    summary.append(f"Tests: {len(evidence.get('nearest_tests', []))}")
    summary.append(f"Owners: {len(evidence.get('owners', []))}")
    summary.append(f"Dependents: {len(evidence.get('dependent_files', []))}")
    
    return " | ".join(summary)


def merge_evidence_packs(pack1: Dict, pack2: Dict) -> Dict:
    """Merge two evidence packs (e.g., KG + RAG)."""
    merged = {
        'pr': pack1.get('pr', pack2.get('pr', {})),
        'changed_files': pack1.get('changed_files', []),
        'nearest_tests': pack1.get('nearest_tests', []),
        'owners': pack1.get('owners', []),
        'dependent_files': pack1.get('dependent_files', []),
        'related_issues': pack1.get('related_issues', []),
        'similar_chunks': pack2.get('similar_chunks', pack1.get('similar_chunks', [])),
        'kg_evidence': pack1.get('kg_evidence', {}),
        'rag_evidence': pack2.get('rag_evidence', {}),
    }
    
    return merged

