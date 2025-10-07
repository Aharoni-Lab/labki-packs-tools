from __future__ import annotations

import json
import os
import sys
from typing import Iterable

from .result_types import ValidationResult

# ────────────────────────────────────────────────────────────────
# Color handling
# ────────────────────────────────────────────────────────────────


def _supports_color() -> bool:
    """Detect whether the current environment supports ANSI color."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    term = os.environ.get("TERM", "")
    return term != "dumb"


USE_COLOR = _supports_color()


def _c(text: str, code: str) -> str:
    """Apply color if enabled."""
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


# ────────────────────────────────────────────────────────────────
# Printing helpers
# ────────────────────────────────────────────────────────────────


def print_error(msg: str) -> None:
    print(f"{_c('ERROR:', '31')} {msg}")  # red


def print_warning(msg: str) -> None:
    print(f"{_c('WARNING:', '33')} {msg}")  # yellow


def print_info(msg: str) -> None:
    print(f"{_c('INFO:', '32')} {msg}")  # green


def print_section(title: str) -> None:
    print(f"\n{_c(title, '1')}")  # bold


# ────────────────────────────────────────────────────────────────
# Result printing orchestration
# ────────────────────────────────────────────────────────────────


def print_results(result: ValidationResult, *, title: str | None = None) -> None:
    """Human-readable console output."""
    if title:
        print_section(title)

    if result.errors:
        print_section("Errors")
        for msg in result.errors:
            print_error(msg)

    if result.warnings:
        print_section("Warnings")
        for msg in result.warnings:
            print_warning(msg)

    print_summary(result)


def print_summary(result: ValidationResult) -> None:
    """One-line colored summary."""
    color = "31" if result.has_errors else ("33" if result.has_warnings else "32")
    print(f"\n{_c('Validation completed:', color)} {result.summary()}")


# ────────────────────────────────────────────────────────────────
# JSON output mode
# ────────────────────────────────────────────────────────────────


def print_results_json(result: ValidationResult) -> None:
    """
    Emit JSON summary to stdout, suitable for CI or machine parsing.
    """
    payload = {
        "summary": {
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "exit_code": result.rc,
        },
        "errors": result.errors,
        "warnings": result.warnings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


# ────────────────────────────────────────────────────────────────
# Aggregate printing
# ────────────────────────────────────────────────────────────────


def aggregate_print(results: Iterable[ValidationResult]) -> ValidationResult:
    aggregate = ValidationResult()
    for r in results:
        aggregate.merge(r)
        print_results(r)
    print_summary(aggregate)
    return aggregate
