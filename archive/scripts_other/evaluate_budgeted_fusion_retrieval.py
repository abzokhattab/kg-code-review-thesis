#!/usr/bin/env python3
"""Zero-cost offline gate for budgeted graph + semantic retrieval.

This is a development-only information-availability experiment. It makes no
network or model calls. See:
  experiments/2026-09-19_budgeted_fusion_retrieval/DESIGN.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EXP2 = ROOT / "experiments/2026-07-05_injection_exp2"
TEST_EXP = ROOT / "experiments/2026-09-06_test_oracle"
OUT_DIR = ROOT / "experiments/2026-09-19_budgeted_fusion_retrieval"
BUDGETS = (2_000, 4_000, 8_000)
RRF_K = 60
TEST_PATH_RE = re.compile(r"(^|[/_.-])(tests?|specs?)([/_.-]|$)", re.I)

sys.path.insert(0, str(EXP2 / "harness"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyzers import ANALYZERS  # noqa: E402
from common import SCOPES, scope_dir  # noqa: E402
from expand_dataset import find_dependents, find_tests  # noqa: E402


Candidate = dict[str, Any]


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def estimate_tokens(text: str) -> int:
    """Match the repository's deterministic 4-chars-per-token approximation."""
    return max(1, math.ceil(len(text) / 4))


def is_test_path(path: str) -> bool:
    return bool(TEST_PATH_RE.search(path.replace("\\", "/")))


def candidate(
    path: str,
    source: str,
    evidence: Iterable[str],
    *,
    score: float | None = None,
) -> Candidate:
    clean_evidence = []
    seen = set()
    for item in evidence:
        text = str(item).strip()
        if text and text not in seen:
            clean_evidence.append(text)
            seen.add(text)
    return {
        "file": str(Path(path)),
        "sources": [source],
        "evidence": clean_evidence,
        "score": score,
    }


def merge_candidate(left: Candidate, right: Candidate) -> Candidate:
    merged = {
        "file": left["file"],
        "sources": list(dict.fromkeys(left["sources"] + right["sources"])),
        "evidence": list(dict.fromkeys(left["evidence"] + right["evidence"])),
        "score": left.get("score"),
    }
    scores = [x for x in (left.get("score"), right.get("score")) if x is not None]
    if scores:
        merged["score"] = max(scores)
    return merged


def dedupe_order(items: Iterable[Candidate]) -> list[Candidate]:
    positions: dict[str, int] = {}
    output: list[Candidate] = []
    for item in items:
        path = item["file"]
        if path in positions:
            idx = positions[path]
            output[idx] = merge_candidate(output[idx], item)
        else:
            positions[path] = len(output)
            output.append(item)
    return output


def candidate_text(item: Candidate) -> str:
    sources = ", ".join(item["sources"])
    lines = [f"FILE: {item['file']}", f"SOURCES: {sources}"]
    lines.extend(item["evidence"])
    return "\n".join(lines) + "\n"


def reciprocal_rank_fusion(*rankings: list[Candidate]) -> list[Candidate]:
    fused: dict[str, Candidate] = {}
    scores: defaultdict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            path = item["file"]
            scores[path] += 1.0 / (RRF_K + rank)
            if path not in fused:
                fused[path] = dict(item)
                continue
            previous = fused[path]
            merged = merge_candidate(previous, item)
            previous_is_graph = bool(set(previous["sources"]) - {"rag_proxy"})
            item_is_graph = bool(set(item["sources"]) - {"rag_proxy"})
            # Score both ranks, but render one compact representation. When
            # graph and semantic retrieval overlap, graph evidence wins and the
            # 800-character semantic preview is suppressed.
            if previous_is_graph and not item_is_graph:
                merged["evidence"] = list(previous["evidence"])
            elif item_is_graph and not previous_is_graph:
                merged["evidence"] = list(item["evidence"])
            fused[path] = merged

    def key(item: Candidate) -> tuple[float, int, str]:
        sources = set(item["sources"])
        has_graph = int(bool(sources - {"rag_proxy"}))
        return (-scores[item["file"]], -has_graph, item["file"])

    output = sorted(fused.values(), key=key)
    for item in output:
        item["rrf_score"] = scores[item["file"]]
    return output


def compact_fusion(
    graph_ranking: list[Candidate], rag_ranking: list[Candidate]
) -> list[Candidate]:
    """Keep graph evidence compact; add only non-overlapping semantic files.

    The v1 naive/RRF policies merged an 800-character semantic preview into
    graph-supported files. That spent the shared budget repeating evidence for
    the same path. This policy preserves the compact graph representation and
    uses the remaining budget only for semantic candidates outside the graph.
    """
    graph_paths = {item["file"] for item in graph_ranking}
    semantic_only = [
        item for item in rag_ranking if item["file"] not in graph_paths
    ]
    return dedupe_order(graph_ranking + semantic_only)


def pack(items: list[Candidate], budget: int) -> tuple[list[Candidate], int]:
    selected: list[Candidate] = []
    rendered_parts: list[str] = []
    for item in items:
        rendered = candidate_text(item)
        trial = "".join(rendered_parts + [rendered])
        if estimate_tokens(trial) > budget:
            break
        packed = dict(item)
        packed["estimated_tokens"] = estimate_tokens(rendered)
        selected.append(packed)
        rendered_parts.append(rendered)
    used = estimate_tokens("".join(rendered_parts)) if rendered_parts else 0
    return selected, used


class SavedRagProxy:
    """Query saved embeddings without a new embedding API call."""

    def __init__(self, repo: str):
        base = EXP2 / "out/rag" / repo
        metadata = load_json(base / "index_meta.json")
        chunks = load_json(base / "chunks.json")
        self.chunks = {row["id"]: row for row in chunks}
        self.embeddings = load_json(base / "embeddings.json")
        if metadata.get("chunk_count") != len(self.embeddings):
            raise AssertionError(
                f"{repo}: index count drift "
                f"{metadata.get('chunk_count')} != {len(self.embeddings)}"
            )
        dimensions = {len(row["embedding"]) for row in self.embeddings}
        if len(dimensions) != 1:
            raise AssertionError(f"{repo}: inconsistent embedding dimensions")
        missing_chunks = [
            row["id"] for row in self.embeddings if row["id"] not in self.chunks
        ]
        if missing_chunks:
            raise AssertionError(
                f"{repo}: {len(missing_chunks)} embedding IDs lack chunks"
            )
        self._norms = [
            math.sqrt(sum(value * value for value in row["embedding"]))
            for row in self.embeddings
        ]
        self._cache: dict[str, list[Candidate]] = {}

    def rank(self, edit_file: str) -> list[Candidate]:
        if edit_file in self._cache:
            return [dict(item) for item in self._cache[edit_file]]

        query_rows = [
            row
            for row in self.embeddings
            if row["metadata"]["file"] == edit_file
        ]
        if not query_rows:
            raise AssertionError(
                f"changed file absent from saved RAG index: {edit_file}"
            )
        query_row = min(
            query_rows,
            key=lambda row: (
                row["metadata"].get("start_line", 1),
                row["metadata"].get("end_line", 1),
            ),
        )
        query = query_row["embedding"]
        query_norm = math.sqrt(sum(value * value for value in query))
        if query_norm == 0:
            raise AssertionError(f"zero query vector: {edit_file}")

        best_by_file: dict[str, Candidate] = {}
        for row, norm in zip(self.embeddings, self._norms):
            metadata = row["metadata"]
            file_path = metadata["file"]
            if file_path == edit_file or norm == 0:
                continue
            similarity = sum(
                left * right for left, right in zip(query, row["embedding"])
            ) / (query_norm * norm)
            chunk = self.chunks.get(row["id"], {})
            preview = str(chunk.get("content", ""))[:800]
            evidence = [
                (
                    f"SEMANTIC {file_path}:"
                    f"{metadata.get('start_line', '?')}-"
                    f"{metadata.get('end_line', '?')} "
                    f"similarity={similarity:.6f}"
                )
            ]
            if preview:
                evidence.append(preview)
            item = candidate(
                file_path,
                "rag_proxy",
                evidence,
                score=similarity,
            )
            old = best_by_file.get(file_path)
            if old is None or similarity > float(old.get("score", -1.0)):
                best_by_file[file_path] = item
        ranked = sorted(
            best_by_file.values(),
            key=lambda item: (-float(item["score"]), item["file"]),
        )
        self._cache[edit_file] = ranked
        return [dict(item) for item in ranked]


class GraphSources:
    def __init__(self):
        self.analyzers = {
            repo: ANALYZERS[cfg["language"]](scope_dir(repo))
            for repo, cfg in SCOPES.items()
        }
        self.symbols = {
            repo: analyzer.symbols() for repo, analyzer in self.analyzers.items()
        }
        self.joern = {
            repo: load_json(EXP2 / "out/joern" / f"edges_{repo}.json")
            for repo in SCOPES
        }

    def _symbol(self, injection: dict[str, Any]) -> dict[str, Any] | None:
        matches = [
            symbol
            for symbol in self.symbols[injection["repo"]]
            if symbol.get("name") == injection.get("symbol")
            and symbol.get("file") == injection.get("edit_file")
        ]
        if matches:
            return matches[0]
        # S5 mutates a barrel/re-export file while the definition remains in its
        # original module. Fall back only when the symbol name is unique.
        by_name = [
            symbol
            for symbol in self.symbols[injection["repo"]]
            if symbol.get("name") == injection.get("symbol")
        ]
        return by_name[0] if len(by_name) == 1 else None

    def deployed(
        self, injection: dict[str, Any], cohort: str
    ) -> list[Candidate]:
        repo = injection["repo"]
        scope = scope_dir(repo)
        items: list[Candidate] = []
        if cohort == "dependency":
            edit_name = Path(injection["edit_file"]).name
            for edge in self.joern[repo].get(injection.get("symbol") or "", []):
                caller_file = edge.get("caller_file", "")
                if not caller_file or Path(caller_file).name == edit_name:
                    continue
                items.append(
                    candidate(
                        caller_file,
                        "joern",
                        [
                            (
                                f"CALLS {caller_file}::{edge.get('caller', '')} -> "
                                f"{injection['edit_file']}::"
                                f"{edge.get('callee', injection.get('symbol', ''))} "
                                f"at line {edge.get('line', '?')}"
                            )
                        ],
                    )
                )
            lexical = find_dependents(
                injection["edit_file"], str(scope), injection["language"]
            )
            for dep in lexical:
                items.append(
                    candidate(
                        dep["path"],
                        "lexical",
                        [
                            (
                                f"LEXICAL basename match from "
                                f"{injection['edit_file']}"
                            )
                        ],
                    )
                )
        else:
            for test in find_tests(injection["edit_file"], scope):
                items.append(
                    candidate(
                        test["path"],
                        "lexical_test",
                        [
                            (
                                f"TEST filename-convention match for "
                                f"{injection['edit_file']}"
                            )
                        ],
                    )
                )
        source_priority = {"joern": 0, "lexical": 1, "lexical_test": 0}
        ordered = sorted(
            items,
            key=lambda item: (
                source_priority.get(item["sources"][0], 9),
                item["file"],
                tuple(item["evidence"]),
            ),
        )
        return dedupe_order(ordered)

    def resolved(
        self, injection: dict[str, Any], cohort: str
    ) -> list[Candidate]:
        analyzer = self.analyzers[injection["repo"]]
        symbol = self._symbol(injection)
        if symbol is None:
            return []
        if cohort == "test":
            resolved = {
                path: evidence
                for path, evidence in analyzer.importers(symbol).items()
                if is_test_path(path)
            }
        else:
            # Development ceiling only. Use all relation families so retrieval
            # never sees the oracle band/edge type that selected the target.
            resolved = {}
            for relation_name, relation_fn in (
                ("IMPORTS", analyzer.importers),
                ("CALLS", analyzer.callers),
                ("INHERITS_FROM", analyzer.subclasses),
            ):
                for path, evidence in relation_fn(symbol).items():
                    resolved.setdefault(path, []).extend(
                        [f"RELATION {relation_name}"] + evidence
                    )
        return [
            candidate(
                path,
                "manifest_resolver",
                evidence,
            )
            for path, evidence in sorted(resolved.items())
            if path != injection["edit_file"]
        ]


def load_cases() -> list[dict[str, Any]]:
    structural = [
        {**row, "cohort": "dependency", "gold": row["true_dependents"]}
        for row in load_json(EXP2 / "out/manifest.json")["injections"]
        if row["band"].startswith("S")
    ]
    tests = [
        {**row, "cohort": "test", "gold": row["true_test_dependents"]}
        for row in load_json(TEST_EXP / "out/manifest.json")["injections"]
    ]
    return sorted(structural + tests, key=lambda row: (row["cohort"], row["id"]))


def evaluate_packed(
    case: dict[str, Any],
    arm: str,
    ranking: list[Candidate],
    budget: int,
) -> dict[str, Any]:
    selected, used = pack(ranking, budget)
    selected_paths = {item["file"] for item in selected}
    gold = set(case["gold"])
    hits = sorted(selected_paths & gold)
    graph_sources = {"joern", "lexical", "lexical_test", "manifest_resolver"}
    has_graph = any(set(item["sources"]) & graph_sources for item in selected)
    has_rag = any("rag_proxy" in item["sources"] for item in selected)
    semantic_only = sum(
        1 for item in selected if set(item["sources"]) == {"rag_proxy"}
    )
    first_rank = next(
        (
            rank
            for rank, item in enumerate(ranking, 1)
            if item["file"] in gold
        ),
        None,
    )
    return {
        "case_id": case["id"],
        "repo": case["repo"],
        "band": case["band"],
        "cohort": case["cohort"],
        "arm": arm,
        "budget": budget,
        "gold_count": len(gold),
        "candidate_count": len(ranking),
        "selected_count": len(selected),
        "tokens_used": used,
        "within_budget": used <= budget,
        "hit_any": bool(hits),
        "hit_count": len(hits),
        "hits": hits,
        "target_recall": len(hits) / len(gold) if gold else 0.0,
        "oracle_path_fraction": (
            len(hits) / len(selected_paths) if selected_paths else 0.0
        ),
        "first_relevant_rank": first_rank,
        "mixed_sources": has_graph and has_rag,
        "semantic_only_count": semantic_only,
        "selected": [
            {
                "file": item["file"],
                "sources": item["sources"],
                "estimated_tokens": item["estimated_tokens"],
                "score": item.get("score"),
                "rrf_score": item.get("rrf_score"),
            }
            for item in selected
        ],
    }


def mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return statistics.fmean(values) if values else 0.0


def aggregate(
    records: list[dict[str, Any]], cohort: str, arm: str, budget: int
) -> dict[str, Any]:
    rows = [
        row
        for row in records
        if row["arm"] == arm
        and row["budget"] == budget
        and (cohort == "all" or row["cohort"] == cohort)
    ]
    first_ranks = [
        int(row["first_relevant_rank"])
        for row in rows
        if row["first_relevant_rank"] is not None
    ]
    return {
        "cohort": cohort,
        "arm": arm,
        "budget": budget,
        "n": len(rows),
        "hit_any_n": sum(int(row["hit_any"]) for row in rows),
        "hit_any_rate": mean(rows, "hit_any"),
        "mean_target_recall": mean(rows, "target_recall"),
        "mean_oracle_path_fraction": mean(rows, "oracle_path_fraction"),
        "mean_selected_count": mean(rows, "selected_count"),
        "mean_tokens_used": mean(rows, "tokens_used"),
        "mixed_sources_rate": mean(rows, "mixed_sources"),
        "semantic_only_case_rate": (
            statistics.fmean(
                1.0 if row["semantic_only_count"] >= 1 else 0.0 for row in rows
            )
            if rows
            else 0.0
        ),
        "mean_semantic_only_count": mean(rows, "semantic_only_count"),
        "mrr": (
            statistics.fmean(
                0.0
                if row["first_relevant_rank"] is None
                else 1.0 / float(row["first_relevant_rank"])
                for row in rows
            )
            if rows
            else 0.0
        ),
        "median_first_relevant_rank_on_hits": (
            statistics.median(first_ranks) if first_ranks else None
        ),
        "within_budget": all(row["within_budget"] for row in rows),
    }


def validate_records(
    cases: list[dict[str, Any]],
    records: list[dict[str, Any]],
    arms: list[str],
) -> None:
    if any(not case["gold"] for case in cases):
        raise AssertionError("empty oracle set")
    for row in records:
        if not row["within_budget"]:
            raise AssertionError(f"budget violation: {row['case_id']}/{row['arm']}")
        for item in row["selected"]:
            path = item["file"]
            if (
                Path(path).is_absolute()
                or "\\" in path
                or ".." in Path(path).parts
            ):
                raise AssertionError(f"noncanonical path: {path}")
    lookup = {
        (row["case_id"], row["arm"], row["budget"]): {
            item["file"] for item in row["selected"]
        }
        for row in records
    }
    for case in cases:
        for arm in arms:
            selected_2k = lookup[(case["id"], arm, 2_000)]
            selected_4k = lookup[(case["id"], arm, 4_000)]
            selected_8k = lookup[(case["id"], arm, 8_000)]
            if not (selected_2k <= selected_4k <= selected_8k):
                raise AssertionError(
                    f"non-nested budget selections: {case['id']}/{arm}"
                )


def gate_decision(
    summary: list[dict[str, Any]],
    records: list[dict[str, Any]],
    *,
    fused_arm: str,
    graph_arm: str,
    naive_arm: str,
) -> dict[str, Any]:
    lookup = {
        (row["cohort"], row["arm"], row["budget"]): row for row in summary
    }
    checks = []
    for cohort in ("dependency", "test"):
        fused = lookup[(cohort, fused_arm, 4_000)]
        graph = lookup[(cohort, graph_arm, 4_000)]
        naive = lookup[(cohort, naive_arm, 4_000)]
        case_rows = {
            (row["case_id"], row["arm"]): row
            for row in records
            if row["cohort"] == cohort
            and row["budget"] == 4_000
            and row["arm"] in (fused_arm, graph_arm)
        }
        lost_hits = sorted(
            case_id
            for case_id, arm in case_rows
            if arm == graph_arm
            and case_rows[(case_id, graph_arm)]["hit_any"]
            and not case_rows[(case_id, fused_arm)]["hit_any"]
        )
        pareto_values = (
            (
                fused["hit_any_rate"],
                naive["hit_any_rate"],
            ),
            (
                fused["mean_target_recall"],
                naive["mean_target_recall"],
            ),
            (
                fused["semantic_only_case_rate"],
                naive["semantic_only_case_rate"],
            ),
        )
        pareto_nonworse = all(left >= right for left, right in pareto_values)
        pareto_strict = any(left > right for left, right in pareto_values)
        checks.extend(
            [
                {
                    "name": f"{cohort}: lose zero deployed-graph case hits",
                    "passed": not lost_hits,
                    "observed": (
                        "none" if not lost_hits else ", ".join(lost_hits)
                    ),
                },
                {
                    "name": f"{cohort}: include semantic-only evidence in >=90% cases",
                    "passed": fused["semantic_only_case_rate"] >= 0.90,
                    "observed": f"{fused['semantic_only_case_rate']:.1%}",
                },
                {
                    "name": f"{cohort}: no lower hit-any than deployed naive",
                    "passed": fused["hit_any_rate"] >= naive["hit_any_rate"],
                    "observed": (
                        f"{fused['hit_any_n']}/{fused['n']} vs "
                        f"{naive['hit_any_n']}/{naive['n']}"
                    ),
                },
                {
                    "name": f"{cohort}: all contexts stay within budget",
                    "passed": fused["within_budget"],
                    "observed": str(fused["within_budget"]).lower(),
                },
                {
                    "name": f"{cohort}: Pareto-dominate deployed naive",
                    "passed": pareto_nonworse and pareto_strict,
                    "observed": (
                        f"hit {fused['hit_any_rate']:.1%}/"
                        f"{naive['hit_any_rate']:.1%}; recall "
                        f"{fused['mean_target_recall']:.1%}/"
                        f"{naive['mean_target_recall']:.1%}; semantic-only "
                        f"{fused['semantic_only_case_rate']:.1%}/"
                        f"{naive['semantic_only_case_rate']:.1%}"
                    ),
                },
            ]
        )
    return {
        "budget": 4_000,
        "fused_arm": fused_arm,
        "graph_comparator": graph_arm,
        "naive_comparator": naive_arm,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def markdown_report(
    cases: list[dict[str, Any]],
    arms: list[str],
    summary: list[dict[str, Any]],
    records: list[dict[str, Any]],
    gate: dict[str, Any],
    unavailable: list[dict[str, str]],
) -> str:
    lines = [
        "# Budgeted graph + semantic retrieval: zero-cost gate",
        "",
        "**Status:** exploratory development result; not confirmatory and not "
        "thesis-quotable as independent resolver validation.",
        "",
        f"- Cases: {len(cases)} "
        f"({sum(c['cohort'] == 'dependency' for c in cases)} dependency, "
        f"{sum(c['cohort'] == 'test' for c in cases)} test)",
        "- API/model cost: $0",
        "- Semantic query: first indexed changed-file chunk embedding (proxy)",
        "- Resolver warning: resolved arms reuse the oracle-generating resolver",
        "",
        "## Go/no-go decision",
        "",
        f"**{'PASS' if gate['passed'] else 'NO-GO'}** for "
        f"`{gate['fused_arm']}` at the 4,000-token development budget.",
        "",
        "| Check | Result | Observed |",
        "|---|:---:|---:|",
    ]
    for check in gate["checks"]:
        lines.append(
            f"| {check['name']} | {'pass' if check['passed'] else 'fail'} "
            f"| {check['observed']} |"
        )

    for cohort in ("dependency", "test", "all"):
        lines.extend(
            [
                "",
                (
                    "## All cohort (descriptive only)"
                    if cohort == "all"
                    else f"## {cohort.capitalize()} cohort"
                ),
                "",
                "| Arm | Budget | Hit-any | Mean target recall | Oracle-path fraction | "
                "Mixed-source cases | Semantic-only cases | Mean tokens |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        lookup = {
            (row["arm"], row["budget"]): row
            for row in summary
            if row["cohort"] == cohort
        }
        for arm in arms:
            for budget in BUDGETS:
                row = lookup[(arm, budget)]
                lines.append(
                    f"| `{arm}` | {budget:,} | "
                    f"{row['hit_any_n']}/{row['n']} ({row['hit_any_rate']:.1%}) | "
                    f"{row['mean_target_recall']:.1%} | "
                    f"{row['mean_oracle_path_fraction']:.1%} | "
                    f"{row['mixed_sources_rate']:.1%} | "
                    f"{row['semantic_only_case_rate']:.1%} | "
                    f"{row['mean_tokens_used']:.0f} |"
                )

    lines.extend(
        [
            "",
            "## Structural cohort at 4k by repository and band",
            "",
            "| Group | Arm | Hit-any | Macro recall | Semantic-only cases |",
            "|---|---|---:|---:|---:|",
        ]
    )
    structural = [
        row
        for row in records
        if row["cohort"] == "dependency"
        and row["budget"] == 4_000
        and row["arm"] in ("deployed_graph", "deployed_naive", "deployed_rrf")
    ]
    for dimension in ("repo", "band"):
        values = sorted({row[dimension] for row in structural})
        for value in values:
            for arm in ("deployed_graph", "deployed_naive", "deployed_rrf"):
                rows = [
                    row
                    for row in structural
                    if row[dimension] == value and row["arm"] == arm
                ]
                lines.append(
                    f"| {dimension}={value} | `{arm}` | "
                    f"{sum(int(row['hit_any']) for row in rows)}/{len(rows)} | "
                    f"{mean(rows, 'target_recall'):.1%} | "
                    f"{statistics.fmean(1.0 if row['semantic_only_count'] else 0.0 for row in rows):.1%} |"
                )

    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "1. All `resolved_*` arms are packing/fusion upper "
            "bounds because the same resolver produced the oracle labels.",
            "2. `rag_proxy` reuses a saved changed-file chunk vector; it is not "
            "the deployed full-prefix query embedding.",
            "3. Hit-any measures evidence availability, not review correctness.",
            "4. A pass permits only a pre-registered held-out generation test.",
        ]
    )
    if unavailable:
        lines.extend(["", "## Missing retrieval inputs", ""])
        for item in unavailable:
            lines.append(f"- `{item['case_id']}`: {item['reason']}")
    lines.append("")
    return "\n".join(lines)


def source_files() -> list[Path]:
    paths = [
        EXP2 / "out/manifest.json",
        TEST_EXP / "out/manifest.json",
        EXP2 / "harness/analyzers.py",
        ROOT / "scripts/expand_dataset.py",
    ]
    for repo in SCOPES:
        paths.extend(
            [
                EXP2 / "out/joern" / f"edges_{repo}.json",
                EXP2 / "out/rag" / repo / "index_meta.json",
                EXP2 / "out/rag" / repo / "chunks.json",
                EXP2 / "out/rag" / repo / "embeddings.json",
            ]
        )
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite files for the selected result stem",
    )
    parser.add_argument(
        "--result-stem",
        default="RESULTS",
        help="output stem under the dated experiment folder (default: RESULTS)",
    )
    args = parser.parse_args()
    if not args.result_stem.replace("_", "").isalnum():
        raise SystemExit("--result-stem must contain only letters, digits, underscores")
    results_json = OUT_DIR / f"{args.result_stem}.json"
    results_md = OUT_DIR / f"{args.result_stem}.md"
    output_exists = (results_json.exists(), results_md.exists())
    if output_exists[0] != output_exists[1] and not args.force:
        raise SystemExit(
            f"partial output state for {args.result_stem}; "
            "inspect it and use --force to replace"
        )
    if all(output_exists) and not args.force:
        print(
            f"{args.result_stem} already exists under {OUT_DIR}; "
            "use --force to recompute"
        )
        return

    missing = [path for path in source_files() if not path.exists()]
    if missing:
        raise SystemExit(
            "missing required input(s):\n" + "\n".join(str(path) for path in missing)
        )

    cases = load_cases()
    graphs = GraphSources()
    records: list[dict[str, Any]] = []
    unavailable: list[dict[str, str]] = []
    arms = [
        "deployed_graph",
        "resolved_graph",
        "rag_proxy",
        "deployed_naive",
        "deployed_rrf",
        "deployed_compact",
        "resolved_naive",
        "resolved_rrf",
        "resolved_compact",
    ]

    done = 0
    for repo in sorted({case["repo"] for case in cases}):
        print(f"[{repo}] loading saved RAG index ...", flush=True)
        rag_proxy = SavedRagProxy(repo)
        for case in [case for case in cases if case["repo"] == repo]:
            # Retrieval receives only query-side fields. Gold labels, evidence,
            # fanout, band, edge type and ground-truth prose stay evaluation-only.
            retrieval_case = {
                key: case[key]
                for key in ("id", "repo", "language", "edit_file", "symbol")
            }
            deployed = graphs.deployed(retrieval_case, case["cohort"])
            resolved = graphs.resolved(retrieval_case, case["cohort"])
            rag = rag_proxy.rank(retrieval_case["edit_file"])

            rankings = {
                "deployed_graph": deployed,
                "resolved_graph": resolved,
                "rag_proxy": rag,
                "deployed_naive": dedupe_order(deployed + rag),
                "deployed_rrf": reciprocal_rank_fusion(deployed, rag),
                "deployed_compact": compact_fusion(deployed, rag),
                "resolved_naive": dedupe_order(resolved + rag),
                "resolved_rrf": reciprocal_rank_fusion(resolved, rag),
                "resolved_compact": compact_fusion(resolved, rag),
            }
            for arm in arms:
                for budget in BUDGETS:
                    records.append(
                        evaluate_packed(case, arm, rankings[arm], budget)
                    )
            done += 1
            if done % 10 == 0 or done == len(cases):
                print(f"evaluated {done}/{len(cases)} cases", flush=True)
        del rag_proxy

    summary = [
        aggregate(records, cohort, arm, budget)
        for cohort in ("dependency", "test", "all")
        for arm in arms
        for budget in BUDGETS
    ]
    validate_records(cases, records, arms)
    gate = gate_decision(
        summary,
        records,
        fused_arm="deployed_rrf",
        graph_arm="deployed_graph",
        naive_arm="deployed_naive",
    )
    output = {
        "experiment": "2026-09-19_budgeted_fusion_retrieval",
        "status": "exploratory-development-only",
        "cost_usd": 0,
        "budgets_approx_context_tokens": list(BUDGETS),
        "token_estimator": "ceil(characters/4)",
        "rrf_k": RRF_K,
        "result_stem": args.result_stem,
        "arms": arms,
        "case_counts": {
            "all": len(cases),
            "dependency": sum(c["cohort"] == "dependency" for c in cases),
            "test": sum(c["cohort"] == "test" for c in cases),
        },
        "validity": {
            "resolver_circularity": (
                "resolved arms reconstruct the same resolver family that produced "
                "the oracle labels; packing/fusion upper bound only"
            ),
            "rag_proxy": (
                "uses first indexed changed-file chunk embedding instead of a new "
                "full-prefix query embedding"
            ),
            "reused_stimuli": True,
        },
        "input_fingerprints": [fingerprint(path) for path in source_files()],
        "gate": gate,
        "summary": summary,
        "unavailable": unavailable,
        "records": records,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results_json.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    results_md.write_text(
        markdown_report(cases, arms, summary, records, gate, unavailable)
    )
    print(
        f"{'PASS' if gate['passed'] else 'NO-GO'}: "
        f"wrote {results_json.relative_to(ROOT)} and "
        f"{results_md.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
