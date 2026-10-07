#!/usr/bin/env python3
"""Extract multi-hop caller edges from existing Joern CPGs.

For each injection's changed symbol, run a BFS through callIn edges:
  hop 1: direct callers of the changed function
  hop 2: callers of hop-1 callers
  hop 3: callers of hop-2 callers

Outputs: hops_<repo>.json — {symbol: [{...edge..., "hop": 1|2|3}, ...]}

Reuses the CPG binaries from Experiment 2 (no re-parsing needed).
Only the Joern query is new.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "2026-07-05_injection_exp2" / "harness"))
from common import OUT as EXP2_OUT, SCOPES, load_manifest  # noqa: E402

HERE = Path(__file__).resolve().parent
JOERN_DIR = EXP2_OUT / "joern"
MAX_HOPS = 3

# Multi-hop CPGQL query: BFS from each symbol through callIn edges
QUERY_TEMPLATE = '''importCpg("{cpg}")
import upickle.default._

val symbols = List({symbols})
val MAX_HOPS = {max_hops}

def bfsCallers(startSym: String): List[Map[String,String]] = {{
  var frontier = cpg.method.nameExact(startSym).l
  var visited = frontier.map(_.fullName).toSet
  var allEdges: List[Map[String,String]] = List()

  for (hop <- 1 to MAX_HOPS) {{
    var nextFrontier: List[io.shiftleft.codepropertygraph.generated.nodes.Method] = List()
    for (m <- frontier) {{
      val callers = m.callIn.l.flatMap {{ call =>
        val cm = call.method
        if (!visited.contains(cm.fullName)) {{
          visited = visited + cm.fullName
          nextFrontier = cm :: nextFrontier
          Some(Map(
            "callee" -> m.name,
            "callee_file" -> m.filename,
            "caller" -> cm.name,
            "caller_file" -> cm.filename,
            "line" -> call.lineNumber.getOrElse(-1).toString,
            "hop" -> hop.toString,
            "root_symbol" -> startSym
          ))
        }} else None
      }}
      allEdges = allEdges ++ callers
    }}
    frontier = nextFrontier.distinct
  }}
  allEdges
}}

val result = symbols.map(s => (s, bfsCallers(s))).toMap
val pw = new java.io.PrintWriter("{out}")
pw.write(write(result, indent=2))
pw.close()
println("JOERN_MULTIHOP_DONE")
'''


def run_repo(repo: str):
    cfg = SCOPES[repo]
    cpg = JOERN_DIR / f"cpg_{repo}.bin"
    if not cpg.exists():
        print(f"[{repo}] CPG not found, skipping")
        return

    out_json = HERE / f"hops_{repo}.json"
    if out_json.exists():
        print(f"[{repo}] hops file exists, skipping")
        return

    inj_all = load_manifest()
    symbols = sorted({i["symbol"] for i in inj_all
                      if i["repo"] == repo and i["symbol"]})
    if not symbols:
        print(f"[{repo}] no symbols, skipping")
        return

    sc = HERE / f"query_hops_{repo}.sc"
    sc.write_text(QUERY_TEMPLATE.format(
        cpg=str(cpg), out=str(out_json), max_hops=MAX_HOPS,
        symbols=", ".join(f'"{s}"' for s in symbols)))

    print(f"[{repo}] querying {len(symbols)} symbols with {MAX_HOPS}-hop BFS ...", flush=True)
    r = subprocess.run(["joern", "--script", str(sc)],
                       capture_output=True, text=True, timeout=1800)
    if "JOERN_MULTIHOP_DONE" in r.stdout and out_json.exists():
        edges = json.loads(out_json.read_text())
        total = sum(len(v) for v in edges.values())
        by_hop = {}
        for sym, elist in edges.items():
            for e in elist:
                h = e.get("hop", "?")
                by_hop[h] = by_hop.get(h, 0) + 1
        print(f"  {total} edges: {dict(sorted(by_hop.items()))}")
    else:
        print(f"  QUERY FAILED")
        print(f"  stdout (tail): {r.stdout[-500:]}")
        print(f"  stderr (tail): {r.stderr[-500:]}")


def main():
    for repo in SCOPES:
        run_repo(repo)


if __name__ == "__main__":
    main()
