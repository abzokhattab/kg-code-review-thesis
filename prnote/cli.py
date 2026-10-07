"""CLI for prnote."""

import sys
from typing import Optional
import typer
from rich.console import Console

from prnote import kg, evidence, note, eval as eval_module, rag, hybrid, ablation, report

app = typer.Typer(
    name="prnote",
    help="Evidence-Anchored PR Review Note Generator",
    no_args_is_help=True
)

console = Console()


# KG commands
kg_app = typer.Typer(help="Knowledge Graph operations")
app.add_typer(kg_app, name="kg")


@kg_app.command("build")
def kg_build(
    repo: str = typer.Option(..., "--repo", help="Path to repository"),
    base: str = typer.Option(..., "--base", help="Base commit SHA"),
    head: str = typer.Option(..., "--head", help="Head commit SHA"),
    out: str = typer.Option("./data/kg", "--out", help="Output directory for KG"),
    pr_title: Optional[str] = typer.Option(None, "--title", help="PR title"),
    owners: Optional[str] = typer.Option(None, "--owners", help="Path to CODEOWNERS file"),
    issues: Optional[str] = typer.Option(None, "--issues", help="Path to issues JSON file"),
):
    """Build knowledge graph from repository."""
    try:
        kg.build(
            repo=repo,
            base=base,
            head=head,
            out=out,
            pr_title=pr_title,
            owners_path=owners,
            issues_json=issues
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# RAG commands
rag_app = typer.Typer(help="RAG (Retrieval-Augmented Generation) operations")
app.add_typer(rag_app, name="rag")


@rag_app.command("build")
def rag_build(
    repo: str = typer.Option(..., "--repo", help="Path to repository"),
    out: str = typer.Option("./data/rag", "--out", help="Output directory for RAG index"),
    use_openai: bool = typer.Option(True, "--openai/--local", help="Use OpenAI embeddings (or local)"),
):
    """Build RAG index from repository code."""
    try:
        rag.build_rag_index(
            repo=repo,
            out=out,
            use_openai=use_openai
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@rag_app.command("query")
def rag_query(
    index: str = typer.Option(..., "--index", help="Path to RAG index directory"),
    code: str = typer.Option(..., "--code", help="Code snippet to query"),
    top_k: int = typer.Option(5, "--top-k", help="Number of results"),
    use_openai: bool = typer.Option(True, "--openai/--local", help="Use OpenAI embeddings (must match build)"),
):
    """Query RAG index for similar code."""
    try:
        results = rag.query_rag(
            index_dir=index,
            query_code=code,
            top_k=top_k,
            use_openai=use_openai
        )
        
        console.print("\n[bold]Similar Code Chunks:[/bold]\n")
        for i, result in enumerate(results, 1):
            console.print(f"{i}. {result['metadata']['file']} (lines {result['metadata']['start_line']}-{result['metadata']['end_line']})")
            console.print(f"   Similarity: {1.0 - result['distance']:.3f}" if result['distance'] else "   Similarity: N/A")
            console.print()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@rag_app.command("pack")
def rag_pack(
    repo: str = typer.Option(..., "--repo", help="Path to repository"),
    index: str = typer.Option(..., "--index", help="Path to RAG index directory"),
    base: str = typer.Option(..., "--base", help="Base commit SHA"),
    head: str = typer.Option(..., "--head", help="Head commit SHA"),
    out: str = typer.Option("./data/rag_evidence.json", "--out", help="Output path for RAG evidence pack"),
    max_results: int = typer.Option(10, "--max-results", help="Maximum similar chunks to include"),
    use_openai: bool = typer.Option(True, "--openai/--local", help="Use OpenAI embeddings"),
):
    """Create RAG-only evidence pack with semantically similar code."""
    try:
        rag.pack_rag_evidence(
            repo=repo,
            rag_dir=index,
            base=base,
            head=head,
            out=out,
            max_results=max_results,
            use_openai=use_openai
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Hybrid commands
hybrid_app = typer.Typer(help="Hybrid (KG + RAG) operations")
app.add_typer(hybrid_app, name="hybrid")


@hybrid_app.command("pack")
def hybrid_pack(
    repo: str = typer.Option(..., "--repo", help="Path to repository"),
    kg: str = typer.Option(..., "--kg", help="Path to KG directory"),
    rag: str = typer.Option(..., "--rag", help="Path to RAG index directory"),
    base: str = typer.Option(..., "--base", help="Base commit SHA"),
    head: str = typer.Option(..., "--head", help="Head commit SHA"),
    out: str = typer.Option("./data/hybrid_evidence.json", "--out", help="Output path for hybrid evidence pack"),
    max_tests: int = typer.Option(3, "--max-tests", help="Maximum tests from KG"),
    max_rag: int = typer.Option(5, "--max-rag", help="Maximum RAG results"),
    use_openai: bool = typer.Option(True, "--openai/--local", help="Use OpenAI embeddings for RAG"),
):
    """Assemble hybrid evidence pack combining KG and RAG."""
    try:
        hybrid.pack_hybrid(
            repo=repo,
            kg_dir=kg,
            rag_dir=rag,
            base=base,
            head=head,
            out=out,
            max_tests=max_tests,
            max_rag_results=max_rag,
            use_openai=use_openai
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Evidence commands
evidence_app = typer.Typer(help="Evidence pack operations")
app.add_typer(evidence_app, name="evidence")


@evidence_app.command("pack")
def evidence_pack(
    repo: str = typer.Option(..., "--repo", help="Path to repository"),
    kg: str = typer.Option(..., "--kg", help="Path to KG directory"),
    base: str = typer.Option(..., "--base", help="Base commit SHA"),
    head: str = typer.Option(..., "--head", help="Head commit SHA"),
    out: str = typer.Option("./data/evidence.json", "--out", help="Output path for evidence pack"),
    max_tests: int = typer.Option(3, "--max-tests", help="Maximum tests to include"),
    max_issues: int = typer.Option(2, "--max-issues", help="Maximum issues to include"),
):
    """Assemble evidence pack from KG."""
    try:
        evidence.pack(
            repo=repo,
            kg=kg,
            base=base,
            head=head,
            out=out,
            max_tests=max_tests,
            max_issues=max_issues
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Note commands
note_app = typer.Typer(help="Note generation and linting")
app.add_typer(note_app, name="note")


@note_app.command("generate")
def note_generate(
    mode: str = typer.Option("kg", "--mode", help="Generation mode: baseline, kg, or hybrid"),
    evidence: Optional[str] = typer.Option(None, "--evidence", help="Path to evidence.json (for kg/hybrid mode)"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Path to repository (for baseline mode)"),
    base: Optional[str] = typer.Option(None, "--base", help="Base commit SHA (for baseline mode)"),
    head: Optional[str] = typer.Option(None, "--head", help="Head commit SHA (for baseline mode)"),
    model: Optional[str] = typer.Option(None, "--model", help="Model identifier (e.g., openai:gpt-4o)"),
    out: str = typer.Option("./outputs/note.md", "--out", help="Output path for note"),
    baseline: bool = typer.Option(False, "--baseline", help="Use baseline mode (legacy flag)"),
):
    """Generate review note using LLM."""
    try:
        note.generate(
            evidence=evidence,
            out=out,
            mode=mode,
            repo=repo,
            base=base,
            head=head,
            model=model,
            baseline=baseline
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@note_app.command("lint")
def note_lint(
    note_path: str = typer.Option(..., "--note", help="Path to note markdown file"),
    repo: str = typer.Option(..., "--repo", help="Path to repository"),
    head: str = typer.Option(..., "--head", help="Head commit SHA"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Lint review note for validity."""
    try:
        exit_code = note.lint(
            note=note_path,
            repo=repo,
            head=head,
            verbose=verbose
        )
        raise typer.Exit(code=exit_code)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Eval commands
eval_app = typer.Typer(help="Evaluation operations")
app.add_typer(eval_app, name="eval")


@eval_app.command("quick")
def eval_quick(
    repo: str = typer.Option(..., "--repo", help="Path to repository"),
    notes: str = typer.Option(..., "--notes", help="Directory containing note files"),
    out: str = typer.Option("./eval/quick_metrics.json", "--out", help="Output path for metrics"),
    head: Optional[str] = typer.Option(None, "--head", help="Head commit SHA"),
):
    """Compute quick evaluation metrics."""
    try:
        eval_module.quick(
            repo=repo,
            notes=notes,
            out=out,
            head=head
        )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Ablation commands
ablation_app = typer.Typer(help="Ablation study operations")
app.add_typer(ablation_app, name="ablation")


@ablation_app.command("kg")
def ablation_kg(
    pr_ids: str = typer.Option("1,2,3,5,6", "--prs", help="Comma-separated PR IDs"),
    data_dir: str = typer.Option("./data/luca_prs", "--data", help="Data directory"),
    out: str = typer.Option("./data/ablation", "--out", help="Output directory"),
):
    """Run KG ablation study (remove tests/deps/owners)."""
    try:
        ids = [int(x.strip()) for x in pr_ids.split(",")]
        ablation.run_kg_ablation_study(ids, data_dir, out)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@ablation_app.command("rag")
def ablation_rag(
    pr_ids: str = typer.Option("2,3,5,6", "--prs", help="Comma-separated PR IDs"),
    data_dir: str = typer.Option("./data/luca_prs", "--data", help="Data directory"),
    out: str = typer.Option("./data/ablation", "--out", help="Output directory"),
):
    """Run RAG ablation study (vary top-k)."""
    try:
        ids = [int(x.strip()) for x in pr_ids.split(",")]
        ablation.run_rag_ablation_study(ids, data_dir, out)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@ablation_app.command("report")
def ablation_report(
    results: str = typer.Option("./results/ablation_results.csv", "--results", help="Ablation results CSV"),
    out: str = typer.Option("./results/ablation_report.md", "--out", help="Output report path"),
):
    """Generate ablation study report."""
    try:
        ablation.generate_ablation_report(results, out)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Report commands
report_app = typer.Typer(help="Report generation operations")
app.add_typer(report_app, name="report")


@report_app.command("thesis")
def report_thesis(
    similarity: str = typer.Option("./results/luca_similarity_metrics.csv", "--similarity", help="Similarity CSV"),
    pipeline: str = typer.Option("./results/luca_pipeline_results.csv", "--pipeline", help="Pipeline CSV"),
    out: str = typer.Option("./results/THESIS_COMPARISON_REPORT.md", "--out", help="Output path"),
):
    """Generate comprehensive thesis comparison report."""
    try:
        report.generate_thesis_report(similarity, pipeline, out)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@report_app.command("latex")
def report_latex(
    similarity: str = typer.Option("./results/luca_similarity_metrics.csv", "--similarity", help="Similarity CSV"),
    out: str = typer.Option("./results/thesis_table.tex", "--out", help="Output path"),
):
    """Generate LaTeX table for thesis."""
    try:
        report.generate_latex_table(similarity, out)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@report_app.command("summary")
def report_summary(
    similarity: str = typer.Option("./results/luca_similarity_metrics.csv", "--similarity", help="Similarity CSV"),
    out: str = typer.Option("./results/thesis_summary.csv", "--out", help="Output path"),
):
    """Generate summary CSV for thesis."""
    try:
        report.generate_csv_summary(similarity, out)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

