"""Defect-injection operators, one per pre-registered band (pre-reg §4).

Each operator takes (scope, symbol/site info) and returns an edit:
  {"file": rel_path, "old": exact_text, "new": replacement}
or None if the operator does not apply cleanly (caller skips the target).
Operators are drawn from the mutation-testing literature (PIT/Major-style:
rename, signature change, return mutation, conditional-boundary,
check removal).
"""
from __future__ import annotations

import re
from pathlib import Path

SUFFIX = "Internal"   # rename suffix: plausible, not screaming "_RENAMED"


def _read(scope: Path, f: str) -> str:
    return (scope / f).read_text(errors="ignore")


def _unique(text: str, old: str) -> bool:
    return text.count(old) == 1


# --- S1: symbol rename (breaks importers) -----------------------------------
def s1_rename(scope: Path, sym: dict, language: str):
    text = _read(scope, sym["file"])
    line = sym["line"]
    name = sym["name"]
    if not _unique(text, line) or name not in line:
        return None
    new_name = name + SUFFIX if not name.startswith("_") else name + "_internal"
    new_line = line.replace(name, new_name, 1)
    return {"file": sym["file"], "old": line, "new": new_line,
            "detail": f"renamed {sym['kind']} {name} -> {new_name}"}


# --- S2: signature change (breaks callers) ----------------------------------
def s2_signature(scope: Path, sym: dict, language: str):
    text = _read(scope, sym["file"])
    line = sym["line"]
    if not _unique(text, line):
        return None
    if language == "python":
        m = re.match(r"^(\s*def\s+\w+\()(.*)$", line)
        if not m:
            return None
        new_line = m.group(1) + "required_ctx, " + m.group(2)
        detail = "added new leading required parameter `required_ctx`"
    elif language == "java":
        m = re.match(r"^(.*\b\w+\s*\()(.*)$", line)
        if not m or "(" not in line:
            return None
        new_line = m.group(1) + "final RequiredContext requiredCtx, " + m.group(2)
        detail = "added new leading required parameter `RequiredContext requiredCtx`"
    else:  # typescript
        m = re.match(r"^(.*\bfunction\s+\w+\s*(?:<[^(]*?>)?\()(.*)$", line)
        if not m:
            return None
        new_line = m.group(1) + "requiredCtx: RequiredContext, " + m.group(2)
        detail = "added new leading required parameter `requiredCtx`"
    return {"file": sym["file"], "old": line, "new": new_line, "detail": detail}


# --- S3: return-contract change (breaks consumers) ---------------------------
def s3_return(scope: Path, sym: dict, language: str):
    """Wrap the function's return value so consumers' unpacking/typing breaks:
    return X -> return (X, None)  (py) / analogous tuple-ish break elsewhere."""
    text = _read(scope, sym["file"])
    lines = text.splitlines()
    start = sym["lineno"] - 1
    indent0 = len(lines[start]) - len(lines[start].lstrip())
    # find last simple `return <expr>` inside the def body
    target_i = None
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.strip() and (len(line) - len(line.lstrip())) <= indent0 and i > start + 1:
            break
        m = re.match(r"^(\s+)return\s+([^#\n]+?)\s*$", line)
        if m and "(" not in m.group(2)[:1] and "," not in m.group(2):
            target_i = i
    if target_i is None:
        return None
    old = lines[target_i]
    expr = re.match(r"^(\s+)return\s+(.*)$", old)
    if language == "python":
        new = f"{expr.group(1)}return ({expr.group(2)}, None)"
        detail = "return value wrapped in a 2-tuple; consumers unpacking the old value break"
    else:
        return None  # S3 restricted to python (deterministic edit); shortfall reported
    if not _unique(text, old):
        return None
    return {"file": sym["file"], "old": old, "new": new, "detail": detail}


# --- S4: base-class rename (breaks subclasses; the Joern blind spot) ---------
def s4_base_rename(scope: Path, sym: dict, language: str):
    # identical edit to S1 but target selection guarantees subclasses exist
    return s1_rename(scope, sym, language)


# --- S5: import/export removal (breaks importers) ----------------------------
def s5_export_removal(scope: Path, sym: dict, language: str):
    """Remove the symbol's re-export from the package barrel (__init__/index)."""
    barrel = sym.get("_barrel")
    if not barrel:
        return None
    text = _read(scope, barrel)
    name = sym["name"]
    old = None
    for line in text.splitlines():
        if re.search(rf"\b{re.escape(name)}\b", line) and ("import" in line or "export" in line):
            old = line
            break
    if old is None or not _unique(text, old):
        return None
    parts = [p.strip() for p in re.split(r"[,{}]", old)]
    if sum(1 for p in parts if p == name) != 1:
        return None
    if f" {name}," in old:
        new = old.replace(f" {name},", "", 1)
    elif f"{name}," in old:
        new = old.replace(f"{name},", "", 1)
    elif f", {name}" in old:
        new = old.replace(f", {name}", "", 1)
    else:
        return None  # sole symbol on the line — removing the whole line is noisier; skip
    return {"file": barrel, "old": old, "new": new,
            "detail": f"removed re-export of {name} from {Path(barrel).name}"}


# --- L1 (control): conditional boundary / wrong operator ---------------------
_L1_SWAPS = [(" <= ", " < "), (" >= ", " > "), (" < ", " <= "), (" > ", " >= ")]


def l1_boundary(scope: Path, site: dict, language: str):
    text = _read(scope, site["file"])
    old = site["line"]
    if not _unique(text, old):
        return None
    for frm, to in _L1_SWAPS:
        if frm in old:
            return {"file": site["file"], "old": old, "new": old.replace(frm, to, 1),
                    "detail": f"comparison operator changed `{frm.strip()}` -> `{to.strip()}` (off-by-one)"}
    return None


# --- L2 (control): removed null/bounds check ---------------------------------
def l2_check_removal(scope: Path, site: dict, language: str):
    """Invert a `if x is None:`-style guard so the check never fires."""
    text = _read(scope, site["file"])
    old = site["line"]
    if not _unique(text, old):
        return None
    if language == "python" and " is None" in old and " is not None" not in old:
        return {"file": site["file"], "old": old,
                "new": old.replace(" is None", " is not None", 1),
                "detail": "None-guard inverted; the guarded path now runs on None"}
    if language in ("java", "typescript") and "== null" in old:
        return {"file": site["file"], "old": old, "new": old.replace("== null", "!= null", 1),
                "detail": "null-guard inverted; the guarded path now runs on null"}
    if language == "typescript" and "=== undefined" in old:
        return {"file": site["file"], "old": old,
                "new": old.replace("=== undefined", "!== undefined", 1),
                "detail": "undefined-guard inverted"}
    return None


OPERATORS = {
    "S1": s1_rename, "S2": s2_signature, "S3": s3_return,
    "S4": s4_base_rename, "S5": s5_export_removal,
    "L1": l1_boundary, "L2": l2_check_removal,
}
