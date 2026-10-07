#!/usr/bin/env python3
"""
PR Review Evaluation — LLM multi-judge panel.

Scores every generated review against Chris's 25-criterion checklist using a
panel of LLM judges. Each judge produces an independent 0/1 verdict per
criterion; verdicts are aggregated per (pr, mode, criterion) via majority
vote (ties break to 0, the strict side). Per-judge detail and pairwise
inter-judge agreement are preserved for validity analysis.

Motivation: single-judge LLM-as-a-judge has known biases (model family,
verbosity, position). Using a small cross-provider panel with majority
vote mitigates this and lets us report inter-judge agreement as a
construct-validity check, following Zheng et al. (2023, MT-Bench /
Chatbot Arena).

Outputs (in `results/`):
  - `checklist_evaluation_llm.json`       majority-vote view (same shape as
                                          the legacy single-judge file, so
                                          downstream scripts keep working)
  - `checklist_evaluation_llm_multi.json` full per-judge detail, pairwise
                                          agreement, and panel metadata
  - `checklist_evaluation_llm.csv`        flat summary (majority vote)
  - `CHECKLIST_EVALUATION_REPORT.md`      human-readable report
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from prnote.llm import generate_completion  # noqa: E402


DEFAULT_PANEL = [
    "openai:gpt-4o-mini",
    "openai:gpt-4o",
    "gemini:gemini-2.5-flash",
]

RESULTS_DIR = REPO_ROOT / "results"
DEFAULT_OUTPUTS_DIR = REPO_ROOT / "outputs" / "luca_prs_fixed"


# ---------------------------------------------------------------------------
# Criteria
# ---------------------------------------------------------------------------


@dataclass
class ReviewCriteria:
    id: str
    category: str
    description: str
    kg_relevant: bool


EVALUATION_CRITERIA: list[ReviewCriteria] = [
    # Category 1: Functionality & Integration
    ReviewCriteria("F1", "Functionality", "Does the review verify that the change addresses the stated problem or requirement?", False),
    ReviewCriteria("F2", "Functionality", "Does the review identify edge cases or boundary conditions that need handling?", False),
    ReviewCriteria("F3", "Functionality", "Does the review check how the change integrates with existing components, APIs, or modules?", True),
    ReviewCriteria("F4", "Functionality", "Does the review warn about potential breaking changes or impact on dependent code?", True),
    # Category 2: Tests & Verification
    ReviewCriteria("T1", "Tests", "Does the review ask about or discuss the need for unit/integration tests?", True),
    ReviewCriteria("T2", "Tests", "Does the review mention testing edge cases, error paths, or failure scenarios?", True),
    ReviewCriteria("T3", "Tests", "Does the review reference specific test files or suggest which tests should be added/updated?", True),
    # Category 3: Readability & Structure  
    ReviewCriteria("R1", "Readability", "Does the review comment on code clarity, naming conventions, or function organization?", False),
    ReviewCriteria("R2", "Readability", "Does the review identify unnecessary complexity or suggest simplification?", False),
    ReviewCriteria("R3", "Readability", "Does the review check if code comments explain the 'why' behind decisions?", False),
    # Category 4: Maintainability & Design
    ReviewCriteria("M1", "Maintainability", "Does the review assess whether the change fits the existing architecture or design patterns?", True),
    ReviewCriteria("M2", "Maintainability", "Does the review flag if the PR scope is too large or should be split?", False),
    ReviewCriteria("M3", "Maintainability", "Does the review check if public APIs or interfaces are properly documented?", True),
    # Category 5: Consistency & Style
    ReviewCriteria("C1", "Consistency", "Does the review check adherence to project style guides or coding conventions?", False),
    ReviewCriteria("C2", "Consistency", "Does the review check if similar problems are solved consistently with existing patterns?", True),
    # Category 6: Performance
    ReviewCriteria("P1", "Performance", "Does the review identify potential performance issues or inefficiencies?", False),
    ReviewCriteria("P2", "Performance", "Does the review ask about benchmarks or performance testing for critical paths?", False),
    # Category 7: Security & Robustness
    ReviewCriteria("S1", "Security", "Does the review check for proper input validation or sanitization?", False),
    ReviewCriteria("S2", "Security", "Does the review flag hardcoded secrets, credentials, or sensitive data?", False),
    ReviewCriteria("S3", "Security", "Does the review assess error handling and failure recovery?", False),
    # Category 8: Review Quality (Meta)
    ReviewCriteria("Q1", "Quality", "Does the review provide an overall summary or assessment of the changes?", False),
    ReviewCriteria("Q2", "Quality", "Are review comments anchored to specific code locations (file paths, line numbers)?", True),
    ReviewCriteria("Q3", "Quality", "Does the review distinguish between blocking issues and minor suggestions?", False),
    ReviewCriteria("Q4", "Quality", "Does the review ask clarifying questions rather than making assumptions?", False),
    ReviewCriteria("Q5", "Quality", "Does the review explain the reasoning behind suggestions (the 'why')?", False),
]

CRITERIA_BY_ID: dict[str, ReviewCriteria] = {c.id: c for c in EVALUATION_CRITERIA}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class JudgeVerdict:
    """One judge's scored rubric for a single review."""
    model: str
    scores: dict[str, int]  # criterion_id -> 0/1; missing → -1 (not scored)
    evidence: dict[str, str]  # criterion_id -> evidence string
    error: str = ""


@dataclass
class CriterionAggregate:
    criterion_id: str
    score: int  # majority vote; -1 if no valid votes
    n_yes: int
    n_valid: int
    unanimous: bool
    evidence: str  # evidence from one judge that sided with the majority (for traceability)


@dataclass
class ReviewEvaluation:
    pr_id: int
    mode: str
    total_score: int
    max_score: int
    percentage: float
    kg_relevant_score: int
    kg_relevant_max: int
    kg_relevant_percentage: float
    criteria_scores: list[dict[str, Any]] = field(default_factory=list)  # majority-vote per criterion
    per_judge: list[dict[str, Any]] = field(default_factory=list)  # per-judge full verdict (JudgeVerdict dicts)
    evaluation_timestamp: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_review(review_path: Path) -> str:
    with review_path.open("r", encoding="utf-8") as f:
        return f.read()


def load_pr_context(pr_id: int) -> dict[str, Any]:
    """Load PR title + body for the judge prompt.

    Priority:
      1. data/luca_prs_v2/pr<N>_evidence.json     (v2 cleaned dataset)
      2. data/luca_prs_fixed/pr<N>_evidence.json  (v1 dataset, same shape)
      3. legacy directory-based candidates (early thesis layout)

    The v2 dataset recovers full PR bodies that were empty in v1 for
    10 of 25 PRs; preferring v2 here ensures the judge sees the same
    title/body that the v2 generator saw, so both halves of the
    pipeline are consistent.

    Set PR_CONTEXT_DIR to search another evidence directory first. This is
    required for any run whose PR ids are not the canonical dataset's: the
    held-out confirmatory set numbers its PRs 1..12, which collide with
    luca_prs_v2, so without the override the judge is handed a completely
    different pull request's title and body than the review it is scoring.
    """
    pack_candidates = []
    override = os.environ.get("PR_CONTEXT_DIR")
    if override:
        override_dir = Path(override)
        if not override_dir.is_absolute():
            override_dir = REPO_ROOT / override_dir
        pack_candidates.append(override_dir / f"pr{pr_id}_evidence.json")
    pack_candidates += [
        REPO_ROOT / "data" / "luca_prs_v2" / f"pr{pr_id}_evidence.json",
        REPO_ROOT / "data" / "luca_prs_fixed" / f"pr{pr_id}_evidence.json",
    ]
    for p in pack_candidates:
        if p.exists():
            with p.open() as f:
                ev = json.load(f)
            pr = ev.get("pr", {})
            return {
                "title": pr.get("title", ""),
                "body": (pr.get("body") or "")[:500],
                "pr_id": pr_id,
            }

    legacy_candidates = [
        REPO_ROOT / "luca_thesis" / "data" / "baseline_pr_stimuli" / str(pr_id) / "original_pr.json",
        REPO_ROOT / "data" / "luca_prs_fixed" / str(pr_id) / "original_pr.json",
    ]
    for p in legacy_candidates:
        if p.exists():
            with p.open() as f:
                pr = json.load(f)
            return {
                "title": pr.get("title", ""),
                "body": (pr.get("body") or "")[:500],
                "pr_id": pr_id,
            }
    return {"title": "", "body": "", "pr_id": pr_id}


SYSTEM_PROMPT = """You are an expert code review evaluator. Your task is to assess whether a PR review meets specific quality criteria.

For each criterion, you must:
1. Determine if the review addresses that criterion (score: 1) or not (score: 0)
2. Provide a brief quote or explanation as evidence

Be strict but fair:
- Score 1 only if the review CLEARLY addresses the criterion
- Score 0 if the criterion is not addressed or only vaguely mentioned
- Base your judgment on meaning and intent, not just keywords"""


JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")

# Fallback regex: used when full JSON parsing fails (typically Gemini returning
# unescaped quotes inside evidence strings). Recovers (id, score) pairs from
# malformed output without requiring the surrounding JSON to be valid.
ENTRY_RE = re.compile(
    r'"id"\s*:\s*"([A-Za-z]\d+)"[\s\S]{0,400}?"score"\s*:\s*([01])',
)
EVIDENCE_RE = re.compile(
    r'"id"\s*:\s*"([A-Za-z]\d+)"[\s\S]{0,400}?"score"\s*:\s*[01][\s\S]{0,30}?"evidence"\s*:\s*"([^\n]{0,300}?)"\s*[,}]',
)


def build_user_prompt(review: str, pr_context: dict[str, Any]) -> str:
    criteria_text = "\n".join(
        f"{i+1}. [{c.id}] {c.description}" for i, c in enumerate(EVALUATION_CRITERIA)
    )
    return f"""## PR Being Reviewed
Title: {pr_context.get('title', 'Unknown') or '(no title)'}
Description: {(pr_context.get('body') or 'N/A')[:400]}

## Review to Evaluate
{review[:4000]}

## Criteria to Check
{criteria_text}

## Instructions
Evaluate the review against each criterion. Respond with a JSON object in this exact format:

```json
{{
  "scores": [
    {{"id": "F1", "score": 0, "evidence": "Review does not verify the change addresses the problem"}},
    {{"id": "F2", "score": 1, "evidence": "Review mentions: 'what about edge cases where X is null'"}}
  ]
}}
```

Important:
- Include ALL 25 criteria (F1-F4, T1-T3, R1-R3, M1-M3, C1-C2, P1-P2, S1-S3, Q1-Q5)
- Each score must be 0 or 1
- Evidence should be a short quote or explanation"""


def judge_one(review: str, pr_context: dict[str, Any], model: str) -> JudgeVerdict:
    """Score all 25 criteria for one review with one judge model."""
    prompt = build_user_prompt(review, pr_context)
    try:
        raw = generate_completion(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            model=model,
            temperature=0.0,
        )
    except Exception as exc:
        return JudgeVerdict(model=model, scores={}, evidence={}, error=f"api_error: {exc}")

    scores, evidence, err = _parse_judge_output(raw or "")
    # Fill missing criteria as -1 (not scored by this judge — distinct from 0)
    for c in EVALUATION_CRITERIA:
        scores.setdefault(c.id, -1)
        evidence.setdefault(c.id, "")

    # If we got fewer than half of the criteria scored validly, treat as error
    # (typical when the fallback regex also fails).
    n_valid = sum(1 for s in scores.values() if s in (0, 1))
    if n_valid < len(EVALUATION_CRITERIA) // 2:
        return JudgeVerdict(model=model, scores=scores, evidence=evidence,
                            error=err or f"parse_error: only {n_valid}/{len(EVALUATION_CRITERIA)} criteria scored")
    return JudgeVerdict(model=model, scores=scores, evidence=evidence)


def _parse_judge_output(raw: str) -> tuple[dict[str, int], dict[str, str], str]:
    """Parse a judge's raw response into (scores, evidence, error_if_any).

    Tries strict JSON first; falls back to a regex-based extraction when the
    JSON is malformed (Gemini occasionally emits unescaped quotes in evidence).
    """
    scores: dict[str, int] = {}
    evidence: dict[str, str] = {}

    match = JSON_OBJECT_RE.search(raw)
    if match:
        try:
            payload = json.loads(match.group())
            for item in payload.get("scores", []) or []:
                cid = str(item.get("id", "")).strip()
                if cid not in CRITERIA_BY_ID:
                    continue
                try:
                    s = int(item.get("score", -1))
                except Exception:
                    s = -1
                if s not in (0, 1):
                    continue
                scores[cid] = s
                evidence[cid] = str(item.get("evidence", ""))[:500]
            return scores, evidence, ""
        except Exception:
            pass  # fall through to regex recovery

    # Regex fallback: robust to broken JSON (unescaped quotes etc.).
    for m in ENTRY_RE.finditer(raw):
        cid = m.group(1)
        if cid in CRITERIA_BY_ID:
            scores[cid] = int(m.group(2))

    for m in EVIDENCE_RE.finditer(raw):
        cid = m.group(1)
        if cid in CRITERIA_BY_ID and cid not in evidence:
            evidence[cid] = m.group(2).strip()[:500]

    if not scores:
        return scores, evidence, f"parse_error: no scores extracted from response: {raw[:200]!r}"
    return scores, evidence, ""


def aggregate_panel(verdicts: list[JudgeVerdict]) -> list[CriterionAggregate]:
    """Majority vote across judges, per criterion. Ties → 0 (strict)."""
    aggregates: list[CriterionAggregate] = []
    for c in EVALUATION_CRITERIA:
        valid = [(v.model, v.scores[c.id], v.evidence[c.id]) for v in verdicts if v.scores.get(c.id) in (0, 1)]
        n_valid = len(valid)
        n_yes = sum(1 for (_, s, _) in valid if s == 1)
        if n_valid == 0:
            agg_score = -1
            unanimous = False
            ev = ""
        else:
            # Strict: need >50% to say Yes
            agg_score = 1 if n_yes > n_valid - n_yes else 0
            unanimous = (n_yes == n_valid) or (n_yes == 0)
            # Pick evidence from a judge whose vote matches the majority
            matching = [e for (_, s, e) in valid if s == agg_score and e]
            ev = matching[0] if matching else ""
        aggregates.append(CriterionAggregate(
            criterion_id=c.id,
            score=agg_score,
            n_yes=n_yes,
            n_valid=n_valid,
            unanimous=unanimous,
            evidence=ev,
        ))
    return aggregates


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def evaluate_single_review(
    review_path: Path,
    pr_id: int,
    mode: str,
    judges: list[str],
) -> ReviewEvaluation:
    review = load_review(review_path)
    pr_context = load_pr_context(pr_id)
    
    verdicts = [judge_one(review, pr_context, m) for m in judges]
    aggregates = aggregate_panel(verdicts)
    
    # Treat unscored criteria (agg score -1) as 0 for aggregate totals, but keep the raw flag
    # in the per-judge detail so analysis can distinguish "judged No" from "not judged".
    scored_sum = sum(a.score for a in aggregates if a.score in (0, 1))
    max_score = len(EVALUATION_CRITERIA)
    
    kg_ids = {c.id for c in EVALUATION_CRITERIA if c.kg_relevant}
    kg_aggs = [a for a in aggregates if a.criterion_id in kg_ids]
    kg_sum = sum(a.score for a in kg_aggs if a.score in (0, 1))
    kg_max = len(kg_aggs)

    criteria_scores_flat: list[dict[str, Any]] = [
        {
            "criterion_id": a.criterion_id,
            "score": a.score if a.score in (0, 1) else 0,  # coerce for legacy consumers
            "evidence": a.evidence,
            "n_yes": a.n_yes,
            "n_valid": a.n_valid,
            "unanimous": a.unanimous,
        }
        for a in aggregates
    ]
    
    return ReviewEvaluation(
        pr_id=pr_id,
        mode=mode,
        total_score=scored_sum,
        max_score=max_score,
        percentage=round(scored_sum / max_score * 100, 1),
        kg_relevant_score=kg_sum,
        kg_relevant_max=kg_max,
        kg_relevant_percentage=round(kg_sum / kg_max * 100, 1) if kg_max else 0.0,
        criteria_scores=criteria_scores_flat,
        per_judge=[asdict(v) for v in verdicts],
        evaluation_timestamp=_now_iso(),
    )


def run_full_evaluation(judges: list[str], outputs_dir: Path, output_suffix: str = "") -> dict[str, Any]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Suffix lets us run cross-generator or sample replications without clobbering
    # the canonical 25-PR gpt-4o result files. "" means: write to canonical names.
    sfx = f"__{output_suffix}" if output_suffix else ""
    review_files = sorted(outputs_dir.glob("pr*_*.md"))
    # Per-review JSON checkpoint: lets us resume if the script crashes or hits
    # an API quota mid-run. ~$3-5 saved per failure on the 72-review v2 panel.
    cache_dir = outputs_dir / ".judge_cache" / (output_suffix or "default") / "_".join(
        j.replace(":", "-").replace("/", "-") for j in judges
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"Panel ({len(judges)} judges): {', '.join(judges)}")
    print(f"Reviews to evaluate: {len(review_files)}  (from {outputs_dir.relative_to(REPO_ROOT)})")
    print(f"Total API calls: {len(review_files) * len(judges)}")
    print(f"Per-review cache: {cache_dir.relative_to(REPO_ROOT)}\n")

    evaluations: list[ReviewEvaluation] = []
    cached_hits = 0
    for i, f in enumerate(review_files, start=1):
        m = re.match(r"pr(\d+)_(\w+)\.md", f.name)
        if not m:
            continue
        pr_id = int(m.group(1))
        mode = m.group(2)
        cache_path = cache_dir / f"pr{pr_id}_{mode}.json"
        if cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text())
                ev = ReviewEvaluation(**cached)
                evaluations.append(ev)
                cached_hits += 1
                per_j = " ".join(
                    f"{pj['model'].split(':')[-1]}={sum(1 for s in pj['scores'].values() if s == 1)}"
                    for pj in ev.per_judge
                )
                print(f"[{i:>3}/{len(review_files)}] PR#{pr_id:<3} {mode:<10} maj={ev.total_score}/{ev.max_score}  ({per_j})  [cached]")
                continue
            except Exception as exc:
                print(f"  warn: cache read failed for {cache_path.name}: {exc}; re-evaluating")
        print(f"[{i:>3}/{len(review_files)}] PR#{pr_id:<3} {mode:<10}", end=" ", flush=True)
        ev = evaluate_single_review(f, pr_id, mode, judges)
        evaluations.append(ev)
        try:
            cache_path.write_text(json.dumps(asdict(ev), indent=2))
        except Exception as exc:
            print(f"\n  warn: cache write failed for {cache_path.name}: {exc}")
        # Per-judge quick summary
        per_j = " ".join(
            f"{pj['model'].split(':')[-1]}={sum(1 for s in pj['scores'].values() if s == 1)}"
            for pj in ev.per_judge
        )
        errs = sum(1 for pj in ev.per_judge if pj.get("error"))
        err_flag = f" errs={errs}" if errs else ""
        print(f"maj={ev.total_score}/{ev.max_score}  ({per_j}){err_flag}")

    if cached_hits:
        print(f"\n  ({cached_hits}/{len(evaluations)} reviews loaded from cache; "
              f"{len(evaluations) - cached_hits} freshly judged)")

    # Crash-safe write: dump the raw per-review verdicts before computing summary,
    # so a bug in generate_summary cannot wipe out 50 min of API calls.
    raw_path = RESULTS_DIR / f"checklist_evaluation_llm_multi{sfx}.raw.json"
    raw_path.write_text(json.dumps({
        "metadata": {
            "evaluation_method": "llm_multi_judge",
            "judges": judges,
            "timestamp": _now_iso(),
            "outputs_dir": str(outputs_dir.relative_to(REPO_ROOT)),
            "note": "Raw per-review verdicts written before summary computation as a crash safety net.",
        },
        "evaluations": [asdict(e) for e in evaluations],
    }, indent=2))

    summary = generate_summary(evaluations)
    panel_meta = compute_panel_meta(evaluations, judges)

    detailed = {
        "metadata": {
            "evaluation_method": "llm_multi_judge",
            "judges": judges,
            "aggregation": "majority_vote (ties → 0)",
            "timestamp": _now_iso(),
            "criteria_count": len(EVALUATION_CRITERIA),
            "kg_relevant_criteria_count": sum(1 for c in EVALUATION_CRITERIA if c.kg_relevant),
            "outputs_dir": str(outputs_dir.relative_to(REPO_ROOT)),
        },
        "criteria_definitions": [
            {"id": c.id, "category": c.category, "description": c.description, "kg_relevant": c.kg_relevant}
            for c in EVALUATION_CRITERIA
        ],
        "evaluations": [asdict(e) for e in evaluations],
        "summary": summary,
        "panel": panel_meta,
    }

    # Full multi-judge detail file
    multi_path = RESULTS_DIR / f"checklist_evaluation_llm_multi{sfx}.json"
    with multi_path.open("w") as f:
        json.dump(detailed, f, indent=2)
    print(f"\n✓ Multi-judge detail → {multi_path.relative_to(REPO_ROOT)}")

    # Backward-compat file: same shape as legacy single-judge output.
    legacy = {
        "metadata": {
            "evaluation_method": "llm_multi_judge_majority",
            "model": " + ".join(judges),  # kept as a string for legacy consumers that assumed single model
            "judges": judges,
            "aggregation": "majority_vote (ties → 0)",
            "timestamp": detailed["metadata"]["timestamp"],
            "criteria_count": len(EVALUATION_CRITERIA),
            "kg_relevant_criteria_count": sum(1 for c in EVALUATION_CRITERIA if c.kg_relevant),
        },
        "criteria_definitions": detailed["criteria_definitions"],
        "evaluations": [
            {
                "pr_id": e.pr_id,
                "mode": e.mode,
                "total_score": e.total_score,
                "max_score": e.max_score,
                "percentage": e.percentage,
                "kg_relevant_score": e.kg_relevant_score,
                "kg_relevant_max": e.kg_relevant_max,
                "kg_relevant_percentage": e.kg_relevant_percentage,
                "criteria_scores": [
                    # Strip multi-judge fields for legacy shape
                    {"criterion_id": cs["criterion_id"], "score": cs["score"], "evidence": cs["evidence"]}
                    for cs in e.criteria_scores
                ],
                "evaluation_timestamp": e.evaluation_timestamp,
            }
            for e in evaluations
        ],
        "summary": summary,
    }
    legacy_path = RESULTS_DIR / f"checklist_evaluation_llm{sfx}.json"
    with legacy_path.open("w") as f:
        json.dump(legacy, f, indent=2)
    print(f"✓ Legacy-shape (majority vote) → {legacy_path.relative_to(REPO_ROOT)}")

    # CSV summary
    csv_path = RESULTS_DIR / f"checklist_evaluation_llm{sfx}.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pr_id", "mode", "total_score", "max_score", "percentage",
                    "kg_relevant_score", "kg_relevant_max", "kg_relevant_percentage"])
        for e in evaluations:
            w.writerow([e.pr_id, e.mode, e.total_score, e.max_score, e.percentage,
                           e.kg_relevant_score, e.kg_relevant_max, e.kg_relevant_percentage])
    print(f"✓ CSV summary     → {csv_path.relative_to(REPO_ROOT)}")

    # Markdown report
    report = generate_markdown_report(summary, evaluations, panel_meta, judges)
    report_path = RESULTS_DIR / f"CHECKLIST_EVALUATION_REPORT{sfx}.md"
    with report_path.open("w") as f:
        f.write(report)
    print(f"✓ Markdown report → {report_path.relative_to(REPO_ROOT)}")

    print_summary_report(summary, panel_meta, judges)
    return detailed


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------


def generate_summary(evaluations: list[ReviewEvaluation]) -> dict[str, Any]:
    # Discover all modes present in the evaluations rather than hard-coding the
    # canonical four. This lets us run priming/ablation modes (e.g. kgempty)
    # through the same pipeline without crashing.
    modes = sorted({e.mode for e in evaluations})
    summary: dict[str, Any] = {"by_mode": {}, "by_criterion": {}, "comparison": {}}
    
    for mode in modes:
        mode_evals = [e for e in evaluations if e.mode == mode]
        if not mode_evals:
            continue
        total_scores = [e.total_score for e in mode_evals]
        kg_scores = [e.kg_relevant_score for e in mode_evals]
        summary["by_mode"][mode] = {
            "count": len(mode_evals),
            "avg_total": round(sum(total_scores) / len(total_scores), 2),
            "avg_percentage": round(sum(e.percentage for e in mode_evals) / len(mode_evals), 1),
            "avg_kg_relevant": round(sum(kg_scores) / len(kg_scores), 2),
            "avg_kg_percentage": round(sum(e.kg_relevant_percentage for e in mode_evals) / len(mode_evals), 1),
            "max_score": mode_evals[0].max_score,
            "kg_max": mode_evals[0].kg_relevant_max,
        }

    for c in EVALUATION_CRITERIA:
        by_mode: dict[str, list[int]] = {m: [] for m in modes}
        for e in evaluations:
            for cs in e.criteria_scores:
                if cs["criterion_id"] == c.id and cs["score"] in (0, 1):
                    by_mode.setdefault(e.mode, []).append(cs["score"])
        summary["by_criterion"][c.id] = {
            "description": c.description,
            "category": c.category,
            "kg_relevant": c.kg_relevant,
            "scores_by_mode": {
                m: round(sum(v) / len(v) * 100, 0) if v else 0
                for m, v in by_mode.items()
            },
        }

    if "baseline" in summary["by_mode"] and "kg" in summary["by_mode"]:
        b = summary["by_mode"]["baseline"]
        k = summary["by_mode"]["kg"]
        summary["comparison"]["kg_vs_baseline"] = {
            "total_improvement": round(k["avg_percentage"] - b["avg_percentage"], 1),
            "kg_relevant_improvement": round(k["avg_kg_percentage"] - b["avg_kg_percentage"], 1),
            "total_multiplier": round(k["avg_percentage"] / b["avg_percentage"], 2) if b["avg_percentage"] else 0,
            "kg_relevant_multiplier": round(k["avg_kg_percentage"] / b["avg_kg_percentage"], 2) if b["avg_kg_percentage"] else 0,
        }
    return summary


def compute_panel_meta(evaluations: list[ReviewEvaluation], judges: list[str]) -> dict[str, Any]:
    """Inter-judge agreement + per-judge aggregates across all (pr, mode, criterion) cells."""
    # Per-judge yes-rate by mode (and overall)
    modes = sorted({e.mode for e in evaluations})
    by_judge_mode: dict[str, dict[str, dict[str, Any]]] = {m: {} for m in judges}
    for jm in judges:
        for mode in modes:
            n = 0
            yes = 0
            errors = 0
            for e in evaluations:
                if e.mode != mode:
                    continue
                pj = next((pj for pj in e.per_judge if pj["model"] == jm), None)
                if pj is None:
                    continue
                if pj.get("error"):
                    errors += 1
                for s in pj.get("scores", {}).values():
                    if s in (0, 1):
                        n += 1
                        if s == 1:
                            yes += 1
            if n:
                by_judge_mode[jm][mode] = {
                    "n_valid_cells": n,
                    "yes_count": yes,
                    "yes_rate_pct": round(100.0 * yes / n, 1),
                    "api_errors": errors,
                }

    # Pairwise agreement across all cells where both judges produced a valid score
    agreement: dict[str, dict[str, Any]] = {}
    for i, a in enumerate(judges):
        for b in judges[i + 1:]:
            both = 0
            agreed = 0
            yes_yes = 0
            no_no = 0
            disagreed_ay_bn = 0  # a=yes, b=no
            disagreed_an_by = 0  # a=no,  b=yes
            for e in evaluations:
                pa = next((pj for pj in e.per_judge if pj["model"] == a), None)
                pb = next((pj for pj in e.per_judge if pj["model"] == b), None)
                if not pa or not pb:
                    continue
                for c in EVALUATION_CRITERIA:
                    sa = pa["scores"].get(c.id, -1)
                    sb = pb["scores"].get(c.id, -1)
                    if sa in (0, 1) and sb in (0, 1):
                        both += 1
                        if sa == sb:
                            agreed += 1
                            if sa == 1:
                                yes_yes += 1
                            else:
                                no_no += 1
                        elif sa == 1 and sb == 0:
                            disagreed_ay_bn += 1
                        else:
                            disagreed_an_by += 1
            if both:
                # Cohen's kappa for binary (2 raters, 2 categories)
                po = agreed / both
                pa_y = (yes_yes + disagreed_ay_bn) / both  # P(a = yes)
                pb_y = (yes_yes + disagreed_an_by) / both  # P(b = yes)
                pa_n = 1 - pa_y
                pb_n = 1 - pb_y
                pe = pa_y * pb_y + pa_n * pb_n
                kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
                agreement[f"{a} vs {b}"] = {
                    "cells": both,
                    "agreed": agreed,
                    "agreement_pct": round(100.0 * po, 1),
                    "cohen_kappa": round(kappa, 3),
                    "yes_yes": yes_yes,
                    "no_no": no_no,
                    "a_yes_b_no": disagreed_ay_bn,
                    "a_no_b_yes": disagreed_an_by,
                }

    return {
        "judges": judges,
        "by_judge_mode": by_judge_mode,
        "inter_judge_agreement": agreement,
    }


def generate_markdown_report(
    summary: dict[str, Any],
    evaluations: list[ReviewEvaluation],
    panel_meta: dict[str, Any],
    judges: list[str],
) -> str:
    lines: list[str] = []
    lines.append("# PR Review Evaluation Report (Multi-Judge LLM Panel)")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Judges:** {', '.join(judges)}")
    lines.append(f"**Aggregation:** majority vote (ties → 0)")
    lines.append(f"**Criteria:** 25 ({sum(1 for c in EVALUATION_CRITERIA if c.kg_relevant)} KG-relevant)")
    lines.append("")
    lines.append("---")
    lines.append("## Average Scores by Mode (majority vote)")
    lines.append("")
    lines.append("| Mode | Total | % | KG-Relevant | KG % |")
    lines.append("|------|-------|---|-------------|------|")
    for mode in ["baseline", "kg", "rag", "hybrid"]:
        if mode in summary["by_mode"]:
            m = summary["by_mode"][mode]
            lines.append(f"| {mode.upper()} | {m['avg_total']:.2f}/{m['max_score']} | {m['avg_percentage']:.1f}% | {m['avg_kg_relevant']:.2f}/{m['kg_max']} | {m['avg_kg_percentage']:.1f}% |")
    lines.append("")

    if "kg_vs_baseline" in summary.get("comparison", {}):
        c = summary["comparison"]["kg_vs_baseline"]
        lines.append("### KG vs Baseline")
        lines.append("")
        lines.append(f"- Total improvement: {c['total_improvement']:+.1f}% ({c['total_multiplier']:.2f}x)")
        lines.append(f"- KG-relevant improvement: {c['kg_relevant_improvement']:+.1f}% ({c['kg_relevant_multiplier']:.2f}x)")
        lines.append("")

    lines.append("---")
    lines.append("## Per-judge Yes rates by mode")
    lines.append("")
    lines.append("| Judge | " + " | ".join(m.upper() for m in ["baseline", "kg", "rag", "hybrid"]) + " |")
    lines.append("|-------|" + "|".join(["---"] * 4) + "|")
    for j in judges:
        row = [j]
        for mode in ["baseline", "kg", "rag", "hybrid"]:
            info = panel_meta["by_judge_mode"].get(j, {}).get(mode)
            row.append(f"{info['yes_rate_pct']}% ({info['yes_count']}/{info['n_valid_cells']})" if info else "—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    if panel_meta["inter_judge_agreement"]:
        lines.append("## Inter-judge agreement (across all (PR × mode × criterion) cells)")
        lines.append("")
        lines.append("| Pair | Cells | Agreed | % | Cohen's κ |")
        lines.append("|------|-------|--------|---|-----------|")
        for pair, info in panel_meta["inter_judge_agreement"].items():
            lines.append(f"| {pair} | {info['cells']} | {info['agreed']} | {info['agreement_pct']}% | {info['cohen_kappa']} |")
        lines.append("")

    lines.append("---")
    lines.append("## KG-relevant criteria: baseline vs KG (majority vote)")
    lines.append("")
    lines.append("| Criterion | Description | Baseline | KG | Δ |")
    lines.append("|-----------|-------------|----------|----|----|")
    for cid, cdata in summary["by_criterion"].items():
        if cdata["kg_relevant"]:
            bl = cdata["scores_by_mode"].get("baseline", 0)
            kg = cdata["scores_by_mode"].get("kg", 0)
            delta = kg - bl
            sign = "+" if delta > 0 else ""
            lines.append(f"| {cid} | {cdata['description'][:60]}… | {bl:.0f}% | {kg:.0f}% | {sign}{delta:.0f}% |")
    lines.append("")

    lines.append("---")
    lines.append("## Per-PR results")
    lines.append("")
    for pr_id in sorted({e.pr_id for e in evaluations}):
        pr_evals = [e for e in evaluations if e.pr_id == pr_id]
        lines.append(f"### PR #{pr_id}")
        lines.append("")
        lines.append("| Mode | Score (maj) | KG-Relevant |")
        lines.append("|------|-------------|-------------|")
        for e in sorted(pr_evals, key=lambda x: x.mode):
            lines.append(f"| {e.mode} | {e.total_score}/{e.max_score} ({e.percentage}%) | {e.kg_relevant_score}/{e.kg_relevant_max} ({e.kg_relevant_percentage}%) |")
        lines.append("")

    lines.append("---")
    lines.append("## Criteria definitions")
    lines.append("")
    cat = None
    for c in EVALUATION_CRITERIA:
        if c.category != cat:
            lines.append(f"### {c.category}")
            lines.append("")
            cat = c.category
        marker = " (KG-relevant)" if c.kg_relevant else ""
        lines.append(f"- **{c.id}**: {c.description}{marker}")
    lines.append("")
    return "\n".join(lines)


def print_summary_report(summary: dict[str, Any], panel_meta: dict[str, Any], judges: list[str]) -> None:
    print("\n" + "=" * 72)
    print("EVALUATION SUMMARY — multi-judge panel (majority vote)")
    print("=" * 72)
    print(f"\nJudges: {', '.join(judges)}\n")
    print(f"{'Mode':<12} {'Total':<14} {'%':<8} {'KG':<12} {'KG %':<8}")
    print("-" * 56)
    for mode in ["baseline", "kg", "rag", "hybrid"]:
        if mode in summary["by_mode"]:
            m = summary["by_mode"][mode]
            print(f"{mode.upper():<12} {m['avg_total']:.2f}/{m['max_score']:<8} {m['avg_percentage']:>5.1f}%   "
                  f"{m['avg_kg_relevant']:.2f}/{m['kg_max']:<6} {m['avg_kg_percentage']:>5.1f}%")

    if "kg_vs_baseline" in summary.get("comparison", {}):
        c = summary["comparison"]["kg_vs_baseline"]
        print(f"\nKG vs Baseline: total {c['total_improvement']:+.1f}% ({c['total_multiplier']:.2f}x) | "
              f"KG-relevant {c['kg_relevant_improvement']:+.1f}% ({c['kg_relevant_multiplier']:.2f}x)")

    print("\n--- Per-judge yes rates ---")
    for j in judges:
        parts = []
        for mode in ["baseline", "kg", "rag", "hybrid"]:
            info = panel_meta["by_judge_mode"].get(j, {}).get(mode)
            if info:
                parts.append(f"{mode}: {info['yes_rate_pct']}%")
        print(f"  {j:<32} {' | '.join(parts)}")

    if panel_meta["inter_judge_agreement"]:
        print("\n--- Inter-judge agreement ---")
        for pair, info in panel_meta["inter_judge_agreement"].items():
            print(f"  {pair:<60} {info['agreement_pct']}%  κ={info['cohen_kappa']}  (n={info['cells']})")
    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PR reviews with a multi-judge LLM panel against Chris's 25-criterion checklist.")
    parser.add_argument("--models", type=str,
                        default=",".join(DEFAULT_PANEL),
                        help=f"Comma-separated judge models (default: {','.join(DEFAULT_PANEL)})")
    parser.add_argument("--outputs-dir", type=str, default=str(DEFAULT_OUTPUTS_DIR),
                        help=f"Directory containing pr*_*.md review files (default: {DEFAULT_OUTPUTS_DIR.relative_to(REPO_ROOT)})")
    parser.add_argument("--single", type=str, default=None,
                        help="Evaluate a single review file (e.g., outputs/luca_prs_fixed/pr1_kg.md)")
    parser.add_argument("--output-suffix", type=str, default="",
                        help="If set, writes to results/*__<suffix>.{json,csv,md} instead of the canonical names. "
                             "Use for cross-generator / sample replications (e.g. 'claude_sample').")
    args = parser.parse_args()
    
    judges = [m.strip() for m in args.models.split(",") if m.strip()]
    if not judges:
        parser.error("at least one judge model is required")
    
    if args.single:
        f = Path(args.single)
        m = re.search(r"pr(\d+)_(\w+)\.md", f.name)
        if not m:
            parser.error(f"could not parse PR id / mode from file name: {f.name}")
        pr_id = int(m.group(1))
        mode = m.group(2)
        ev = evaluate_single_review(f, pr_id, mode, judges)
        print(json.dumps(asdict(ev), indent=2))
    else:
        outputs_dir = Path(args.outputs_dir)
        if not outputs_dir.is_absolute():
            outputs_dir = REPO_ROOT / outputs_dir
        run_full_evaluation(judges, outputs_dir, output_suffix=args.output_suffix)


if __name__ == "__main__":
    main()
