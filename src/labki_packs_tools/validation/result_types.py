from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class ValidationResult:
    """
    Container for collected validation messages.

    Used by all validator modules (schema, pages, packs, etc.)
    to accumulate errors and warnings in a consistent structure.
    """

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # ────────────────────────────────────────────────
    # Convenience methods
    # ────────────────────────────────────────────────
    def add_error(self, msg: str) -> None:
        """Add a single error message."""
        if msg and msg not in self.errors:
            self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        """Add a single warning message."""
        if msg and msg not in self.warnings:
            self.warnings.append(msg)

    def extend_errors(self, msgs: Iterable[str]) -> None:
        """Add multiple error messages."""
        for m in msgs:
            self.add_error(m)

    def extend_warnings(self, msgs: Iterable[str]) -> None:
        """Add multiple warning messages."""
        for m in msgs:
            self.add_warning(m)

    def merge(self, other: ValidationResult) -> None:
        """Merge another ValidationResult into this one."""
        self.extend_errors(other.errors)
        self.extend_warnings(other.warnings)

    # ────────────────────────────────────────────────
    # Computed properties
    # ────────────────────────────────────────────────
    @property
    def rc(self) -> int:
        """Return 1 if any errors exist, else 0 (for CLI exit codes)."""
        return 1 if self.errors else 0

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    # ────────────────────────────────────────────────
    # Representation helpers
    # ────────────────────────────────────────────────
    def summary(self) -> str:
        """Return a short summary string (for logging/printing)."""
        return f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)"

    def __bool__(self) -> bool:
        """True if there are no errors (allows 'if result:' usage)."""
        return not self.has_errors
