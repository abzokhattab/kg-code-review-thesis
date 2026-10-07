#!/usr/bin/env python3
"""run_priming_placebo_v2.py — does the graph, or the instruction, produce the lift?

The `kg` prompt differs from `baseline` in two ways at once: it carries repository
facts, and its system prompt tells the model to look for integration risks, missing
tests and ownership concerns. A lift over `baseline` is therefore ambiguous between
"the model used the relations" and "the model was told what to look for".

This runs the placebo that separates them: the *identical* KG system prompt and the
*identical* v2 user-prompt template, with the context block empty. Three arms then
decompose the effect additively:

    baseline  -> kgempty    the instruction alone (priming)
    kgempty   -> kg         the facts alone (content)
    baseline  -> kg         the headline effect, = priming + content

The existing control (results/KG_EMPTY_PRIMING_CONTROL.md) cannot settle this. It
covers 5 PRs, generated at T=0.3 against `data/luca_prs_fixed_ast_scoped` with a
hand-rolled user prompt, so it is crossed with the v2 rebuild on dataset, era,
temperature *and* prompt template. Chapter 6 already concedes it "does not support
the claim it was built to support".

Parity here is by construction, not by transcription: the kgempty arm is registered
into `regenerate_reviews_v2`'s own dispatch tables and generated through its own
`generate_one`, so the template, diff truncation, title/body handling, model and
temperature are necessarily the same objects the `kg` arm used. Only the context
builder differs, and it returns "".

The baseline and kg arms are NOT regenerated or re-judged: their cells are read from
the headline panel file, which used the same PRs, judges and rubric. That keeps this
to 40 generations + 120 judge calls.

Both stages are parallel and idempotent:
  * generation skips a PR whose review .md already exists;
  * judging skips a PR whose per-review cache entry already exists, and writes into
    the exact path `run_full_evaluation` reads, so assembly costs no API calls.

Reads:
  data/luca_prs_v2/pr{N}_evidence.json
  results/checklist_evaluation_llm_multi__v2.json      (baseline + kg cells)
Writes:
  outputs/luca_prs_v2_kgempty/pr{N}_kgempty.md
  results/checklist_evaluation_llm_multi__kgempty_priming_v2.{json,csv,md}
  results/PRIMING_PLACEBO_v2.md

Usage:
  source load_env.sh
  python3 scripts/run_priming_placebo_v2.py --dry-run
  python3 scripts/run_priming_placebo_v2.py
  python3 scripts/run_priming_placebo_v2.py --stage analyse   # no API calls
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

EVIDENCE_DIR = REPO_ROOT / "data" / "luca_prs_v2"
REVIEW_DIR = REPO_ROOT / "outputs" / "luca_prs_v2_kgempty"
HEADLINE = REPO_ROOT / "results" / "checklist_evaluation_llm_multi__v2.json"
REPORT = REPO_ROOT / "results" / "PRIMING_PLACEBO_v2.md"
SUFFIX = "kgempty_priming_v2"

ARM = "kgempty"
TEMPERATURE = 0.0
GENERATOR = "openai:gpt-4o"

_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def locked_pr_ids() -> list[int]:
    """The locked v2 PR list, read from the generator so it cannot drift."""
    src = (REPO_ROOT / "dataset_v2" / "scripts"
           / "regenerate_reviews_v2.py").read_text()
    body = src.split("ALL_PRS = [", 1)[1].split("]", 1)[0]
    body = "\n".join(line.split("#", 1)[0] for line in body.splitlines())
    return [int(tok) for tok in body.replace(",", " ").split()]


def with_retries(fn, label: str, max_retries: int = 6):
    """Retry on 429/5xx/transient transport errors with linear backoff."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - provider SDKs raise many types
            msg = str(exc).lower()
            transient = any(t in msg for t in (
                "429", "rate_limit", "500", "502", "503", "529",
                "overloaded", "timeout", "connection",
            ))
            if transient and attempt < max_retries:
                sleep_s = 10 + 5 * attempt
                log(f"    {label}: transient ({str(exc)[:70]}); sleep {sleep_s}s "
                    f"[{attempt + 1}/{max_retries}]")
                time.sleep(sleep_s)
                continue
            raise


# ---------------------------------------------------------------------------
# Stage 1 — generation (parallel, idempotent)
# ---------------------------------------------------------------------------

def stage_generate(pr_ids: list[int], workers: int, force: bool) -> int:
    os.environ["REGEN_EVIDENCE_DIR"] = str(EVIDENCE_DIR)
    os.environ["REGEN_OUTPUT_DIR"] = str(REVIEW_DIR)
    os.environ.setdefault("MODEL_NAME", GENERATOR)

    regen = _load_module(
        REPO_ROOT / "dataset_v2" / "scripts" / "regenerate_reviews_v2.py",
        "regenerate_reviews_v2",
    )

    # The placebo is the KG arm with its facts removed. Registering it in the
    # generator's own tables means the prompt template, diff handling, model and
    # temperature cannot drift from the kg arm -- the failure that made the 5-PR
    # control uninterpretable.
    regen.PROMPTS[ARM] = regen.SYSTEM_PROMPT_KG
    regen.CONTEXT_BUILDERS[ARM] = lambda _ev: ""

    unknown = set(pr_ids) - set(regen.ALL_PRS)
    if unknown:
        raise SystemExit(f"PR ids not in the locked v2 list: {sorted(unknown)}")

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    jobs, skipped = [], 0
    for pr_id in pr_ids:
        pack = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        if not pack.exists():
            log(f"  pr{pr_id}: no evidence pack, skipping")
            continue
        out = REVIEW_DIR / f"pr{pr_id}_{ARM}.md"
        if out.exists() and out.stat().st_size > 0 and not force:
            skipped += 1
            continue
        jobs.append((pr_id, pack, out))

    log(f"  {len(jobs)} to generate, {skipped} already present")
    if not jobs:
        return 0

    errors = 0

    def run(job):
        pr_id, pack, out = job
        t0 = time.time()
        review, meta = with_retries(
            lambda: regen.generate_one(pack, ARM, TEMPERATURE), f"pr{pr_id}"
        )
        # Write through a temp file so an interrupted run cannot leave a truncated
        # review that the idempotency check would later accept as complete.
        tmp = out.with_suffix(".md.part")
        tmp.write_text(review)
        tmp.replace(out)
        return pr_id, meta, time.time() - t0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(run, j): j for j in jobs}
        for fut in as_completed(futs):
            pr_id = futs[fut][0]
            try:
                pr_id, meta, dt = fut.result()
                # context_chars must be 0 for every row; anything else means the
                # placebo leaked facts.
                log(f"  pr{pr_id:<3} OK {dt:5.1f}s  prompt={meta['prompt_chars']:>6} "
                    f"review={meta['review_chars']:>5} ctx={meta['context_chars']}")
            except Exception as exc:  # noqa: BLE001
                errors += 1
                log(f"  pr{pr_id:<3} ERR {exc}")
    return errors


# ---------------------------------------------------------------------------
# Stage 2 — judging (parallel, idempotent)
# ---------------------------------------------------------------------------

def stage_judge(pr_ids: list[int], workers: int) -> int:
    os.environ["PR_CONTEXT_DIR"] = str(EVIDENCE_DIR)

    ev = _load_module(REPO_ROOT / "scripts" / "evaluate_reviews.py", "evaluate_reviews")
    judges = list(ev.DEFAULT_PANEL)

    cache_dir = REVIEW_DIR / ".judge_cache" / SUFFIX / "_".join(
        j.replace(":", "-").replace("/", "-") for j in judges
    )
    cache_dir.mkdir(parents=True, exist_ok=True)

    log(f"  judges: {', '.join(judges)}")
    log(f"  PR#1 context resolves to: {ev.load_pr_context(1)['title'][:70]!r}")

    jobs, skipped = [], 0
    for pr_id in pr_ids:
        review = REVIEW_DIR / f"pr{pr_id}_{ARM}.md"
        if not review.exists():
            continue
        if (cache_dir / f"pr{pr_id}_{ARM}.json").exists():
            skipped += 1
            continue
        jobs.append((pr_id, review))

    log(f"  {len(jobs)} to judge, {skipped} already cached")

    errors = 0
    if jobs:
        def run(job):
            pr_id, review = job
            t0 = time.time()
            result = with_retries(
                lambda: ev.evaluate_single_review(review, pr_id, ARM, judges),
                f"pr{pr_id}",
            )
            tmp = cache_dir / f"pr{pr_id}_{ARM}.json.part"
            tmp.write_text(json.dumps(asdict(result), indent=2))
            tmp.replace(cache_dir / f"pr{pr_id}_{ARM}.json")
            return result, time.time() - t0

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(run, j): j for j in jobs}
            for fut in as_completed(futs):
                pr_id = futs[fut][0]
                try:
                    result, dt = fut.result()
                    log(f"  pr{pr_id:<3} OK {dt:5.1f}s  "
                        f"total={result.total_score}/{result.max_score} "
                        f"kg_rel={result.kg_relevant_score}/{result.kg_relevant_max}")
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    log(f"  pr{pr_id:<3} ERR {exc}")
    if errors:
        return errors

    log("  assembling panel artefacts from cache ...")
    ev.run_full_evaluation(judges, REVIEW_DIR, output_suffix=SUFFIX)
    return 0


# ---------------------------------------------------------------------------
# Stage 3 — the three-arm decomposition
# ---------------------------------------------------------------------------

def paired_perm(pairs: list[tuple[float, float]], n_iter: int,
                rng: random.Random) -> tuple[float, float]:
    """Two-sided paired sign-flip test. Returns (mean difference, p)."""
    diffs = [b - a for a, b in pairs]
    obs = statistics.mean(diffs)
    hits = sum(
        1 for _ in range(n_iter)
        if abs(statistics.mean([d if rng.random() < 0.5 else -d for d in diffs]))
        >= abs(obs) - 1e-12
    )
    return obs, (hits + 1) / (n_iter + 1)


def boot_ci(vals: list[float], n_iter: int, rng: random.Random) -> tuple[float, float]:
    n = len(vals)
    means = sorted(
        statistics.mean([vals[rng.randrange(n)] for _ in range(n)])
        for _ in range(n_iter)
    )
    return means[int(0.025 * n_iter)], means[int(0.975 * n_iter)]


def stage_analyse(n_boot: int, seed: int) -> int:
    panel = REPO_ROOT / "results" / f"checklist_evaluation_llm_multi__{SUFFIX}.json"
    if not panel.exists():
        print(f"error: {panel} missing; run the judge stage first", file=sys.stderr)
        return 2

    head = json.loads(HEADLINE.read_text())["evaluations"]
    plac = json.loads(panel.read_text())["evaluations"]

    def index(evals, mode):
        return {e["pr_id"]: e for e in evals if e["mode"] == mode}

    arms = {"baseline": index(head, "baseline"), "kg": index(head, "kg"),
            ARM: index(plac, ARM)}
    common = sorted(set(arms["baseline"]) & set(arms["kg"]) & set(arms[ARM]))
    if not common:
        print("error: no PRs common to all three arms", file=sys.stderr)
        return 2

    rng = random.Random(seed)
    contrasts = [
        ("baseline", ARM, "instruction only (priming)"),
        (ARM, "kg", "facts only (content)"),
        ("baseline", "kg", "headline effect (priming + content)"),
    ]

    rows = []
    for lo, hi, label in contrasts:
        for metric, key in (("total", "total_score"),
                            ("kgrel", "kg_relevant_score")):
            pairs = [(arms[lo][p][key], arms[hi][p][key]) for p in common]
            d, p = paired_perm(pairs, n_boot, rng)
            ci = boot_ci([b - a for a, b in pairs], n_boot, rng)
            rows.append({"lo": lo, "hi": hi, "label": label, "metric": metric,
                         "delta": d, "ci": ci, "p": p})

    means = {
        a: {m: statistics.mean([arms[a][p][k] for p in common])
            for m, k in (("total", "total_score"), ("kgrel", "kg_relevant_score"))}
        for a in arms
    }

    lengths = {}
    for a, d in (("baseline", REPO_ROOT / "outputs" / "luca_prs_v2"),
                 ("kg", REPO_ROOT / "outputs" / "luca_prs_v2"),
                 (ARM, REVIEW_DIR)):
        vals = [len((d / f"pr{p}_{a}.md").read_text())
                for p in common if (d / f"pr{p}_{a}.md").exists()]
        if vals:
            lengths[a] = statistics.mean(vals)

    def get(label_metric):
        return next(r for r in rows
                    if r["label"].startswith(label_metric[0])
                    and r["metric"] == label_metric[1])

    prime_kr = get(("instruction", "kgrel"))
    cont_kr = get(("facts", "kgrel"))
    total_kr = get(("headline", "kgrel"))
    share = (prime_kr["delta"] / total_kr["delta"] * 100
             if abs(total_kr["delta"]) > 1e-9 else float("nan"))

    L = ["# Priming placebo, v2 parity run — is it the instruction or the facts?\n"]
    L.append(f"**Arms:** `baseline`, `{ARM}` (KG system prompt, empty context), `kg`  ")
    L.append(f"**PRs:** {len(common)}  **Generator:** {GENERATOR} @ T={TEMPERATURE}  ")
    L.append(f"**Judges:** headline 3-judge panel  ")
    L.append(f"**Script:** `scripts/run_priming_placebo_v2.py`  ")
    L.append(f"**Method:** paired sign-flip test, B={n_boot:,}, seed={seed}; "
             f"bootstrap percentile CIs.\n")
    L.append("The placebo arm is generated through `regenerate_reviews_v2.generate_one` "
             "with the KG system prompt and a context builder that returns `\"\"`, so it "
             "differs from the `kg` arm in exactly one respect: the facts.\n")

    L.append("## Arm means\n")
    L.append("| Arm | total /25 | KG-relevant /9 | mean review chars |\n")
    L.append("|---|---:|---:|---:|\n")
    for a in ("baseline", ARM, "kg"):
        ln = f"{lengths[a]:.0f}" if a in lengths else "—"
        L.append(f"| {a} | {means[a]['total']:.2f} | {means[a]['kgrel']:.2f} | {ln} |\n")

    L.append("\n## Decomposition\n")
    L.append("| Contrast | What it isolates | Metric | Δ | 95% CI | p |\n")
    L.append("|---|---|---|---:|---|---:|\n")
    for r in rows:
        L.append(f"| {r['lo']} → {r['hi']} | {r['label']} | {r['metric']} | "
                 f"{r['delta']:+.2f} | [{r['ci'][0]:+.2f}, {r['ci'][1]:+.2f}] | "
                 f"{r['p']:.3f} |\n")

    L.append(f"\n## Reading\n\n")
    L.append(f"On the KG-relevant subscale the instruction accounts for "
             f"{prime_kr['delta']:+.2f} of the {total_kr['delta']:+.2f} headline "
             f"difference ({share:.0f}%), leaving {cont_kr['delta']:+.2f} "
             f"(p = {cont_kr['p']:.3f}) attributable to the graph facts themselves.\n")
    L.append("\nThe decisive quantity is the `kgempty → kg` row: it is the only "
             "contrast in Experiment 1 that isolates the structural content from "
             "everything else in the prompt. If it is near zero the KG lift is a "
             "prompt-engineering result, not a knowledge-graph result, and the thesis "
             "must say so. Experiment 2 is unaffected either way — a prompt with no "
             "facts cannot name a dependent file it was never given.\n")
    L.append(f"\nSupersedes `results/KG_EMPTY_PRIMING_CONTROL.md` (5 PRs, T=0.3, "
             f"pre-v2 evidence, hand-rolled prompt).\n")

    REPORT.write_text("".join(L))

    print()
    for r in rows:
        print(f"  {r['lo']:>9} -> {r['hi']:<9} {r['metric']:<6} "
              f"{r['delta']:+.2f} [{r['ci'][0]:+.2f}, {r['ci'][1]:+.2f}] p={r['p']:.3f}")
    print(f"\n  priming share of the KG-relevant effect: {share:.0f}%")
    print(f"wrote {REPORT.relative_to(REPO_ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--stage", choices=["generate", "judge", "analyse", "all"],
                    default="all")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--n-boot", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()

    pr_ids = locked_pr_ids()

    print("=" * 70)
    print("Priming placebo — v2 parity, 40 PRs, headline configuration")
    print("=" * 70)
    print(f"  arm       : {ARM} = SYSTEM_PROMPT_KG + empty context block")
    print(f"  generator : {GENERATOR} @ T={TEMPERATURE} (v2 prompt template)")
    print(f"  judges    : headline 3-judge panel")
    print(f"  new work  : {len(pr_ids)} reviews, {len(pr_ids) * 3} judge calls")
    print(f"  reused    : baseline + kg cells from "
          f"{HEADLINE.relative_to(REPO_ROOT)} (no re-judging)")
    print(f"  reviews  -> {REVIEW_DIR.relative_to(REPO_ROOT)}")
    print(f"  results  -> results/checklist_evaluation_llm_multi__{SUFFIX}.json")
    print(f"             {REPORT.relative_to(REPO_ROOT)}")
    print(f"  workers   : {args.workers}   idempotent: yes")
    print("  est. cost : ~$5   est. wall-clock: ~15-20 min")
    print("=" * 70)
    if args.dry_run:
        return 0

    if not (os.environ.get("OPENAI_API_KEY") or (REPO_ROOT / ".env").exists()):
        print("error: no OPENAI_API_KEY and no .env; run `source load_env.sh`",
              file=sys.stderr)
        return 2

    t0 = time.time()
    if args.stage in ("generate", "all"):
        print("  generating placebo reviews")
        if stage_generate(pr_ids, args.workers, args.force):
            print("errors during generation; re-run to retry (idempotent)",
                  file=sys.stderr)
            return 1

    if args.stage in ("judge", "all"):
        print("  judging with the headline panel")
        if stage_judge(pr_ids, args.workers):
            print("errors during judging; re-run to retry (idempotent)",
                  file=sys.stderr)
            return 1

    if args.stage in ("analyse", "all"):
        print("  decomposing")
        rc = stage_analyse(args.n_boot, args.seed)
        if rc:
            return rc

    print(f"done in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
