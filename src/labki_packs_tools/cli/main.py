import click

from labki_packs_tools.cli.graph import graph_command
from labki_packs_tools.cli.ingest import ingest
from labki_packs_tools.cli.validate import validate


@click.group("labki")
def main() -> None:
    """Labki CLI - Tools for validating and visualizing Labki content packs"""


main.add_command(ingest)
main.add_command(validate)
main.add_command(graph_command)
