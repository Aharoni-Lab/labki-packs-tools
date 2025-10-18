from pathlib import Path

import click

from labki_packs_tools.graph_repo import graph


@click.command("graph")
@click.argument(
    "manifest",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dot", "mermaid", "json"], case_sensitive=False),
    default="dot",
    help="Output format for the graph",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="-",
    help="Output file path (use '-' for stdout)",
)
def graph_command(manifest: Path, fmt: str, output: Path) -> None:
    """
    Generate a graph of packs and pages from a manifest.

    Creates a visual representation of the pack dependencies and page relationships.
    Supports multiple output formats: DOT (Graphviz), Mermaid, and JSON.
    """
    rc = graph(manifest, fmt=fmt, output=str(output))
    raise SystemExit(rc)
