#!/usr/bin/env python3
"""
AST-based KG evidence extraction using tree-sitter.

Replaces grep/find heuristics with actual syntax tree parsing to extract:
- Function/method definitions in changed files
- Import relationships (precise, not pattern-matched)
- Function calls across files
- Test functions that reference changed code

Supports: Python, Java, TypeScript
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Optional, Tuple
from dataclasses import dataclass, asdict, field

import tree_sitter_python as tspython
import tree_sitter_java as tsjava
import tree_sitter_typescript as tstypescript
import tree_sitter_go as tsgo
import tree_sitter_cpp as tscpp
import tree_sitter_scala as tsscala
from tree_sitter import Language, Parser, Node

# ── Language setup ────────────────────────────────────────────────────────────

LANGUAGES = {
    "python": Language(tspython.language()),
    "java": Language(tsjava.language()),
    "typescript": Language(tstypescript.language_typescript()),
    "go": Language(tsgo.language()),
    "cpp": Language(tscpp.language()),
    "scala": Language(tsscala.language()),
}

EXTENSION_MAP = {
    ".py": "python",
    ".java": "java",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "typescript",
    ".jsx": "typescript",
    ".go": "go",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
    ".mm": "cpp",
    ".scala": "scala",
}


@dataclass
class FunctionDef:
    name: str
    file_path: str
    start_line: int
    end_line: int
    is_test: bool = False
    class_name: Optional[str] = None


@dataclass
class ImportRef:
    source_module: str
    imported_names: List[str]
    file_path: str
    line: int


@dataclass
class FunctionCall:
    caller_file: str
    caller_func: Optional[str]
    callee_name: str
    line: int


@dataclass
class ASTEvidence:
    changed_files: List[Dict[str, Any]] = field(default_factory=list)
    functions_in_changed_files: List[Dict[str, Any]] = field(default_factory=list)
    nearest_tests: List[Dict[str, Any]] = field(default_factory=list)
    dependent_files: List[Dict[str, Any]] = field(default_factory=list)
    callers: List[Dict[str, Any]] = field(default_factory=list)
    call_graph_edges: List[Dict[str, Any]] = field(default_factory=list)


# ── Parsing helpers ───────────────────────────────────────────────────────────

def get_parser(lang: str) -> Optional[Parser]:
    if lang not in LANGUAGES:
        return None
    parser = Parser(LANGUAGES[lang])
    return parser


def parse_file(file_path: str, lang: str) -> Optional[Node]:
    parser = get_parser(lang)
    if not parser:
        return None
    try:
        with open(file_path, "rb") as f:
            source = f.read()
        tree = parser.parse(source)
        return tree.root_node
    except Exception:
        return None


def node_text(node: Node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


# ── Python extraction ─────────────────────────────────────────────────────────

def extract_python_functions(root: Node, source: bytes, file_path: str) -> List[FunctionDef]:
    funcs = []
    for node in _walk(root):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = node_text(name_node, source)
                parent_class = None
                if node.parent and node.parent.type == "class_definition":
                    cn = node.parent.child_by_field_name("name")
                    if cn:
                        parent_class = node_text(cn, source)
                is_test = name.startswith("test_") or name.startswith("test")
                funcs.append(FunctionDef(
                    name=name, file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    is_test=is_test, class_name=parent_class,
                ))
    return funcs


def extract_python_imports(root: Node, source: bytes, file_path: str) -> List[ImportRef]:
    imports = []
    for node in _walk(root):
        if node.type == "import_from_statement":
            mod_node = node.child_by_field_name("module_name")
            if mod_node:
                module = node_text(mod_node, source)
                names = []
                for child in node.children:
                    if child.type == "dotted_name" and child != mod_node:
                        names.append(node_text(child, source))
                    elif child.type == "aliased_import":
                        n = child.child_by_field_name("name")
                        if n:
                            names.append(node_text(n, source))
                imports.append(ImportRef(module, names, file_path, node.start_point[0] + 1))
        elif node.type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    imports.append(ImportRef(node_text(child, source), [], file_path, node.start_point[0] + 1))
    return imports


def extract_python_calls(root: Node, source: bytes, file_path: str) -> List[FunctionCall]:
    calls = []
    for node in _walk(root):
        if node.type == "call":
            func_node = node.child_by_field_name("function")
            if func_node:
                name = node_text(func_node, source)
                caller_func = _find_enclosing_function(node, source)
                calls.append(FunctionCall(file_path, caller_func, name, node.start_point[0] + 1))
    return calls


# ── Java extraction ───────────────────────────────────────────────────────────

def extract_java_functions(root: Node, source: bytes, file_path: str) -> List[FunctionDef]:
    funcs = []
    for node in _walk(root):
        if node.type == "method_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = node_text(name_node, source)
                parent_class = None
                p = node.parent
                while p:
                    if p.type == "class_declaration":
                        cn = p.child_by_field_name("name")
                        if cn:
                            parent_class = node_text(cn, source)
                        break
                    p = p.parent
                is_test = _has_test_annotation(node, source)
                funcs.append(FunctionDef(
                    name=name, file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    is_test=is_test, class_name=parent_class,
                ))
    return funcs


def _has_test_annotation(node: Node, source: bytes) -> bool:
    """Check if a Java method has @Test annotation."""
    if node.parent:
        for sibling in node.parent.children:
            if sibling.type == "marker_annotation" and sibling.end_point[0] <= node.start_point[0]:
                text = node_text(sibling, source)
                if "@Test" in text:
                    return True
    # Also check preceding siblings
    idx = None
    if node.parent:
        for i, child in enumerate(node.parent.children):
            if child == node:
                idx = i
                break
        if idx and idx > 0:
            prev = node.parent.children[idx - 1]
            if prev.type == "modifiers":
                text = node_text(prev, source)
                if "@Test" in text:
                    return True
    return False


def extract_java_imports(root: Node, source: bytes, file_path: str) -> List[ImportRef]:
    imports = []
    for node in _walk(root):
        if node.type == "import_declaration":
            text = node_text(node, source).replace("import ", "").replace(";", "").strip()
            if text.startswith("static "):
                text = text[7:]
            parts = text.rsplit(".", 1)
            module = parts[0] if len(parts) > 1 else text
            name = parts[1] if len(parts) > 1 else ""
            imports.append(ImportRef(module, [name] if name else [], file_path, node.start_point[0] + 1))
    return imports


def extract_java_calls(root: Node, source: bytes, file_path: str) -> List[FunctionCall]:
    calls = []
    for node in _walk(root):
        if node.type == "method_invocation":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = node_text(name_node, source)
                obj_node = node.child_by_field_name("object")
                if obj_node:
                    name = f"{node_text(obj_node, source)}.{name}"
                caller_func = _find_enclosing_function(node, source)
                calls.append(FunctionCall(file_path, caller_func, name, node.start_point[0] + 1))
    return calls


# ── TypeScript extraction ─────────────────────────────────────────────────────

def extract_ts_functions(root: Node, source: bytes, file_path: str) -> List[FunctionDef]:
    funcs = []
    for node in _walk(root):
        if node.type in ("function_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                name = node_text(name_node, source)
                is_test = name.startswith("test") or "it(" in name or "describe(" in name
                parent_class = None
                p = node.parent
                while p:
                    if p.type == "class_declaration":
                        cn = p.child_by_field_name("name")
                        if cn:
                            parent_class = node_text(cn, source)
                        break
                    p = p.parent
                funcs.append(FunctionDef(
                    name=name, file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    is_test=is_test, class_name=parent_class,
                ))
        elif node.type == "arrow_function" and node.parent:
            if node.parent.type == "variable_declarator":
                name_node = node.parent.child_by_field_name("name")
                if name_node:
                    name = node_text(name_node, source)
                    funcs.append(FunctionDef(
                        name=name, file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        is_test=False, class_name=None,
                    ))
    return funcs


def extract_ts_imports(root: Node, source: bytes, file_path: str) -> List[ImportRef]:
    imports = []
    for node in _walk(root):
        if node.type == "import_statement":
            source_node = node.child_by_field_name("source")
            if source_node:
                module = node_text(source_node, source).strip("'\"")
                names = []
                for child in _walk(node):
                    if child.type == "import_specifier":
                        n = child.child_by_field_name("name")
                        if n:
                            names.append(node_text(n, source))
                imports.append(ImportRef(module, names, file_path, node.start_point[0] + 1))
    return imports


def extract_ts_calls(root: Node, source: bytes, file_path: str) -> List[FunctionCall]:
    calls = []
    for node in _walk(root):
        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                name = node_text(func_node, source)
                caller_func = _find_enclosing_function(node, source)
                calls.append(FunctionCall(file_path, caller_func, name, node.start_point[0] + 1))
    return calls


# ── Go extraction ────────────────────────────────────────────────────────────

def extract_go_functions(root: Node, source: bytes, file_path: str) -> List[FunctionDef]:
    funcs = []
    for node in _walk(root):
        if node.type in ("function_declaration", "method_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                name = node_text(name_node, source)
                is_test = name.startswith("Test") or name.startswith("Benchmark")
                funcs.append(FunctionDef(
                    name=name, file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    is_test=is_test, class_name=None,
                ))
    return funcs


def extract_go_imports(root: Node, source: bytes, file_path: str) -> List[ImportRef]:
    imports = []
    for node in _walk(root):
        if node.type == "import_spec":
            path_node = node.child_by_field_name("path")
            if path_node:
                module = node_text(path_node, source).strip('"')
                name_node = node.child_by_field_name("name")
                alias = node_text(name_node, source) if name_node else ""
                imports.append(ImportRef(module, [alias] if alias else [], file_path, node.start_point[0] + 1))
    return imports


def extract_go_calls(root: Node, source: bytes, file_path: str) -> List[FunctionCall]:
    calls = []
    for node in _walk(root):
        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                name = node_text(func_node, source)
                caller_func = _find_enclosing_function(node, source)
                calls.append(FunctionCall(file_path, caller_func, name, node.start_point[0] + 1))
    return calls


# ── C++ extraction ───────────────────────────────────────────────────────────

def extract_cpp_functions(root: Node, source: bytes, file_path: str) -> List[FunctionDef]:
    funcs = []
    for node in _walk(root):
        if node.type == "function_definition":
            declarator = node.child_by_field_name("declarator")
            name = _extract_cpp_func_name(declarator, source) if declarator else None
            if name:
                parent_class = None
                if "::" in name:
                    parts = name.rsplit("::", 1)
                    parent_class = parts[0]
                    name = parts[1]
                is_test = "test" in name.lower() or "TEST" in name
                funcs.append(FunctionDef(
                    name=name, file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    is_test=is_test, class_name=parent_class,
                ))
    return funcs


def _extract_cpp_func_name(node: Node, source: bytes) -> Optional[str]:
    if node is None:
        return None
    if node.type in ("identifier", "field_identifier", "destructor_name"):
        return node_text(node, source)
    if node.type == "qualified_identifier":
        return node_text(node, source)
    if node.type == "function_declarator":
        decl = node.child_by_field_name("declarator")
        return _extract_cpp_func_name(decl, source)
    if node.type == "pointer_declarator":
        decl = node.child_by_field_name("declarator")
        return _extract_cpp_func_name(decl, source)
    return node_text(node, source)


def extract_cpp_imports(root: Node, source: bytes, file_path: str) -> List[ImportRef]:
    imports = []
    for node in _walk(root):
        if node.type == "preproc_include":
            path_node = node.child_by_field_name("path")
            if path_node:
                inc = node_text(path_node, source).strip('<>"')
                imports.append(ImportRef(inc, [], file_path, node.start_point[0] + 1))
    return imports


def extract_cpp_calls(root: Node, source: bytes, file_path: str) -> List[FunctionCall]:
    calls = []
    for node in _walk(root):
        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                name = node_text(func_node, source)
                caller_func = _find_enclosing_function(node, source)
                calls.append(FunctionCall(file_path, caller_func, name, node.start_point[0] + 1))
    return calls


# ── Scala extraction ────────────────────────────────────────────────────────

def extract_scala_functions(root: Node, source: bytes, file_path: str) -> List[FunctionDef]:
    funcs = []
    for node in _walk(root):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = node_text(name_node, source)
                parent_class = None
                p = node.parent
                while p:
                    if p.type in ("class_definition", "object_definition", "trait_definition"):
                        cn = p.child_by_field_name("name")
                        if cn:
                            parent_class = node_text(cn, source)
                        break
                    p = p.parent
                is_test = name.startswith("test") or _path_looks_like_test(file_path)
                funcs.append(FunctionDef(
                    name=name, file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    is_test=is_test, class_name=parent_class,
                ))
    return funcs


def extract_scala_imports(root: Node, source: bytes, file_path: str) -> List[ImportRef]:
    imports = []
    for node in _walk(root):
        if node.type == "import_declaration":
            text = node_text(node, source).replace("import ", "").strip()
            parts = text.rsplit(".", 1)
            module = parts[0]
            name = parts[1] if len(parts) > 1 else ""
            imports.append(ImportRef(module, [name] if name and name != "_" else [], file_path, node.start_point[0] + 1))
    return imports


def extract_scala_calls(root: Node, source: bytes, file_path: str) -> List[FunctionCall]:
    calls = []
    for node in _walk(root):
        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node:
                name = node_text(func_node, source)
                caller_func = _find_enclosing_function_scala(node, source)
                calls.append(FunctionCall(file_path, caller_func, name, node.start_point[0] + 1))
    return calls


def _find_enclosing_function_scala(node: Node, source: bytes) -> Optional[str]:
    p = node.parent
    while p:
        if p.type == "function_definition":
            name_node = p.child_by_field_name("name")
            if name_node:
                return node_text(name_node, source)
        p = p.parent
    return None


# ── Shared helpers ────────────────────────────────────────────────────────────

def _walk(node: Node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _find_enclosing_function(node: Node, source: bytes) -> Optional[str]:
    p = node.parent
    while p:
        if p.type in ("function_definition", "method_declaration",
                       "function_declaration", "method_definition"):
            name_node = p.child_by_field_name("name")
            if name_node:
                return node_text(name_node, source)
        p = p.parent
    return None


# ── Language dispatch ─────────────────────────────────────────────────────────

EXTRACTORS = {
    "python": (extract_python_functions, extract_python_imports, extract_python_calls),
    "java": (extract_java_functions, extract_java_imports, extract_java_calls),
    "typescript": (extract_ts_functions, extract_ts_imports, extract_ts_calls),
    "go": (extract_go_functions, extract_go_imports, extract_go_calls),
    "cpp": (extract_cpp_functions, extract_cpp_imports, extract_cpp_calls),
    "scala": (extract_scala_functions, extract_scala_imports, extract_scala_calls),
}


def extract_file(file_path: str, lang: str) -> Tuple[List[FunctionDef], List[ImportRef], List[FunctionCall]]:
    if lang not in EXTRACTORS:
        return [], [], []
    try:
        with open(file_path, "rb") as f:
            source = f.read()
        parser = get_parser(lang)
        if not parser:
            return [], [], []
        tree = parser.parse(source)
        root = tree.root_node
        fn_ext, imp_ext, call_ext = EXTRACTORS[lang]
        return fn_ext(root, source, file_path), imp_ext(root, source, file_path), call_ext(root, source, file_path)
    except Exception as e:
        print(f"    [warn] Could not parse {file_path}: {e}")
        return [], [], []


# ── Evidence builder ──────────────────────────────────────────────────────────

PR_CONFIGS = {
    1:  {"repo": "luca_repos/godotengine_godot", "lang": "cpp"},
    2:  {"repo": "luca_repos/grafana_grafana", "lang": "go"},
    3:  {"repo": "luca_repos/grafana_grafana", "lang": "typescript"},
    5:  {"repo": "luca_repos/jenkinsci_jenkins", "lang": "java"},
    6:  {"repo": "luca_repos/apache_kafka", "lang": "java"},
    7:  {"repo": "luca_repos/microsoft_TypeScript", "lang": "typescript"},
    8:  {"repo": "luca_repos/grafana_grafana", "lang": "go"},
    9:  {"repo": "luca_repos/grafana_grafana", "lang": "go"},
    10: {"repo": "luca_repos/scikit-learn_scikit-learn", "lang": "python"},
    11: {"repo": "luca_repos/django_django", "lang": "python"},
    12: {"repo": "luca_repos/godotengine_godot", "lang": "cpp"},
    13: {"repo": "luca_repos/godotengine_godot", "lang": "cpp"},
    14: {"repo": "luca_repos/grafana_grafana", "lang": "typescript"},
    15: {"repo": "luca_repos/grafana_grafana", "lang": "typescript"},
    16: {"repo": "luca_repos/grafana_grafana", "lang": "go"},
    17: {"repo": "luca_repos/jenkinsci_jenkins", "lang": "java"},
    18: {"repo": "luca_repos/jenkinsci_jenkins", "lang": "java"},
    19: {"repo": "luca_repos/jenkinsci_jenkins", "lang": "java"},
    20: {"repo": "luca_repos/apache_kafka", "lang": "scala"},
    21: {"repo": "luca_repos/apache_kafka", "lang": "java"},
    22: {"repo": "luca_repos/apache_kafka", "lang": "java"},
    23: {"repo": "luca_repos/scikit-learn_scikit-learn", "lang": "python"},
    24: {"repo": "luca_repos/scikit-learn_scikit-learn", "lang": "python"},
    25: {"repo": "luca_repos/django_django", "lang": "python"},
    26: {"repo": "luca_repos/django_django", "lang": "python"},
    # ─── v2 dataset expansions (added 2026-05-13 for scoped-AST sensitivity
    # analysis, pre-registered in dataset_v2/docs/PRE_REGISTRATION_scoped_ast.md).
    # PRs 27-33 came from the 18→25 expansion (2026-05-05); PRs 34-48 came from
    # the 25→40 KG-richness expansion (2026-05-12). Repo paths and primary
    # languages were derived deterministically from the v2 evidence packs.
    # Where a PR touches files in more than one language, "lang" names the
    # majority language; tree-sitter still picks up other extensions via
    # EXTENSION_MAP above. Provenance is logged inline. ───
    27: {"repo": "luca_repos/grafana_grafana",               "lang": "go"},         # mixed go+ts; majority go
    28: {"repo": "luca_repos/grafana_grafana",               "lang": "typescript"},
    29: {"repo": "luca_repos/apache_kafka",                  "lang": "java"},
    30: {"repo": "luca_repos/godotengine_godot",             "lang": "cpp"},
    31: {"repo": "luca_repos/scikit-learn_scikit-learn",     "lang": "python"},
    32: {"repo": "luca_repos/scikit-learn_scikit-learn",     "lang": "python"},
    33: {"repo": "luca_repos/jenkinsci_jenkins",             "lang": "java"},
    34: {"repo": "luca_repos/grafana_grafana",               "lang": "typescript"},
    35: {"repo": "luca_repos/grafana_grafana",               "lang": "go"},
    36: {"repo": "luca_repos/grafana_grafana",               "lang": "go"},
    37: {"repo": "luca_repos/grafana_grafana",               "lang": "go"},
    38: {"repo": "luca_repos/grafana_grafana",               "lang": "typescript"},
    39: {"repo": "luca_repos/apache_kafka",                  "lang": "scala"},
    40: {"repo": "luca_repos/apache_kafka",                  "lang": "java"},
    41: {"repo": "luca_repos/apache_kafka",                  "lang": "java"},       # mixed java+scala; majority java
    42: {"repo": "luca_repos/scikit-learn_scikit-learn",     "lang": "python"},
    43: {"repo": "luca_repos/scikit-learn_scikit-learn",     "lang": "python"},
    44: {"repo": "luca_repos/scikit-learn_scikit-learn",     "lang": "python"},
    45: {"repo": "luca_repos/godotengine_godot",             "lang": "cpp"},
    46: {"repo": "luca_repos/godotengine_godot",             "lang": "cpp"},
    47: {"repo": "luca_repos/jenkinsci_jenkins",             "lang": "java"},
    48: {"repo": "luca_repos/jenkinsci_jenkins",             "lang": "java"},
}

BASE_DIR = Path(__file__).resolve().parent.parent
# Default paths are v1 (luca_prs_fixed) for backwards compatibility with the
# original v1 sensitivity runs. For the v2 (40-PR) scoped-AST sensitivity
# analysis, override via environment variables:
#   KG_EVIDENCE_DIR=data/luca_prs_v2  KG_OUTPUT_DIR=data/luca_prs_v2_ast
# (added 2026-05-13 alongside the PR_CONFIGS expansion to PRs 27-48).
EVIDENCE_DIR = Path(os.environ.get("KG_EVIDENCE_DIR", BASE_DIR / "data" / "luca_prs_fixed"))
if not EVIDENCE_DIR.is_absolute():
    EVIDENCE_DIR = BASE_DIR / EVIDENCE_DIR
OUTPUT_DIR = Path(os.environ.get("KG_OUTPUT_DIR", BASE_DIR / "data" / "luca_prs_fixed_ast"))
if not OUTPUT_DIR.is_absolute():
    OUTPUT_DIR = BASE_DIR / OUTPUT_DIR


def build_ast_evidence(pr_id: int) -> ASTEvidence:
    config = PR_CONFIGS[pr_id]
    repo_path = BASE_DIR / config["repo"]
    lang = config["lang"]

    # Load existing evidence for changed files list and diff
    with open(EVIDENCE_DIR / f"pr{pr_id}_evidence.json") as f:
        orig = json.load(f)

    evidence = ASTEvidence()
    evidence.changed_files = orig.get("changed_files", [])

    changed_paths = set()
    for cf in evidence.changed_files:
        p = cf["path"] if isinstance(cf, dict) else cf
        changed_paths.add(p)

    # Extract functions from changed files
    changed_func_names: Set[str] = set()
    print(f"  Parsing {len(changed_paths)} changed files with tree-sitter ({lang})...")

    for cf_path in sorted(changed_paths):
        full_path = repo_path / cf_path
        if not full_path.exists():
            continue
        file_lang = EXTENSION_MAP.get(full_path.suffix, lang)
        funcs, imports, calls = extract_file(str(full_path), file_lang)
        for fn in funcs:
            changed_func_names.add(fn.name)
            if fn.class_name:
                changed_func_names.add(f"{fn.class_name}.{fn.name}")
            evidence.functions_in_changed_files.append({
                "name": fn.name,
                "class": fn.class_name,
                "file": cf_path,
                "lines": f"{fn.start_line}-{fn.end_line}",
                "is_test": fn.is_test,
            })

    print(f"    Found {len(evidence.functions_in_changed_files)} functions in changed files")
    print(f"    Function names: {sorted(changed_func_names)[:15]}")

    # Scan repo for files that import/call changed code
    print(f"  Scanning repo for dependents and tests...")
    changed_stems = {Path(p).stem for p in changed_paths}
    scanned = 0
    max_scan = 5000  # limit for performance

    for root_dir, dirs, files in os.walk(repo_path):
        # Skip hidden dirs, node_modules, build dirs
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("node_modules", "build", "dist", "__pycache__",
                                 ".git", "vendor", "target")]
        for fname in files:
            ext = Path(fname).suffix
            file_lang = EXTENSION_MAP.get(ext)
            if not file_lang:
                continue
            full_path = Path(root_dir) / fname
            rel_path = str(full_path.relative_to(repo_path))
            if rel_path in changed_paths:
                continue
            scanned += 1
            if scanned > max_scan:
                break

            funcs, imports, calls = extract_file(str(full_path), file_lang)

            # Check imports: does this file import any changed file?
            for imp in imports:
                mod_parts = imp.source_module.replace("/", ".").split(".")
                for stem in changed_stems:
                    if stem in mod_parts or stem in imp.imported_names:
                        is_test = any(fn.is_test for fn in funcs) or _path_looks_like_test(rel_path)
                        entry = {
                            "path": rel_path,
                            "relationship": "imports",
                            "source_file": _match_stem_to_changed(stem, changed_paths),
                            "import_statement": imp.source_module,
                            "line": imp.line,
                        }
                        if is_test:
                            evidence.nearest_tests.append({
                                **entry, "relationship": "tests"
                            })
                        else:
                            evidence.dependent_files.append(entry)
                        break

            # Check calls: does this file call functions defined in changed files?
            for call in calls:
                callee = call.callee_name.split(".")[-1]
                if callee in changed_func_names:
                    evidence.callers.append({
                        "path": rel_path,
                        "calls_function": call.callee_name,
                        "from_function": call.caller_func,
                        "line": call.line,
                        "source_file": _match_func_to_file(callee, evidence.functions_in_changed_files),
                    })

        if scanned > max_scan:
            break

    # Naming-convention fallback: find {ClassName}Test files that import tracing missed
    # (common in Java where tests use reflection or inherit base test classes)
    existing_test_paths = {t["path"] for t in evidence.nearest_tests}
    convention_tests_found = 0
    for cf_path in changed_paths:
        stem = Path(cf_path).stem
        if _path_looks_like_test(cf_path):
            continue
        # Build patterns: FooTest, Foo_test, test_foo, FooSpec
        patterns = [
            f"{stem}Test", f"{stem}_test", f"test_{stem}",
            f"{stem}Spec", f"{stem}_spec",
            f"Test{stem}",
        ]
        patterns_lower = [p.lower() for p in patterns]
        for root_dir, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")
                       and d not in ("node_modules", "build", "dist", "__pycache__",
                                     ".git", "vendor", "target")]
            for fname in files:
                fstem = Path(fname).stem.lower()
                if any(fstem == p for p in patterns_lower):
                    full_path = Path(root_dir) / fname
                    rel_path = str(full_path.relative_to(repo_path))
                    if rel_path not in existing_test_paths and rel_path not in changed_paths:
                        evidence.nearest_tests.append({
                            "path": rel_path,
                            "relationship": "naming_convention",
                            "source_file": cf_path,
                        })
                        existing_test_paths.add(rel_path)
                        convention_tests_found += 1

    if convention_tests_found:
        print(f"    Naming-convention test fallback found: {convention_tests_found} additional tests")

    # Deduplicate
    evidence.nearest_tests = _dedupe_by_path(evidence.nearest_tests)
    evidence.dependent_files = _dedupe_by_path(evidence.dependent_files)
    evidence.callers = _dedupe_by_path(evidence.callers)

    print(f"    Scanned {scanned} files")
    print(f"    Tests found: {len(evidence.nearest_tests)}")
    print(f"    Dependents found: {len(evidence.dependent_files)}")
    print(f"    Callers found: {len(evidence.callers)}")

    return evidence


def _path_looks_like_test(path: str) -> bool:
    p = path.lower()
    return ("test" in p or "spec" in p or "__tests__" in p)


def _match_stem_to_changed(stem: str, changed_paths: Set[str]) -> str:
    for p in changed_paths:
        if Path(p).stem == stem:
            return p
    return stem


def _match_func_to_file(func_name: str, func_list: List[Dict]) -> str:
    for f in func_list:
        if f["name"] == func_name:
            return f["file"]
    return ""


def _dedupe_by_path(items: List[Dict]) -> List[Dict]:
    seen = set()
    result = []
    for item in items:
        if item["path"] not in seen:
            seen.add(item["path"])
            result.append(item)
    return result


def save_evidence(pr_id: int, evidence: ASTEvidence, orig_evidence: dict):
    """Save AST evidence merged with original (keeps diff, PR metadata)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    merged = {
        "pr": orig_evidence.get("pr", {}),
        "full_diff": orig_evidence.get("full_diff", ""),
        "changed_files": evidence.changed_files,
        "functions_in_changed_files": evidence.functions_in_changed_files,
        "nearest_tests": evidence.nearest_tests,
        "dependent_files": evidence.dependent_files,
        "callers": evidence.callers,
        "call_graph_edges": evidence.call_graph_edges,
        "extraction_method": "tree-sitter-ast",
        "similar_chunks": orig_evidence.get("similar_chunks", []),
    }

    out_path = OUTPUT_DIR / f"pr{pr_id}_evidence.json"
    with open(out_path, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"  Saved → {out_path}")
    return merged


def compare_evidence(pr_id: int, ast_ev: ASTEvidence, grep_ev: dict):
    """Print side-by-side comparison of grep vs AST evidence."""
    grep_tests = grep_ev.get("nearest_tests", [])
    grep_deps = grep_ev.get("dependent_files", [])

    print(f"\n  ┌── Evidence Comparison: PR{pr_id} ──┐")
    print(f"  │ {'':30s} │ {'Grep':>6s} │ {'AST':>6s} │")
    print(f"  ├──────────────────────────────┼────────┼────────┤")
    print(f"  │ {'Functions extracted':30s} │ {'N/A':>6s} │ {len(ast_ev.functions_in_changed_files):>6d} │")
    print(f"  │ {'Tests found':30s} │ {len(grep_tests):>6d} │ {len(ast_ev.nearest_tests):>6d} │")
    print(f"  │ {'Dependents found':30s} │ {len(grep_deps):>6d} │ {len(ast_ev.dependent_files):>6d} │")
    print(f"  │ {'Callers found':30s} │ {'N/A':>6s} │ {len(ast_ev.callers):>6d} │")
    print(f"  └──────────────────────────────┴────────┴────────┘")

    # Show what AST found that grep didn't
    grep_test_paths = {t["path"] if isinstance(t, dict) else t for t in grep_tests}
    ast_test_paths = {t["path"] for t in ast_ev.nearest_tests}
    new_tests = ast_test_paths - grep_test_paths
    if new_tests:
        print(f"\n  NEW tests found by AST (not in grep):")
        for t in sorted(new_tests)[:5]:
            print(f"    + {t}")

    grep_dep_paths = {d["path"] if isinstance(d, dict) else d for d in grep_deps}
    ast_dep_paths = {d["path"] for d in ast_ev.dependent_files}
    new_deps = ast_dep_paths - grep_dep_paths
    if new_deps:
        print(f"\n  NEW dependents found by AST (not in grep):")
        for d in sorted(new_deps)[:5]:
            print(f"    + {d}")

    if ast_ev.functions_in_changed_files:
        print(f"\n  Functions in changed files (AST-extracted):")
        for fn in ast_ev.functions_in_changed_files[:10]:
            cls = f"{fn['class']}." if fn.get('class') else ""
            test_tag = " [TEST]" if fn.get("is_test") else ""
            print(f"    {cls}{fn['name']}  ({fn['file']}:{fn['lines']}){test_tag}")


def main():
    pr_ids = list(PR_CONFIGS.keys())
    if len(sys.argv) > 1:
        pr_ids = [int(x) for x in sys.argv[1:]]

    print("=" * 60)
    print("AST-based KG Evidence Extraction (tree-sitter)")
    print("=" * 60)

    for pr_id in pr_ids:
        if pr_id not in PR_CONFIGS:
            print(f"\nPR{pr_id}: No config, skipping")
            continue

        evidence_path = EVIDENCE_DIR / f"pr{pr_id}_evidence.json"
        if not evidence_path.exists():
            print(f"\nPR{pr_id}: No evidence file at {evidence_path}, skipping")
            continue

        print(f"\n{'='*50}")
        print(f"PR #{pr_id}")
        print(f"{'='*50}")

        with open(evidence_path) as f:
            orig = json.load(f)

        ast_ev = build_ast_evidence(pr_id)
        compare_evidence(pr_id, ast_ev, orig)
        save_evidence(pr_id, ast_ev, orig)

    print(f"\n{'='*60}")
    print("Done! AST evidence saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
