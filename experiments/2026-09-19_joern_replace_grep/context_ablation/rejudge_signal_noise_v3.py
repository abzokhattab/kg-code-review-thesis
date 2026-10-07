#!/usr/bin/env python3
"""Rejudge signal-vs-noise ablation with the corrected v3 procedure.

Applies the same two-step adjudication as the main Exp2 correction:
  1. Deterministic exact filename/basename match against true dependents
  2. LLM judges only causal linkage when a match is found

Only rejudges the two NEW arms (noise_matched, relevant_only).
For baseline/kg_deployed/kg_idealised, the corrected results are
imported from the main Exp2 v3 correction.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path("/Users/akhattab/ai")
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "experiments" / "2026-07-05_injection_exp2" / "harness"))

ENV_PATH = REPO_ROOT / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from common import load_manifest  # noqa: E402
from prnote.llm import generate_completion  # noqa: E402

HERE = Path(__file__).resolve().parent
REVIEWS_DIR = HERE / "reviews_signal"
JUDGMENTS_DIR = HERE / "judgments_signal_v3"
RESULTS_MD = HERE / "RESULTS_SIGNAL_NOISE_V3.md"

JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
NEW_ARMS = ["noise_matched", "relevant_only"]
PROMPT_VERSION = "exp2-adjudication-v3"
PRINT_LOCK = threading.Lock()

STRUCTURAL_SYSTEM = """You adjudicate one binary code-review detection criterion.

A deterministic prefilter established that every CANDIDATE_MENTION is an exact
full-path or exact-basename mention of a manifest-listed true dependent. Path
identity is a fact. Do not re-evaluate it or require every dependent.

TASK: Decide whether the review links at least one matched file or usage to the
injected change as broken, requiring an update, or otherwise causally affected.

Rules:
- One matched file causally linked is enough for detected=true.
- Hedging words ("may", "potential") do NOT invalidate a specific causal warning.
- A generic statement ("make sure callers are updated") with no specific file is NOT detection.
- If the review mentions the file but does NOT link it to the injected change, that is NOT detection.

Output strict JSON only, no prose wrapping:
{
  "schema_version": "exp2-adjudication-v3",
  "detected": true|false,
  "evidence_id": "M001"|null,
  "finding_passage_id": "P004"|null,
  "causal_passage_id": "P007"|null,
  "reason_code": "specific_cross_file_link"|"mention_only"|"generic_risk_only"|"wrong_defect"|"no_supporting_review_text"
}

If detected=true: evidence_id must be one supplied M-id; reason_code must be "specific_cross_file_link".
If detected=false: evidence_id, finding_passage_id, causal_passage_id must be null.
"""


def safe_model(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def true_file_mentions(injection: dict[str, Any], review: str) -> list[dict[str, Any]]:
    basename_counts: dict[str, int] = {}
    for raw_path in injection["true_dependents"]:
        basename_counts[Path(raw_path).name] = (
            basename_counts.get(Path(raw_path).name, 0) + 1
        )
    matches = []
    for index, raw_path in enumerate(injection["true_dependents"], 1):
        path = Path(raw_path)
        full_path = str(path)
        start = review.find(full_path)
        match_kind = "full_path"
        match_text = full_path
        if start < 0:
            basename_match = re.search(
                rf"(?<![A-Za-z0-9_]){re.escape(path.name)}(?![A-Za-z0-9_])",
                review,
            )
            if basename_match is None:
                continue
            start = basename_match.start()
            match_kind = "basename"
            match_text = basename_match.group(0)
        end = start + len(match_text)
        excerpt = review[max(0, start - 160): min(len(review), end + 260)]
        matches.append({
            "evidence_id": f"M{index:03d}",
            "oracle_path": full_path,
            "match_kind": match_kind,
            "match_text": match_text,
            "start": start,
            "end": end,
            "excerpt": excerpt,
            "basename_collision": basename_counts[path.name] > 1,
        })
    return matches


def review_passages(review: str) -> list[dict[str, Any]]:
    passages = []
    offset = 0
    for raw_line in review.splitlines(keepends=True):
        line = raw_line.strip()
        start = offset + (len(raw_line) - len(raw_line.lstrip()))
        end = start + len(line)
        offset += len(raw_line)
        if not line or line == "```":
            continue
        passages.append({
            "passage_id": f"P{len(passages) + 1:03d}",
            "text": line,
            "start": start,
            "end": end,
        })
    return passages


def attach_passages(
    matches: list[dict[str, Any]], passages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    output = []
    for match in matches:
        containing = [
            p["passage_id"]
            for p in passages
            if p["start"] <= match["start"] < p["end"]
        ]
        if not containing:
            containing = [
                p["passage_id"]
                for p in passages
                if abs(p["start"] - match["start"]) < 5
                or (p["start"] <= match["start"] and match["end"] <= p["end"] + 5)
            ]
        if not containing:
            containing = ["P_UNRESOLVED"]
        output.append({**match, "finding_passage_id": containing[0]})
    return output


def structural_prompt(
    injection: dict[str, Any],
    matches: list[dict[str, Any]],
    passages: list[dict[str, Any]],
) -> str:
    injection_payload = {
        key: injection[key]
        for key in ("id", "band", "edit_file", "old", "new", "operator")
    }
    return (
        "INJECTION_JSON\n"
        f"{json.dumps(injection_payload, sort_keys=True)}\n\n"
        "CANDIDATE_MENTIONS_JSON\n"
        f"{json.dumps(matches, sort_keys=True)}\n\n"
        "REVIEW_PASSAGES_JSON\n"
        f"{json.dumps(passages, sort_keys=True)}\n\n"
        "Required schema keys: schema_version, detected, evidence_id, "
        "finding_passage_id, causal_passage_id, reason_code.\n"
        f"schema_version must be {PROMPT_VERSION!r}.\n"
        "If true: evidence_id must be one supplied M-id and reason_code must be "
        "'specific_cross_file_link'.\n"
        "If false: evidence_id/finding_passage_id/causal_passage_id must be null and "
        "reason_code must be one of mention_only, generic_risk_only, "
        "wrong_defect, no_supporting_review_text."
    )


SCHEMA_KEYS = {
    "schema_version", "detected", "evidence_id",
    "finding_passage_id", "causal_passage_id", "reason_code",
}
VALID_FALSE_REASONS = {
    "mention_only", "generic_risk_only", "wrong_defect", "no_supporting_review_text",
}


def validate_verdict(raw: str) -> dict[str, Any] | None:
    txt = raw.strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```\w*\s*", "", txt)
        txt = re.sub(r"\s*```\s*$", "", txt)
    start, end = txt.find("{"), txt.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(txt[start:end])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if set(data.keys()) != SCHEMA_KEYS:
        return None
    if data.get("schema_version") != PROMPT_VERSION:
        return None
    if not isinstance(data.get("detected"), bool):
        return None
    if data["detected"]:
        if data.get("reason_code") != "specific_cross_file_link":
            return None
        if not data.get("evidence_id", "").startswith("M"):
            return None
    else:
        if data.get("reason_code") not in VALID_FALSE_REASONS:
            return None
        for k in ("evidence_id", "finding_passage_id", "causal_passage_id"):
            if data.get(k) is not None:
                return None
    return data


def judge_one(inj: dict, arm: str, judge_model: str) -> dict | None:
    jm_safe = safe_model(judge_model)
    out_j = JUDGMENTS_DIR / inj["id"] / f"{arm}__{jm_safe}.json"
    if out_j.exists():
        try:
            d = json.loads(out_j.read_text())
            if d.get("detected") is not None:
                return d
        except Exception:
            pass
    out_j.parent.mkdir(parents=True, exist_ok=True)

    review_md = REVIEWS_DIR / inj["id"] / f"{arm}.md"
    if not review_md.exists():
        return None
    review_text = review_md.read_text()
    if review_text.startswith("ERROR"):
        result = {"detected": False, "reason_code": "error", "judge": judge_model,
                  "deterministic": True}
        out_j.write_text(json.dumps(result, indent=2))
        return result

    # Stage 1: deterministic filename matching
    matches = true_file_mentions(inj, review_text)
    if not matches:
        result = {"detected": False, "reason_code": "no_filename_match",
                  "judge": judge_model, "deterministic": True,
                  "schema_version": PROMPT_VERSION}
        out_j.write_text(json.dumps(result, indent=2))
        return result

    # Stage 2: LLM causal adjudication
    passages = review_passages(review_text)
    enriched = attach_passages(matches, passages)
    prompt = structural_prompt(inj, enriched, passages)

    delay = 2.0
    for attempt in range(6):
        try:
            raw = generate_completion(
                prompt=prompt, system=STRUCTURAL_SYSTEM,
                model=judge_model, temperature=0.0)
            verdict = validate_verdict(raw)
            if verdict is None:
                if attempt < 5:
                    time.sleep(delay * (2 ** attempt))
                    continue
                result = {"detected": False, "reason_code": "validation_failed",
                          "judge": judge_model, "raw": raw[:500]}
                out_j.write_text(json.dumps(result, indent=2))
                return result
            result = {**verdict, "judge": judge_model, "deterministic": False}
            out_j.write_text(json.dumps(result, indent=2))
            return result
        except Exception as e:
            if attempt == 5:
                result = {"detected": False, "reason_code": f"error: {str(e)[:150]}",
                          "judge": judge_model}
                out_j.write_text(json.dumps(result, indent=2))
                return result
            time.sleep(min(delay * (2 ** attempt) * (1 + random.random() * 0.3), 90))
    return None


def majority_detected(inj_id: str, arm: str) -> bool:
    votes = 0
    for jm in JUDGES:
        jm_safe = safe_model(jm)
        jf = JUDGMENTS_DIR / inj_id / f"{arm}__{jm_safe}.json"
        if jf.exists():
            d = json.loads(jf.read_text())
            if d.get("detected"):
                votes += 1
    return votes >= 2


def main():
    JUDGMENTS_DIR.mkdir(parents=True, exist_ok=True)

    inj_all = load_manifest()
    structural = [i for i in inj_all if i["band"].startswith("S")]

    # Stage 1: deterministic pre-check
    print("=== Signal-vs-noise v3 rejudge ===")
    print(f"Injections: {len(structural)}")
    print(f"Arms: {NEW_ARMS}")
    print(f"Judges: {JUDGES}")
    print()

    det_skips = 0
    for inj in structural:
        for arm in NEW_ARMS:
            review_md = REVIEWS_DIR / inj["id"] / f"{arm}.md"
            if not review_md.exists():
                continue
            review = review_md.read_text()
            matches = true_file_mentions(inj, review)
            if not matches:
                det_skips += 1
    print(f"Deterministic false (no filename match): {det_skips} cells → no API call")
    api_cells = len(structural) * len(NEW_ARMS) * len(JUDGES) - det_skips * len(JUDGES)
    est_cost = api_cells * 0.003
    print(f"Estimated API calls: ~{api_cells}")
    print(f"Estimated cost: ~${est_cost:.2f}")
    print()

    # Stage 2: judge
    judge_tasks = []
    for arm in NEW_ARMS:
        for inj in structural:
            for jm in JUDGES:
                jm_safe = safe_model(jm)
                out_j = JUDGMENTS_DIR / inj["id"] / f"{arm}__{jm_safe}.json"
                if out_j.exists():
                    try:
                        if json.loads(out_j.read_text()).get("detected") is not None:
                            continue
                    except Exception:
                        pass
                judge_tasks.append((inj, arm, jm))

    if not judge_tasks:
        print("[judge] All cached")
    else:
        print(f"[judge] {len(judge_tasks)} calls to make...", flush=True)
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(judge_one, inj, arm, jm): (inj["id"], arm, jm)
                    for inj, arm, jm in judge_tasks}
            done = 0
            for fut in as_completed(futs):
                done += 1
                r = fut.result()
                det_str = "det" if r and r.get("detected") else ("skip" if r and r.get("deterministic") else "no")
                if done % 10 == 0 or done == len(judge_tasks):
                    with PRINT_LOCK:
                        cid, arm, jm = futs[fut]
                        print(f"  [{done}/{len(judge_tasks)}] {cid}/{arm}/{jm.split(':')[1]}: {det_str}", flush=True)

    # Import corrected results for baseline/kg/idealised from main v3
    v3_results = json.loads(
        (REPO_ROOT / "experiments/2026-09-19_exp2_rejudge_v2/RESULTS_V3.json").read_text()
    )
    v3_corrected = {}
    for flip in v3_results.get("flips", []):
        if flip["cohort"] != "structural":
            continue
        key = (flip["case_id"], flip["arm"])
        v3_corrected[key] = flip["corrected"]

    # Build complete v3 results for all 5 arms
    ARMS = ["baseline", "noise_matched", "kg_deployed", "relevant_only", "kg_idealised"]
    arm_map = {"baseline": "baseline", "kg_deployed": "kg", "kg_idealised": "kg_idealised"}

    print()
    print("=" * 60)
    print("RESULTS: Signal vs noise (v3 corrected adjudication)")
    print("=" * 60)
    print(f"{'Arm':>20} {'Detected':>10} {'Rate':>8}")
    print("-" * 45)

    results = {}
    for arm in ARMS:
        detected = 0
        for inj in structural:
            if arm in NEW_ARMS:
                d = majority_detected(inj["id"], arm)
            else:
                orig_arm = arm_map[arm]
                orig_key = (inj["id"], orig_arm)
                if orig_key in v3_corrected:
                    d = v3_corrected[orig_key]
                else:
                    # Use original result (unchanged by correction)
                    orig_results = json.loads(
                        (REPO_ROOT / "experiments/2026-07-05_injection_exp2/out/results.json").read_text()
                    )
                    orig_det = orig_results["detection"].get(f"structural:{orig_arm}", {}).get("detected", 0)
                    # Check per-injection from original judgments
                    from common import load_json
                    orig_j_dir = REPO_ROOT / "experiments/2026-07-05_injection_exp2/out/judgments" / inj["id"]
                    votes = 0
                    for jm in JUDGES:
                        jm_safe = safe_model(jm)
                        jf = orig_j_dir / f"{orig_arm}__{jm_safe}.json"
                        if jf.exists():
                            jd = json.loads(jf.read_text())
                            if jd.get("detected"):
                                votes += 1
                    d = votes >= 2
            if d:
                detected += 1
        rate = detected / len(structural)
        results[arm] = {"detected": detected, "n": len(structural), "rate": rate}
        print(f"{arm:>20} {detected:>6}/{len(structural)}   {rate:.1%}")

    # Write results
    lines = [
        "# Signal vs. Noise Ablation Results (v3 corrected adjudication)",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        "**Adjudication:** corrected v3 (deterministic filename match + LLM causal assessment)",
        "**Generator:** gpt-4o (T=0.0)",
        "**Judges:** gpt-4o-mini + gpt-4o + gemini-2.5-flash (3-judge majority)",
        f"**n:** {len(structural)} structural injections",
        "",
        "## Results",
        "",
        "| Arm | What the LLM sees | Detected | Rate |",
        "|---|---|---|---|",
    ]
    arm_desc = {
        "baseline": "diff only",
        "noise_matched": "diff + same-count WRONG edges",
        "kg_deployed": "diff + Joern edges + grep deps (as built)",
        "relevant_only": "diff + only edges hitting true dependents",
        "kg_idealised": "diff + ground-truth resolver",
    }
    for arm in ARMS:
        r = results[arm]
        lines.append(f"| {arm} | {arm_desc[arm]} | {r['detected']}/{r['n']} | {r['rate']:.1%} |")

    lines.extend(["", "## Comparison with original adjudication", ""])

    # Load original results
    orig_results_data = {}
    for arm in ARMS:
        if arm in NEW_ARMS:
            detected = 0
            for inj in structural:
                orig_j_dir = HERE / "judgments_signal" / inj["id"]
                votes = 0
                for jm in JUDGES:
                    jm_safe = safe_model(jm)
                    jf = orig_j_dir / f"{arm}__{jm_safe}.json"
                    if jf.exists():
                        jd = json.loads(jf.read_text())
                        if jd.get("detected"):
                            votes += 1
                if votes >= 2:
                    detected += 1
            orig_results_data[arm] = detected
        else:
            orig_arm = arm_map[arm]
            orig_det_data = json.loads(
                (REPO_ROOT / "experiments/2026-07-05_injection_exp2/out/results.json").read_text()
            )
            orig_results_data[arm] = orig_det_data["detection"][f"structural:{orig_arm}"]["detected"]

    lines.append("| Arm | Original | Corrected v3 |")
    lines.append("|---|---|---|")
    for arm in ARMS:
        o = orig_results_data[arm]
        c = results[arm]["detected"]
        lines.append(f"| {arm} | {o}/{len(structural)} | {c}/{len(structural)} |")

    RESULTS_MD.write_text("\n".join(lines) + "\n")
    print(f"\nResults written to {RESULTS_MD}")


if __name__ == "__main__":
    main()
