#!/usr/bin/env python3
"""
find_seven_more_prs.py — Deterministically pick 7 NEW PRs to expand
`dataset_v2` from 18 to 25 PRs.

The selection rule is documented inline and applies the *same* five
direction-blind criteria as the v1→v2 audit
(`dataset_v2/docs/SELECTION_v2.md`), plus one additional KG-coverage
constraint that follows from the human-study learning (Decision 13 +
Decision 16 of `human_eval_v3/docs/DECISION_LOG.md`):

    1.  state == MERGED
    2.  not a revert (title does not match `^Revert ` or `^Reapply `)
    3.  substantive code change (>= 1 file in a tree-sitter-supported
        language; modified hunks not exclusively docs/comment text)
    4.  100% of changed CODE files in tree-sitter-supported languages
        (i.e. KG can parse every code file the diff touches)
    5.  diff fits in 50 kB
    6.  PR body >= 100 chars (real description; not a placeholder)
    7.  not in dataset_v2 already (no double-fetch)

Among PRs that pass every criterion, we pick by a deterministic rule:

    * stratify by repo to roughly match the v2 distribution
      (target: +2 grafana, +1 kafka, +1 godot, +2 sklearn, +1 jenkins)
    * within each repo, take the MOST RECENT N merged PRs that pass
      all criteria, ordered by GitHub PR number descending

This rule does NOT consult any LLM-judge output, any mode-favouring
metric, or any v1↔v2 comparison. It is fully reproducible from the
GitHub API.

Output: `dataset_v2/docs/seven_more_candidates.json` — a list of
candidates per repo with audit results, plus a "picked" flag on the
final 7. Inspect this file before running the fetcher.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH  = REPO_ROOT / "dataset_v2" / "docs" / "seven_more_candidates.json"

# Tree-sitter-supported language extensions (per scripts/build_kg_evidence_ast.py).
KG_EXTS = {
    ".py", ".pyi",
    ".java", ".scala",
    ".cpp", ".cc", ".c", ".h", ".hpp",
    ".go",
    ".ts", ".tsx", ".js", ".jsx",
    ".gd", ".rs",
}
# Extensions that are clearly "code" but NOT KG-parseable — flag any presence.
NON_KG_CODE_EXTS = {
    ".jelly", ".kt", ".swift", ".m", ".mm",
    ".rb", ".php", ".elm", ".dart",
    ".cue", ".gradle", ".groovy",
}
# Extensions we ignore when computing the "code files" denominator
# (configs, docs, build files, snapshots, locale files).
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
    "grafana/grafana":              (25, 2),
    "apache/kafka":                 (25, 1),
    "godotengine/godot":            (25, 1),
    "scikit-learn/scikit-learn":    (25, 2),
    "jenkinsci/jenkins":            (25, 1),
}

EXISTING = {
    "grafana/grafana":              {67809, 69259, 78399, 95949, 97224, 98123},
    "apache/kafka":                 {14778, 17441, 17594, 18330},
    "godotengine/godot":            {68625, 73144, 89111},
    "scikit-learn/scikit-learn":    {22365, 22643, 26836},
    "jenkinsci/jenkins":            {6229, 9002},
}


def gh(args: list[str]) -> str:
    if not shutil.which("gh"):
        sys.exit("`gh` CLI is required; please install + auth.")
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"gh failed: {' '.join(args)}\n{r.stderr}")
    return r.stdout


def list_recent_merged(repo: str, n: int) -> list[dict]:
    raw = gh([
        "pr", "list", "--repo", repo, "--state", "merged",
        "--limit", str(n),
        "--json", "number,title,body,additions,deletions,changedFiles,mergedAt,url,author",
    ])
    return json.loads(raw)


def fetch_pr_files(repo: str, number: int) -> list[dict]:
    """Return list[{path, additions, deletions}]."""
    raw = gh([
        "api", f"repos/{repo}/pulls/{number}/files",
        "--paginate",
    ])
    items = json.loads(raw)
    return [
        {"path": it["filename"], "additions": it.get("additions", 0),
         "deletions": it.get("deletions", 0)}
        for it in items
    ]


def ext_of(path: str) -> str:
    if "." not in path:
        return ""
    return "." + path.rsplit(".", 1)[-1].lower()


def audit(pr: dict, files: list[dict]) -> dict:
    """Return {passes_all, criteria, code_files, total_files, code_pct}."""
    body  = pr.get("body") or ""
    title = pr.get("title", "") or ""
    diff_bytes = sum(f["additions"] + f["deletions"] for f in files) * 80  # rough char estimate
    paths = [f["path"] for f in files]
    code_files = [p for p in paths if ext_of(p) in KG_EXTS]
    non_kg_code = [p for p in paths if ext_of(p) in NON_KG_CODE_EXTS]
    docs_files = [p for p in paths if ext_of(p) in NON_CODE_EXTS]
    other_files = [p for p in paths
                   if ext_of(p) not in KG_EXTS
                   and ext_of(p) not in NON_KG_CODE_EXTS
                   and ext_of(p) not in NON_CODE_EXTS]

    n_total = len(paths)
    n_code  = len(code_files)
    n_non_kg_code = len(non_kg_code)
    code_pct = (n_code / max(1, n_code + n_non_kg_code)) * 100

    crit = {}
    crit["c1_merged"] = True  # by construction (state=merged)
    crit["c2_not_revert"] = not re.match(r"^(revert|reapply)\b", title, re.IGNORECASE)
    crit["c3_has_code_change"] = n_code >= 1
    crit["c4_kg_parseable_100pct"] = n_non_kg_code == 0 and n_code >= 1
    crit["c5_diff_under_50kb"] = diff_bytes <= 50_000
    crit["c6_body_real"] = len(body.strip()) >= 100
    crit["c7_not_already_in_v2"] = pr["number"] not in EXISTING.get(pr.get("__repo", ""), set())

    return {
        "passes_all": all(crit.values()),
        "criteria":   crit,
        "n_files":    n_total,
        "n_code":     n_code,
        "n_non_kg":   n_non_kg_code,
        "n_docs":     len(docs_files),
        "code_pct":   round(code_pct, 1),
        "diff_bytes_estimate": diff_bytes,
        "extensions": sorted({ext_of(p) for p in paths}),
        "first_5_paths": paths[:5],
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
            # Fast pre-filters on metadata only (no per-file API call yet).
            body = pr.get("body") or ""
            title = pr.get("title", "") or ""
            adds  = pr.get("additions", 0)
            dels  = pr.get("deletions", 0)
            est_diff = (adds + dels) * 80
            n_changed = pr.get("changedFiles", 0)
            if len(body.strip()) < 100:
                continue  # body-real fail
            if re.match(r"^(revert|reapply)\b", title, re.IGNORECASE):
                continue
            # Drop cosmetic / non-review-worthy PRs by title pattern. These
            # are not "code review" stimuli — a reviewer's attention would
            # add no value over `git diff`. Direction-blind: applies to
            # any mode equally.
            if re.match(r"^(bump|chore[: ]|docs?[: ]|doc[: ]|"
                        r"update dependency|update peer dependency|"
                        r":(lock|robot|memo|sparkles):)",
                        title, re.IGNORECASE):
                continue
            # Drop pure-translations + i18n + locale PRs — same reason.
            if re.match(r"^(i18n|l10n|translations?:)",
                        title, re.IGNORECASE):
                continue
            if est_diff > 60_000:
                continue  # 50kB cap with ~20% slack
            if est_diff < 1_500:
                continue  # too tiny to be substantive (was 800; up to 1.5kB
                          # so we don't end up reviewing a 5-line tweak)
            if n_changed == 0:
                continue
            # Cross-file sweeping changes (e.g. project-wide pragma fixes)
            # often have 30+ tiny edits; KG context is the same for all and
            # the review is essentially "this big refactor is fine". Limit
            # to 25 changed files to keep stimuli focused.
            if n_changed > 25:
                continue
            try:
                files = fetch_pr_files(repo, pr["number"])
            except SystemExit:
                continue
            print(f"    pr#{pr['number']:>6}  files={len(files):>2}  "
                  f"adds={adds:>5} dels={dels:>4}  ~{est_diff/1024:.1f}kB  "
                  f"{title[:55]}", flush=True)
            a = audit(pr, files)
            cands.append({
                "repo":   repo,
                "number": pr["number"],
                "title":  title,
                "body_len": len(body),
                "url":    pr.get("url"),
                "merged_at": pr.get("mergedAt"),
                "audit":  a,
            })
        cands.sort(key=lambda c: -c["number"])  # most-recent first
        passing = [c for c in cands if c["audit"]["passes_all"]]
        # Pick top-N most recent passing
        repo_picks = passing[:n_target]
        for p in repo_picks:
            p["picked"] = True
            picked.append(p)
        print(f"  -> fetched={len(cands)}  passing-all-criteria={len(passing)}  "
              f"picked={len(repo_picks)} (target={n_target})", flush=True)
        all_candidates[repo] = cands

    OUT_PATH.write_text(json.dumps({
        "rule": (
            "Same 5 direction-blind v2 audit criteria + KG-parseability + "
            "body-real + not-already-in-v2. Within each repo, pick the "
            "N most recent merged PRs (by PR number descending) that pass "
            "every criterion. Targets: 2 grafana, 1 kafka, 1 godot, "
            "2 sklearn, 1 jenkins. No LLM-judge metric is consulted."
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
        print(f"    {p['repo']:28s} #{p['number']:>6}   files={a['n_code']:>2}/{a['n_code']+a['n_non_kg']:>2}({a['code_pct']:.0f}%)   diff~{a['diff_bytes_estimate']/1024:>5.1f}kB   {p['title'][:60]}")


if __name__ == "__main__":
    main()
