#!/usr/bin/env python3
"""
find_confirmatory_prs.py — Select 12 NEW PRs for the confirmatory KG experiment.

Purpose: Validate the exploratory finding (KG v3 improves structural review quality)
on held-out data that was never part of the original 40-PR dataset.

Same 8 direction-blind criteria as dataset_v2:
  1. Merged
  2. Not a revert/backport
  3. Substantive code change (≥1 KG-parseable file)
  4. 100% KG-parseable (no .kt, .swift, etc.)
  5. Diff < 50 kB
  6. Real PR body (≥100 chars)
  7. Not cosmetic/chore/docs/bump
  8. KG-rich: ≥2 KG-parseable code files

Selection rule: most recent merged PRs by descending PR number, excluding all
existing 40-PR dataset entries. No LLM output is consulted.

Targets: 4 grafana, 2 kafka, 2 sklearn, 2 godot, 2 jenkins = 12 PRs

Output: experiments/2026-05-14_confirmatory_kg/candidates.json
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_PATH = SCRIPT_DIR / "candidates.json"

KG_EXTS = {
    ".py", ".pyi",
    ".java", ".scala",
    ".cpp", ".cc", ".c", ".h", ".hpp",
    ".go",
    ".ts", ".tsx", ".js", ".jsx",
    ".gd", ".rs",
}
NON_KG_CODE_EXTS = {
    ".jelly", ".kt", ".swift", ".m", ".mm",
    ".rb", ".php", ".elm", ".dart",
    ".cue", ".gradle", ".groovy",
}

REPOS = {
    "grafana/grafana":           (80,  4),
    "apache/kafka":              (80,  2),
    "scikit-learn/scikit-learn": (80,  2),
    "godotengine/godot":         (80,  2),
    "jenkinsci/jenkins":         (300, 2),
}

# ALL existing PRs from the 40-PR dataset (GitHub PR numbers, NOT local IDs)
EXISTING = {
    "grafana/grafana": {
        67809, 69259, 78399, 95949, 97224, 98123,
        124099, 124090, 124601, 124598, 124593, 124572, 124557,
    },
    "apache/kafka": {
        14778, 17441, 17594, 18330, 22195, 22255, 22249, 22241,
    },
    "godotengine/godot": {
        68625, 73144, 89111, 119132, 119412, 119349,
    },
    "scikit-learn/scikit-learn": {
        22365, 22643, 26836, 33918, 33878, 33979, 33964, 33957,
    },
    "jenkinsci/jenkins": {
        6229, 9002, 26711, 26749, 26636,
    },
}


def gh(args: list[str]) -> str:
    if not shutil.which("gh"):
        sys.exit("`gh` CLI is required.")
    r = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        sys.exit(f"gh failed: {' '.join(args)}\n{r.stderr}")
    return r.stdout


def list_recent_merged(repo: str, n: int) -> list[dict]:
    raw = gh([
        "pr", "list", "--repo", repo, "--state", "merged",
        "--limit", str(n),
        "--json", "number,title,body,additions,deletions,changedFiles,mergedAt,url",
    ])
    return json.loads(raw)


def fetch_pr_files(repo: str, number: int) -> list[dict]:
    raw = gh([
        "api", f"repos/{repo}/pulls/{number}/files",
        "--paginate",
    ])
    items = json.loads(raw)
    return [{"path": it["filename"],
             "additions": it.get("additions", 0),
             "deletions": it.get("deletions", 0)} for it in items]


def ext_of(path: str) -> str:
    return "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""


def audit(pr: dict, files: list[dict], repo: str) -> dict:
    body = pr.get("body") or ""
    title = pr.get("title", "") or ""
    diff_bytes = sum(f["additions"] + f["deletions"] for f in files) * 80
    paths = [f["path"] for f in files]
    code_files = [p for p in paths if ext_of(p) in KG_EXTS]
    non_kg_code = [p for p in paths if ext_of(p) in NON_KG_CODE_EXTS]

    n_code = len(code_files)
    n_non_kg_code = len(non_kg_code)

    crit = {}
    crit["c1_merged"] = True
    crit["c2_not_revert"] = not re.match(r"^(revert|reapply)\b", title, re.IGNORECASE)
    crit["c3_has_code_change"] = n_code >= 1
    crit["c4_kg_parseable_100pct"] = n_non_kg_code == 0 and n_code >= 1
    crit["c5_diff_under_50kb"] = diff_bytes <= 50_000
    crit["c6_body_real"] = len(body.strip()) >= 100
    crit["c7_not_in_existing"] = pr["number"] not in EXISTING.get(repo, set())
    crit["c8_kg_rich_multifile"] = n_code >= 2

    return {
        "passes_all": all(crit.values()),
        "criteria": crit,
        "n_files": len(paths),
        "n_code": n_code,
        "n_non_kg": n_non_kg_code,
        "diff_bytes_estimate": diff_bytes,
        "extensions": sorted({ext_of(p) for p in paths}),
    }


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_candidates = {}
    picked = []

    for repo, (n_fetch, n_target) in REPOS.items():
        print(f"\n==> {repo}: fetching last {n_fetch} merged PRs", flush=True)
        prs = list_recent_merged(repo, n_fetch)
        cands = []
        for pr in prs:
            if pr["number"] in EXISTING.get(repo, set()):
                continue
            body = pr.get("body") or ""
            title = pr.get("title", "") or ""
            adds = pr.get("additions", 0)
            dels = pr.get("deletions", 0)
            est_diff = (adds + dels) * 80
            n_changed = pr.get("changedFiles", 0)
            # Quick filters before expensive API call
            if len(body.strip()) < 100:
                continue
            if re.match(r"^(revert|reapply)\b", title, re.IGNORECASE):
                continue
            if re.match(r"^(bump|chore[: ]|docs?[: ]|doc[: ]|"
                        r"update dependency|update peer dependency|"
                        r":(lock|robot|memo|sparkles):)",
                        title, re.IGNORECASE):
                continue
            if re.match(r"^(i18n|l10n|translations?:)", title, re.IGNORECASE):
                continue
            if re.search(r"\(#\d{2,6}\)\s*$", title):
                continue
            if est_diff > 60_000 or est_diff < 1_500:
                continue
            if n_changed < 2 or n_changed > 25:
                continue
            try:
                files = fetch_pr_files(repo, pr["number"])
            except (SystemExit, Exception):
                continue
            a = audit(pr, files, repo)
            if not a["passes_all"]:
                continue
            print(f"    pr#{pr['number']:>7}  files={a['n_code']:>2}/{a['n_files']:<2}  "
                  f"~{est_diff/1024:>5.1f}kB  "
                  f"{title[:55]}", flush=True)
            cands.append({
                "repo": repo,
                "number": pr["number"],
                "title": title,
                "body_len": len(body),
                "url": pr.get("url"),
                "merged_at": pr.get("mergedAt"),
                "audit": a,
            })
        cands.sort(key=lambda c: -c["number"])
        repo_picks = cands[:n_target]
        for p in repo_picks:
            p["picked"] = True
            picked.append(p)
        print(f"  -> passing={len(cands)}  picked={len(repo_picks)} (target={n_target})",
              flush=True)
        all_candidates[repo] = cands

    OUT_PATH.write_text(json.dumps({
        "experiment": "confirmatory_kg_2026-05-14",
        "rule": (
            "Same 8 direction-blind criteria as dataset_v2 SELECTION_v2.md. "
            "Excludes all 40 existing PR numbers. Within each repo, pick the "
            "N most recent merged PRs that pass every criterion. "
            "Targets: 4 grafana, 2 kafka, 2 sklearn, 2 godot, 2 jenkins = 12. "
            "No LLM-judge metric is consulted. This is a confirmatory experiment "
            "on held-out data."
        ),
        "targets": {r: t for r, (_, t) in REPOS.items()},
        "candidates_by_repo": all_candidates,
        "picked": picked,
        "n_picked": len(picked),
    }, indent=2))

    print(f"\n{'='*70}")
    print(f"Wrote {OUT_PATH}")
    print(f"Picked {len(picked)} new PRs for confirmatory experiment:")
    print(f"{'='*70}")
    for p in picked:
        a = p["audit"]
        print(f"  {p['repo']:30s} #{p['number']:>7}   "
              f"files={a['n_code']:>2}/{a['n_files']:<3}   "
              f"~{a['diff_bytes_estimate']/1024:>5.1f}kB   "
              f"{p['title'][:60]}")


if __name__ == "__main__":
    main()
