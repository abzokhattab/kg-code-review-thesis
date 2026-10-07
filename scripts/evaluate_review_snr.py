#!/usr/bin/env python3
"""evaluate_review_snr.py — signal-to-noise / precision evaluation of reviews.

Motivation: the 25-criterion checklist is a *coverage* metric. The 2025/2026
code-review literature (CR-Bench arXiv:2603.11078; CRScore NAACL 2025;
DeepCRCEval 2025; Uber uReview; Cloudflare) shows coverage is the wrong target —
what predicts developer trust is signal-to-noise (precision / actionability):
more comments => more noise => fatigue. This evaluator scores reviews on that
axis instead of breadth.

For each review, a judge extracts the distinct points it raises and labels each:
  * useful   — a specific, correct, actionable issue/recommendation grounded in the diff
  * generic  — true but vague/boilerplate ("add tests", "consider error handling") with no specificity
  * wrong    — incorrect, unsupported, or hallucinated relative to the diff

Per review we compute:
  signal = #useful
  noise  = #generic + #wrong
  total  = signal + noise
  snr    = signal / total           (precision / actionability)

Threaded; cached per (tag, pr, mode). No checklist; complements evaluate_reviews.

Usage:
  python3 scripts/evaluate_review_snr.py --reviews outputs/luca_prs_v2          --tag verbose --workers 8
  python3 scripts/evaluate_review_snr.py --reviews outputs/luca_prs_v2_concise  --tag concise --workers 8
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
ENV = REPO / ".env"
import os
if ENV.exists():
    for line in ENV.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from prnote.llm import generate_completion  # noqa: E402
from prnote.note import get_diff_from_evidence  # noqa: E402

SYSTEM = """You are auditing a code-review note for SIGNAL vs NOISE, the way a busy senior engineer would.

You are given a PR diff and a review note. Extract the DISTINCT CONCERNS the review raises.

CRITICAL deduplication rule: review notes typically restate the SAME concern across multiple
sections (Problem, Impact, Recommendation, Evidence). Count each underlying concern EXACTLY ONCE,
no matter how many sections mention it. Example: "missing tests" in Problem + "insufficient test
coverage" in Impact + "add tests" in Recommendation = ONE concern, not three. Do not reward a
review for repeating itself.

For each distinct concern assign exactly one label:
- "useful": specific, correct, and actionable; grounded in the actual diff; a senior engineer would act on it.
- "generic": plausibly true but vague/boilerplate with no specificity to THIS diff (e.g. "add tests", "consider error handling", "update documentation") — low value.
- "wrong": incorrect, unsupported by the diff, speculative, or hallucinated.

Be strict: reward precision, penalize padding. Output STRICT JSON only:
{"points":[{"text":"<short paraphrase>","label":"useful|generic|wrong"}]}"""

JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def judge(review: str, diff: str, model: str) -> dict:
    prompt = (f"## PR Diff\n```\n{diff[:20000]}\n```\n\n## Review Note\n{review}\n\n"
              "Audit the review. Output the strict JSON object.")
    raw = generate_completion(prompt=prompt, system=SYSTEM, model=model, temperature=0.0)
    m = JSON_RE.search(raw)
    points = []
    if m:
        try:
            points = json.loads(m.group()).get("points", [])
        except Exception:
            points = []
    labels = [str(p.get("label", "")).lower() for p in points]
    useful = sum(1 for l in labels if l == "useful")
    generic = sum(1 for l in labels if l == "generic")
    wrong = sum(1 for l in labels if l == "wrong")
    total = useful + generic + wrong
    return {
        "useful": useful, "generic": generic, "wrong": wrong, "total": total,
        "signal": useful, "noise": generic + wrong,
        "snr": round(useful / total, 3) if total else 0.0,
        "points": points, "parse_ok": bool(points),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reviews", required=True)
    ap.add_argument("--tag", required=True, help="verbose|concise (cache namespace)")
    ap.add_argument("--model", default="openai:gpt-4o")
    ap.add_argument("--evidence", default="data/luca_prs_v2")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    cache_dir = REPO / "results" / "snr_cache" / args.tag / args.model.replace(":", "-")
    cache_dir.mkdir(parents=True, exist_ok=True)
    ev_dir = REPO / args.evidence

    diff_cache: dict[int, str] = {}

    def get_diff(pr_id: int) -> str:
        if pr_id not in diff_cache:
            ev = json.loads((ev_dir / f"pr{pr_id}_evidence.json").read_text())
            diff_cache[pr_id] = get_diff_from_evidence(ev, max_chars=50000)
        return diff_cache[pr_id]

    todo = []
    cached = 0
    for f in sorted(glob.glob(f"{REPO/args.reviews}/pr*_*.md")):
        m = re.match(r"pr(\d+)_(\w+)\.md", Path(f).name)
        if not m:
            continue
        pr_id, mode = int(m.group(1)), m.group(2)
        cp = cache_dir / f"pr{pr_id}_{mode}.json"
        if cp.exists():
            cached += 1
            continue
        todo.append((Path(f), pr_id, mode, cp))

    print(f"tag={args.tag} model={args.model} reviews={cached+len(todo)} cached={cached} todo={len(todo)}")

    def work(item):
        f, pr_id, mode, cp = item
        res = judge(f.read_text(), get_diff(pr_id), args.model)
        res.update({"pr_id": pr_id, "mode": mode, "tag": args.tag})
        cp.write_text(json.dumps(res, indent=2))
        return res

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, it): it for it in todo}
        for fut in as_completed(futs):
            try:
                r = fut.result(); done += 1
                print(f"[{done+cached:>3}] PR#{r['pr_id']:<3} {r['mode']:<9} "
                      f"signal={r['signal']} noise={r['noise']} snr={r['snr']}"
                      f"{'' if r['parse_ok'] else '  PARSE_FAIL'}", flush=True)
            except Exception as e:  # noqa: BLE001
                it = futs[fut]; print(f"  ERR pr{it[1]} {it[2]}: {e}", flush=True)

    print(f"done. cache: {cache_dir.relative_to(REPO)}")


if __name__ == "__main__":
    main()
