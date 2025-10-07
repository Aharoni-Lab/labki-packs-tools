from __future__ import annotations
from pathlib import Path

from labki_packs_tools.validation.repo_validator import validate_repo


def test_pack_cycle_detection(base_manifest, schema_v1: Path):
    mpath = base_manifest(
        {
            "packs": {
                "a": {"version": "1.0.0", "pages": [], "depends_on": ["b"]},
                "b": {"version": "1.0.0", "pages": [], "depends_on": ["a"]},
            }
        }
    )
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any("cycle" in e for e in result.errors)


def test_pack_references_unknown_page(base_manifest, schema_v1: Path):
    mpath = base_manifest(
        {"packs": {"x": {"version": "1.0.0", "pages": ["Template:Missing"]}}, "pages": {}}
    )
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any("references unknown page" in e for e in result.errors)


def test_pack_version_must_be_semver(base_manifest, schema_v1: Path):
    mpath = base_manifest({"packs": {"p": {"version": "v1", "pages": []}}})
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any("semantic version" in e for e in result.errors)


def test_depends_on_unknown_pack_id(base_manifest, schema_v1: Path):
    mpath = base_manifest({"packs": {"p": {"version": "1.0.0", "pages": [], "depends_on": ["q"]}}})
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any("depends_on unknown pack id" in e for e in result.errors)


def test_pack_pages_must_be_array(base_manifest, schema_v1: Path, tmp_page):
    p = tmp_page(name="T")
    mpath = base_manifest(
        {"pages": {"Template:T": p}, "packs": {"p": {"version": "1.0.0", "pages": "Template:T"}}}
    )
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any("pages must be an array" in e for e in result.errors)


def test_duplicate_page_across_packs(base_manifest, schema_v1: Path, tmp_page):
    p = tmp_page(name="Shared")
    mpath = base_manifest(
        {
            "pages": {"Template:Shared": p},
            "packs": {
                "a": {"version": "1.0.0", "pages": ["Template:Shared"]},
                "b": {"version": "1.0.0", "pages": ["Template:Shared"]},
            },
        }
    )
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any("included in multiple packs" in e for e in result.errors)
