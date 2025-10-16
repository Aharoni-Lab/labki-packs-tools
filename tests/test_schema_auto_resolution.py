from __future__ import annotations

from pathlib import Path
import pytest

from labki_packs_tools.validation.schema_resolver import resolve_schema
from labki_packs_tools.validation.repo_validator import validate_repo


def test_schema_resolution(tmp_path: Path, base_manifest, tmp_page):
    """Ensure schema_version resolves to the correct local schema file."""
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "1.0.0",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )

    schema_path = resolve_schema(mpath)
    assert schema_path.exists(), "Resolved schema path should exist"
    assert schema_path.parent.name == "v1_0_0"
    assert schema_path.name == "manifest.schema.json"


def test_schema_auto_unmapped_version_fails(tmp_path: Path, base_manifest, tmp_page):
    """Schema resolution should raise ValueError for unknown schema_version."""
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


def test_validate_repo_fails_for_unmapped_schema(tmp_path: Path, base_manifest, tmp_page):
    """End-to-end: validate_repo should gracefully fail on unmapped schema_version."""
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "9.9.9",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )

    rc, results = validate_repo(mpath)
    # The new system catches this internally and records a structured ValidationItem
    assert rc
