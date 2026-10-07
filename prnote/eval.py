"""Evaluation metrics for review notes."""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from prnote.utils import validate_file_line
from prnote.note import _extract_section, _extract_bullets, _extract_anchor


def quick(
    repo: str,
    notes: str,
    out: str,
    head: Optional[str] = None
) -> None:
    """
    Compute quick evaluation metrics for notes.
    
    Args:
        repo: Path to repository
        notes: Directory containing note files (*.md)
        out: Output path for metrics JSON
        head: Head commit SHA to validate against
    """
    notes_dir = Path(notes)
    note_files = list(notes_dir.glob("*.md"))
    
    if not note_files:
        print(f"No note files found in {notes}")
        return
    
    print(f"Evaluating {len(note_files)} note(s)...")
    
    results = {}
    
    for note_file in note_files:
        note_name = note_file.stem
        metrics = compute_metrics(str(note_file), repo, head)
        results[note_name] = metrics
        
        print(f"\n{note_name}:")
        print(f"  Anchor validity: {metrics['anchor_validity']:.2f}")
        print(f"  Coverage score: {metrics['coverage_score']}/5")
        print(f"  Interrogative rate: {metrics['interrogative_rate']:.1%}")
        print(f"  Evidence bullets: {metrics['evidence_bullets']}")
    
    # Save results
    os.makedirs(Path(out).parent, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Metrics saved to {out}")
    
    # Summary
    if len(results) >= 2:
        print("\nComparison:")
        for name, metrics in results.items():
            status = "✓" if _passes_criteria(metrics) else "✗"
            print(f"  {status} {name}: "
                  f"validity={metrics['anchor_validity']:.2f}, "
                  f"coverage={metrics['coverage_score']}/5, "
                  f"questions={metrics['interrogative_rate']:.1%}")


def compute_metrics(note_path: str, repo: str, head: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute metrics for a single note.
    
    Returns:
        Dict with metrics:
        - anchor_validity: float (0-1)
        - coverage_score: int (0-5)
        - interrogative_rate: float (0-1)
        - evidence_bullets: int
        - valid_anchors: int
        - total_anchors: int
    """
    with open(note_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Anchor validity
    evidence_section = _extract_section(content, "Evidence")
    evidence_bullets = _extract_bullets(evidence_section) if evidence_section else []
    
    anchors = []
    for bullet in evidence_bullets:
        anchor = _extract_anchor(bullet)
        if anchor:
            anchors.append(anchor)
    
    valid_anchors = 0
    if head:
        for anchor in anchors:
            if validate_file_line(anchor, repo, head):
                valid_anchors += 1
    else:
        # If no head provided, assume all parsed anchors are valid
        valid_anchors = len(anchors)
    
    anchor_validity = valid_anchors / len(anchors) if anchors else 0.0
    
    # 2. Coverage score (0-5)
    sections_present = 0
    required_sections = ['Problem', 'Evidence', 'Impact', 'Recommendation', 'Traceability']
    
    for section in required_sections:
        if _extract_section(content, section):
            sections_present += 1
    
    coverage_score = sections_present
    
    # 3. Interrogative rate
    lines = content.split('\n')
    question_lines = sum(1 for line in lines if line.strip().endswith('?'))
    interrogative_rate = question_lines / len(lines) if lines else 0.0
    
    return {
        'anchor_validity': anchor_validity,
        'coverage_score': coverage_score,
        'interrogative_rate': interrogative_rate,
        'evidence_bullets': len(evidence_bullets),
        'valid_anchors': valid_anchors,
        'total_anchors': len(anchors)
    }


def _passes_criteria(metrics: Dict[str, Any]) -> bool:
    """Check if metrics pass POC criteria."""
    return (
        metrics['anchor_validity'] >= 0.90 and
        metrics['coverage_score'] >= 4 and
        metrics['interrogative_rate'] <= 0.10
    )


def compare(baseline_metrics: Dict[str, Any], kg_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare baseline vs KG metrics.
    
    Returns:
        Comparison dict with deltas and pass/fail
    """
    comparison = {
        'baseline': baseline_metrics,
        'kg': kg_metrics,
        'deltas': {
            'anchor_validity': kg_metrics['anchor_validity'] - baseline_metrics['anchor_validity'],
            'coverage_score': kg_metrics['coverage_score'] - baseline_metrics['coverage_score'],
            'interrogative_rate': kg_metrics['interrogative_rate'] - baseline_metrics['interrogative_rate']
        },
        'kg_passes': _passes_criteria(kg_metrics),
        'kg_better_or_equal_coverage': kg_metrics['coverage_score'] >= baseline_metrics['coverage_score']
    }
    
    # Overall pass
    comparison['overall_pass'] = (
        comparison['kg_passes'] and
        comparison['kg_better_or_equal_coverage']
    )
    
    return comparison










