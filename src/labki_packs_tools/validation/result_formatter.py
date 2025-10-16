from __future__ import annotations

import json
import os
import sys
from typing import Iterable

from labki_packs_tools.validation.result_types import ValidationItem, ValidationResults


# ────────────────────────────────────────────────
# Color utilities
# ────────────────────────────────────────────────

def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    return term != "dumb"


USE_COLOR = _supports_color()


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def print_section(title: str) -> None:
    print(f"\n{_c(title, '1')}")  # bold


# ────────────────────────────────────────────────
# Level-specific printing
# ────────────────────────────────────────────────

def _print_item(item: ValidationItem) -> None:
    if item.level == "error":
        print(f"{_c('ERROR:', '31')} {item}")
    elif item.level == "warning":
        print(f"{_c('WARNING:', '33')} {item}")
    elif item.level == "info":
        print(f"{_c('INFO:', '32')} {item}")
    else:
        print(item)


# ────────────────────────────────────────────────
# Main printing entry points
# ────────────────────────────────────────────────

def print_results(results: ValidationResults, *, title: str | None = None) -> None:
    if title:
        print_section(title)

    if results.errors:
        print_section("Errors")
        for item in results.errors:
            _print_item(item)

    if results.warnings:
        print_section("Warnings")
        for item in results.warnings:
            _print_item(item)

    if results.infos:
        print_section("Info")
        for item in results.infos:
            _print_item(item)

    print_summary(results)


def print_summary(results: ValidationResults) -> None:
    color = "31" if results.has_errors else ("33" if results.has_warnings else "32")
    print(f"\n{_c('Validation completed:', color)} {results.summary()}")


# ────────────────────────────────────────────────
# JSON output mode
# ────────────────────────────────────────────────

def print_results_json(results: ValidationResults) -> None:
    payload = {
        "summary": {
            "errors": len(results.errors),
            "warnings": len(results.warnings),
            "infos": len(results.infos),
            "exit_code": results.rc,
        },
        "items": [item.__dict__ for item in results],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


# ────────────────────────────────────────────────
# Aggregate printing
# ────────────────────────────────────────────────

def aggregate_print(results_list: Iterable[ValidationResults]) -> ValidationResults:
    aggregate = ValidationResults()
    for res in results_list:
        aggregate.merge(res)
        print_results(res)
    print_summary(aggregate)
    return aggregate
