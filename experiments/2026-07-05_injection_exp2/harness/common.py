"""Shared config + helpers for the Experiment 2 injection harness.

All outputs live under experiments/2026-07-05_injection_exp2/out/.
Nothing outside this folder is written (pre-reg §12).
Every stage is idempotent: it skips work whose output file already exists.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # harness/
EXP = HERE.parent                                # 2026-07-05_injection_exp2/
OUT = EXP / "out"
REPO_ROOT = Path("/Users/akhattab/ai")
LUCA = REPO_ROOT / "luca_repos"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

GEN_MODEL = "openai:gpt-4o"
JUDGES = ["openai:gpt-4o-mini", "openai:gpt-4o", "gemini:gemini-2.5-flash"]
ARMS = ["baseline", "kg", "rag", "hybrid", "kg_idealised", "kg_joern_inherit"]

# Feature ablation added 2026-09-06 (results/EXP2_FEATURE_ABLATION.md). The
# deployed `kg` arm carries two kinds of dependency evidence at once: a lexical
# grep file list and Joern-resolved function-level call edges. These two arms
# hold everything else fixed and supply one of them, so the detection rate
# attributes the cross-file finding to a specific kind of edge. Kept separate
# from ARMS so the pre-registered stats.py output is unchanged.
ABLATION_ARMS = ["kg_deps_only", "kg_edges_only"]
ALL_ARMS = ARMS + ABLATION_ARMS
SEED = 2026

# Per-repo scope: the sub-tree copied into out/scopes/<repo>/ on which
# discovery, the Joern CPG, and the RAG index are all built. Contexts are
# built from the CLEAN scope; the mutation exists only in the diff.
SCOPES = {
    "sklearn": {
        "language": "python",
        "src": LUCA / "scikit-learn_scikit-learn",
        # copied preserving the sklearn package layout
        "subdirs": ["sklearn/preprocessing", "sklearn/linear_model",
                    "sklearn/cluster", "sklearn/decomposition"],
        "extra_files": ["sklearn/base.py"],
        "joern_language": "pysrc",
    },
    "kafka": {
        "language": "java",
        "src": LUCA / "apache_kafka",
        "subdirs": ["streams/src/main/java/org/apache/kafka/streams"],
        "extra_files": [],
        "joern_language": "javasrc",
    },
    "grafana": {
        "language": "typescript",
        "src": LUCA / "grafana_grafana",
        "subdirs": ["packages/grafana-data/src"],
        "extra_files": [],
        "joern_language": "jssrc",
    },
}

# Band quotas per repo (pre-reg §5 + DECISIONS.md §1). Shortfalls are
# reported, never back-filled by hand.
BAND_QUOTA = {"S1": 3, "S2": 3, "S3": 2, "S4": 2, "S5": 2, "L1": 2, "L2": 2}
STRUCTURAL_BANDS = ["S1", "S2", "S3", "S4", "S5"]
LOCAL_BANDS = ["L1", "L2"]

BAND_TITLES = {  # direction-blind, defect-neutral PR titles
    "S1": "refactor: internal naming cleanup in {mod}",
    "S2": "refactor: extend {sym} for upcoming feature work",
    "S3": "refactor: simplify {sym} result handling",
    "S4": "refactor: internal naming cleanup in {mod}",
    "S5": "refactor: tidy package exports in {mod}",
    "L1": "refactor: simplify condition handling in {mod}",
    "L2": "refactor: remove redundant checks in {mod}",
}
PR_BODY = ("Small internal cleanup as part of ongoing maintenance. "
           "No behavior change intended.")


def scope_dir(repo: str) -> Path:
    return OUT / "scopes" / repo


def load_json(path: Path, default=None):
    if path.exists():
        return json.loads(path.read_text())
    return default


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def manifest_path() -> Path:
    return OUT / "manifest.json"


def load_manifest() -> list[dict]:
    m = load_json(manifest_path())
    if m is None:
        raise SystemExit("manifest.json missing — run inject.py first")
    return m["injections"]
