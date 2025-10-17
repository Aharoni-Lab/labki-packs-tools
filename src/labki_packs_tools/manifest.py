"""
Pydantic models for manipulating the manifest within the package.

At the moment, the manually-created json schema is the
source of truth for the manifest, and this is just for programmatic use.
These models are thus *not* strictly validating,
e.g. the fields don't have the correct regex patterns
to avoid defining them twice in a conflicting way.

see the `validation` subpackage.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer


def _to_utc(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    value = value.replace(tzinfo=UTC)
    return value


def _to_isoformat(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


UTCDateTime = Annotated[datetime, BeforeValidator(_to_utc), PlainSerializer(_to_isoformat)]


class ManifestPage(BaseModel):
    file: str
    last_updated: UTCDateTime
    description: str | None = None


class ManifestPack(BaseModel):
    description: str | None = None
    version: str
    pages: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    schema_version: str = "1.0.0"
    name: str
    last_updated: UTCDateTime | None = None
    pages: dict[str, ManifestPage] = Field(default_factory=dict)
    packs: dict[str, ManifestPack] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path | str) -> "Manifest":
        path = Path(path)
        with open(path) as f:
            data = yaml.safe_load(f)
        return Manifest(**data)
