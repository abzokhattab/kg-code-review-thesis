#!/usr/bin/env python3
"""
Build proper KG evidence packs from Luca's PR data and cloned repositories.

This script:
1. Reads the original PR JSON from Luca's data
2. Extracts changed files from the PR
3. Finds related tests in the repository
4. Finds dependent files (imports/calls)
5. Creates comprehensive evidence packs for KG mode

Note: Code owners removed - only 1/5 repos have CODEOWNERS and it's
not relevant to review quality (routing concern, not content concern).
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PRInfo:
    """Information about a PR."""
    number: int
    title: str
    body: str
    repo_owner: str
    repo_name: str
    base_sha: str
    head_sha: str
    changed_files: List[str]


# Map PR IDs to their repos
PR_CONFIG = {
    1: {
        "repo_path": "luca_repos/godotengine_godot",
        "pr_number": 73144,
        "repo_owner": "godotengine",
        "repo_name": "godot",
        "language": "cpp",
    },
    2: {
        "repo_path": "luca_repos/grafana_grafana", 
        "pr_number": 69259,
        "repo_owner": "grafana",
        "repo_name": "grafana",
        "language": "go,typescript",
    },
    3: {
        "repo_path": "luca_repos/grafana_grafana",
        "pr_number": 97224,
        "repo_owner": "grafana", 
        "repo_name": "grafana",
        "language": "go,typescript",
    },
    # PR 4 is skipped (not merged)
    5: {
        "repo_path": "luca_repos/jenkinsci_jenkins",
        "pr_number": 7142,
        "repo_owner": "jenkinsci",
        "repo_name": "jenkins",
        "language": "java",
    },
    6: {
        "repo_path": "luca_repos/apache_kafka",
        "pr_number": 14778,
        "repo_owner": "apache",
        "repo_name": "kafka",
        "language": "java,scala",
    },
}

# Path to Luca's PR data
LUCA_DATA_PATH = "/Users/akhattab/Downloads/thesis code/additional data, plots, etc/experiment/prs"

# Path to existing evidence packs (which have changed files)
EXISTING_EVIDENCE_PATH = "/Users/akhattab/ai/data/luca_prs"

# Hardcoded changed files for PRs where data was missing
HARDCODED_CHANGED_FILES = {
    3: [  # PR #97224 - Grafana Reduce component
        "public/app/features/expressions/components/Reduce.tsx",
        "public/locales/en-US/grafana.json",
        "public/locales/pseudo-LOCALE/grafana.json",
    ],
    6: [  # PR #14778 - Kafka DelayedRemoteFetch
        "clients/src/main/java/org/apache/kafka/clients/consumer/ConsumerConfig.java",
        "core/src/main/scala/kafka/server/DelayedRemoteFetch.scala",
        "core/src/main/scala/kafka/server/ReplicaManager.scala",
        "core/src/test/scala/integration/kafka/server/DelayedRemoteFetchTest.scala",
        "storage/src/main/java/org/apache/kafka/server/log/remote/storage/RemoteLogManagerConfig.java",
        "storage/src/test/java/org/apache/kafka/server/log/remote/storage/RemoteLogManagerConfigTest.java",
    ],
}


def load_pr_json(pr_id: int) -> Dict[str, Any]:
    """Load the original PR JSON from Luca's data."""
    pr_json_path = Path(LUCA_DATA_PATH) / str(pr_id) / "versions" / "original" / "original_pr.json"
    
    if not pr_json_path.exists():
        print(f"  ⚠️ PR JSON not found at {pr_json_path}")
        return {}
    
    with open(pr_json_path, 'r') as f:
        return json.load(f)


def load_existing_evidence(pr_id: int) -> Dict[str, Any]:
    """Load existing evidence pack to get changed files."""
    evidence_path = Path(EXISTING_EVIDENCE_PATH) / f"pr{pr_id}_evidence.json"
    
    if not evidence_path.exists():
        print(f"  ⚠️ Existing evidence not found at {evidence_path}")
        return {}
    
    with open(evidence_path, 'r') as f:
        return json.load(f)


def get_changed_files_from_github(pr_number: int, repo_owner: str, repo_name: str) -> List[str]:
    """Get changed files from GitHub API (requires gh CLI)."""
    try:
        result = subprocess.run(
            ['gh', 'pr', 'view', str(pr_number), 
             '--repo', f'{repo_owner}/{repo_name}',
             '--json', 'files', '--jq', '.files[].path'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    except Exception as e:
        print(f"  ⚠️ Could not get files from GitHub: {e}")
    return []


def find_tests_for_file(file_path: str, repo_path: str, language: str) -> List[Dict[str, Any]]:
    """Find test files related to a source file using grep (universally available)."""
    tests = []
    file_name = Path(file_path).stem
    file_dir = Path(file_path).parent
    
    # Skip very generic file names
    if file_name.lower() in ['index', 'main', 'mod', 'lib']:
        return []
    
    # Strategy 1: Find test files by name pattern using find
    test_name_patterns = [
        f"*{file_name}*[Tt]est*",      # ConsumerConfigTest, test_config
        f"*[Tt]est*{file_name}*",      # TestConsumerConfig
        f"*{file_name}*[Ss]pec*",      # ConsumerConfig.spec.ts
        f"*{file_name}*_test*",        # config_test.go
    ]
    
    for pattern in test_name_patterns:
        try:
            result = subprocess.run(
                ['find', repo_path, '-name', pattern, '-type', 'f'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                for test_file in result.stdout.strip().split('\n'):
                    if test_file:
                        rel_path = os.path.relpath(test_file, repo_path)
                        if rel_path not in [t['path'] for t in tests]:
                            tests.append({
                                "path": rel_path,
                                "relationship": "tests",
                                "source_file": file_path,
                            })
        except Exception:
            pass
    
    # Strategy 2: Find test files in same directory structure
    # e.g., src/main/java/Foo.java -> src/test/java/FooTest.java
    try:
        # Look for parallel test directory
        path_parts = list(file_dir.parts)
        for i, part in enumerate(path_parts):
            if part in ['main', 'src']:
                test_dir = Path(*path_parts[:i], 'test', *path_parts[i+1:])
                result = subprocess.run(
                    ['find', str(Path(repo_path) / test_dir), '-name', f'*{file_name}*', '-type', 'f'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for test_file in result.stdout.strip().split('\n'):
                        if test_file:
                            rel_path = os.path.relpath(test_file, repo_path)
                            if rel_path not in [t['path'] for t in tests]:
                                tests.append({
                                    "path": rel_path,
                                    "relationship": "tests",
                                    "source_file": file_path,
                                })
    except Exception:
        pass
    
    # Strategy 3: Use grep to find files that mention this file in test directories
    try:
        result = subprocess.run(
            ['grep', '-rl', file_name, repo_path, 
             '--include=*[Tt]est*', '--include=*[Ss]pec*', '--include=*_test*'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            for match in result.stdout.strip().split('\n'):
                if match:
                    rel_path = os.path.relpath(match, repo_path)
                    if rel_path not in [t['path'] for t in tests]:
                        tests.append({
                            "path": rel_path,
                            "relationship": "may_test",
                            "source_file": file_path,
                        })
    except Exception:
        pass
    
    return tests[:10]  # Limit to 10 tests


def find_dependents_for_file(file_path: str, repo_path: str, language: str) -> List[Dict[str, Any]]:
    """Find files that import/depend on the changed file using grep."""
    dependents = []
    file_name = Path(file_path).stem
    
    # Skip very common/generic names that would match too much
    if file_name.lower() in ['index', 'main', 'utils', 'helpers', 'types', 'constants', 'mod', 'lib']:
        return []
    
    # File extensions to search based on language
    extensions = {
        "java": ["*.java"],
        "go": ["*.go"],
        "typescript": ["*.ts", "*.tsx"],
        "cpp": ["*.cpp", "*.h", "*.hpp", "*.cc"],
        "scala": ["*.scala"],
    }
    
    # Build include patterns for grep
    include_patterns = []
    for lang in language.split(','):
        include_patterns.extend(extensions.get(lang.strip(), []))
    
    if not include_patterns:
        include_patterns = ["*.java", "*.go", "*.ts", "*.tsx", "*.cpp", "*.scala"]
    
    # Search for imports/usage of this file
    try:
        grep_args = ['grep', '-rl', file_name, repo_path]
        for pattern in include_patterns:
            grep_args.extend(['--include', pattern])
        
        result = subprocess.run(
            grep_args,
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode == 0:
            for match in result.stdout.strip().split('\n'):
                if match and match != file_path:
                    rel_path = os.path.relpath(match, repo_path)
                    # Skip test files - we want production dependents
                    if ('test' not in rel_path.lower() and 
                        'spec' not in rel_path.lower() and
                        rel_path not in [d['path'] for d in dependents]):
                        dependents.append({
                            "path": rel_path,
                            "relationship": "imports",
                            "target": file_path,
                        })
    except Exception as e:
        print(f"  ⚠️ Error finding dependents: {e}")
    
    return dependents[:15]  # Limit to 15 dependents


def get_diff_content(pr_json: Dict[str, Any], changed_files: List[str]) -> str:
    """Extract diff-like content from PR data."""
    diff_lines = []
    
    # Add PR title and body as context
    diff_lines.append(f"PR: {pr_json.get('title', 'Unknown')}")
    diff_lines.append(f"Description: {pr_json.get('body', '')[:500]}")
    diff_lines.append("")
    
    # List changed files
    for f in changed_files:
        diff_lines.append(f"Changed: {f}")
    
    return "\n".join(diff_lines)


def build_evidence_pack(pr_id: int) -> Dict[str, Any]:
    """Build a comprehensive evidence pack for a PR."""
    
    if pr_id not in PR_CONFIG:
        return {"error": f"PR {pr_id} not configured"}
    
    config = PR_CONFIG[pr_id]
    repo_path = Path("/Users/akhattab/ai") / config["repo_path"]
    
    print(f"\n{'='*60}")
    print(f"Building evidence pack for PR #{pr_id}")
    print(f"{'='*60}")
    
    # Load PR JSON
    pr_json = load_pr_json(pr_id)
    if not pr_json:
        print(f"  ⚠️ Could not load PR JSON")
        return {"error": "PR JSON not found"}
    
    print(f"  Title: {pr_json.get('title', 'Unknown')}")
    
    # Get changed files from existing evidence (already computed)
    existing = load_existing_evidence(pr_id)
    changed_files = [f['path'] for f in existing.get('changed_files', [])]
    
    if not changed_files:
        # Fallback to hardcoded files (for PRs 3 and 6)
        if pr_id in HARDCODED_CHANGED_FILES:
            changed_files = HARDCODED_CHANGED_FILES[pr_id]
            print(f"  Using hardcoded changed files")
        else:
            # Last resort: GitHub API
            changed_files = get_changed_files_from_github(
                config["pr_number"],
                config["repo_owner"],
                config["repo_name"]
            )
    
    if not changed_files:
        print(f"  ⚠️ No changed files found!")
        changed_files = []
    
    print(f"  Changed files: {len(changed_files)}")
    for f in changed_files[:5]:
        print(f"    - {f}")
    if len(changed_files) > 5:
        print(f"    ... and {len(changed_files) - 5} more")
    
    # Find tests
    all_tests = []
    for f in changed_files[:10]:  # Limit to first 10 files
        tests = find_tests_for_file(f, str(repo_path), config["language"])
        all_tests.extend(tests)
    
    # Deduplicate tests
    seen_tests = set()
    unique_tests = []
    for t in all_tests:
        if t['path'] not in seen_tests:
            seen_tests.add(t['path'])
            unique_tests.append(t)
    
    print(f"  Related tests: {len(unique_tests)}")
    for t in unique_tests[:3]:
        print(f"    - {t['path']}")
    
    # Find dependents
    all_dependents = []
    for f in changed_files[:10]:
        deps = find_dependents_for_file(f, str(repo_path), config["language"])
        all_dependents.extend(deps)
    
    # Deduplicate dependents
    seen_deps = set()
    unique_deps = []
    for d in all_dependents:
        if d['path'] not in seen_deps:
            seen_deps.add(d['path'])
            unique_deps.append(d)
    
    print(f"  Dependent files: {len(unique_deps)}")
    for d in unique_deps[:3]:
        print(f"    - {d['path']}")
    
    # Build evidence pack
    evidence_pack = {
        "pr": {
            "number": pr_json.get("number", config["pr_number"]),
            "title": pr_json.get("title", "Unknown"),
            "url": pr_json.get("url", f"https://github.com/{config['repo_owner']}/{config['repo_name']}/pull/{config['pr_number']}"),
            "state": pr_json.get("state", "MERGED"),
            "repo_owner": config["repo_owner"],
            "repo_name": config["repo_name"],
        },
        "changed_files": [
            {
                "path": f,
                "language": config["language"].split(',')[0],
            }
            for f in changed_files
        ],
        "nearest_tests": unique_tests,
        "dependent_files": unique_deps,
        "diff_summary": get_diff_content(pr_json, changed_files),
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "build_kg_evidence.py",
            "repo_path": str(repo_path),
        }
    }
    
    return evidence_pack


def main():
    """Build evidence packs for all PRs."""
    output_dir = Path("/Users/akhattab/ai/data/luca_prs_fixed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Building KG Evidence Packs for Luca's PRs")
    print("="*60)
    
    for pr_id in [1, 2, 3, 5, 6]:  # Skip PR 4 (not merged)
        evidence = build_evidence_pack(pr_id)
        
        # Save evidence pack
        output_path = output_dir / f"pr{pr_id}_evidence.json"
        with open(output_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        print(f"\n✓ Saved to {output_path}")
    
    print("\n" + "="*60)
    print("Done! Evidence packs saved to:", output_dir)
    print("="*60)


if __name__ == "__main__":
    main()

