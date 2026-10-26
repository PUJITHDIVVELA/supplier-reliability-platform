"""
Supplier Reliability Platform CLI.
Provides high-fidelity terminal commands for generation, validation, reproducibility verification,
supplier explainability inspection, and launching the interactive Streamlit dashboard.
"""
import sys
import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from supplier_reliability.config import DEFAULT_SEED
from supplier_reliability.generator.pipeline import run_pipeline
from supplier_reliability.storage.exporter import export_dataset, compute_file_sha256
from supplier_reliability.validator.audit_engine import AuditEngine

app = typer.Typer(
    name="supplier-reliability",
    help="Enterprise Supplier Reliability Scoring & Synthetic Data Audit Platform",
    add_completion=False,
)
console = Console()


@app.command()
def generate(
    scale: str = typer.Option("starter", "--scale", "-s", help="Scale profile: 'micro', 'starter', 'full'"),
    seed: int = typer.Option(DEFAULT_SEED, "--seed", help="Random seed for deterministic generation"),
    output_dir: Path = typer.Option(Path("./data"), "--output-dir", "-o", help="Target output directory"),
    inject_anomalies: bool = typer.Option(True, "--anomalies/--no-anomalies", help="Inject labeled edge cases"),
):
    """
    Generate synthetic relational dataset across all 11 entities + ground truth labels.
    """
    console.print(f"[bold cyan]▶ Initiating Synthetic Data Generation Pipeline...[/bold cyan]")
    console.print(f"  • Scale Profile: [bold green]{scale}[/bold green]")
    console.print(f"  • Deterministic Seed: [bold yellow]{seed}[/bold yellow]")
    console.print(f"  • Injected Anomalies: [bold magenta]{inject_anomalies}[/bold magenta]")

    with console.status("[bold green]Generating entities & computing multi-signal scores..."):
        dataset = run_pipeline(scale=scale, seed=seed, inject_anomalies=inject_anomalies)
        manifest = export_dataset(dataset, output_dir)

    console.print(f"\n[bold green]✔ Successfully Generated & Exported Dataset to {output_dir}![/bold green]\n")

    # Table of row counts
    table = Table(title="Generated Entity Summary", show_header=True, header_style="bold magenta")
    table.add_column("Entity / Table", style="dim", width=26)
    table.add_column("Record Count", justify="right", style="bold green")
    table.add_column("Key Relation", style="cyan")

    table.add_row("suppliers", str(len(dataset.suppliers)), "PK: supplier_id (SUP-000001)")
    table.add_row("sites", str(len(dataset.sites)), "FK: supplier_id")
    table.add_row("contracts", str(len(dataset.contracts)), "FK: supplier_id")
    table.add_row("purchase_orders", str(len(dataset.purchase_orders)), "FK: supplier_id, site_id, contract_id")
    table.add_row("po_lines", str(len(dataset.po_lines)), "FK: po_id")
    table.add_row("shipments", str(len(dataset.shipments)), "FK: po_id, supplier_id, site_id")
    table.add_row("delivery_events", str(len(dataset.delivery_events)), "FK: shipment_id")
    table.add_row("inspections", str(len(dataset.inspections)), "FK: shipment_id, po_id, supplier_id")
    table.add_row("invoices", str(len(dataset.invoices)), "FK: po_id, supplier_id")
    table.add_row("risk_signals", str(len(dataset.risk_signals)), "FK: supplier_id")
    table.add_row("supplier_scores", str(len(dataset.supplier_scores)), "FK: supplier_id (Explainable 6 Pillars)")
    table.add_row("ground_truth (Isolated)", str(len(dataset.ground_truth)), "Non-leaked validation labels", style="bold yellow")

    console.print(table)
    console.print(f"\n[cyan]Manifest saved at:[/cyan] [bold]{output_dir}/manifest.json[/bold]")


@app.command()
def validate(
    scale: str = typer.Option("starter", "--scale", "-s", help="Scale profile used for verification"),
    seed: int = typer.Option(DEFAULT_SEED, "--seed", help="Random seed"),
):
    """
    Execute comprehensive audit suite (PK, FK, Enums, Dates, Arithmetic, Tenancy, Provenance).
    """
    console.print(f"[bold cyan]▶ Running Audit & Integrity Engine (Seed: {seed}, Scale: {scale})...[/bold cyan]")
    dataset = run_pipeline(scale=scale, seed=seed, inject_anomalies=True)
    engine = AuditEngine(dataset)
    report = engine.run_all_validations()

    # Results Table
    table = Table(title="Audit Suite Integrity Results", show_header=True, header_style="bold blue")
    table.add_column("Rule / Anomaly Code", style="bold red")
    table.add_column("Detected Violations", justify="right", style="bold yellow")
    table.add_column("Category & Description", style="white")

    for rule, count in report.issues_by_rule.items():
        sample = next(i for i in report.issues if i.rule_code == rule)
        table.add_row(rule, str(count), sample.message[:70] + "...")

    console.print(table)

    # Benchmark vs Ground Truth
    gt_eval = report.ground_truth_evaluation
    eval_panel = Panel(
        f"[bold]Ground Truth Detection Performance:[/bold]\n"
        f"  • Injected Anomalies: [bold cyan]{gt_eval['total_ground_truth_anomalies']}[/bold cyan]\n"
        f"  • Detected Violations: [bold yellow]{gt_eval['total_detected_anomalies']}[/bold yellow]\n"
        f"  • True Positives (TP): [bold green]{gt_eval['true_positives']}[/bold green]\n"
        f"  • False Positives (FP): [bold]{gt_eval['false_positives']}[/bold]\n"
        f"  • False Negatives (FN): [bold]{gt_eval['false_negatives']}[/bold]\n"
        f"  • [bold green]Precision: {gt_eval['precision'] * 100:.2f}%[/bold green]\n"
        f"  • [bold green]Recall:    {gt_eval['recall'] * 100:.2f}%[/bold green]\n"
        f"  • [bold green]F1-Score:  {gt_eval['f1_score']:.4f}[/bold green]\n",
        title="Validation Accuracy vs Ground Truth",
        border_style="green" if gt_eval["precision"] == 1.0 and gt_eval["recall"] == 1.0 else "yellow"
    )
    console.print(eval_panel)


@app.command()
def reproduce(
    seed: int = typer.Option(DEFAULT_SEED, "--seed", help="Random seed to verify twice"),
    scale: str = typer.Option("starter", "--scale", help="Scale profile"),
):
    """
    Step 10: Regenerate twice with identical seed and verify identical row counts & SHA-256 checksums.
    """
    console.print(f"[bold cyan]▶ Verifying Fixed-Seed Determinism & Reproducibility (Seed: {seed})...[/bold cyan]")
    
    tmp_dir1 = Path("./data/reproduce_run_1")
    tmp_dir2 = Path("./data/reproduce_run_2")

    console.print("  • Executing Run 1...")
    ds1 = run_pipeline(scale=scale, seed=seed, inject_anomalies=True)
    manifest1 = export_dataset(ds1, tmp_dir1)

    console.print("  • Executing Run 2 (Independent Re-generation)...")
    ds2 = run_pipeline(scale=scale, seed=seed, inject_anomalies=True)
    manifest2 = export_dataset(ds2, tmp_dir2)

    # Compare checksums
    match = True
    comp_table = Table(title="Run 1 vs Run 2 Checksum & Row Verification", show_header=True, header_style="bold cyan")
    comp_table.add_column("Export File", style="white")
    comp_table.add_column("Run 1 Rows", justify="right")
    comp_table.add_column("Run 2 Rows", justify="right")
    comp_table.add_column("Run 1 SHA-256 (Prefix)", style="dim")
    comp_table.add_column("Run 2 SHA-256 (Prefix)", style="dim")
    comp_table.add_column("Status", style="bold green")

    for fpath, meta1 in manifest1["files"].items():
        meta2 = manifest2["files"].get(fpath, {})
        rows1 = meta1.get("rows", "-")
        rows2 = meta2.get("rows", "-")
        hash1 = meta1.get("sha256", "")
        hash2 = meta2.get("sha256", "")

        is_match = (rows1 == rows2) and (hash1 == hash2)
        if not is_match:
            match = False

        status_str = "[bold green]IDENTICAL[/bold green]" if is_match else "[bold red]MISMATCH[/bold red]"
        comp_table.add_row(
            fpath,
            str(rows1),
            str(rows2),
            hash1[:12] + "...",
            hash2[:12] + "...",
            status_str,
        )

    console.print(comp_table)

    if match:
        console.print(
            Panel(
                "[bold green]✔ PERFECT REPRODUCIBILITY CONFIRMED![/bold green]\n"
                "Both independent pipeline executions produced 100% bit-for-bit identical "
                "row counts, primary/foreign keys, derived calculations, and cryptographic SHA-256 hashes.",
                border_style="green",
            )
        )
    else:
        console.print("[bold red]✘ Reproducibility Check Failed![/bold red]")
        sys.exit(1)


@app.command()
def explain(
    supplier_id: str = typer.Argument(..., help="Supplier ID, e.g. SUP-000001"),
    scale: str = typer.Option("starter", "--scale", help="Scale profile"),
    seed: int = typer.Option(DEFAULT_SEED, "--seed", help="Random seed"),
):
    """
    Decompose explainable 6-pillar score for an individual supplier.
    """
    console.print(f"[bold cyan]▶ Calculating Score Breakdown for {supplier_id}...[/bold cyan]")
    dataset = run_pipeline(scale=scale, seed=seed, inject_anomalies=False)
    score = next((sc for sc in dataset.supplier_scores if sc.supplier_id == supplier_id), None)
    sup = next((s for s in dataset.suppliers if s.supplier_id == supplier_id), None)

    if not score or not sup:
        console.print(f"[bold red]Supplier {supplier_id} not found.[/bold red]")
        sys.exit(1)

    exp = score.explainability_summary
    tree = Tree(f"[bold yellow]{sup.name} ({sup.supplier_id})[/bold yellow] | [bold cyan]Score: {score.composite_reliability_score}/100[/bold cyan] | Tier: [bold green]{score.reliability_tier.value}[/bold green]")
    tree.add(f"Category: {sup.category.value} | Country: {sup.country} | Recommendation: [bold]{score.decision_recommendation.value}[/bold]")

    sub_branch = tree.add("[bold magenta]Pillar Sub-Scores (Weighted)[/bold magenta]")
    sub_branch.add(f"Delivery Score:   [cyan]{score.delivery_score:6.2f}[/cyan] (Weight: 25%) | OTD Rate: {exp['raw_metrics']['on_time_rate_pct']}%")
    sub_branch.add(f"Quality Score:    [cyan]{score.quality_score:6.2f}[/cyan] (Weight: 25%) | Defect PPM: {exp['raw_metrics']['defect_ppm']} PPM")
    sub_branch.add(f"Cost Score:       [cyan]{score.cost_score:6.2f}[/cyan] (Weight: 15%) | Spend Variance: {exp['raw_metrics']['spend_variance_pct']}%")
    sub_branch.add(f"Capacity Score:   [cyan]{score.capacity_score:6.2f}[/cyan] (Weight: 15%) | Site Utilization: {exp['raw_metrics']['capacity_utilization_pct']}%")
    sub_branch.add(f"Compliance Score: [cyan]{score.compliance_score:6.2f}[/cyan] (Weight: 10%)")
    sub_branch.add(f"Disruption Score: [cyan]{(100.0 - score.disruption_penalty):6.2f}[/cyan] (Weight: 10%) | Penalty: -{score.disruption_penalty} pts")

    drivers = tree.add("[bold red]Driver Diagnostics[/bold red]")
    drivers.add(f"Primary Drag:    [bold red]{exp['top_drivers']['primary_drag'][0]}[/bold red] ({exp['top_drivers']['primary_drag'][1]:.1f}/100)")
    drivers.add(f"Secondary Drag:  [bold yellow]{exp['top_drivers']['secondary_drag'][0]}[/bold yellow] ({exp['top_drivers']['secondary_drag'][1]:.1f}/100)")
    drivers.add(f"Strongest Asset: [bold green]{exp['top_drivers']['strongest_pillar'][0]}[/bold green] ({exp['top_drivers']['strongest_pillar'][1]:.1f}/100)")

    console.print(tree)


@app.command()
def dashboard(
    port: int = typer.Option(8501, "--port", "-p", help="Port to run Streamlit app"),
):
    """
    Launch interactive Streamlit dashboard.
    """
    import subprocess
    import os
    app_path = Path(__file__).parent / "web" / "app.py"
    console.print(f"[bold green]▶ Launching Supplier Reliability Interactive Dashboard on http://localhost:{port}...[/bold green]")
    cmd = ["streamlit", "run", str(app_path), "--server.port", str(port), "--server.headless", "true"]
    subprocess.run(cmd)


if __name__ == "__main__":
    app()
