"""CLI interface for nomenclator."""

import json
import sys

import click

try:
    from nomenclator.core import Scanner
    from nomenclator.rules import RuleEngine
    from nomenclator.report import ReportGenerator
    from nomenclator.apply import SuggestionApplier
except ImportError:
    # Allow running as module for development
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from nomenclator.core import Scanner
    from nomenclator.rules import RuleEngine
    from nomenclator.report import ReportGenerator
    from nomenclator.apply import SuggestionApplier


@click.group()
def main():
    """Nomenclator - A gentle naming-convention intelligence bot."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--out", "-o", default="scan.json", help="Output file for scan results")
@click.option("--rules", "-r", default="rules.yaml", help="Path to rules YAML file")
def scan(path: str, out: str, rules: str):
    """Scan a directory or file for naming patterns."""
    click.echo(f"Scanning {path}...")

    scanner = Scanner(rules_path=rules)
    scan_result = scanner.scan(path)

    # Apply rules
    rule_engine = RuleEngine(rules_path=rules)
    scan_result = rule_engine.analyze_scan(scan_result)

    # Save results
    with open(out, "w", encoding="utf-8") as f:
        json.dump(scan_result, f, indent=2)

    stats = scan_result.get("violation_statistics", {})
    scan_stats = scan_result.get("statistics", {})

    click.echo(f"✓ Scanned {scan_stats.get('total_items', 0)} items")
    click.echo(f"✓ Found {stats.get('total', 0)} violations")
    click.echo(f"  - Errors: {stats.get('by_severity', {}).get('error', 0)}")
    click.echo(f"  - Warnings: {stats.get('by_severity', {}).get('warning', 0)}")
    click.echo(f"✓ Results saved to {out}")


@main.command()
@click.option("--format", "-f", type=click.Choice(["html", "json", "csv"]), default="html",
              help="Report format")
@click.option("--in", "-i", "input_file", default="scan.json", help="Input scan result file")
@click.option("--out", "-o", help="Output file (default: report.{format})")
def report(format: str, input_file: str, out: str):
    """Generate a report from scan results."""
    if not out:
        out = f"report.{format}"

    # Load scan results
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            scan_result = json.load(f)
    except FileNotFoundError:
        click.echo(f"Error: {input_file} not found. Run 'nomenclator scan' first.", err=True)
        sys.exit(1)

    # Generate report
    generator = ReportGenerator(scan_result)
    generator.generate(format, out)

    click.echo(f"✓ Report generated: {out}")


@main.command()
@click.option("--in", "-i", "input_file", default="scan.json", help="Input scan result file")
@click.option("--dry-run/--no-dry-run", default=True, help="Show what would be changed")
@click.option("--out", "-o", help="Output file for dry-run plan")
def apply_suggestions(input_file: str, dry_run: bool, out: str):
    """Apply naming suggestions to codebase."""
    try:
        applier = SuggestionApplier(input_file)
    except FileNotFoundError:
        click.echo(f"Error: {input_file} not found. Run 'nomenclator scan' first.", err=True)
        sys.exit(1)

    if dry_run:
        click.echo("Generating dry-run plan...")
        plan_output = applier.apply_dry_run(out)
        if not out:
            click.echo(plan_output)
    else:
        click.echo("Applying suggestions...")
        applier.apply(dry_run=False)
        click.echo("✓ Suggestions applied")


if __name__ == "__main__":
    main()
