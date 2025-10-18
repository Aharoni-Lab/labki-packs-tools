import click

from labki_packs_tools.cli.ingest import ingest


@click.group("labki")
def main() -> None:
    """Labki CLI"""


main.add_command(ingest)
