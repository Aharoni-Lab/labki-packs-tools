from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from labki_packs_tools.ingest import update_manifest
from labki_packs_tools.manifest import Manifest


@click.command("ingest")
@click.argument(
    "export",
    type=click.Path(),
)
@click.option(
    "-m",
    "--manifest",
    type=click.Path(),
    help="Path to a manifest.yml file, if none is passed, look in cwd.",
)
def ingest(export: Path, manifest: Path | None = None) -> None:
    """
    Ingest pages from a mediawiki XML export to a manifest
    (created from `Special:Export`, see: https://www.mediawiki.org/wiki/Help:Export)

    Updates any pages with a more recent timestamp than in the manifest,
    adds any pages that are missing,
    and writes the content of the pages when updated or added.
    """
    if not export:
        return
    else:
        export = Path(export)
        if not export.exists():
            raise FileNotFoundError(f"Export file not found at {export}")

    if not manifest:
        manifests = list(Path.cwd().glob("manifest.y*ml"))
        if not manifests:
            raise FileNotFoundError("No manifest passed, and none found in current directory")
        manifest = manifests[0]
    else:
        manifest = Path(manifest)

    updated = update_manifest(manifest, export)
    if not updated:
        click.echo("No pages updated")
        return

    new_manifest = Manifest.from_yaml(manifest)
    table = Table(title="Pages updated")
    table.add_column("Title")
    table.add_column("Last Updated")
    table.add_column("File")
    for page in updated:
        table.add_row(page.name, page.last_updated.isoformat(), new_manifest.pages[page.name].file)

    console = Console()
    console.print(table)
