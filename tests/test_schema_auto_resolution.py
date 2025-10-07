from __future__ import annotations
from pathlib import Path

from labki_packs_tools.validation.repo_validator import validate_repo


def test_schema_auto_requires_exact_version(tmp_path: Path, base_manifest, tmp_page):
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "1.0.0",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )
    rc, result = validate_repo(mpath, "auto")
    assert rc == 0


def test_schema_auto_unmapped_version_fails(tmp_path: Path, base_manifest, tmp_page):
    page = tmp_page(name="Example")
    mpath = base_manifest(
        {
            "schema_version": "9.9.9",
            "pages": {"Template:Example": page},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )
    rc, result = validate_repo(mpath, "auto")
    assert rc != 0
    assert any("Schema version '9.9.9' not found in index" in e for e in result.errors)
