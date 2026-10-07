#!/usr/bin/env python3
"""One-shot Playwright pilot: complete the v4 human study end-to-end."""

from __future__ import annotations

import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STUDY_URL = os.environ.get("STUDY_URL", "http://localhost:8080/index.html")
RATER_ID = os.environ.get("RATER_ID", "cursor_full_run_001")

# Task order + A/B flip for RATER_ID (matches index.html seeded shuffle)
def _hash(s: str) -> int:
    h = 0
    for ch in s:
        h = ((h << 5) - h + ord(ch)) & 0xFFFFFFFF
    return h


def _rng(seed: int):
    def r() -> float:
        nonlocal seed
        seed = (seed + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((seed ^ (seed >> 15)) * (1 | seed)) & 0xFFFFFFFF
        t = (t + ((t ^ (t >> 7)) * (61 | t))) & 0xFFFFFFFF
        t = (t ^ (t >> 14)) & 0xFFFFFFFF
        return t / 4294967296
    return r


def build_task_plan() -> list[dict]:
    sd_path = os.path.join(REPO_ROOT, "human_eval_v3", "study_data.json")
    with open(sd_path) as f:
        study = json.load(f)
    comp = study["comparisons"][0]
    r = _rng(_hash(RATER_ID))
    pr_indices = list(range(len(study["prs"])))
    for i in range(len(pr_indices) - 1, 0, -1):
        j = int(r() * (i + 1))
        pr_indices[i], pr_indices[j] = pr_indices[j], pr_indices[i]
    plan = []
    for pi in pr_indices:
        pr = study["prs"][pi]
        flip = r() < 0.5
        plan.append({
            "pr_id": pr["pr_id"],
            "title": pr["title"],
            "flip": flip,
            "A": comp["mode_b"] if flip else comp["mode_a"],
            "B": comp["mode_a"] if flip else comp["mode_b"],
        })
    return plan


# Ratings keyed by pr_id: preference toward Joern (+) vs baseline (-)
JOERN_BIAS = {
    24: 0,    # tie
    47: -1,   # prefer baseline
    22: -1,   # prefer baseline
    44: 0,    # tie
    38: 1,    # prefer joern
    31: 1,    # prefer joern
}
DIFFICULTY = {24: 4, 47: 2, 22: 3, 44: 4, 38: 2, 31: 2}
WHY = {
    24: "Both reviews paraphrase the same _raise_for_params edge-case warnings; neither notes the fixture/test updates already in the diff.",
    47: "Review B stays anchored to Nodes.setNodes and the new unit test; Review A's CLI caller list feels speculative.",
    22: "Review B cites the moved test files from the diff; Review A lists unrelated client integration tests not touched by this PR.",
    44: "Both give generic refactor warnings with long file lists; neither flags the duplicate BITSET_INNER_DTYPE_C import in common.pxd.",
    38: "Review A names GrafanaRoute.tsx and interceptLinkClicks.ts as integration points; Review B only cites location.ts line numbers.",
    31: "Review A names concrete predict() callers and the fit_intercept=False gap; Review B stays closer to diff lines but less integration-specific.",
}


def pref_label(bias: int, flip: bool) -> str:
    """Map joern-bias to UI label text given A/B assignment."""
    # bias>0 => prefer joern, bias<0 => prefer baseline, 0 => no preference
    if bias == 0:
        return "No preference"
    prefer_a = (bias > 0 and flip) or (bias < 0 and not flip)
    strength = "Strongly" if abs(bias) >= 2 else "Slightly"
    return f"{strength} prefer {'A' if prefer_a else 'B'}"


def click_label(page, text: str, *, scope: str = "") -> None:
    root = page.locator(scope) if scope else page
    root.locator("label").filter(has_text=text).first.click()


def main() -> int:
    plan = build_task_plan()
    print(f"Rater: {RATER_ID}")
    print(f"URL:   {STUDY_URL}")
    for i, t in enumerate(plan, 1):
        print(f"  Task {i}: PR{t['pr_id']} flip={t['flip']} A={t['A']} -> {pref_label(JOERN_BIAS[t['pr_id']], t['flip'])}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("dialog", lambda d: d.accept())
        page.goto(STUDY_URL, wait_until="networkidle")

        # Welcome
        page.fill("#raterInput", RATER_ID)
        page.click("#startBtn")

        # Consent
        page.check("#consentBox")
        page.click("#consentBtn")

        # Demographics
        click_label(page, "Software Engineer", scope="#demographics")
        click_label(page, "5–10", scope="#demographics")
        click_label(page, "Weekly", scope="#demographics")
        page.click("#demoBtn")

        # Briefing -> warmup
        page.click("#beginBtn")
        click_label(page, "Strongly prefer A", scope="#warmup")
        click_label(page, "1 — Very Easy", scope="#warmup")
        page.click("#warmDoneBtn")

        # 6 evaluation tasks
        for i, task in enumerate(plan):
            page.wait_for_selector("#evaluation.active", timeout=10000)
            time.sleep(0.4)
            pref = pref_label(JOERN_BIAS[task["pr_id"]], task["flip"])
            click_label(page, pref, scope="#evaluation #pref5Opts")
            page.fill("#whyText", WHY[task["pr_id"]])
            diff = str(DIFFICULTY[task["pr_id"]])
            page.locator(f'#evaluation input[name="taskDiff"][value="{diff}"]').locator("xpath=..").click()
            if i < len(plan) - 1:
                page.click("#nextBtn")
            else:
                page.click("#nextBtn")  # Submit & Finish

        # Feedback -> completion
        page.wait_for_selector("#feedback.active", timeout=10000)
        page.fill("#feedbackText", "Pilot run via Playwright. UI flow works end-to-end. Long sklearn diffs are fatiguing; Grafana PR body has template noise.")
        page.click("#submitFbBtn")

        page.wait_for_selector("#completion.active", timeout=10000)
        prs_reviewed = page.locator("#stR").inner_text()
        total_time = page.locator("#stT").inner_text()
        avg_time = page.locator("#stA").inner_text()
        print(f"\nComplete: PRs={prs_reviewed}, total={total_time}, avg={avg_time}")

        # Pull localStorage backup
        outbox = page.evaluate(
            """(rater) => {
              const key = 'heval4_outbox_human_eval_v4_' + rater;
              return JSON.parse(localStorage.getItem(key) || '[]');
            }""",
            RATER_ID,
        )
        out_path = os.path.join(REPO_ROOT, "human_eval_v3", "data", "exported_payloads", f"{RATER_ID}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump({"rater_id": RATER_ID, "outbox": outbox}, f, indent=2)
        print(f"Saved {len(outbox)} webhook payloads -> {out_path}")

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
