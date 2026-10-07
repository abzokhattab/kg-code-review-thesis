#!/usr/bin/env python3
"""Generate and judge the test-oracle band.

Pre-registration: ../docs/PRE_REGISTRATION_test_oracle.md

Three arms.  `kg` carries the dependency list with the test files removed;
`kg_plus_tests` adds exactly one thing, a labelled Related Tests section naming
the true test dependents.  So the contrast isolates the test section.

The judge asks a narrower question than Experiment 2's: not "did the review
find the cross-file breakage" but "did it name one of these specific test
files as breaking or needing update", plus a pre-declared fairness check on
whether the review talks about tests generically without naming one.

Both stages are idempotent and parallel.

    python3 run_and_judge.py --stage generate
    python3 run_and_judge.py --stage judge
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path("/Users/akhattab/ai")
EXP2 = REPO_ROOT / "experiments/2026-07-05_injection_exp2/harness"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(EXP2))

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from expand_dataset import find_tests  # noqa: E402
from common import scope_dir  # noqa: E402
from prnote import note  # noqa: E402
from prnote.llm import generate_completion  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
REVIEWS = OUT / "reviews"
JUDG = OUT / "judgments"

GEN_MODEL = "openai:gpt-4o"
JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
ARMS = ["baseline", "kg", "kg_plus_tests", "kg_plus_tests_lexical"]
LOCK = threading.Lock()


def load() -> list[dict]:
    return json.loads((OUT / "manifest.json").read_text())["injections"]


def kg_context(inj: dict, tests: str) -> dict:
    """Dependency list without the tests, plus an optional Related Tests section.

    tests = "none"     no test section (the `kg` arm)
            "oracle"   ground-truth broken tests, the idealised ceiling
            "lexical"  whatever the deployed filename-convention finder returns,
                       which is what the real pipeline would have supplied
    """
    ctx = {
        "changed_files": [{"path": inj["edit_file"]}],
        "dependent_files": [{"path": p, "relationship": "imports"}
                            for p in inj["true_other_dependents"][:15]],
        "functions_changed": [inj["symbol"]],
    }
    if tests == "oracle":
        paths = inj["true_test_dependents"][:12]
    elif tests == "lexical":
        paths = [t["path"] for t in
                 find_tests(inj["edit_file"], scope_dir(inj["repo"]))][:12]
    else:
        paths = []
    if paths:
        ctx["nearest_tests"] = [{"path": p, "relationship": "tests"}
                                for p in paths]
    return ctx


def generate_one(inj: dict, arm: str) -> str:
    out = REVIEWS / inj["id"] / f"{arm}.md"
    if out.exists() and out.stat().st_size > 200:
        return "cached"
    out.parent.mkdir(parents=True, exist_ok=True)
    kind = {"kg": "none", "kg_plus_tests": "oracle",
            "kg_plus_tests_lexical": "lexical"}.get(arm, "none")
    kg = None if arm == "baseline" else kg_context(inj, kind)
    mode = "baseline" if arm == "baseline" else "kg"
    for attempt in range(6):
        try:
            text = note.generate_review_direct(
                diff=inj["diff"], pr_title=inj["pr_title"], mode=mode,
                kg_context=kg, rag_context=None, model=GEN_MODEL)
            out.write_text(text)
            return "generated"
        except Exception as e:
            if attempt == 5:
                return f"ERROR: {str(e)[:120]}"
            time.sleep(min(2.0 * (2 ** attempt) * (1 + random.random() * 0.3), 90))


JUDGE_PROMPT = """You are scoring a code-review note against a known ground truth.

A symbol was renamed in `{edit_file}`. That rename breaks every file importing
it. Among the broken files are these TEST files, which are NOT shown in the diff:

{tests}

Answer two questions about the review note below.

1. named_test: Does the review explicitly name at least one of those exact test
   files (or its filename) as breaking, failing, or needing to be updated?
   Naming a different test file does not count. Mentioning the changed file
   itself does not count.

2. generic_test_talk: Does the review say that tests are affected or need
   updating, WITHOUT naming any of the specific files listed above?

Reply with strict JSON only:
{{"named_test": true/false, "generic_test_talk": true/false, "reason": "<one sentence>"}}

--- REVIEW NOTE ---
{review}
--- END ---"""


def judge_one(inj: dict, arm: str, model: str) -> str:
    slug = model.replace(":", "_").replace("/", "_")
    out = JUDG / inj["id"] / f"{arm}__{slug}.json"
    if out.exists():
        return "cached"
    review = (REVIEWS / inj["id"] / f"{arm}.md")
    if not review.exists():
        return "missing-review"
    out.parent.mkdir(parents=True, exist_ok=True)
    prompt = JUDGE_PROMPT.format(
        edit_file=inj["edit_file"],
        tests="\n".join(f"  - {t}" for t in inj["true_test_dependents"]),
        review=review.read_text()[:8000])
    for attempt in range(6):
        try:
            raw = generate_completion(prompt=prompt, system="", model=model,
                                      temperature=0.0)
            m = re.search(r"\{.*\}", raw, re.S)
            d = json.loads(m.group(0))
            out.write_text(json.dumps(
                {"named_test": bool(d.get("named_test")),
                 "generic_test_talk": bool(d.get("generic_test_talk")),
                 "reason": str(d.get("reason", ""))[:300],
                 "judge": model}, indent=2))
            return "judged"
        except Exception as e:
            if attempt == 5:
                return f"ERROR: {str(e)[:120]}"
            time.sleep(min(2.0 * (2 ** attempt) * (1 + random.random() * 0.3), 90))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["generate", "judge"], required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    inj = load()

    tasks = ([(i, a, None) for i in inj for a in ARMS] if args.stage == "generate"
             else [(i, a, j) for i in inj for a in ARMS for j in JUDGES])
    print(f"{len(tasks)} {args.stage} tasks (cached skipped)")

    done = {"cached": 0, "ok": 0, "err": 0}
    fn = (lambda t: generate_one(t[0], t[1])) if args.stage == "generate" \
        else (lambda t: judge_one(t[0], t[1], t[2]))
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fn, t): t for t in tasks}
        for n, f in enumerate(as_completed(futs), 1):
            r = f.result() or "ERROR: none"
            done["cached" if r == "cached" else
                 "err" if r.startswith("ERROR") else "ok"] += 1
            if r.startswith("ERROR"):
                with LOCK:
                    print(f"  {futs[f][0]['id']}/{futs[f][1]}: {r}")
            if n % 25 == 0:
                print(f"  [{n}/{len(tasks)}]", flush=True)
    print(f"DONE {args.stage} ok={done['ok']} cached={done['cached']} "
          f"errors={done['err']}")


if __name__ == "__main__":
    main()
