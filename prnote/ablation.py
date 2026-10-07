"""Ablation study module for RQ2.1 - KG Feature importance analysis.

Provides configurations and utilities for systematically removing KG features
(tests, dependencies) from evidence packs and measuring the impact on review quality.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class AblationConfig:
    """Configuration for a single KG ablation experiment."""
    name: str
    description: str
    remove_tests: bool = False
    remove_dependencies: bool = False

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'remove_tests': self.remove_tests,
            'remove_dependencies': self.remove_dependencies,
        }


ABLATION_CONFIGS = [
    AblationConfig(
        name="full_kg",
        description="Full KG with all features (baseline for ablation)"
    ),
    AblationConfig(
        name="kg_no_tests",
        description="KG without test coverage information",
        remove_tests=True
    ),
    AblationConfig(
        name="kg_no_deps",
        description="KG without dependency/caller information",
        remove_dependencies=True
    ),
    AblationConfig(
        name="kg_minimal",
        description="Minimal KG (files + diff only, no tests/deps)",
        remove_tests=True,
        remove_dependencies=True
    ),
]

ALL_PR_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]

PRS_WITH_TESTS = [2, 3, 6, 8, 9, 10, 14, 15, 18, 19, 21, 22, 23, 24, 25, 26]
PRS_WITH_DEPS = [2, 3, 6, 7, 8, 9, 10, 11, 14, 15, 17, 18, 19, 21, 22, 23, 24, 25, 26]
PRS_WITH_BOTH = sorted(set(PRS_WITH_TESTS) & set(PRS_WITH_DEPS))

ABLATION_PR_FILTER: Dict[str, List[int]] = {
    "full_kg": ALL_PR_IDS,
    "kg_no_tests": PRS_WITH_TESTS,
    "kg_no_deps": PRS_WITH_DEPS,
    "kg_minimal": PRS_WITH_BOTH,
}


def get_config(name: str) -> AblationConfig:
    """Look up an ablation config by name."""
    for c in ABLATION_CONFIGS:
        if c.name == name:
            return c
    raise ValueError(f"Unknown ablation config: {name}")


def get_relevant_pr_ids(config_name: str) -> List[int]:
    """Return the PR IDs where this ablation is meaningful."""
    return ABLATION_PR_FILTER.get(config_name, ALL_PR_IDS)


def create_ablated_evidence(
    original_evidence_path: str,
    config: AblationConfig,
    output_path: str
) -> Dict[str, Any]:
    """
    Create an ablated evidence pack by removing specified KG features.

    Returns the ablated evidence dict (also saved to output_path).
    """
    with open(original_evidence_path, 'r', encoding='utf-8') as f:
        evidence = json.load(f)

    ablated = json.loads(json.dumps(evidence))

    if config.remove_tests:
        ablated['nearest_tests'] = []
        if 'kg_evidence' in ablated:
            ablated['kg_evidence']['nearest_tests'] = []

    if config.remove_dependencies:
        ablated['dependent_files'] = []
        if 'kg_evidence' in ablated:
            ablated['kg_evidence']['dependent_files'] = []

    ablated['_ablation'] = config.to_dict()

    os.makedirs(Path(output_path).parent, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ablated, f, indent=2)

    return ablated


def create_all_ablated_evidence(
    data_dir: str = "data/luca_prs_fixed",
    output_dir: str = "data/ablation"
) -> Dict[str, List[str]]:
    """
    Create ablated evidence packs for all non-baseline configs.

    Returns dict mapping config name -> list of output paths.
    """
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, List[str]] = {}

    for config in ABLATION_CONFIGS:
        if config.name == "full_kg":
            continue

        pr_ids = get_relevant_pr_ids(config.name)
        results[config.name] = []

        for pr_id in pr_ids:
            original_path = data_dir / f"pr{pr_id}_evidence.json"
            if not original_path.exists():
                print(f"  SKIP PR {pr_id}: evidence not found")
                continue

            ablated_path = output_dir / f"pr{pr_id}_{config.name}.json"
            create_ablated_evidence(str(original_path), config, str(ablated_path))
            results[config.name].append(str(ablated_path))

        print(f"  {config.name}: {len(results[config.name])} evidence packs created")

    return results
