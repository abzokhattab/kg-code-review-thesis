#!/usr/bin/env python3
"""
find_fifteen_more_prs.py — Deterministically pick 15 NEW PRs to expand
`dataset_v2` from 25 to 40 PRs.

Same direction-blind audit as find_seven_more_prs.py, plus one
**KG-richness** filter requested by the supervisor on 2026-05-12:

    Pick PRs where the knowledge graph has meaningful structural
    relationships to surface — i.e., the diff is not a single-file
    one-line change. This gives KG mode a fair chance to demonstrate
    its multi-file context value.

Operationalised as a stimulus-side constraint, not an outcome-side one:

    8. ≥ 2 KG-parseable code files in the diff
       (KG has at least one inter-file relationship to traverse)

This is consistent with the criteria the supervisor signed off on:
"more PRs if that would serve the thesis; pick good PRs that are
usable for KG to see its performance".

Selection rule (within each repo, after every constraint passes):
take the MOST RECENT N merged PRs by descending PR number. No
LLM-judge metric is ever consulted.

Targets (matching the v2 25-PR distribution):
    grafana   +5  → 13
    kafka     +3  → 8
    sklearn   +3  → 8
    godot     +2  → 6
    jenkins   +2  → 5
    Total     +15 → 40

Output: `dataset_v2/docs/fifteen_more_candidates.json`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH  = REPO_ROOT / "dataset_v2" / "docs" / "fifteen_more_candidates.json"

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
NON_CODE_EXTS = {
    ".md", ".rst", ".txt", ".mdx",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".env",
    ".xml", ".html", ".css", ".scss",
    ".lock", ".sum",
    ".snap", ".golden", ".results",
    ".png", ".gif", ".jpg", ".jpeg", ".ico", ".svg", ".webp",
    ".gitignore", ".dockerignore",
}

REPOS = {
    # repo: (n_to_fetch, target_to_pick)
    "grafana/grafana":              (60,  5),
    "apache/kafka":                 (60,  3),
    "scikit-learn/scikit-learn":    (60,  3),
    "godotengine/godot":            (60,  2),
    "jenkinsci/jenkins":            (300, 2),  # jenkins merges slowly
}

# Existing v2 PRs (the 25 already on disk): do not double-fetch.
EXISTING = {
    "grafana/grafana":              {67809, 69259, 78399, 95949, 97224, 98123,
                                     124099, 124090},
    "apache/kafka":                 {14778, 17441, 17594, 18330, 22195},
    "godotengine/godot":            {68625, 73144, 89111, 119132},
    "scikit-learn/scikit-learn":    {22365, 22643, 26836, 33918, 33878},
    "jenkinsci/jenkins":            {6229, 9002, 26711},
}


def gh(args: list[str]) -> str:
    if not shutil.which("gh"):
        sys.exit("`gh` CLI is required.")
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
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


def audit(pr: dict, files: list[dict]) -> dict:
    body  = pr.get("body") or ""
    title = pr.get("title", "") or ""
    diff_bytes = sum(f["additions"] + f["deletions"] for f in files) * 80
    paths      = [f["path"] for f in files]
    code_files = [p for p in paths if ext_of(p) in KG_EXTS]
    non_kg_code = [p for p in paths if ext_of(p) in NON_KG_CODE_EXTS]

    n_code  = len(code_files)
    n_non_kg_code = len(non_kg_code)

    crit = {}
    crit["c1_merged"] = True
    crit["c2_not_revert"] = not re.match(r"^(revert|reapply)\b", title, re.IGNORECASE)
    crit["c3_has_code_change"] = n_code >= 1
    crit["c4_kg_parseable_100pct"] = n_non_kg_code == 0 and n_code >= 1
    crit["c5_diff_under_50kb"] = diff_bytes <= 50_000
    crit["c6_body_real"] = len(body.strip()) >= 100
    crit["c7_not_already_in_v2"] = pr["number"] not in EXISTING.get(pr.get("__repo", ""), set())
    # Supervisor's KG-richness ask, operationalised:
    crit["c8_kg_rich_multifile"] = n_code >= 2

    return {
        "passes_all": all(crit.values()),
        "criteria":   crit,
        "n_files":    len(paths),
        "n_code":     n_code,
        "n_non_kg":   n_non_kg_code,
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
            pr["__repo"] = repo
            if pr["number"] in EXISTING.get(repo, set()):
                continue
            body = pr.get("body") or ""
            title = pr.get("title", "") or ""
            adds  = pr.get("additions", 0)
            dels  = pr.get("deletions", 0)
            est_diff = (adds + dels) * 80
            n_changed = pr.get("changedFiles", 0)
            if len(body.strip()) < 100: continue
            if re.match(r"^(revert|reapply)\b", title, re.IGNORECASE): continue
            if re.match(r"^(bump|chore[: ]|docs?[: ]|doc[: ]|"
                        r"update dependency|update peer dependency|"
                        r":(lock|robot|memo|sparkles):)",
                        title, re.IGNORECASE): continue
            if re.match(r"^(i18n|l10n|translations?:)", title, re.IGNORECASE): continue
            # Drop backports (title ends with "(#NNNNN)" referencing the original).
            if re.search(r"\(#\d{2,6}\)\s*$", title): continue
            if est_diff > 60_000 or est_diff < 1_500: continue
            if n_changed < 2 or n_changed > 25: continue  # 2 minimum for KG-rich
            try:
                files = fetch_pr_files(repo, pr["number"])
            except SystemExit:
                continue
            a = audit(pr, files)
            if not a["passes_all"]:
                continue  # only keep passing rows for log readability
            print(f"    pr#{pr['number']:>7}  files={a['n_code']:>2}/{a['n_files']:<2}  "
                  f"~{est_diff/1024:>5.1f}kB  "
                  f"{title[:55]}", flush=True)
            cands.append({
                "repo":     repo,
                "number":   pr["number"],
                "title":    title,
                "body_len": len(body),
                "url":      pr.get("url"),
                "merged_at": pr.get("mergedAt"),
                "audit":    a,
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
        "rule": (
            "Same 7 direction-blind v2 audit criteria + "
            "c8: ≥ 2 KG-parseable code files (KG-richness, per supervisor "
            "2026-05-12). Within each repo, pick the N most recent merged "
            "PRs that pass every criterion. Targets: 5 grafana, 3 kafka, "
            "3 sklearn, 2 godot, 2 jenkins. No LLM-judge metric is consulted."
        ),
        "targets":         {r: t for r, (_, t) in REPOS.items()},
        "candidates_by_repo": all_candidates,
        "picked":          picked,
        "n_picked":        len(picked),
    }, indent=2))

    print(f"\n==> Wrote {OUT_PATH.relative_to(REPO_ROOT)}")
    print(f"==> Picked {len(picked)} new PRs:")
    for p in picked:
        a = p["audit"]
        print(f"    {p['repo']:30s} #{p['number']:>7}   "
              f"files={a['n_code']:>2}/{a['n_files']:<3}   "
              f"~{a['diff_bytes_estimate']/1024:>5.1f}kB   "
              f"{p['title'][:60]}")


if __name__ == "__main__":
    main()
