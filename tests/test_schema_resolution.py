from __future__ import annotations

from pathlib import Path

import pytest

from labki_packs_tools.validation.repo_validator import validate_repo
from labki_packs_tools.validation.schema_resolver import resolve_schema


def test_schema_version_resolves_correctly(tmp_path: Path, base_manifest, tmp_page):
    """Schema version in manifest should resolve to the correct local schema file."""
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "1.0.0",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )

    schema_path = resolve_schema(mpath)
    assert schema_path.exists()
    assert schema_path.parent.name == "v1_0_0"
    assert schema_path.name == "manifest.schema.json"


def test_unknown_schema_version_raises(tmp_path: Path, base_manifest, tmp_page):
    """resolve_schema() should raise ValueError when schema_version is not mapped."""
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "9.9.9",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )

    with pytest.raises(ValueError):
        resolve_schema(mpath)


def test_validate_repo_handles_unknown_schema_version(tmp_path: Path, base_manifest, tmp_page):
    """validate_repo() should fail gracefully when schema_version is unmapped."""
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "9.9.9",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )

    rc, results = validate_repo(mpath)
    assert rc != 0
    assert any("schema_version" in e.message or "not found" in e.message for e in results.errors)
