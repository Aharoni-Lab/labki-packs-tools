from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Optional
from packaging.version import Version, InvalidVersion

from labki_packs_tools.validation.result_types import ValidationItem


class Validator(ABC):
    """
    Base class for structured, version-aware validation checks.
    Subclass this to define custom rules.
    """

    code: ClassVar[str]
    message: ClassVar[str]
    level: ClassVar[str] = "error"  # or "warning", "info"
    min_version: ClassVar[Optional[str]] = None
    max_version: ClassVar[Optional[str]] = None

    registry: ClassVar[list[type[Validator]]] = []

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        Validator.registry.append(cls)

    @classmethod
    def applies_to_version(cls, version: str) -> bool:
        try:
            v = Version(version)
        except InvalidVersion:
            return True  # be permissive if unknown

        if cls.min_version and v < Version(cls.min_version):
            return False
        if cls.max_version and v > Version(cls.max_version):
            return False
        return True

    @abstractmethod
    def validate(self, *, manifest: dict, pages: dict, packs: dict) -> list[ValidationItem]:
        """Perform validation and return results."""
        raise NotImplementedError
