#!/usr/bin/env python3
"""Build per-repo context artifacts on the CLEAN scopes.

  --stage joern   joern-parse each scope + CPGQL caller query   ($0, CPU)
  --stage rag     RAG embedding index per scope                 (paid, ~$0.30)

Idempotent: skips any artifact that already exists.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, REPO_ROOT, SCOPES, load_manifest, scope_dir  # noqa: E402

JOERN_DIR = OUT / "joern"
RAG_DIR = OUT / "rag"
PER_FILE_CHUNK_CAP = 25
EMBED_BATCH = 128

QUERY_TEMPLATE = '''importCpg("{cpg}")
import upickle.default._

val symbols = List({symbols})

def edgesFor(sym: String): List[Map[String,String]] = {{
  val mc = cpg.method.nameExact(sym).flatMap {{ m =>
    m.callIn.l.map {{ call =>
      val cm = call.method
      Map("callee"->m.name, "callee_file"->m.filename, "caller"->cm.name,
          "caller_file"->cm.filename, "line"->call.lineNumber.getOrElse(-1).toString,
          "kind"->"method_callIn")
    }}
  }}.l
  val cs = cpg.call.nameExact(sym).l.map {{ call =>
    val cm = call.method
    Map("callee"->sym, "callee_file"->"", "caller"->cm.name,
        "caller_file"->cm.filename, "line"->call.lineNumber.getOrElse(-1).toString,
        "kind"->"call_site")
  }}
  val tc = cpg.typeDecl.nameExact(sym).flatMap {{ t =>
    t.method.flatMap {{ m =>
      m.callIn.l.map {{ call =>
        val cm = call.method
        Map("callee"->(sym+"."+m.name), "callee_file"->m.filename, "caller"->cm.name,
            "caller_file"->cm.filename, "line"->call.lineNumber.getOrElse(-1).toString,
            "kind"->"type_method_callIn")
      }}
    }}
  }}.l
  (mc ++ cs ++ tc).distinct
}}

val result = symbols.map(s => (s, edgesFor(s))).toMap
val pw = new java.io.PrintWriter("{out}")
pw.write(write(result, indent=2))
pw.close()
println("JOERN_QUERY_DONE")
'''


def _parse_cmd(cfg, cpg: Path, scope: Path) -> list[str]:
    """joern-parse wrapper is broken for pysrc in joern 4.0.530
    (None.get); call the frontend binary directly for python."""
    if cfg["joern_language"] == "pysrc":
        import glob
        cands = glob.glob("/opt/homebrew/Cellar/joern/*/libexec/frontends/pysrc2cpg/bin/pysrc2cpg")
        if cands:
            return [cands[-1], str(scope), "--output", str(cpg)]
    return ["joern-parse", "--language", cfg["joern_language"],
            "-o", str(cpg), str(scope)]


def stage_joern():
    inj = load_manifest()
    JOERN_DIR.mkdir(parents=True, exist_ok=True)
    for repo, cfg in SCOPES.items():
        cpg = JOERN_DIR / f"cpg_{repo}.bin"
        if not cpg.exists():
            print(f"[{repo}] joern-parse ({cfg['joern_language']}) ...", flush=True)
            r = subprocess.run(
                _parse_cmd(cfg, cpg, scope_dir(repo)),
                capture_output=True, text=True, timeout=3600)
            if not cpg.exists():
                print(f"  PARSE FAILED\n  stdout: {r.stdout[-500:]}\n  stderr: {r.stderr[-500:]}")
                continue
            print(f"  cpg: {cpg.stat().st_size/1e6:.1f} MB")
        else:
            print(f"[{repo}] cpg exists ({cpg.stat().st_size/1e6:.1f} MB)")

        out_json = JOERN_DIR / f"edges_{repo}.json"
        if out_json.exists():
            print(f"  edges exist: {out_json.name}")
            continue
        symbols = sorted({i["symbol"] for i in inj
                          if i["repo"] == repo and i["symbol"]})
        sc = JOERN_DIR / f"query_{repo}.sc"
        sc.write_text(QUERY_TEMPLATE.format(
            cpg=str(cpg), out=str(out_json),
            symbols=", ".join(f'"{s}"' for s in symbols)))
        print(f"  querying {len(symbols)} symbols ...", flush=True)
        r = subprocess.run(["joern", "--script", str(sc)],
                           capture_output=True, text=True, timeout=1800)
        if "JOERN_QUERY_DONE" not in r.stdout or not out_json.exists():
            print(f"  QUERY FAILED\n  stdout: {r.stdout[-500:]}\n  stderr: {r.stderr[-500:]}")
        else:
            edges = json.loads(out_json.read_text())
            n = sum(len(v) for v in edges.values())
            print(f"  {n} raw edges for {len(edges)} symbols")


def stage_rag():
    sys.path.insert(0, str(REPO_ROOT))
    from prnote import rag  # noqa: E402
    import openai
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    for repo in SCOPES:
        out_dir = RAG_DIR / repo
        if (out_dir / "index_meta.json").exists():
            print(f"[{repo}] rag index exists")
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        scope = scope_dir(repo)
        exts = {"python": (".py",), "java": (".java",),
                "typescript": (".ts", ".tsx")}[SCOPES[repo]["language"]]
        all_chunks = []
        for p in sorted(scope.rglob("*")):
            if not (p.is_file() and p.suffix in exts):
                continue
            rel = str(p.relative_to(scope))
            content = p.read_text(errors="ignore")
            if len(content) <= 100:
                continue
            all_chunks.extend(rag.chunk_file(rel, content)[:PER_FILE_CHUNK_CAP])
        print(f"[{repo}] embedding {len(all_chunks)} chunks ...", flush=True)
        embeddings = []
        for i in range(0, len(all_chunks), EMBED_BATCH):
            batch = all_chunks[i:i + EMBED_BATCH]
            resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=[c["content"][:8000] for c in batch])
            for c, dd in zip(batch, resp.data):
                embeddings.append({"id": c["id"], "embedding": dd.embedding,
                                   "metadata": {"file": c["file"],
                                                "start_line": c["start_line"],
                                                "end_line": c["end_line"],
                                                "language": c["language"]}})
        (out_dir / "embeddings.json").write_text(json.dumps(embeddings))
        (out_dir / "chunks.json").write_text(json.dumps([
            {"id": c["id"], "file": c["file"], "start_line": c["start_line"],
             "end_line": c["end_line"], "language": c["language"],
             "content": c["content"][:1000]} for c in all_chunks]))
        (out_dir / "index_meta.json").write_text(json.dumps(
            {"version": "1.0-fast", "embedding_model": "text-embedding-3-small",
             "chunk_count": len(embeddings)}))
        print(f"  indexed {len(embeddings)} chunks")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["joern", "rag"], required=True)
    args = ap.parse_args()
    stage_joern() if args.stage == "joern" else stage_rag()
