#!/usr/bin/env python3
"""Rejudge frozen Experiment 2 reviews with a concise, validated protocol.

Original judgments are never modified. Corrected verdicts are written under
experiments/2026-09-19_exp2_rejudge_v2/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXP = ROOT / "experiments/2026-07-05_injection_exp2"
SOURCE_OUT = SOURCE_EXP / "out"
MANIFEST_PATH = SOURCE_OUT / "manifest.json"
REVIEWS = SOURCE_OUT / "reviews"
ORIGINAL_JUDGMENTS = SOURCE_OUT / "judgments"
EXP = ROOT / "experiments/2026-09-19_exp2_rejudge_v2"
JUDGMENTS = EXP / "judgments_v3"
PREFLIGHT = EXP / "PREFLIGHT_V3.md"
USAGE_LOG = EXP / "usage_log.jsonl"
RESULTS_JSON = EXP / "RESULTS_V3.json"
RESULTS_MD = EXP / "RESULTS_V3.md"

sys.path.insert(0, str(SOURCE_EXP / "harness"))
sys.path.insert(0, str(ROOT))

from common import ALL_ARMS, JUDGES, load_manifest  # noqa: E402
from prnote.llm import _USAGE_LOG, generate_completion  # noqa: E402


STRUCTURAL_SYSTEM = """You adjudicate one binary code-review detection criterion.

A deterministic prefilter established that every CANDIDATE_MENTION is an exact
full-path or exact-basename mention of a manifest-listed true dependent. Path
identity is a fact. Do not re-evaluate it or require every dependent.

Return detected=true iff the review connects at least one candidate to a
consequence of the injected edit: the candidate still imports, calls, inherits
from, exports, or otherwise relies on the changed symbol/signature/contract and
therefore can break or requires an update.

Rules:
- One causally linked candidate is sufficient.
- Normal hedges ("may", "might", "could", "potential") are acceptable when the
  concrete failure mechanism is stated.
- The path mention and causal explanation may be in separate review passages.
- Do not require the word "broken" or the oracle's exact wording.
- A path merely listed with no connection to the edit is false.
- Generic "check callers", "update dependencies", or "add tests" is false
  unless tied to a candidate.
- Judge only the review; do not invent a missing causal link.

Select finding_passage_id from a supplied passage that contains the candidate
mention. Select causal_passage_id from a supplied passage expressing the causal
connection. They may be identical. Return one JSON object only, with no
Markdown."""

LOCAL_SYSTEM = """You adjudicate whether a code review detects the actual local
defect introduced by an edit.

Judge semantic equivalence to ORACLE_TARGET; do not require its wording.
Return detected=true only when the review identifies the specific wrong
behavior and a concrete mechanism or consequence. Merely restating the edit,
requesting tests, or saying the change is risky is false. Normal hedges are
acceptable only with a specific correct mechanism.

Select finding_passage_id and causal_passage_id from the supplied review
passages. They may be identical. Return one JSON object only, with no
Markdown."""

SCHEMA_KEYS = {
    "schema_version",
    "detected",
    "evidence_id",
    "finding_passage_id",
    "causal_passage_id",
    "reason_code",
}
TRUE_REASON = {
    "structural": "specific_cross_file_link",
    "local": "specific_local_defect",
}
FALSE_REASONS = {
    "no_exact_dependent_mention",
    "mention_only",
    "generic_risk_only",
    "wrong_defect",
    "no_supporting_review_text",
}
PROMPT_VERSION = "exp2-adjudication-v3"
INDEPENDENT_JUDGES = [
    "anthropic:claude-sonnet-4-5",
    "deepseek:deepseek-v4-pro",
    "xai:grok-4.6",
]
SUPPORTED_JUDGES = list(dict.fromkeys(JUDGES + INDEPENDENT_JUDGES))
ADJUDICATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": sorted(SCHEMA_KEYS),
    "properties": {
        "schema_version": {"type": "string", "const": PROMPT_VERSION},
        "detected": {"type": "boolean"},
        "evidence_id": {"type": ["string", "null"]},
        "finding_passage_id": {"type": ["string", "null"]},
        "causal_passage_id": {"type": ["string", "null"]},
        "reason_code": {"type": "string"},
    },
}

COST_PER_1M = {
    "openai:gpt-4o": {"input": 2.50, "output": 10.00},
    "openai:gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini:gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "anthropic:claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "deepseek:deepseek-v4-pro": {"input": 1.32, "output": 3.96},
    "xai:grok-4.6": {"input": 2.00, "output": 6.00},
}
ESTIMATED_OUTPUT_TOKENS = 120
PRINT_LOCK = threading.Lock()
USAGE_LOCK = threading.Lock()


def safe_model(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def audit_metadata(
    *,
    review: str,
    system: str | None,
    prompt: str | None,
    judge: str,
) -> dict[str, Any]:
    return {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_alias": judge,
        "model_snapshot": "unavailable-from-original-wrapper",
        "manifest_sha256": sha256_text(MANIFEST_PATH.read_text()),
        "review_sha256": sha256_text(review),
        "system_sha256": sha256_text(system or ""),
        "prompt_sha256": sha256_text(prompt or ""),
        "schema_sha256": sha256_text("|".join(sorted(SCHEMA_KEYS))),
    }


def true_file_mentions(injection: dict[str, Any], review: str) -> list[dict[str, Any]]:
    """Return exact path/basename mentions; never infer from stems."""
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
        excerpt = review[max(0, start - 160) : min(len(review), end + 260)]
        matches.append(
            {
                "evidence_id": f"M{index:03d}",
                "oracle_path": full_path,
                "match_kind": match_kind,
                "match_text": match_text,
                "start": start,
                "end": end,
                "excerpt": excerpt,
                "basename_collision": basename_counts[path.name] > 1,
            }
        )
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
        passages.append(
            {
                "passage_id": f"P{len(passages) + 1:03d}",
                "text": line,
                "start": start,
                "end": end,
            }
        )
    return passages


def attach_passages(
    matches: list[dict[str, Any]], passages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    output = []
    for match in matches:
        containing = [
            passage["passage_id"]
            for passage in passages
            if passage["start"] <= match["start"] < passage["end"]
        ]
        if len(containing) != 1:
            raise ValueError(
                f"match offset has {len(containing)} containing passages: {match}"
            )
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


def local_oracle_target(injection: dict[str, Any]) -> tuple[str, str]:
    """Return audited target and category without mutating the source manifest."""
    if injection["id"] == "grafana_L2_02" and "=!=" in injection["new"]:
        return (
            "The edited expression uses the invalid operator sequence '=!=' and "
            "cannot parse or compile.",
            "syntax_error",
        )
    operator = injection["operator"].casefold()
    if "guard" in operator or "null" in operator or "none" in operator:
        category = "guard_inversion"
    elif "comparison" in operator or "off-by-one" in operator:
        category = "boundary_change"
    else:
        category = "local_behavior"
    return injection["ground_truth"], category


def local_prompt(
    injection: dict[str, Any], passages: list[dict[str, Any]]
) -> str:
    target, category = local_oracle_target(injection)
    payload = {
        "id": injection["id"],
        "edit_file": injection["edit_file"],
        "old": injection["old"],
        "new": injection["new"],
        "operator": injection["operator"],
        "oracle_category": category,
        "oracle_target": target,
    }
    return (
        "LOCAL_INJECTION_JSON\n"
        f"{json.dumps(payload, sort_keys=True)}\n\n"
        "REVIEW_PASSAGES_JSON\n"
        f"{json.dumps(passages, sort_keys=True)}\n\n"
        "Required schema keys: schema_version, detected, evidence_id, "
        "finding_passage_id, causal_passage_id, reason_code.\n"
        f"schema_version must be {PROMPT_VERSION!r}; a positive local verdict "
        "must use evidence_id='local-edit' and reason_code='specific_local_defect'.\n"
        "If false: evidence_id/finding_passage_id/causal_passage_id must be null and "
        "reason_code must be one of generic_risk_only, wrong_defect, "
        "no_supporting_review_text."
    )


def extract_json(raw: str) -> tuple[dict[str, Any], str]:
    text = raw.strip()
    wrapper = "bare"
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) < 3 or lines[0] not in ("```", "```json") or lines[-1] != "```":
            raise ValueError("invalid Markdown fence wrapper")
        text = "\n".join(lines[1:-1]).strip()
        wrapper = "single_json_fence"
    if not (text.startswith("{") and text.endswith("}")):
        raise ValueError("response must be one bare JSON object")
    data = json.loads(text)
    if set(data) != SCHEMA_KEYS:
        raise ValueError(f"schema keys mismatch: {sorted(data)}")
    if data.get("schema_version") != PROMPT_VERSION:
        raise ValueError("schema_version mismatch")
    if not isinstance(data.get("detected"), bool):
        raise ValueError("detected must be a JSON boolean")
    return data, wrapper


def validate_verdict(
    data: dict[str, Any],
    matches: list[dict[str, Any]] | None,
    passages: list[dict[str, Any]],
) -> dict[str, Any]:
    detected = data["detected"]
    evidence_id = data.get("evidence_id")
    model_evidence_id = evidence_id
    evidence_id_normalized = False
    finding_passage_id = data.get("finding_passage_id")
    causal_passage_id = data.get("causal_passage_id")
    reason_code = data.get("reason_code")
    passage_ids = {passage["passage_id"] for passage in passages}

    if detected:
        if finding_passage_id not in passage_ids:
            raise ValueError("finding_passage_id is not supplied")
        if causal_passage_id not in passage_ids:
            raise ValueError("causal_passage_id is not supplied")
        if matches is not None:
            by_id = {item["evidence_id"]: item for item in matches}
            if evidence_id not in by_id:
                raise ValueError("evidence_id is not a deterministic candidate")
            if by_id[evidence_id]["finding_passage_id"] != finding_passage_id:
                candidates_in_passage = sorted(
                    item["evidence_id"]
                    for item in matches
                    if item["finding_passage_id"] == finding_passage_id
                )
                if not candidates_in_passage:
                    raise ValueError(
                        "finding passage contains no deterministic candidate"
                    )
                # evidence_id is clerical and redundant with the validated
                # passage. Canonicalize it to the candidate actually present.
                evidence_id = candidates_in_passage[0]
                evidence_id_normalized = True
            if reason_code != TRUE_REASON["structural"]:
                raise ValueError("wrong structural reason_code")
        else:
            if evidence_id != "local-edit":
                raise ValueError("positive local verdict needs evidence_id=local-edit")
            if reason_code != TRUE_REASON["local"]:
                raise ValueError("wrong local reason_code")
    else:
        if (
            evidence_id is not None
            or finding_passage_id is not None
            or causal_passage_id is not None
        ):
            raise ValueError("negative verdict evidence fields must be null")
        if reason_code not in FALSE_REASONS:
            raise ValueError("invalid negative reason_code")

    return {
        "schema_version": PROMPT_VERSION,
        "detected": detected,
        "evidence_id": evidence_id,
        "model_evidence_id": model_evidence_id,
        "evidence_id_normalized": evidence_id_normalized,
        "finding_passage_id": finding_passage_id,
        "causal_passage_id": causal_passage_id,
        "reason_code": reason_code,
    }


def judgment_path(case_id: str, arm: str, judge: str) -> Path:
    return JUDGMENTS / case_id / f"{arm}__{safe_model(judge)}.json"


def panel_tag(judges: list[str]) -> str:
    if judges == JUDGES:
        return "V3"
    if judges == INDEPENDENT_JUDGES:
        return "INDEPENDENT"
    return "_".join(safe_model(judge) for judge in judges).upper()


def panel_result_paths(judges: list[str]) -> tuple[Path, Path]:
    tag = panel_tag(judges)
    return EXP / f"RESULTS_{tag}.json", EXP / f"RESULTS_{tag}.md"


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def flush_usage() -> None:
    with USAGE_LOCK:
        if not _USAGE_LOG:
            return
        USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with USAGE_LOG.open("a") as handle:
            for entry in _USAGE_LOG:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        _USAGE_LOG.clear()


def generate_adjudication(
    *,
    prompt: str,
    system: str,
    judge: str,
) -> str:
    if judge.startswith("anthropic:"):
        import anthropic

        model_name = judge.split(":", 1)[1]
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url="https://api.anthropic.com",
        )
        response = client.messages.create(
            model=model_name,
            max_tokens=512,
            temperature=0.0,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": ADJUDICATION_SCHEMA,
                }
            },
        )
        usage = getattr(response, "usage", None)
        if usage is not None:
            _USAGE_LOG.append(
                {
                    "model": judge,
                    "prompt_tokens": getattr(usage, "input_tokens", 0) or 0,
                    "completion_tokens": getattr(usage, "output_tokens", 0) or 0,
                }
            )
        return response.content[0].text
    return generate_completion(
        prompt=prompt,
        system=system,
        model=judge,
        temperature=0.0,
    )


def old_verdict(case_id: str, arm: str, judge: str) -> bool | None:
    path = ORIGINAL_JUDGMENTS / case_id / f"{arm}__{safe_model(judge)}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text()).get("detected")


def call_judge(
    injection: dict[str, Any],
    arm: str,
    judge: str,
    *,
    force: bool,
) -> str:
    output = judgment_path(injection["id"], arm, judge)
    if output.exists() and not force:
        try:
            if json.loads(output.read_text()).get("detected") is not None:
                return "cached"
        except Exception:
            pass

    review_path = REVIEWS / injection["id"] / f"{arm}.md"
    review = review_path.read_text()
    passages = review_passages(review)
    structural = injection["band"].startswith("S")
    matches = (
        attach_passages(true_file_mentions(injection, review), passages)
        if structural
        else None
    )

    if structural and not matches:
        write_json_atomic(
            output,
            {
                "schema_version": PROMPT_VERSION,
                "detected": False,
                "evidence_id": None,
                "finding_passage_id": None,
                "causal_passage_id": None,
                "reason_code": "no_exact_dependent_mention",
                "judge": judge,
                "decision_source": "deterministic_no_match",
                "candidate_mentions": [],
                "original_verdict": old_verdict(injection["id"], arm, judge),
                **audit_metadata(
                    review=review,
                    system=STRUCTURAL_SYSTEM,
                    prompt=None,
                    judge=judge,
                ),
            },
        )
        return "deterministic"

    system = STRUCTURAL_SYSTEM if structural else LOCAL_SYSTEM
    prompt = (
        structural_prompt(injection, matches or [], passages)
        if structural
        else local_prompt(injection, passages)
    )
    delay = 2.0
    last_error = ""
    for attempt in range(3):
        try:
            attempt_prompt = prompt
            if last_error:
                attempt_prompt += (
                    "\n\nPREVIOUS RESPONSE INVALID\n"
                    f"{last_error}\n"
                    "Return a corrected object. Choose only supplied evidence and "
                    "passage IDs, and obey the schema exactly."
                )
            raw = generate_adjudication(
                prompt=attempt_prompt,
                system=system,
                judge=judge,
            )
            flush_usage()
            raw_data, response_wrapper = extract_json(raw)
            verdict = validate_verdict(raw_data, matches, passages)
            write_json_atomic(
                output,
                {
                    **verdict,
                    "judge": judge,
                    "decision_source": "llm_causal_adjudication",
                    "candidate_mentions": matches or [],
                    "response_wrapper": response_wrapper,
                    "original_verdict": old_verdict(injection["id"], arm, judge),
                    **audit_metadata(
                        review=review,
                        system=system,
                        prompt=attempt_prompt,
                        judge=judge,
                    ),
                },
            )
            return "judged"
        except Exception as exc:
            flush_usage()
            last_error = str(exc)
            if attempt < 2:
                time.sleep(min(delay * (2**attempt) * (1 + random.random() * 0.2), 45))
    write_json_atomic(
        output,
        {
            "detected": None,
            "error": last_error[:200],
            "judge": judge,
            "decision_source": "error",
            "schema_version": PROMPT_VERSION,
            **audit_metadata(
                review=review,
                system=system,
                prompt=prompt,
                judge=judge,
            ),
        },
    )
    return f"ERROR: {last_error[:120]}"


def majority(values: list[bool | None]) -> bool:
    return sum(value is True for value in values) >= 2


def assemble_results(
    injections: list[dict[str, Any]],
    arms: list[str],
    judges: list[str],
) -> None:
    rows = []
    old_rows = []
    reference_lookup = {}
    reference_label = "original_panel"
    if judges != JUDGES and RESULTS_JSON.exists():
        canonical = json.loads(RESULTS_JSON.read_text())
        reference_lookup = {
            (row["case_id"], row["arm"]): row["majority_detected"]
            for row in canonical["rows"]
        }
        reference_label = "corrected_original_3"
    for injection in injections:
        cohort = "structural" if injection["band"].startswith("S") else "local"
        for arm in arms:
            if not (REVIEWS / injection["id"] / f"{arm}.md").exists():
                continue
            new_values = []
            old_values = []
            sources = []
            for judge in judges:
                path = judgment_path(injection["id"], arm, judge)
                if not path.exists():
                    new_values.append(None)
                    sources.append("missing")
                else:
                    payload = json.loads(path.read_text())
                    new_values.append(payload.get("detected"))
                    sources.append(payload.get("decision_source", "unknown"))
                old_values.append(old_verdict(injection["id"], arm, judge))
            if any(not isinstance(value, bool) for value in new_values):
                raise RuntimeError(
                    f"incomplete corrected panel: {injection['id']}/{arm} "
                    f"{new_values}"
                )
            rows.append(
                {
                    "case_id": injection["id"],
                    "band": injection["band"],
                    "cohort": cohort,
                    "arm": arm,
                    "judge_values": new_values,
                    "decision_sources": sources,
                    "majority_detected": majority(new_values),
                }
            )
            old_rows.append(
                {
                    "case_id": injection["id"],
                    "arm": arm,
                    "majority_detected": (
                        reference_lookup[(injection["id"], arm)]
                        if reference_lookup
                        else majority(old_values)
                    ),
                }
            )

    old_lookup = {
        (row["case_id"], row["arm"]): row["majority_detected"] for row in old_rows
    }
    summary = []
    flips = []
    for cohort in ("structural", "local"):
        for arm in arms:
            selected = [
                row for row in rows if row["cohort"] == cohort and row["arm"] == arm
            ]
            if not selected:
                continue
            detected = sum(row["majority_detected"] for row in selected)
            old_detected = sum(
                old_lookup[(row["case_id"], arm)] for row in selected
            )
            summary.append(
                {
                    "cohort": cohort,
                    "arm": arm,
                    "n": len(selected),
                    "detected": detected,
                    "rate": detected / len(selected),
                    "original_detected": old_detected,
                    "original_rate": old_detected / len(selected),
                }
            )
            for row in selected:
                old = old_lookup[(row["case_id"], arm)]
                if old != row["majority_detected"]:
                    flips.append(
                        {
                            "case_id": row["case_id"],
                            "cohort": cohort,
                            "arm": arm,
                            "original": old,
                            "corrected": row["majority_detected"],
                        }
                    )

    payload = {
        "status": "post-hoc-measurement-correction",
        "prompt_version": PROMPT_VERSION,
        "judges": judges,
        "reference_panel": reference_label,
        "arms": arms,
        "summary": summary,
        "flips": flips,
        "rows": rows,
    }
    out_json, out_md = panel_result_paths(judges)
    write_json_atomic(out_json, payload)

    lines = [
        "# Experiment 2 corrected judge panel",
        "",
        "**Status:** post-hoc measurement correction; original judgments preserved.",
        "",
        "| Cohort | Arm | Original | Corrected |",
        "|---|---|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['cohort']} | `{row['arm']}` | "
            f"{row['original_detected']}/{row['n']} "
            f"({row['original_rate']:.1%}) | "
            f"{row['detected']}/{row['n']} ({row['rate']:.1%}) |"
        )
    lines.extend(
        [
            "",
            f"Verdict flips: {len(flips)}",
            "",
            "## Interpretation",
            "",
            "The corrected panel uses deterministic true-file matching followed by "
            "LLM adjudication of causal linkage. It is a post-hoc sensitivity "
            "analysis and must be reported beside, not silently substituted for, "
            "the original panel.",
            "",
        ]
    )
    out_md.write_text("\n".join(lines))


def preflight(
    injections: list[dict[str, Any]],
    arms: list[str],
    judges: list[str],
) -> dict[str, Any]:
    api_tasks = []
    deterministic_cells = 0
    missing_reviews = []
    basename_collision_cells = 0
    for injection in injections:
        structural = injection["band"].startswith("S")
        for arm in arms:
            review_path = REVIEWS / injection["id"] / f"{arm}.md"
            if not review_path.exists():
                missing_reviews.append(f"{injection['id']}/{arm}")
                continue
            review = review_path.read_text()
            passages = review_passages(review)
            matches = (
                attach_passages(true_file_mentions(injection, review), passages)
                if structural
                else None
            )
            if matches and any(item["basename_collision"] for item in matches):
                basename_collision_cells += 1
            if structural and not matches:
                deterministic_cells += len(judges)
                continue
            system = STRUCTURAL_SYSTEM if structural else LOCAL_SYSTEM
            prompt = (
                structural_prompt(injection, matches or [], passages)
                if structural
                else local_prompt(injection, passages)
            )
            for judge in judges:
                api_tasks.append(
                    {
                        "case_id": injection["id"],
                        "arm": arm,
                        "judge": judge,
                        "input_tokens": estimate_tokens(system + "\n" + prompt),
                    }
                )

    by_model = {}
    total_cost = 0.0
    for judge in judges:
        tasks = [task for task in api_tasks if task["judge"] == judge]
        input_tokens = sum(task["input_tokens"] for task in tasks)
        output_tokens = len(tasks) * ESTIMATED_OUTPUT_TOKENS
        rates = COST_PER_1M[judge]
        cost = (
            input_tokens / 1_000_000 * rates["input"]
            + output_tokens / 1_000_000 * rates["output"]
        )
        total_cost += cost
        by_model[judge] = {
            "calls": len(tasks),
            "estimated_input_tokens": input_tokens,
            "estimated_output_tokens": output_tokens,
            "estimated_cost_usd": cost,
        }
    return {
        "review_cells": len(api_tasks) // len(judges) + deterministic_cells // len(judges),
        "api_calls": len(api_tasks),
        "deterministic_judge_cells": deterministic_cells,
        "basename_collision_review_cells": basename_collision_cells,
        "missing_reviews": missing_reviews,
        "by_model": by_model,
        "estimated_cost_usd": total_cost,
    }


def write_preflight(
    data: dict[str, Any],
    arms: list[str],
    judges: list[str],
    workers: int,
) -> Path:
    lines = [
        "# Experiment 2 rejudge v2 — pre-flight",
        "",
        f"- Arms: {', '.join(arms)}",
        f"- Judges: {', '.join(judges)}",
        f"- Review cells: {data['review_cells']}",
        f"- Paid judge calls: {data['api_calls']}",
        f"- Deterministic no-match judge cells: {data['deterministic_judge_cells']}",
        f"- Review cells with a matched basename collision: "
        f"{data['basename_collision_review_cells']}",
        f"- Missing reviews: {len(data['missing_reviews'])}",
        f"- Workers: {workers}",
        "",
        "| Model | Calls | Estimated input tokens | Estimated output tokens | Estimated cost |",
        "|---|---:|---:|---:|---:|",
    ]
    for model, row in data["by_model"].items():
        lines.append(
            f"| `{model}` | {row['calls']} | "
            f"{row['estimated_input_tokens']:,} | "
            f"{row['estimated_output_tokens']:,} | "
            f"${row['estimated_cost_usd']:.2f} |"
        )
    lines.extend(
        [
            "",
            f"**Estimated total cost: ${data['estimated_cost_usd']:.2f}**",
            "",
            "Manifest correction ledger: `grafana_L2_02` is adjudicated as an "
            "actual syntax error (`=!=`), with the original label preserved in "
            "the source manifest.",
            "",
            "No review generation is performed. Original judgments are read-only.",
            "",
        ]
    )
    path = EXP / f"PREFLIGHT_{panel_tag(judges)}.md"
    path.write_text("\n".join(lines))
    return path


def selftest() -> None:
    injection = {
        "true_dependents": ["pkg/a.py", "pkg/other.py"],
        "operator": "renamed f -> f2",
        "edit_file": "pkg/base.py",
        "old": "def f():",
        "new": "def f2():",
        "ground_truth": "a.py breaks",
        "band": "S1",
    }
    review = "The rename breaks `pkg/a.py`; update its import."
    passages = review_passages(review)
    matches = attach_passages(true_file_mentions(injection, review), passages)
    assert [item["oracle_path"] for item in matches] == ["pkg/a.py"]
    data = {
        "schema_version": PROMPT_VERSION,
        "detected": True,
        "evidence_id": matches[0]["evidence_id"],
        "finding_passage_id": matches[0]["finding_passage_id"],
        "causal_passage_id": passages[0]["passage_id"],
        "reason_code": "specific_cross_file_link",
    }
    assert validate_verdict(data, matches, passages)["detected"] is True
    try:
        validate_verdict(
            {**data, "causal_passage_id": "P999"}, matches, passages
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unknown passage ID was accepted")
    stem_injection = {**injection, "true_dependents": ["pkg/example_file.py"]}
    assert true_file_mentions(stem_injection, "example_file may break") == []
    assert true_file_mentions(injection, "A.py may break") == []
    fenced_payload = {
        "schema_version": PROMPT_VERSION,
        "detected": False,
        "evidence_id": None,
        "finding_passage_id": None,
        "causal_passage_id": None,
        "reason_code": "mention_only",
    }
    parsed, wrapper = extract_json(
        "```json\n" + json.dumps(fenced_payload) + "\n```"
    )
    assert parsed == fenced_payload
    assert wrapper == "single_json_fence"
    try:
        extract_json("prefix " + json.dumps(fenced_payload))
    except ValueError:
        pass
    else:
        raise AssertionError("prose-wrapped JSON was accepted")
    local_data = {
        "schema_version": PROMPT_VERSION,
        "detected": True,
        "evidence_id": "local-edit",
        "finding_passage_id": passages[0]["passage_id"],
        "causal_passage_id": passages[0]["passage_id"],
        "reason_code": "specific_local_defect",
    }
    assert validate_verdict(local_data, None, passages)["detected"] is True
    assert majority([True, True, False]) is True
    assert majority([True, False, False]) is False
    print("SELFTEST_OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arms", nargs="+", default=ALL_ARMS, choices=ALL_ARMS)
    parser.add_argument(
        "--judges",
        nargs="+",
        default=JUDGES,
        choices=SUPPORTED_JUDGES,
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return

    injections = load_manifest()
    EXP.mkdir(parents=True, exist_ok=True)
    estimate = preflight(injections, args.arms, args.judges)
    preflight_path = write_preflight(
        estimate, args.arms, args.judges, args.workers
    )
    if args.dry_run:
        print(preflight_path.read_text())
        return
    if estimate["missing_reviews"]:
        raise SystemExit(
            "missing reviews:\n" + "\n".join(estimate["missing_reviews"])
        )

    tasks = []
    for injection in injections:
        for arm in args.arms:
            review_path = REVIEWS / injection["id"] / f"{arm}.md"
            if not review_path.exists():
                continue
            for judge in args.judges:
                output = judgment_path(injection["id"], arm, judge)
                if output.exists() and not args.force:
                    try:
                        if json.loads(output.read_text()).get("detected") is not None:
                            continue
                    except Exception:
                        pass
                tasks.append((injection, arm, judge))

    print(
        f"{len(tasks)} corrected judge cells to process "
        f"({estimate['api_calls']} estimated API calls before cache)"
    )
    done = failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                call_judge,
                injection,
                arm,
                judge,
                force=args.force,
            ): (injection["id"], arm, judge)
            for injection, arm, judge in tasks
        }
        for future in as_completed(futures):
            result = future.result()
            done += 1
            if result.startswith("ERROR"):
                failed += 1
                with PRINT_LOCK:
                    print(f"[{done}/{len(tasks)}] {futures[future]} {result}")
            elif done % 25 == 0 or done == len(tasks):
                with PRINT_LOCK:
                    print(f"[{done}/{len(tasks)}]", flush=True)
    flush_usage()
    assemble_results(injections, args.arms, args.judges)
    _, result_md = panel_result_paths(args.judges)
    print(
        f"DONE corrected={done - failed} failed={failed} "
        f"results={result_md}"
    )


if __name__ == "__main__":
    main()
