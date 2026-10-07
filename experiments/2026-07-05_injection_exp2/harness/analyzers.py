"""Language analyzers for injection-target discovery.

Uniform interface per language:
  symbols(scope)                -> [ {name, kind, file, lineno, line, bases, params_line} ]
  importers(scope, sym)         -> {rel_file: [evidence_line, ...]}
  callers(scope, sym)           -> {rel_file: [...]}   (importers that also call)
  subclasses(scope, sym)        -> {rel_file: [...]}   (importers that extend/subclass)

Python uses the `ast` module (exact). Java/TS use strict import-statement
and word-boundary regexes; every dependent is recorded with the evidence
line so the claim is verifiable. Recorded in the manifest as
`resolver: ast` / `resolver: import-regex`.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

EXCLUDE_PAT = re.compile(r"(^|/)(tests?|testing|__pycache__|\.git)(/|$)")


def code_files(scope: Path, exts: tuple[str, ...]) -> list[Path]:
    out = []
    for p in sorted(scope.rglob("*")):
        if p.is_file() and p.suffix in exts and not EXCLUDE_PAT.search(str(p.relative_to(scope))):
            out.append(p)
    return out


def rel(scope: Path, p: Path) -> str:
    return str(p.relative_to(scope))


# ---------------------------------------------------------------------------
# Python (exact, via ast)
# ---------------------------------------------------------------------------
class PyAnalyzer:
    exts = (".py",)
    resolver = "ast"

    def __init__(self, scope: Path):
        self.scope = scope
        self.files = code_files(scope, self.exts)
        self._trees = {}
        for p in self.files:
            try:
                self._trees[p] = ast.parse(p.read_text(errors="ignore"))
            except SyntaxError:
                pass

    def symbols(self):
        out = []
        for p, tree in self._trees.items():
            if p.name == "__init__.py":
                continue
            lines = p.read_text(errors="ignore").splitlines()
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name.startswith("__"):
                        continue
                    bases = []
                    if isinstance(node, ast.ClassDef):
                        bases = [ast.unparse(b) for b in node.bases]
                    out.append({
                        "name": node.name,
                        "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                        "file": rel(self.scope, p), "lineno": node.lineno,
                        "line": lines[node.lineno - 1], "bases": bases,
                        "private": node.name.startswith("_"),
                    })
        return out

    def _module_of(self, def_file: str) -> str:
        # sklearn/preprocessing/_data.py -> stem "_data", pkg tuple for matching
        return Path(def_file).stem

    def importers(self, sym: dict):
        """Files with `from <...>.<defstem> import <name>` (any package prefix)."""
        stem = self._module_of(sym["file"])
        name = sym["name"]
        hits = {}
        for p, tree in self._trees.items():
            r = rel(self.scope, p)
            if r == sym["file"]:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    last = node.module.split(".")[-1]
                    if last == stem and any(a.name == name for a in node.names):
                        hits.setdefault(r, []).append(
                            f"L{node.lineno}: from {node.module} import {name}")
        return hits

    def callers(self, sym: dict):
        imps = self.importers(sym)
        name = sym["name"]
        call_re = re.compile(rf"\b{re.escape(name)}\s*\(")
        out = {}
        for f, ev in imps.items():
            text = (self.scope / f).read_text(errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                if call_re.search(line) and not line.lstrip().startswith(("from ", "import ", "#")):
                    out.setdefault(f, list(ev)).append(f"L{i}: {line.strip()[:100]}")
        return {f: v for f, v in out.items() if len(v) > len(imps.get(f, []))}

    def subclasses(self, sym: dict):
        if sym["kind"] != "class":
            return {}
        imps = self.importers(sym)
        name = sym["name"]
        out = {}
        for f in imps:
            tree = self._trees.get(self.scope / f)
            if not tree:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for b in node.bases:
                        if ast.unparse(b).split(".")[-1] == name:
                            out.setdefault(f, list(imps[f])).append(
                                f"L{node.lineno}: class {node.name}({ast.unparse(b)})")
        return {f: v for f, v in out.items() if len(v) > len(imps.get(f, []))}


# ---------------------------------------------------------------------------
# Java (strict import + word-boundary regex)
# ---------------------------------------------------------------------------
class JavaAnalyzer:
    exts = (".java",)
    resolver = "import-regex"
    _class_re = re.compile(
        r"^(?:public\s+)?(?:final\s+|abstract\s+)*(?:class|interface|enum)\s+(\w+)"
        r"(?:<[^\n{]*?>)?(?:\s+extends\s+([\w.<>, ]+))?", re.M)
    _method_re = re.compile(
        r"^\s{4}(?:public|protected)\s+(?:static\s+)?(?:final\s+)?(?:<[^>]+>\s+)?"
        r"([A-Z][\w<>\[\], .?]*|void|int|long|boolean|double|float|byte|short|char)\s+"
        r"(\w+)\s*\(([^)]*)\)", re.M)

    def __init__(self, scope: Path):
        self.scope = scope
        self.files = code_files(scope, self.exts)
        self._text = {p: p.read_text(errors="ignore") for p in self.files}
        self._pkg = {}
        for p, t in self._text.items():
            m = re.search(r"^package\s+([\w.]+);", t, re.M)
            self._pkg[p] = m.group(1) if m else ""

    def symbols(self):
        out = []
        for p, text in self._text.items():
            lines = text.splitlines()
            # top-level type whose name matches the filename (the public type)
            for m in self._class_re.finditer(text):
                name = m.group(1)
                if name != p.stem:
                    continue
                lineno = text[:m.start()].count("\n") + 1
                out.append({"name": name, "kind": "class", "file": rel(self.scope, p),
                            "lineno": lineno, "line": lines[lineno - 1],
                            "bases": [b.strip() for b in (m.group(2) or "").split(",") if b.strip()],
                            "private": False})
            # public/protected methods (only if method name is unique across scope defs)
            for m in self._method_re.finditer(text):
                ret, name, params = m.group(1), m.group(2), m.group(3)
                if name == p.stem or name.startswith(("get", "set", "is", "to", "equals", "hashCode", "toString")):
                    continue
                lineno = text[:m.start()].count("\n") + 1
                out.append({"name": name, "kind": "method", "file": rel(self.scope, p),
                            "lineno": lineno, "line": lines[lineno - 1].rstrip(),
                            "bases": [], "private": False,
                            "ret": ret.strip(), "params": params.strip(),
                            "owner": p.stem})
        # drop methods whose name is defined in >1 place (overload/ambiguity guard)
        from collections import Counter
        counts = Counter(s["name"] for s in out if s["kind"] == "method")
        return [s for s in out if s["kind"] != "method" or counts[s["name"]] == 1]

    def _refs(self, sym: dict, needs_call=False, needs_extends=False):
        name = sym["name"]
        def_file = sym["file"]
        def_pkg = self._pkg[self.scope / def_file]
        word = re.compile(rf"\b{re.escape(name)}\b")
        imp = re.compile(rf"^import\s+(?:static\s+)?[\w.]*\.{re.escape(name)};", re.M)
        ext = re.compile(rf"\b(?:extends|implements)\s+(?:[\w.]+,\s*)*{re.escape(name)}\b")
        call = re.compile(rf"(?:\.|\b){re.escape(name)}\s*\(")
        hits = {}
        for p, text in self._text.items():
            r = rel(self.scope, p)
            if r == def_file:
                continue
            imported = bool(imp.search(text))
            same_pkg = self._pkg[p] == def_pkg and def_pkg != ""
            if not (imported or (same_pkg and word.search(text))):
                continue
            ev = []
            for i, line in enumerate(text.splitlines(), 1):
                ls = line.strip()
                if ls.startswith("import ") and name in ls:
                    ev.append(f"L{i}: {ls[:100]}")
                elif needs_extends and ext.search(line):
                    ev.append(f"L{i}: {ls[:100]}")
                elif needs_call and call.search(line) and not ls.startswith(("import", "*", "//")):
                    ev.append(f"L{i}: {ls[:100]}")
                elif not needs_call and not needs_extends and word.search(line) \
                        and not ls.startswith(("import", "package", "*", "//")):
                    ev.append(f"L{i}: {ls[:100]}")
            key_needed = needs_extends or needs_call
            substantive = [e for e in ev if not e.split(": ", 1)[1].startswith("import")]
            if (key_needed and substantive) or (not key_needed and ev):
                hits[r] = ev[:6]
        return hits

    def importers(self, sym):
        return self._refs(sym)

    def callers(self, sym):
        return self._refs(sym, needs_call=True)

    def subclasses(self, sym):
        if sym["kind"] != "class":
            return {}
        return self._refs(sym, needs_extends=True)


# ---------------------------------------------------------------------------
# TypeScript (relative-import resolution + word-boundary regex)
# ---------------------------------------------------------------------------
class TsAnalyzer:
    exts = (".ts", ".tsx")
    resolver = "import-regex"
    _def_res = [
        (re.compile(r"^export\s+(?:abstract\s+)?class\s+(\w+)(?:<[^{\n]*?>)?(?:\s+extends\s+([\w.<>]+))?", re.M), "class"),
        (re.compile(r"^export\s+function\s+(\w+)\s*(?:<[^(\n]*?>)?\(", re.M), "function"),
    ]
    _imp_re = re.compile(r"import\s+(?:type\s+)?\{([^}]*)\}\s+from\s+['\"]([^'\"]+)['\"]")

    def __init__(self, scope: Path):
        self.scope = scope
        self.files = code_files(scope, self.exts)
        self._text = {p: p.read_text(errors="ignore") for p in self.files}

    def _resolve(self, from_file: Path, spec: str) -> str | None:
        if not spec.startswith("."):
            return None
        base = (from_file.parent / spec).resolve()
        for cand in (base.with_suffix(".ts"), base.with_suffix(".tsx"),
                     base / "index.ts", base / "index.tsx"):
            try:
                return str(cand.relative_to(self.scope.resolve()))
            except ValueError:
                continue
        return None

    def symbols(self):
        out = []
        for p, text in self._text.items():
            if p.name.startswith("index."):
                continue
            lines = text.splitlines()
            for rx, kind in self._def_res:
                for m in rx.finditer(text):
                    lineno = text[:m.start()].count("\n") + 1
                    bases = [m.group(2)] if kind == "class" and m.lastindex and m.group(2) else []
                    out.append({"name": m.group(1), "kind": kind,
                                "file": rel(self.scope, p), "lineno": lineno,
                                "line": lines[lineno - 1], "bases": bases,
                                "private": False})
        return out

    def importers(self, sym):
        name, def_file = sym["name"], sym["file"]
        hits = {}
        for p, text in self._text.items():
            r = rel(self.scope, p)
            if r == def_file:
                continue
            for m in self._imp_re.finditer(text):
                names = [n.strip().split(" as ")[0] for n in m.group(1).split(",")]
                if name not in names:
                    continue
                target = self._resolve(p, m.group(2))
                # direct import from the module, or via a barrel that re-exports it
                if target == def_file or (target and target.endswith("index.ts")):
                    if target != def_file:
                        idx_text = self._text.get(self.scope / target, "")
                        if not re.search(rf"\b{re.escape(name)}\b", idx_text):
                            continue
                    lineno = text[:m.start()].count("\n") + 1
                    hits.setdefault(r, []).append(f"L{lineno}: {m.group(0)[:110]}")
        return hits

    def callers(self, sym):
        imps = self.importers(sym)
        call = re.compile(rf"\b{re.escape(sym['name'])}\s*[(<]")
        out = {}
        for f, ev in imps.items():
            text = self._text[self.scope / f]
            for i, line in enumerate(text.splitlines(), 1):
                if call.search(line) and "import" not in line:
                    out.setdefault(f, list(ev)).append(f"L{i}: {line.strip()[:100]}")
        return {f: v for f, v in out.items() if len(v) > len(imps.get(f, []))}

    def subclasses(self, sym):
        if sym["kind"] != "class":
            return {}
        imps = self.importers(sym)
        ext = re.compile(rf"\bextends\s+{re.escape(sym['name'])}\b")
        out = {}
        for f, ev in imps.items():
            text = self._text[self.scope / f]
            for i, line in enumerate(text.splitlines(), 1):
                if ext.search(line):
                    out.setdefault(f, list(ev)).append(f"L{i}: {line.strip()[:100]}")
        return {f: v for f, v in out.items() if len(v) > len(imps.get(f, []))}


ANALYZERS = {"python": PyAnalyzer, "java": JavaAnalyzer, "typescript": TsAnalyzer}
