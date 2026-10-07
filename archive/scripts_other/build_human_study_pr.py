#!/usr/bin/env python3
"""
build_human_study_pr.py — End-to-end builder for ONE new human-study PR
(baseline_strict vs joern), for the Option-B out-of-dataset RQ3 set.

Chains the existing, verified pieces (nothing reinvented):
  1. base evidence pack  <- dataset_v2/scripts/fetch_evidence_v2.build_evidence()
  2. Joern CPG + export + call-graph + enriched evidence
                          <- experiments/.../run_experiment.py {generate_cpg,
                             export_cpg, extract_call_graph, build_evidence}
  3. joern review (gpt-4o, strict prompt + KG context)
                          <- experiments/.../exp_gpt4o_joern.STRICT_SYSTEM_PROMPT
  4. baseline_strict review (gpt-4o, strict prompt, NO KG)
                          <- experiments/human_study_reviews/generate_baseline_strict
  5. judge both arms with the human-study panel
                          <- scripts/evaluate_reviews.evaluate_single_review

Every step is idempotent (skips if its output already exists). No new PR is
added to the 40-PR RQ2 dataset; these ids live above 49 and feed only the
human study.

Usage:
  source load_env.sh && python3 scripts/build_human_study_pr.py \
      --repo scikit-learn/scikit-learn --pr 32846 --id 50 \
      --local-repo scikit-learn_scikit-learn --language python \
      --parse-paths sklearn/utils sklearn/linear_model sklearn/metrics \
                    sklearn/decomposition sklearn/mixture
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "dataset_v2" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "2026-05-15_joern_kg_main"))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "human_study_reviews"))

BASE_EV_DIR = REPO_ROOT / "data" / "luca_prs_v2"
JOERN_EXP = REPO_ROOT / "experiments" / "2026-05-15_joern_kg_main"
JOERN_REVIEW_DIR = JOERN_EXP / "exp_gpt4o_joern"
HS_DIR = REPO_ROOT / "experiments" / "human_study_reviews"

GEN_MODEL = "gpt-4o"
JUDGE_PANEL = ["gemini:gemini-2.5-flash", "gemini:gemini-2.5-pro"]  # == judge_human_study_pairs.py


def step1_base_evidence(repo: str, pr: int, pr_id: int, local_repo: str, language: str) -> Path:
    out = BASE_EV_DIR / f"pr{pr_id}_evidence.json"
    if out.exists():
        print(f"[1] base evidence cached: {out.name}")
        return out
    import fetch_evidence_v2 as fe
    ev = fe.build_evidence(pr_id, repo, pr, local_repo, language)
    out.write_text(json.dumps(ev, indent=2))
    print(f"[1] wrote base evidence: {out.name}")
    return out


def _build_cpg(rx, pr_id: int, local_repo: str, parse_paths: list[str], language: str,
               timeout: int) -> None:
    """joern-parse a SINGLE input dir (joern 4.x takes one [input]).

    If several parse_paths are given we parse their common parent so all of
    them land in one CPG (needed to see cross-subpackage callers).
    """
    import subprocess
    cpg_file = rx.CPG_DIR / f"pr{pr_id}.bin"
    if cpg_file.exists():
        print(f"[2] CPG cached: {cpg_file.name}")
        return
    repo_dir = rx.LUCA_REPOS / local_repo
    abs_paths = [repo_dir / p for p in parse_paths]
    for p in abs_paths:
        if not p.exists():
            raise RuntimeError(f"parse path missing: {p}")
    if len(abs_paths) == 1:
        input_path = abs_paths[0]
    else:
        import os
        input_path = Path(os.path.commonpath([str(p) for p in abs_paths]))
    cmd = ["joern-parse", str(input_path), "--language", language,
           "--output", str(cpg_file)]
    print(f"[2] joern-parse {input_path.relative_to(repo_dir)} "
          f"(lang={language}, timeout={timeout}s)...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not cpg_file.exists():
        raise RuntimeError(f"joern-parse failed: {r.stderr[-800:]}")
    print(f"[2] CPG built ({cpg_file.stat().st_size/1e6:.1f} MB)")


def step2_joern_evidence(pr_id: int, local_repo: str, parse_paths: list[str],
                         language: str, cpg_timeout: int) -> Path:
    out = JOERN_EXP / "evidence" / f"pr{pr_id}_evidence.json"
    if out.exists():
        print(f"[2] joern evidence cached: {out.name}")
        return out
    import run_experiment as rx
    rx.PR_META[pr_id] = {"repo": local_repo, "lang": language, "parse_paths": parse_paths}
    for d in (rx.CPG_DIR, rx.EXPORT_DIR, rx.EVIDENCE_DIR, rx.CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)
    progress = {"steps_completed": {}, "errors": []}
    _build_cpg(rx, pr_id, local_repo, parse_paths, language, cpg_timeout)
    rx.mark_done(progress, f"cpg_pr{pr_id}")
    if not rx.export_cpg(pr_id, progress):
        raise RuntimeError(f"CPG export failed: {progress['errors']}")
    if not rx.extract_call_graph(pr_id, progress):
        raise RuntimeError(f"call-graph extract failed: {progress['errors']}")
    if not rx.build_evidence(pr_id, progress):
        raise RuntimeError(f"evidence enrich failed: {progress['errors']}")
    print(f"[2] wrote joern evidence: {out.name}")
    return out


def step3_joern_review(pr_id: int) -> Path:
    out = JOERN_REVIEW_DIR / f"pr{pr_id}_review.md"
    if out.exists():
        print(f"[3] joern review cached: {out.name}")
        return out
    from prnote.llm import generate_completion
    from prnote.note import format_kg_context, get_diff_from_evidence
    import exp_gpt4o_joern as ej
    ev = json.loads((JOERN_EXP / "evidence" / f"pr{pr_id}_evidence.json").read_text())
    diff = get_diff_from_evidence(ev, max_chars=50000)
    pr_title = ev.get("pr", {}).get("title", f"PR {pr_id}")
    pr_body = ev.get("pr", {}).get("body", "")[:500]
    context = format_kg_context(ev)
    user_prompt = (f"## Pull Request: {pr_title}\n\n## Description\n{pr_body}\n\n"
                   f"## Diff\n```\n{diff}\n```\n\n{context}\n\n"
                   "Generate your review note following the required format. You MUST "
                   "cover all 9 mandatory points. Reference specific callers, test files, "
                   "and function signatures from the structural context above.")
    print("[3] generating joern review (gpt-4o)...")
    review = generate_completion(prompt=user_prompt, system=ej.STRICT_SYSTEM_PROMPT,
                                 model=GEN_MODEL, temperature=0.0)
    JOERN_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(review)
    print(f"[3] wrote joern review: {out.name}")
    return out


def step4_baseline_strict(pr_id: int) -> Path:
    out = HS_DIR / f"pr{pr_id}_baseline_strict.md"
    if out.exists():
        print(f"[4] baseline_strict cached: {out.name}")
        return out
    import generate_baseline_strict as gbs
    print("[4] generating baseline_strict review (gpt-4o)...")
    gbs.generate_baseline_strict(pr_id)  # reads BASE_EV_DIR, writes HS_DIR
    print(f"[4] wrote baseline_strict: {out.name}")
    return out


def step5_judge(pr_id: int) -> dict:
    from evaluate_reviews import evaluate_single_review
    results = {}
    for mode, path in (("baseline_strict", HS_DIR / f"pr{pr_id}_baseline_strict.md"),
                       ("joern", JOERN_REVIEW_DIR / f"pr{pr_id}_review.md")):
        eval_path = HS_DIR / f"pr{pr_id}_{mode}_eval.json"
        if eval_path.exists():
            results[mode] = json.loads(eval_path.read_text())
            print(f"[5] {mode} eval cached")
            continue
        print(f"[5] judging {mode} with {JUDGE_PANEL}...")
        r = asdict(evaluate_single_review(path, pr_id, mode, JUDGE_PANEL))
        eval_path.write_text(json.dumps(r, indent=2))
        results[mode] = r
    b, j = results["baseline_strict"], results["joern"]
    print(f"\n== PR{pr_id} RESULT ==")
    print(f"  total    bl={b['total_score']} joern={j['total_score']} "
          f"(Δ={j['total_score']-b['total_score']:+d})")
    print(f"  kg-rel   bl={b['kg_relevant_score']} joern={j['kg_relevant_score']} "
          f"(Δ={j['kg_relevant_score']-b['kg_relevant_score']:+d})")
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--id", type=int, required=True)
    ap.add_argument("--local-repo", required=True)
    ap.add_argument("--language", default="python", help="evidence-pack language tag")
    ap.add_argument("--joern-language", default=None,
                    help="joern-parse --language value (default: derive from --language)")
    ap.add_argument("--parse-paths", nargs="+", required=True)
    ap.add_argument("--cpg-timeout", type=int, default=1800)
    ap.add_argument("--skip-judge", action="store_true")
    a = ap.parse_args()

    joern_lang = a.joern_language or {
        "python": "PYTHONSRC", "java": "JAVASRC", "typescript": "JSSRC",
        "javascript": "JSSRC", "go": "GOLANG", "cpp": "NEWC", "c": "NEWC",
    }.get(a.language.split(",")[0].strip(), a.language)

    step1_base_evidence(a.repo, a.pr, a.id, a.local_repo, a.language)
    step2_joern_evidence(a.id, a.local_repo, a.parse_paths, joern_lang, a.cpg_timeout)
    step3_joern_review(a.id)
    step4_baseline_strict(a.id)
    if not a.skip_judge:
        step5_judge(a.id)
    print(f"\nDONE PR{a.id} ({a.repo}#{a.pr})")


if __name__ == "__main__":
    main()
