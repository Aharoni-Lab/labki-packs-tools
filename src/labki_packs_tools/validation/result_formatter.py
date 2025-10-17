from __future__ import annotations

import json
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from labki_packs_tools.validation.result_types import ValidationItem, ValidationResults

console = Console()


def print_results(results: ValidationResults, *, title: str | None = None) -> None:
    """Pretty-print results using Rich tables and summary."""
    if title:
        console.rule(f"[bold cyan]{title}")

    _print_section(results.errors, "Errors", "red")
    _print_section(results.warnings, "Warnings", "yellow")
    _print_section(results.infos, "Info", "green")

    # Summary panel at the bottom
    color = "red" if results.has_errors else ("yellow" if results.has_warnings else "green")
    text = Text(f"Validation completed: {results.summary()}", style=f"bold {color}")
    console.print(Panel(text, border_style=color))


def _print_section(items: list[ValidationItem], label: str, color: str) -> None:
    if not items:
        return
    table = Table(title=f"[bold {color}]{label}[/bold {color}]", show_header=False)
    table.add_column("Level", style=color, width=10)
    table.add_column("Code", style="bold magenta", width=16)
    table.add_column("Message", style="white")

    for item in items:
        table.add_row(item.level.upper(), item.code or "-", item.message)
    console.print(table)


def print_results_json(results: ValidationResults) -> None:
    """Emit JSON for programmatic use."""
    payload = {
        "summary": {
            "errors": len(results.errors),
            "warnings": len(results.warnings),
            "infos": len(results.infos),
            "exit_code": results.rc,
        },
        "items": [item.__dict__ for item in results],
    }
    console.print_json(json.dumps(payload, indent=2, sort_keys=True))


def aggregate_print(results_list: Iterable[ValidationResults]) -> ValidationResults:
    """Print multiple result sets and return an aggregate."""
    aggregate = ValidationResults()
    for res in results_list:
        aggregate.merge(res)
        res.print()
    return aggregate
