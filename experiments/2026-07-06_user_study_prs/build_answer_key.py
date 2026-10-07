#!/usr/bin/env python3
"""
build_answer_key.py — reference-verification answer key for the study UI.

For every concrete file reference in each review, records existence plus a
neutral, audited relationship to the changed behavior. A module import is not
treated as proof that a file is affected.

$0, AST/grep only. Output: answer_key.json
"""
import ast
import json
import os
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
FILE_RE = re.compile(
    r'[`\s(]((?:[\w./-]+/)?[\w.-]+\.(?:py|rst|md|txt|cfg|toml))[`\s):,]'
)

PRS = {
    "requests_7433": "psf_requests",
    "flask_5637": "pallets_flask",
    "click_3493": "pallets_click",
    "requests_7328": "psf_requests",
    "flask_5799": "pallets_flask",
    "click_3578": "pallets_click",
}

# Source-audited relationship labels for off-diff references. These describe
# repository facts only; they deliberately do not validate the review's risk
# or consequence claims. Any future uncurated reference falls back to the
# conservative module_only / exists categories below.
RELATION_OVERRIDES = {
    "requests_7433": {
        "src/requests/api.py": (
            "indirect",
            "Public API calls Session.request, which reaches request-body preparation.",
        ),
        "src/requests/sessions.py": (
            "indirect",
            "Session prepares a PreparedRequest; PreparedRequest.prepare then calls prepare_body.",
        ),
    },
    "flask_5637": {
        "src/flask/logging.py": (
            "exists",
            "Reads request.environ; no import of changed app.py or TRUSTED_HOSTS behavior connection was established.",
        ),
        "src/flask/sessions.py": (
            "type_only",
            "References Flask for typing; no host-validation behavior connection was established.",
        ),
        "tests/test_instance_config.py": (
            "exists",
            "File exists, but its tests do not establish a TRUSTED_HOSTS connection.",
        ),
    },
    "click_3493": {
        "src/click/core.py": (
            "direct",
            "Contains runtime call sites of echo, the function changed by this PR.",
        ),
        "src/click/termui.py": (
            "direct",
            "Contains runtime call sites of echo, the function changed by this PR.",
        ),
        "src/click/testing.py": (
            "module_only",
            "Imports utilities from the changed module, but no changed echo behavior connection was established.",
        ),
    },
    "requests_7328": {
        "src/requests/__init__.py": (
            "indirect",
            "Exports the public request API; redirect handling is reached indirectly through Session.",
        ),
        "src/requests/api.py": (
            "indirect",
            "Public API constructs a Session, whose redirect path reaches resolve_redirects.",
        ),
    },
    "flask_5799": {
        "src/flask/blueprints.py": (
            "module_only",
            "Imports another helper from helpers.py; it does not use stream_with_context.",
        ),
        "src/flask/templating.py": (
            "direct",
            "Directly imports and calls stream_with_context when streaming templates.",
        ),
    },
    "click_3578": {
        "src/click/parser.py": (
            "type_only",
            "References core parameter classes only for typing; no make_metavar display connection was established.",
        ),
        "src/click/types.py": (
            "related",
            "Choice and DateTime provide bracketed metavar text consumed by Argument.make_metavar.",
        ),
        "tests/test_context.py": (
            "exists",
            "File exists, but no test of the changed metavar behavior was established.",
        ),
        "tests/test_defaults.py": (
            "exists",
            "File exists, but no test of the changed metavar behavior was established.",
        ),
        "tests/test_shell_completion.py": (
            "exists",
            "Tests Choice completion; no data-flow connection to changed usage-message formatting was established.",
        ),
    },
}


def imports_of(pyfile):
    try:
        tree = ast.parse(Path(pyfile).read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, FileNotFoundError):
        return set()
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module)
            mods.update(a.name for a in node.names)
    return mods


def main():
    key_out = {}
    for key, repo_dir in PRS.items():
        repo = BASE / "pr_hunt" / "repos" / repo_dir
        ev = json.loads((BASE / "evidence" / f"{key}_evidence.json").read_text())
        sha = ev["pr"]["head_sha"]
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", sha], check=True)

        changed = [c["path"] for c in ev["changed_files"]]
        changed_bases = {os.path.basename(c) for c in changed}
        changed_mods = {Path(c).stem for c in changed if c.endswith(".py")} - {"__init__"}

        key_out[key] = {}
        for mode in ("baseline_strict", "kg"):
            txt = (BASE / "reviews" / f"{key}_{mode}.md").read_text()
            refs = sorted({m.group(1) for m in FILE_RE.finditer(txt)})
            verdicts = {}
            for r in refs:
                base = os.path.basename(r)
                if base in changed_bases:
                    verdicts[r] = {
                        "existence": "exists",
                        "relationship": "changed",
                        "basis": "This file is changed by the PR itself.",
                    }
                    continue
                hits = [p for p in repo.rglob(base)]
                if not hits:
                    verdicts[r] = {
                        "existence": "not_found",
                        "relationship": "not_found",
                        "basis": "No file with this name was found at the PR's pinned commit.",
                    }
                    continue
                override = RELATION_OVERRIDES.get(key, {}).get(r)
                if override:
                    relationship, basis = override
                    verdicts[r] = {
                        "existence": "exists",
                        "relationship": relationship,
                        "basis": basis,
                    }
                    continue
                connected = False
                for h in hits:
                    if h.suffix == ".py":
                        mods = imports_of(h)
                        if any(m == cm or m.endswith("." + cm) for m in mods for cm in changed_mods):
                            connected = True
                            break
                    else:
                        content = h.read_text(encoding="utf-8", errors="ignore")
                        if any(cm in content for cm in changed_mods):
                            connected = True
                            break
                verdicts[r] = {
                    "existence": "exists",
                    "relationship": "module_only" if connected else "exists",
                    "basis": (
                        "Imports or mentions a changed module; relevance to the changed "
                        "behavior was not established."
                        if connected else
                        "File exists; no connection to the changed behavior was established."
                    ),
                }
            key_out[key][mode] = verdicts

    (BASE / "answer_key.json").write_text(json.dumps(key_out, indent=1))
    for k, modes in key_out.items():
        print(f"\n=== {k} ===")
        for mode, verdicts in modes.items():
            counts = {}
            for v in verdicts.values():
                rel = v["relationship"]
                counts[rel] = counts.get(rel, 0) + 1
            print(f"  {mode:16} {counts}")
            for r, v in verdicts.items():
                print(f"      {v['relationship']:11} {r}")


if __name__ == "__main__":
    main()
