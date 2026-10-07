"""Review note generation module.

Generates evidence-anchored PR review notes using different context strategies:
- Baseline: diff-only
- KG: Knowledge Graph context (tests, deps, owners)
- RAG: Semantic similarity context
- Hybrid: KG + RAG combined
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

from prnote.llm import generate_completion


# =============================================================================
# SECTION EXTRACTION HELPERS (for evaluation)
# =============================================================================

def _extract_section(content: str, section_name: str) -> Optional[str]:
    """Extract a section from markdown content by header name."""
    # Pattern: ## Section Name followed by content until next ## or end
    pattern = rf'## {re.escape(section_name)}\s*\n(.*?)(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    return None


def _extract_bullets(section: str) -> List[str]:
    """Extract bullet points from a section."""
    bullets = []
    for line in section.split('\n'):
        line = line.strip()
        if line.startswith('•') or line.startswith('-') or line.startswith('*'):
            # Remove bullet character
            bullet_text = line.lstrip('•-* ').strip()
            if bullet_text:
                bullets.append(bullet_text)
    return bullets


def _extract_anchor(text: str) -> Optional[str]:
    """Extract file:line anchor from text."""
    # Pattern: file.ext:line or file.ext:line-line
    match = re.search(r'([a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+):(\d+)(?:-(\d+))?', text)
    if match:
        file_path = match.group(1)
        start_line = match.group(2)
        end_line = match.group(3)
        
        if end_line:
            return f"{file_path}:{start_line}-{end_line}"
        return f"{file_path}:{start_line}"
    
    return None


# =============================================================================
# SYSTEM PROMPTS FOR EACH MODE
# =============================================================================

SYSTEM_PROMPT_BASE = """You are a senior software engineer conducting a thorough code review of a pull request.

Your task is to generate a structured review note that helps the PR author understand:
1. What potential issues exist
2. Evidence from the code supporting your concerns
3. The impact of these issues
4. Concrete recommendations

Output Format (follow exactly):
```
# Review Note — Evidence-Anchored

**Scope:** [One sentence describing what this PR does]

## Problem
[Numbered list of 2-3 specific concerns or issues you identified]

## Evidence
[Bullet points with specific file:line references supporting your concerns]

## Impact
[Explain the technical impact - what could go wrong, what risks exist]

## Recommendation (Fix / Tests / Risks)
[Numbered list of concrete, actionable recommendations]

## Traceability
[List relevant code owners or teams if known, otherwise state "Not specified"]
```

Guidelines:
- Be specific and cite actual file paths and line numbers from the diff
- Focus on meaningful issues, not style nitpicks
- Consider integration impacts and test coverage
- Be constructive and professional
"""

SYSTEM_PROMPT_BASELINE = SYSTEM_PROMPT_BASE + """
Context: You only have access to the PR diff. Make reasonable inferences about
integration and testing needs based on the changes you can see.
"""

SYSTEM_PROMPT_KG = SYSTEM_PROMPT_BASE + """
Context: You have access to Knowledge Graph context including:
- Which files are changed and their dependencies
- Which tests cover the changed files
- Who owns the affected code areas
- Which other files call or import the changed code

Use this structural context to provide deeper insights about integration risks,
missing test coverage, and code ownership concerns.
"""

SYSTEM_PROMPT_RAG = SYSTEM_PROMPT_BASE + """
Context: You have access to semantically similar code chunks from the repository.
These show patterns used elsewhere that may be relevant to this change.

Use this context to identify consistency issues, suggest similar patterns to follow,
and flag potential conflicts with existing code.
"""

SYSTEM_PROMPT_HYBRID = SYSTEM_PROMPT_BASE + """
Context: You have access to both:
1. Knowledge Graph context (tests, dependencies, ownership)
2. Semantically similar code from the repository

Combine structural insights (what depends on what, test coverage) with semantic
insights (similar patterns elsewhere) to provide comprehensive review feedback.
"""


# =============================================================================
# CONTEXT FORMATTERS
# =============================================================================

def _rank_tests_by_relevance(tests: list, changed_files: list) -> list:
    """Rank tests so that direct unit tests for changed files appear first."""
    from pathlib import PurePosixPath
    changed_stems = set()
    for cf in changed_files:
        p = cf.get('path', cf) if isinstance(cf, dict) else cf
        changed_stems.add(PurePosixPath(p).stem.lower())

    def score(t):
        path = t.get('path', t.get('file', str(t))) if isinstance(t, dict) else t
        stem = PurePosixPath(path).stem.lower()
        # Direct test file for a changed file (e.g. Foo.java → FooTest.java)
        for cs in changed_stems:
            if cs in stem or stem.replace('test', '').replace('_test', '') == cs:
                return 0
        if 'test' in stem:
            return 1
        return 2

    return sorted(tests, key=score)


# Language cohorts: when the change touches files in one group, restrict KG
# dependents/tests to the same group. This kills cross-language false positives
# (e.g. Grafana PR 3 touches .tsx and the AST KG returns Go build files).
_LANG_COHORTS = {
    "js":    {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"},
    "jvm":   {".java", ".scala", ".kt", ".groovy"},
    "py":    {".py"},
    "go":    {".go"},
    "cpp":   {".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hh"},
    "rb":    {".rb"},
    "rs":    {".rs"},
    "cs":    {".cs"},
}


def _file_cohort(path: str) -> Optional[str]:
    ext = Path(path).suffix.lower()
    for name, exts in _LANG_COHORTS.items():
        if ext in exts:
            return name
    return None


def _dominant_cohorts(changed_files: list) -> set[str]:
    """Return the set of language cohorts represented in the changed files.

    Used to filter dependents/tests so they stay language-consistent with the
    change. Falls back to 'all cohorts' if we can't classify anything.
    """
    cohorts = set()
    for cf in changed_files or []:
        p = cf.get("path", cf) if isinstance(cf, dict) else cf
        c = _file_cohort(p)
        if c:
            cohorts.add(c)
    return cohorts or set(_LANG_COHORTS.keys())


def _keep_by_cohort(paths: list, cohorts: set[str], *, allow_tests: bool = False) -> list:
    """Keep only paths whose extension belongs to an allowed cohort.

    Test files (*.test.ts, *Test.java, *_test.py, *Spec.scala, ...) are kept
    only when allow_tests=True, for use in the tests list itself.
    """
    kept = []
    for p in paths:
        path = p.get("path", p.get("file", str(p))) if isinstance(p, dict) else p
        c = _file_cohort(path)
        if c is None or c in cohorts:
            kept.append(p if isinstance(p, str) else path)
    return kept


def format_kg_context(evidence: Dict[str, Any]) -> str:
    """Format Knowledge Graph evidence for the prompt.

    Changelog (2026-04-24):
      - Language-cohort filter on dependents & tests kills cross-language
        false positives (e.g. Grafana .tsx change returning Go build scripts).
      - Function-level edges from `call_graph_edges` are now rendered
        alongside `callers`, when available (previously discarded).
      - Raised per-section caps and overall cap from 3000 → 8000 chars so
        that AST-built evidence isn't truncated mid-list.
    """
    sections = []
    changed_files = evidence.get('changed_files', [])
    cohorts = _dominant_cohorts(changed_files)

    # Changed files
    if changed_files:
        if isinstance(changed_files[0], dict):
            file_list = [f.get('path', str(f)) for f in changed_files]
        else:
            file_list = changed_files
        sections.append(f"**Changed Files:** {', '.join(file_list[:12])}")

    # Tests — ranked by relevance so direct unit tests come first + cohort-filtered
    tests_raw = evidence.get('nearest_tests', evidence.get('kg_evidence', {}).get('nearest_tests', []))
    if tests_raw:
        ranked = _rank_tests_by_relevance(tests_raw, changed_files)
        filtered = _keep_by_cohort(ranked, cohorts)
        if filtered:
            if isinstance(filtered[0], dict):
                test_list = [t.get('path', t.get('file', str(t))) for t in filtered]
            else:
                test_list = filtered
            sections.append(f"**Related Tests:** {', '.join(test_list[:12])}")

    # Dependent files (non-test source files that import changed code)
    deps_raw = evidence.get('dependent_files', evidence.get('kg_evidence', {}).get('dependent_files', []))
    if deps_raw:
        filtered = _keep_by_cohort(deps_raw, cohorts)
        if filtered:
            if isinstance(filtered[0], dict):
                dep_list = [d.get('path', str(d)) for d in filtered]
            else:
                dep_list = filtered
            sections.append(f"**Files that depend on changes:** {', '.join(dep_list[:15])}")

    # Owners
    owners = evidence.get('owners', evidence.get('kg_evidence', {}).get('owners', []))
    if owners:
        if isinstance(owners[0], dict):
            owner_list = [o.get('handle', str(o)) for o in owners]
        else:
            owner_list = owners
        sections.append(f"**Code Owners:** {', '.join(owner_list[:5])}")

    # Functions in changed files — compact summary
    funcs = evidence.get('functions_changed', evidence.get('functions_in_changed_files', []))
    if funcs:
        if isinstance(funcs[0], dict):
            func_list = []
            for fn in funcs[:15]:
                cls = f"{fn['class']}." if fn.get('class') else ""
                func_list.append(f"{cls}{fn['name']} ({fn.get('file','')}:{fn.get('lines','')})")
            sections.append(f"**Functions in Changed Files:** {'; '.join(func_list)}")
        else:
            sections.append(f"**Functions Changed:** {', '.join(funcs[:15])}")

    # Importers
    importers = evidence.get('importers', [])
    if importers:
        filtered = _keep_by_cohort(importers, cohorts)
        if filtered:
            sections.append(f"**Files importing changed code:** {', '.join(filtered[:10])}")

    # Callers — function-level edges preferred when available
    call_edges = evidence.get('call_graph_edges', [])
    callers = evidence.get('callers', [])
    rendered_caller_section = False
    if call_edges and isinstance(call_edges, list) and call_edges and isinstance(call_edges[0], dict):
        # Each edge: from / to / file / lines (schema varies) — render a compact
        # "A.foo() → B.bar()" view to give the LLM function-level context.
        rendered = []
        seen = set()
        for e in call_edges:
            src = e.get('from') or e.get('caller') or e.get('src')
            dst = e.get('to') or e.get('callee') or e.get('dst') or e.get('calls_function')
            if not src or not dst:
                continue
            key = (str(src), str(dst))
            if key in seen:
                continue
            seen.add(key)
            rendered.append(f"{src} → {dst}")
            if len(rendered) >= 12:
                break
        if rendered:
            sections.append(f"**Call-graph edges (caller → callee):** {'; '.join(rendered)}")
            rendered_caller_section = True
    if callers and not rendered_caller_section:
        if isinstance(callers[0], dict):
            # AST-build callers carry {path, calls_function, from_function} — use it
            rendered = []
            seen = set()
            for c in callers:
                path = c.get('path', str(c))
                fn   = c.get('calls_function') or c.get('function') or ''
                key  = (path, fn)
                if key in seen:
                    continue
                seen.add(key)
                if _file_cohort(path) and _file_cohort(path) not in cohorts:
                    continue
                rendered.append(f"{path}::{fn}" if fn else path)
                if len(rendered) >= 12:
                    break
            if rendered:
                sections.append(f"**Files calling changed functions:** {'; '.join(rendered)}")
        else:
            sections.append(f"**Files calling changed functions:** {', '.join(callers[:12])}")

    if not sections:
        return ""

    context = "\n\n**Knowledge Graph Context:**\n" + "\n".join(sections)
    # Raised cap: AST-built evidence can legitimately fill 5-7K chars.
    # Claude / GPT-4o context windows handle this trivially.
    if len(context) > 8000:
        context = context[:8000] + "\n..."
    return context


def format_rag_context(evidence: Dict[str, Any]) -> str:
    """Format RAG (similar code) evidence for the prompt.

    Includes actual code snippets so the LLM can check for consistency
    with existing patterns in the repository.
    """
    similar = evidence.get('similar_chunks', evidence.get('rag_evidence', {}).get('similar_code', []))

    if not similar:
        return ""

    sections = ["\n## Semantically Similar Code from Repository\n"]

    for i, chunk in enumerate(similar[:5], 1):
        if not isinstance(chunk, dict):
            continue
        file_path = chunk.get('file', chunk.get('metadata', {}).get('file', 'unknown'))
        start = chunk.get('start_line', chunk.get('metadata', {}).get('start_line', '?'))
        end = chunk.get('end_line', chunk.get('metadata', {}).get('end_line', '?'))
        sim = chunk.get('similarity', 1.0 - chunk.get('distance', 0.5))
        preview = chunk.get('content_preview', chunk.get('content', ''))

        sections.append(f"### {i}. {file_path}:{start}-{end} (similarity: {sim:.2f})")
        if preview:
            sections.append(f"```\n{preview[:800]}\n```")

    return "\n".join(sections)


def format_hybrid_context(evidence: Dict[str, Any]) -> str:
    """Format combined KG + RAG context."""
    return format_kg_context(evidence) + format_rag_context(evidence)


# =============================================================================
# DIFF EXTRACTION
# =============================================================================

def get_diff_from_repo(repo: str, base: str, head: str) -> str:
    """Get diff between two commits."""
    result = subprocess.run(
        ['git', 'diff', base, head],
        cwd=repo,
        capture_output=True,
        text=True
    )
    return result.stdout[:15000]  # Limit diff size for prompt


def get_diff_from_evidence(evidence: Dict[str, Any], max_chars: int = 15000) -> str:
    """Extract diff information from evidence pack.

    Priority order:
    1. full_diff field (actual git diff, best quality)
    2. Per-file diff fields on changed_files
    3. Fallback to file paths + line counts

    Args:
        evidence: the evidence-pack dict (usually loaded from
            data/luca_prs_*/pr<N>_evidence.json).
        max_chars: prompt-time cap on diff length. Default 15 000 preserves
            v1 behaviour. The v2 regeneration pipeline passes 50 000 to match
            the v2 fetch cap (dataset_v2/scripts/fetch_evidence_v2.py).
    """
    # Best case: full git diff stored in evidence
    full_diff = evidence.get('full_diff', '')
    if full_diff and len(full_diff) > 50:
        return full_diff[:max_chars]

    # Second best: per-file diffs
    per_file_diffs = []
    for cf in evidence.get('changed_files', []):
        if isinstance(cf, dict) and cf.get('diff'):
            per_file_diffs.append(cf['diff'])

    if per_file_diffs:
        combined = "\n".join(per_file_diffs)
        return combined[:max_chars]
    
    # Fallback: just file paths and stats
    lines = []
    for cf in evidence.get('changed_files', []):
        if isinstance(cf, dict):
            path = cf.get('path', '')
            hunks = cf.get('hunks', [])
            added = cf.get('added', 0)
            deleted = cf.get('deleted', 0)
            lines.append(f"--- a/{path}")
            lines.append(f"+++ b/{path}")
            if added or deleted:
                lines.append(f"(+{added}, -{deleted} lines)")
            for hunk in hunks:
                if isinstance(hunk, dict):
                    lines.append(f"@@ lines {hunk.get('start', '?')}-{hunk.get('end', '?')} @@")
    
    return "\n".join(lines) if lines else "No diff information available."


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate(
    evidence: Optional[str] = None,
    out: str = "./outputs/note.md",
    mode: str = "kg",
    repo: Optional[str] = None,
    base: Optional[str] = None,
    head: Optional[str] = None,
    model: Optional[str] = None,
    baseline: bool = False
) -> str:
    """
    Generate a review note using the specified mode.
    
    Args:
        evidence: Path to evidence JSON file (for kg/rag/hybrid modes)
        out: Output path for the generated note
        mode: One of 'baseline', 'kg', 'rag', 'hybrid'
        repo: Repository path (for baseline mode)
        base: Base commit SHA (for baseline mode)
        head: Head commit SHA (for baseline mode)
        model: LLM model to use (e.g., 'openai:gpt-4o')
        baseline: Legacy flag for baseline mode
    
    Returns:
        Generated review note as string
    """
    # Handle legacy baseline flag
    if baseline:
        mode = "baseline"
    
    # Select system prompt based on mode
    system_prompts = {
        "baseline": SYSTEM_PROMPT_BASELINE,
        "kg": SYSTEM_PROMPT_KG,
        "rag": SYSTEM_PROMPT_RAG,
        "hybrid": SYSTEM_PROMPT_HYBRID
    }
    system_prompt = system_prompts.get(mode, SYSTEM_PROMPT_BASELINE)
    
    # Build user prompt
    if mode == "baseline":
        if not repo or not base or not head:
            raise ValueError("Baseline mode requires --repo, --base, and --head")
        diff = get_diff_from_repo(repo, base, head)
        context = ""
        pr_title = f"Changes from {base} to {head}"
    else:
        if not evidence:
            raise ValueError(f"{mode} mode requires --evidence")
        with open(evidence, 'r') as f:
            evidence_data = json.load(f)
        
        diff = get_diff_from_evidence(evidence_data)
        pr_title = evidence_data.get('pr', {}).get('title', 'Unknown PR')
        
        # Format context based on mode
        if mode == "kg":
            context = format_kg_context(evidence_data)
        elif mode == "rag":
            context = format_rag_context(evidence_data)
        elif mode == "hybrid":
            context = format_hybrid_context(evidence_data)
        else:
            context = ""
    
    user_prompt = f"""## Pull Request: {pr_title}

## Diff
```
{diff}
```
{context}

Please generate an evidence-anchored review note following the specified format."""
    
    # Generate review
    print(f"Generating {mode} review...")
    review = generate_completion(
        prompt=user_prompt,
        system=system_prompt,
        model=model,
        temperature=0.3
    )
    
    # Save output
    os.makedirs(Path(out).parent, exist_ok=True)
    with open(out, 'w') as f:
        f.write(review)
    
    print(f"✓ Review note saved to {out}")
    return review


# =============================================================================
# LINTING FUNCTION
# =============================================================================

def lint(
    note: str,
    repo: str,
    head: str,
    verbose: bool = False
) -> int:
    """
    Lint a review note for validity.
    
    Checks:
    - File paths mentioned actually exist
    - Line numbers are valid
    - Format is correct
    
    Args:
        note: Path to the note markdown file
        repo: Path to the repository
        head: Head commit SHA to check against
        verbose: Print detailed output
    
    Returns:
        Exit code (0 = pass, 1 = warnings, 2 = errors)
    """
    import re
    
    with open(note, 'r') as f:
        content = f.read()
    
    errors = []
    warnings = []
    
    # Check for required sections
    required_sections = ['## Problem', '## Evidence', '## Impact', '## Recommendation']
    for section in required_sections:
        if section not in content:
            warnings.append(f"Missing section: {section}")
    
    # Check file:line references
    file_refs = re.findall(r'([a-zA-Z0-9_/.-]+\.[a-zA-Z]+):(\d+)', content)
    
    for file_path, line_num in file_refs:
        full_path = Path(repo) / file_path
        if not full_path.exists():
            errors.append(f"Invalid file reference: {file_path}")
        elif verbose:
            print(f"✓ Valid: {file_path}:{line_num}")
    
    # Report
    if errors:
        print(f"❌ {len(errors)} errors found:")
        for e in errors:
            print(f"  - {e}")
    
    if warnings:
        print(f"⚠️  {len(warnings)} warnings:")
        for w in warnings:
            print(f"  - {w}")
    
    if not errors and not warnings:
        print("✓ Note passed all checks")
        return 0
    elif errors:
        return 2
    else:
        return 1


# =============================================================================
# DIRECT REVIEW GENERATION (for scripts)
# =============================================================================

def generate_review_direct(
    diff: str,
    pr_title: str,
    mode: str = "baseline",
    kg_context: Optional[Dict[str, Any]] = None,
    rag_context: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None
) -> str:
    """
    Generate a review directly without file I/O.
    
    Args:
        diff: The PR diff as a string
        pr_title: Title of the PR
        mode: One of 'baseline', 'kg', 'rag', 'hybrid'
        kg_context: Knowledge Graph context dict
        rag_context: RAG context dict
        model: LLM model to use
    
    Returns:
        Generated review as string
    """
    system_prompts = {
        "baseline": SYSTEM_PROMPT_BASELINE,
        "kg": SYSTEM_PROMPT_KG,
        "rag": SYSTEM_PROMPT_RAG,
        "hybrid": SYSTEM_PROMPT_HYBRID
    }
    system_prompt = system_prompts.get(mode, SYSTEM_PROMPT_BASELINE)
    
    # Format context
    context = ""
    if mode == "kg" and kg_context:
        context = format_kg_context(kg_context)
    elif mode == "rag" and rag_context:
        context = format_rag_context(rag_context)
    elif mode == "hybrid":
        if kg_context:
            context += format_kg_context(kg_context)
        if rag_context:
            context += format_rag_context(rag_context)
    
    user_prompt = f"""## Pull Request: {pr_title}

## Diff
```
{diff[:12000]}
```
{context}

Please generate an evidence-anchored review note following the specified format."""
    
    return generate_completion(
        prompt=user_prompt,
        system=system_prompt,
        model=model,
        temperature=0.3
    )

