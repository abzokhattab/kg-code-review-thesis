#!/usr/bin/env python3
"""
assemble_study_draft.py — study_data_draft.json for the new Python-PR pilot.

Same schema as human_eval_v3/study_data.json (so the existing index.html UI
and the counts/unique scripts work on it), plus a per-PR "answer_key" layer
so raters can verify concrete file references without knowing the codebase.

Modes: baseline_strict vs kg. Summaries are hand-authored from review text
only (blinding-safe, identifiers preserved), per the v3 convention.

$0. Run generate_review_counts.py / generate_review_unique.py after this.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parent.parent

PRS = [
    dict(pr_id=101, key="requests_7433", repo="psf/requests"),
    dict(pr_id=102, key="flask_5637", repo="pallets/flask"),
    dict(pr_id=103, key="click_3493", repo="pallets/click"),
    dict(pr_id=104, key="requests_7328", repo="psf/requests"),
    dict(pr_id=105, key="flask_5799", repo="pallets/flask"),
    dict(pr_id=106, key="click_3578", repo="pallets/click"),
]

# Plain-language PR context (added 2026-07-13). Raters know nothing about
# these repos and may not know Python well; the raw PR body is written by
# maintainers for maintainers. Each blurb is hand-written from the PR
# title/body/diff ONLY — never from either review — so it is arm-neutral
# and blinding-safe. Rendered above the original PR description in the UI.
PR_CONTEXT = {
    "requests_7433": (
        "`requests` is the most widely used Python library for making HTTP "
        "calls. When you attach data to a request, an internal function "
        "called `prepare_body` decides how to send it — as a plain value or "
        "as a stream (read bit by bit). This PR adjusts the check that "
        "detects \"file-like\" data so a special kind of wrapper object is "
        "correctly treated as a stream, and adds one test for that case."),
    "flask_5637": (
        "`flask` is a popular Python web framework. This PR adds a new "
        "setting called `TRUSTED_HOSTS`: a list of website host names the "
        "app should accept requests for. When it is set, requests sent to "
        "any other host name get rejected with an error. The check runs in "
        "the code that prepares every incoming request."),
    "click_3493": (
        "`click` is a Python library for building command-line tools. Its "
        "`echo` function prints text to the terminal (handling colors, "
        "pipes, and other quirks for you). This PR fixes a crash when "
        "printing an empty byte string, and tightens the declared type of "
        "what the function accepts."),
    "requests_7328": (
        "`requests` is the most widely used Python library for making HTTP "
        "calls. When a URL redirects, the library follows the redirect and "
        "records the chain of hops in `response.history`. This PR fixes a "
        "quirk where a response could appear inside its own history list, "
        "and adds a test for that."),
    "flask_5799": (
        "`flask` is a popular Python web framework. Its helper "
        "`stream_with_context` lets a page send its response piece by piece "
        "(streaming) while still having access to the current request. This "
        "PR reworks how the helper sets up its internal state so it also "
        "works in async views (a newer style of writing request handlers)."),
    "click_3578": (
        "`click` is a Python library for building command-line tools. The "
        "usage line of a command shows placeholders for its arguments, e.g. "
        "`[a|b]` for an optional choice between a and b. This PR fixes a "
        "small display bug where such placeholders got doubled square "
        "brackets (`[[a|b]]`), and adds tests."),
}

# Plain-language criteria wording (2026-07-13). Same 6 criteria and ids as
# v3 (the analysis keys on the id, e.g. "F3*"); only the rater-facing
# descriptions are reworded to avoid reviewer jargon ("design patterns",
# "boundary conditions"). Meaning preserved; recorded in ANALYSIS_PLAN.md.
CRITERIA = [
    # "short" (added 2026-08-01, v2): compact label rendered as the main line
    # in the criteria grid; the full question becomes the sub-line. Pilot
    # feedback: six long "Which review better..." sentences felt repetitive.
    {"id": "F3*", "category": "Functionality",
     "short": "Names the affected code",
     "description": "Which review better names the specific functions, classes, "
                    "or files that this change could affect?"},
    {"id": "F2*", "category": "Functionality",
     "short": "Describes failure cases",
     "description": "Which review better describes specific situations where the "
                    "changed code could fail or misbehave (unusual inputs, empty "
                    "values, error cases)?"},
    {"id": "T3", "category": "Tests",
     "short": "Points to tests",
     "description": "Which review better points to specific test files, or says "
                    "which tests should be added or updated?"},
    {"id": "Q5", "category": "Quality",
     "short": "Explains why",
     "description": "Which review better explains WHY something is a problem "
                    "(\"X could cause Y\"), rather than just saying it is one?"},
    {"id": "R1", "category": "Readability",
     "short": "Comments on code clarity",
     "description": "Which review better comments on how clear and well-organized "
                    "the code is (naming, structure)?"},
    {"id": "C6", "category": "Completeness",
     "short": "Covers the important issues",
     "description": "Which review better covers the important issues in this PR, "
                    "without obvious gaps?"},
]

# Plain-language rule (2026-07-06 revision; tightened 2026-07-13 for raters
# with no knowledge of these repos or Python): every bullet starts with a
# verb, avoids jargon a junior dev wouldn't know (glossing it in parentheses
# where the identifier must stay), keeps concrete identifiers, and never
# hints at which arm produced the review (blinding-safe; written from the
# review text only).
#
# 2026-08-01 pilot audit amendment: opening verbs are deliberately varied so
# neither arm has a signature verb (previously every kg summary led with
# "Names ..." and every baseline with "Warns ...", letting a rater identify
# a review from the first word of its summary). Bullet ORDER is no longer
# hand-chosen either — order_bullets() sorts them by where each point
# appears in the review body.
#
# 2026-08-17 risk-parity amendment: every review in both arms flags breakage,
# but the summaries rendered it as "could break" for baseline (5/6) and the
# weaker "could be affected" for kg (5/6), understating kg on the criteria
# that ask whether a review finds real problems. The kg bullets now state
# breakage at the strength the kg review itself uses, in the same plain
# register as the baseline bullets. Baseline summaries were audited against
# the same standard and needed no change. File lists are untouched: an
# asymmetry that mirrors the reviews is the effect under measurement, an
# asymmetry introduced here is not.
SUMMARIES = {
    "requests_7433": {
        "baseline_strict": [
            "Warns that the new stream-detection logic in `prepare_body` could break code that relied on the old behavior.",
            "Notes the new test in `tests/test_requests.py` covers only the one wrapper type this PR fixes; other file-like objects stay untested.",
            "Flags that the documentation was not updated for the new behavior.",
        ],
        "kg": [
            "Lists `src/requests/sessions.py` and `src/requests/api.py` as files that use `prepare_body` and could be affected.",
            "Notes the new test in `tests/test_requests.py` covers only the one wrapper type this PR fixes; other wrapper types stay untested.",
            "Warns the new detection logic could break other code that relied on how `prepare_body` behaved before.",
        ],
    },
    "flask_5637": {
        "baseline_strict": [
            "Cautions that a wrongly configured `TRUSTED_HOSTS` would make the app reject requests with unexpected \"400\" errors (request refused).",
            "Flags missing tests for `TRUSTED_HOSTS` left unset (`None`) and for invalid host patterns; the test file is `tests/test_request.py`.",
            "Notes `docs/config.rst` gives no examples for development vs production setups.",
        ],
        "kg": [
            "Names `src/flask/logging.py` and `src/flask/sessions.py` as files that read request data and could be affected by the new host check.",
            "Suggests adding tests for `TRUSTED_HOSTS` set to `None` or empty in `tests/test_instance_config.py`.",
            "Warns `request.host` behavior now depends on configuration — a breaking change to call out in release notes.",
        ],
    },
    "click_3493": {
        "baseline_strict": [
            "Points out that changing the `message` parameter from `t.Any` to `object` could break code that passes other kinds of values.",
            "Questions whether the new `match` statement (a newer Python feature) works on older Python versions.",
            "Flags that `None` and empty text with the `nl=False` option (print without a line break) are untested; the test file is `tests/test_utils.py`.",
        ],
        "kg": [
            "Warns the stricter type could break code that calls `echo` with anything other than text or bytes.",
            "Identifies `src/click/core.py` and `src/click/termui.py` as files that use `echo`, and `src/click/testing.py` as a related testing helper.",
            "Flags there is no test for calling `echo` with values that are not text or bytes (`str`/`bytes`/`bytearray`).",
        ],
    },
    "requests_7328": {
        "baseline_strict": [
            "Warns that changing how `resp.history` is built could break integrations that rely on the previous redirect-history behavior.",
            "Names the new test `test_redirect_history_no_self_reference` in `tests/test_requests.py`.",
            "Flags that long or multi-step redirect chains stay untested.",
        ],
        "kg": [
            "Points to `src/requests/__init__.py` and `src/requests/api.py` as files that depend on `resolve_redirects`.",
            "Notes the new test in `tests/test_requests.py` covers only the self-reference case; longer redirect chains stay untested.",
            "Warns the change could break code that expects the original request to still appear in `resp.history`, and suggests keeping it there so existing code works.",
        ],
    },
    "flask_5799": {
        "baseline_strict": [
            "Notes the `stream_with_context` rewrite changes when request information is available during streaming, which could break existing async views.",
            "Flags missing tests for nested usage and for errors raised mid-stream; the test file is `tests/test_helpers.py`.",
            "Notes the updated documentation text may not fully explain the change for existing users.",
        ],
        "kg": [
            "Names `src/flask/templating.py` and `src/flask/blueprints.py` as files that use `stream_with_context` and could be affected.",
            "Flags missing tests for an error raised mid-stream or for the context being manually popped before iteration.",
            "Warns the rewrite could break ordinary (non-async) views that use `stream_with_context`, because it changes how request information is kept during streaming.",
        ],
    },
    "click_3578": {
        "baseline_strict": [
            "Warns the fix changes the usage message shown to users, which could break scripts that parse that output.",
            "Notes new tests in `tests/test_basic.py` cover `Choice` and `DateTime` placeholders; other bracketed placeholder types stay untested.",
            "Suggests checking the codebase for other places that format placeholders the same way.",
        ],
        "kg": [
            "Lists `src/click/types.py` and `src/click/parser.py` as files that rely on `make_metavar` (the function that builds those placeholders), where the fix could break how placeholders are shown.",
            "Points to `tests/test_shell_completion.py`, `tests/test_context.py`, and `tests/test_defaults.py` as related test files.",
            "Flags that nested choice placeholders stay untested and the API documentation was not updated.",
        ],
    },
}


# Hand-curated unique-content markers (2026-07-06, Chris spec — same process
# as final v3): a phrase is a marker only if the point/identifier is absent
# from the other review. Replaced generate_review_unique.py output after an
# audit found ~10 of its keys were section headers or identifiers present in
# BOTH reviews (e.g. "api contract violation", "prepare_body"), which would
# shade shared points. Do NOT re-run generate_review_unique.py on this study.
#
# Re-audited 2026-07-13 after normalize_review_surfaces.py stripped the
# prompt-scaffolding tail: 5 markers that only occurred in the removed tail
# were dropped (separation of concerns; test_HTTP_302/307_ALLOW_REDIRECT_*;
# requests.get; documentation generators) and 2 body-anchored replacements
# added after verifying absence from the other arm's review (invalid host
# patterns; CHANGES.md).
CURATED_UNIQUE = {
    "requests_7433": {
        "baseline_strict": ["deprecation warnings"],
        "kg": ["src/requests/sessions.py", "src/requests/api.py"]},
    "flask_5637": {
        "baseline_strict": ["docs/config.rst", "invalid host patterns",
                            "logging or warnings"],
        "kg": ["src/flask/logging.py", "src/flask/sessions.py",
               "tests/test_instance_config.py", "release notes", "request.host"]},
    "click_3493": {
        "baseline_strict": ["older Python versions", "pattern matching with",
                            "nl=False"],
        "kg": ["src/click/core.py", "src/click/termui.py", "src/click/testing.py",
               "complex objects", "widely used across the codebase"]},
    "requests_7328": {
        "baseline_strict": ["test_redirect_history_no_self_reference"],
        "kg": ["src/requests/__init__.py", "src/requests/api.py",
               "optionally including the original request"]},
    "flask_5799": {
        "baseline_strict": ["nested context usage", "fallback mechanism",
                            "migration steps"],
        "kg": ["src/flask/templating.py", "src/flask/blueprints.py",
               "manually popped", "used synchronously"]},
    "click_3578": {
        "baseline_strict": ["parse these messages", "CHANGES.md"],
        "kg": ["src/click/types.py", "src/click/parser.py",
               "tests/test_shell_completion.py", "tests/test_context.py",
               "tests/test_defaults.py", "nested choice types"]},
}


BACKTICK = re.compile(r"`([^`]+)`")


def strip_html_comments(body):
    """Remove HTML comments from the PR body before raters see it.

    GitHub hides these, but the study's renderer escapes `<` and `>` before
    rendering, so a contributor checklist left in a comment printed as visible
    text. On PR 103 (click #3493) that text instructed the reader to add tests,
    update the docs and add a changelog entry, priming three rubric criteria on
    one stimulus. Applied to every PR so the rule belongs to the pipeline
    rather than being a patch for the one case where it happened to bite.
    """
    out = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def order_bullets(bullets, review_text):
    """Order summary bullets by where their point appears in the review body.

    Blinding rationale (2026-08-01 pilot audit): the hand-authored bullet
    order leaked a surface pattern — one arm's summaries always led with
    'Names ... files', the other's with 'Warns ...' — so a rater could pick
    a review from the first word of its summary without reading it. This
    deterministic, arm-blind rule anchors each bullet at the first review
    position of any backticked identifier it mentions (bullets with no
    anchor keep their relative order, after anchored ones — matching where
    unanchored points like documentation gaps sit in the review template).
    """
    def anchor(item):
        idx, bullet = item
        positions = [review_text.find(tok) for tok in BACKTICK.findall(bullet)]
        positions = [p for p in positions if p >= 0]
        return (min(positions) if positions else len(review_text), idx)
    return [b for _, b in sorted(enumerate(bullets), key=anchor)]


def main():
    answer_key = json.loads((BASE / "answer_key.json").read_text())

    # Preserve the frozen review_counts layer across re-assembly (it is only
    # valid while the review texts are unchanged; regenerate with
    # generate_review_counts.py --force if they ever change).
    old_path = BASE / "study_data_draft.json"
    old = json.loads(old_path.read_text()) if old_path.exists() else {}
    old_counts = {pr["pr_id"]: pr.get("review_counts")
                  for pr in old.get("prs", [])}

    prs = []
    for cfg in PRS:
        key = cfg["key"]
        ev = json.loads((BASE / "evidence" / f"{key}_evidence.json").read_text())
        reviews = {mode: (BASE / "reviews" / f"{key}_{mode}.md").read_text()
                   for mode in ("baseline_strict", "kg")}
        pr = {
            "pr_id": cfg["pr_id"],
            "repo": cfg["repo"],
            "pr_number": ev["pr"]["number"],
            "title": ev["pr"]["title"],
            "url": f"https://github.com/{cfg['repo']}/pull/{ev['pr']['number']}",
            "body": strip_html_comments(ev["pr"].get("body") or ""),
            "pr_context": PR_CONTEXT[key],
            "diff": ev["full_diff"],
            "reviews": reviews,
            "review_summaries": {arm: order_bullets(SUMMARIES[key][arm],
                                                    reviews[arm])
                                 for arm in SUMMARIES[key]},
            "review_unique": CURATED_UNIQUE[key],
            "answer_key": answer_key[key],
        }
        if old_counts.get(cfg["pr_id"]):
            pr["review_counts"] = old_counts[cfg["pr_id"]]
        prs.append(pr)

    out = {
        # Final pre-data instrument version. Review texts remain frozen. The UI
        # labels summaries as review claims and renders neutral, source-audited
        # repository relationships rather than correctness-signalling badges.
        "version": "python-prs-study-v4-diff-default-r14",
        "criteria": CRITERIA,
        "modes": ["baseline_strict", "kg"],
        "comparisons": [{"id": "bl_vs_kg", "label": "Baseline vs KG",
                         "mode_a": "baseline_strict", "mode_b": "kg"}],
        "prs": prs,
        "summary_meta": {"model": "hand-authored",
                         "note": "Summary of review claims from review text only "
                                 "(not researcher-verified facts; blinding-safe), "
                                 "identifiers preserved; v3 convention. Reworded "
                                 "2026-07-13 into plainer language for raters "
                                 "unfamiliar with the repos/Python (same points, "
                                 "same identifiers, arm-symmetric edits). "
                                 "2026-08-01 amendment: opening verbs varied and "
                                 "bullets ordered by position in the review body "
                                 "(order_bullets), removing the per-arm signature "
                                 "pattern (kg always led with 'Names', baseline "
                                 "with 'Warns')."},
        "pr_context_meta": {
            "method": "hand-written from PR title/body/diff only (never from a "
                      "review) — arm-neutral, blinding-safe",
            "note": "One plain-language paragraph per PR: what the library is, "
                    "what the change does. Added 2026-07-13 because raters know "
                    "neither the repos nor necessarily Python.",
        },
        "highlight_meta": {
            "method": "curated-semantic",
            "note": "Hand-curated 2026-07-06 (Chris spec, same as final v3): a phrase "
                    "is a marker only if the point/identifier is absent from the other "
                    "review; paraphrases of shared points stay unshaded.",
        },
        "answer_key_meta": {
            "method": "build_answer_key.py — existence check plus source-audited "
                      "relationship classification at PR head SHA",
            "warning": "Relationship evidence does not validate the review's "
                       "risk or consequence claim.",
            "legend": {
                "changed": "file is part of the PR's changed files",
                "direct": "direct runtime use/call of the changed symbol",
                "indirect": "indirect execution or public-entry path",
                "related": "participates in a related data flow",
                "module_only": "module import only; behavioral relevance unestablished",
                "type_only": "type-only reference; behavioral relevance unestablished",
                "exists": "file exists; connection unestablished",
                "not_found": "no such file found at the pinned commit",
            },
        },
    }
    if old.get("count_meta"):
        out["count_meta"] = old["count_meta"]

    encoded = json.dumps(out, indent=2)
    paths = [BASE / "study_data_draft.json", BASE / "pilot" / "study_data.json"]
    for path in paths:
        path.write_text(encoded)
    print(f"wrote {', '.join(p.name for p in paths)}: "
          f"{len(prs)} PRs, modes {out['modes']}")


if __name__ == "__main__":
    main()
