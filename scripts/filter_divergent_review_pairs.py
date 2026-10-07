"""
filter_divergent_review_pairs.py

Divergence filter for baseline vs KG review pairs.

For each PR, checks whether the two generated reviews address the same
concerns or have diverged into unrelated topics. A pair is flagged as
divergent when:
  - The changed files cited in both reviews have low overlap, OR
  - The key technical terms (class/function/variable names) are almost
    entirely non-overlapping

Outputs a per-PR verdict table and a summary. Any flagged PR should be
manually inspected before being included in the judge scoring.

Usage:
    python scripts/filter_divergent_review_pairs.py
    python scripts/filter_divergent_review_pairs.py --modes baseline kg
    python scripts/filter_divergent_review_pairs.py --threshold 0.15
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


REVIEW_DIR = Path("outputs/luca_prs_v2")
EVIDENCE_DIR = Path("data/luca_prs_v2")

PR_IDS = [1,2,3,6,8,9,10,12,13,14,15,18,19,20,21,22,23,24,
          27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48]

# ── helpers ──────────────────────────────────────────────────────────────────

def load_review(pr_id: int, mode: str) -> str:
    path = REVIEW_DIR / f"pr{pr_id}_{mode}.md"
    if not path.exists():
        return ""
    return path.read_text()


def extract_cited_files(text: str) -> set:
    """File paths mentioned in the review (e.g. foo/bar.py:123)."""
    return set(re.findall(r'[\w/\-]+\.\w{1,6}(?::\d+)?', text))


def extract_technical_terms(text: str) -> set:
    """
    CamelCase identifiers, snake_case identifiers longer than 4 chars,
    and backtick-quoted tokens — the vocabulary of what the review is
    actually talking about.
    """
    camel = set(re.findall(r'\b[A-Z][a-zA-Z0-9]{3,}\b', text))
    snake = set(t for t in re.findall(r'\b[a-z][a-z0-9_]{4,}\b', text)
                if '_' in t)
    ticked = set(re.findall(r'`([^`]{3,})`', text))
    return camel | snake | ticked


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0  # both empty → vacuously the same
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def get_pr_changed_files(pr_id: int) -> set:
    """Ground-truth file list from the evidence pack."""
    path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
    if not path.exists():
        return set()
    ev = json.loads(path.read_text())
    files = ev.get("changed_files", [])
    # changed_files is a list of dicts with a 'filename' key
    return set(
        os.path.basename(f.get("filename") or f.get("path", "")) if isinstance(f, dict) else os.path.basename(f)
        for f in files
    )


# ── main divergence check ────────────────────────────────────────────────────

def check_pair(pr_id: int, mode_a: str, mode_b: str,
               file_threshold: float, term_threshold: float):
    """
    Returns a dict with divergence metrics for one PR pair.
    A pair is FLAGGED when BOTH file_jaccard AND term_jaccard are below
    their respective thresholds — requiring both signals to be low
    reduces false positives.
    """
    text_a = load_review(pr_id, mode_a)
    text_b = load_review(pr_id, mode_b)

    if not text_a or not text_b:
        return {
            "pr_id": pr_id,
            "status": "MISSING",
            "file_jaccard": None,
            "term_jaccard": None,
            "flagged": True,
            "note": f"Missing review file for mode '{mode_a if not text_a else mode_b}'",
        }

    files_a = extract_cited_files(text_a)
    files_b = extract_cited_files(text_b)
    terms_a = extract_technical_terms(text_a)
    terms_b = extract_technical_terms(text_b)

    # Also factor in ground-truth changed files — if both cite at least
    # one real changed file, they're clearly reviewing the same diff.
    gt_files = get_pr_changed_files(pr_id)
    a_cites_gt = bool(files_a & gt_files)
    b_cites_gt = bool(files_b & gt_files)

    fj = jaccard(files_a, files_b)
    tj = jaccard(terms_a, terms_b)

    # Flagging logic: both metrics low AND neither arm cites a real changed file
    flagged = (fj < file_threshold and tj < term_threshold
               and not (a_cites_gt and b_cites_gt))

    note = ""
    if not a_cites_gt:
        note += f"{mode_a} cites no ground-truth changed files. "
    if not b_cites_gt:
        note += f"{mode_b} cites no ground-truth changed files. "

    return {
        "pr_id": pr_id,
        "status": "FLAGGED" if flagged else "OK",
        "file_jaccard": round(fj, 3),
        "term_jaccard": round(tj, 3),
        "a_cites_gt": a_cites_gt,
        "b_cites_gt": b_cites_gt,
        "flagged": flagged,
        "note": note.strip(),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modes", nargs=2, default=["baseline", "kg"],
                        metavar=("MODE_A", "MODE_B"),
                        help="Two review modes to compare (default: baseline kg)")
    parser.add_argument("--threshold", type=float, default=0.15,
                        help="Jaccard threshold below which a signal is 'low' (default 0.15)")
    parser.add_argument("--pr-ids", nargs="+", type=int, default=None,
                        help="Restrict to specific PR ids")
    parser.add_argument("--json", dest="json_out", action="store_true",
                        help="Also write results to results/divergence_filter.json")
    args = parser.parse_args()

    mode_a, mode_b = args.modes
    pr_ids = args.pr_ids or PR_IDS
    ft = args.threshold
    tt = args.threshold

    print(f"Divergence filter: {mode_a} vs {mode_b}  |  threshold={ft}")
    print(f"{'PR':<6} {'File-J':<10} {'Term-J':<10} {'A→GT':<7} {'B→GT':<7} {'Status':<10} Note")
    print("-" * 80)

    results = []
    flagged_prs = []

    for pr_id in sorted(pr_ids):
        r = check_pair(pr_id, mode_a, mode_b, ft, tt)
        results.append(r)
        status = r["status"]
        fj = f"{r['file_jaccard']:.3f}" if r["file_jaccard"] is not None else "N/A"
        tj = f"{r['term_jaccard']:.3f}" if r["term_jaccard"] is not None else "N/A"
        agt = "yes" if r.get("a_cites_gt") else "no"
        bgt = "yes" if r.get("b_cites_gt") else "no"
        flag_marker = "⚠️ " if r["flagged"] else "   "
        print(f"PR{pr_id:<4} {fj:<10} {tj:<10} {agt:<7} {bgt:<7} {flag_marker}{status:<8} {r['note']}")
        if r["flagged"]:
            flagged_prs.append(pr_id)

    total = len(results)
    n_ok = sum(1 for r in results if r["status"] == "OK")
    n_flagged = len(flagged_prs)
    n_missing = sum(1 for r in results if r["status"] == "MISSING")

    print("\n" + "=" * 80)
    print(f"SUMMARY  |  n={total}  OK={n_ok}  flagged={n_flagged}  missing={n_missing}")
    if flagged_prs:
        print(f"Flagged PRs: {flagged_prs}")
        print("Action: manually inspect flagged pairs before including in scoring.")
    else:
        print("All pairs pass the divergence filter. No PRs need to be excluded.")

    if args.json_out:
        out_path = Path("results/divergence_filter.json")
        out_path.parent.mkdir(exist_ok=True)
        out_path.write_text(json.dumps({
            "modes": [mode_a, mode_b],
            "threshold": ft,
            "results": results,
            "flagged_prs": flagged_prs,
            "summary": {"total": total, "ok": n_ok,
                        "flagged": n_flagged, "missing": n_missing}
        }, indent=2))
        print(f"\nResults written to {out_path}")

    sys.exit(1 if flagged_prs else 0)


if __name__ == "__main__":
    main()
