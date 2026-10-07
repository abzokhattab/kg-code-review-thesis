#!/usr/bin/env python3
"""
Rebuild evidence packs with ACTUAL git diffs included.

The previous evidence packs only had file paths with no code changes.
This script fetches real diffs from the cloned repos using the PR's
base/head commit SHAs and merges them into the existing evidence packs.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# PR Configuration with commit SHAs (from GitHub API)
# ============================================================================

PR_CONFIGS = {
    1: {
        "github_repo": "godotengine/godot",
        "pr_number": 73144,
    },
    2: {
        "github_repo": "grafana/grafana",
        "pr_number": 69259,
    },
    3: {
        "github_repo": "grafana/grafana",
        "pr_number": 97224,
    },
    5: {
        "github_repo": "jenkinsci/jenkins",
        "pr_number": 7142,
    },
    6: {
        "github_repo": "apache/kafka",
        "pr_number": 14778,
    },
    7: {
        "github_repo": "microsoft/TypeScript",
        "pr_number": 57375,
    },
    8: {
        "github_repo": "grafana/grafana",
        "pr_number": 95949,
    },
    9: {
        "github_repo": "grafana/grafana",
        "pr_number": 98123,
    },
    10: {
        "github_repo": "scikit-learn/scikit-learn",
        "pr_number": 22365,
    },
    11: {
        "github_repo": "django/django",
        "pr_number": 18523,
    },
}

BASE_DIR = Path("/Users/akhattab/ai")
EVIDENCE_DIR = BASE_DIR / "data" / "luca_prs_fixed"


def get_git_diff(repo_path: Path, base_sha: str, head_sha: str, max_chars: int = 15000) -> str:
    """Get the actual git diff between two commits."""
    try:
        result = subprocess.run(
            ["git", "diff", base_sha, head_sha],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout[:max_chars]
        else:
            print(f"    git diff failed (exit {result.returncode}): {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"    git diff timed out")
    except Exception as e:
        print(f"    git diff error: {e}")
    return ""


def get_per_file_stats(repo_path: Path, base_sha: str, head_sha: str) -> Dict[str, Dict[str, int]]:
    """Get per-file added/deleted line counts."""
    stats = {}
    try:
        result = subprocess.run(
            ["git", "diff", "--numstat", base_sha, head_sha],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) == 3:
                    added = int(parts[0]) if parts[0] != "-" else 0
                    deleted = int(parts[1]) if parts[1] != "-" else 0
                    file_path = parts[2]
                    stats[file_path] = {"added": added, "deleted": deleted}
    except Exception as e:
        print(f"    numstat error: {e}")
    return stats


def get_file_diff(repo_path: Path, base_sha: str, head_sha: str, file_path: str, max_chars: int = 3000) -> str:
    """Get the diff for a single file."""
    try:
        result = subprocess.run(
            ["git", "diff", base_sha, head_sha, "--", file_path],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout[:max_chars]
    except Exception:
        pass
    return ""


def get_github_diff(github_repo: str, pr_number: int, max_chars: int = 15000) -> str:
    """Get PR diff from GitHub using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr_number), "--repo", github_repo],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout[:max_chars]
        # Exit code 141 is SIGPIPE (from truncation) -- output is still valid
        if result.stdout and len(result.stdout) > 50:
            return result.stdout[:max_chars]
        print(f"    gh pr diff failed (exit {result.returncode}): {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"    gh pr diff timed out")
    except Exception as e:
        print(f"    gh pr diff error: {e}")
    return ""


def get_github_file_stats(github_repo: str, pr_number: int) -> Dict[str, Dict[str, int]]:
    """Get per-file stats from GitHub using gh CLI."""
    stats = {}
    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(pr_number), "--repo", github_repo,
             "--json", "files", "--jq", r'.files[] | "\(.additions)\t\(.deletions)\t\(.path)"'],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) == 3:
                    stats[parts[2]] = {
                        "added": int(parts[0]),
                        "deleted": int(parts[1]),
                    }
    except Exception as e:
        print(f"    file stats error: {e}")
    return stats


def rebuild_evidence(pr_id: int) -> bool:
    """Rebuild evidence pack with actual diffs from GitHub."""
    if pr_id not in PR_CONFIGS:
        print(f"  PR{pr_id}: Not configured, skipping")
        return False

    config = PR_CONFIGS[pr_id]
    evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"

    if not evidence_path.exists():
        print(f"  PR{pr_id}: Evidence pack not found at {evidence_path}")
        return False

    # Load existing evidence
    with open(evidence_path, "r") as f:
        evidence = json.load(f)

    github_repo = config["github_repo"]
    pr_number = config["pr_number"]

    # Get full diff from GitHub
    print(f"  Fetching diff from GitHub ({github_repo}#{pr_number})...")
    full_diff = get_github_diff(github_repo, pr_number)

    if not full_diff:
        print(f"  PR{pr_id}: Could not get diff!")
        return False

    # Get per-file stats from GitHub
    file_stats = get_github_file_stats(github_repo, pr_number)

    # Update changed_files with actual stats
    changed_files = evidence.get("changed_files", [])
    for cf in changed_files:
        path = cf.get("path", "")
        if path in file_stats:
            cf["added"] = file_stats[path]["added"]
            cf["deleted"] = file_stats[path]["deleted"]

    # Store full diff (truncated to fit in prompt)
    evidence["full_diff"] = full_diff

    # Save updated evidence
    with open(evidence_path, "w") as f:
        json.dump(evidence, f, indent=2)

    diff_size = len(full_diff)
    files_with_stats = sum(1 for cf in changed_files if cf.get("added", 0) > 0 or cf.get("deleted", 0) > 0)
    print(f"  PR{pr_id}: Updated! diff={diff_size} chars, {files_with_stats}/{len(changed_files)} files with stats")
    return True


def main():
    print("=" * 60)
    print("Rebuilding Evidence Packs with Actual Git Diffs")
    print("=" * 60)

    success = 0
    failed = 0

    for pr_id in sorted(PR_CONFIGS.keys()):
        print(f"\nPR #{pr_id}:")
        if rebuild_evidence(pr_id):
            success += 1
        else:
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Done! {success} updated, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
