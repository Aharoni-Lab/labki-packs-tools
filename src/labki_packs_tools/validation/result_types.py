from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Literal, Optional


# ────────────────────────────────────────────────
# Container for multiple validation messages
# ────────────────────────────────────────────────
@dataclass
class ValidationResults:
    """
    Container for all validation messages produced during repo validation.
    Provides convenience accessors and merge methods.
    """

    _items: List[ValidationItem] = field(default_factory=list)

    def add(self, item: ValidationItem) -> None:
        self._items.append(item)

    def extend(self, items: Iterable[ValidationItem]) -> None:
        self._items.extend(items)

    def merge(self, other: ValidationResults) -> None:
        self.extend(other._items)

    # ─── Filters ─────────────────────────────────
    @property
    def errors(self) -> List[ValidationItem]:
        return [i for i in self._items if i.level == "error"]

    @property
    def warnings(self) -> List[ValidationItem]:
        return [i for i in self._items if i.level == "warning"]

    @property
    def infos(self) -> List[ValidationItem]:
        return [i for i in self._items if i.level == "info"]

    # ─── Status and summaries ────────────────────
    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    @property
    def rc(self) -> int:
        """CLI-friendly return code (1 if errors, else 0)."""
        return 1 if self.has_errors else 0

    def summary(self) -> str:
        return (
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s), "
            f"{len(self.infos)} info(s)"
        )

    def __bool__(self) -> bool:
        """True if no errors."""
        return not self.has_errors

    def __iter__(self):
        yield from self._items


# ────────────────────────────────────────────────
# Core structured result
# ────────────────────────────────────────────────
@dataclass
class ValidationItem:
    """
    A single validation message with structured context.
    """

    level: Literal["info", "warning", "error"]
    message: str
    repo_url: Optional[str] = None
    page: Optional[str] = None
    code: Optional[str] = None  # optional code for documentation / silencing

    def __str__(self) -> str:
        loc = f"{self.repo_url or ''} / {self.page or ''}".strip(" /")
        prefix = f"[{self.level.upper()}]"
        return f"{prefix} {loc}: {self.message}" if loc else f"{prefix} {self.message}"
