from __future__ import annotations

from pathlib import Path

import pytest

from labki_packs_tools.validation.repo_schema_resolver import resolve_schema
from labki_packs_tools.validation.repo_validator import validate_repo


def test_schema_resolution(tmp_path: Path, base_manifest, tmp_page):
    """The schema specified in schema_version is correctly resolved, when present"""
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "1.0.0",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )
    schema_path = resolve_schema(mpath)
    assert schema_path.parent.name == "v1_0_0"
    assert schema_path.name == "manifest.schema.json"
    assert schema_path.exists()


def test_schema_auto_unmapped_version_fails(tmp_path: Path, base_manifest, tmp_page):
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "9.9.9",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )
    with pytest.raises(ValueError):
        validate_repo(mpath)
