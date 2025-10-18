from __future__ import annotations

from labki_packs_tools.validation.repo_validator import validate_repo


def _messages(results, level: str) -> list[str]:
    """Helper: extract messages of a given level ('error', 'warning', etc.)."""
    return [i.message for i in getattr(results, f"{level}s", [])]


def test_pack_cycle_detection(base_manifest):
    mpath = base_manifest(
        {
            "packs": {
                "a": {"version": "1.0.0", "pages": [], "depends_on": ["b"]},
                "b": {"version": "1.0.0", "pages": [], "depends_on": ["a"]},
            }
        }
    )
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")

    assert rc != 0
    assert any("cycle" in e for e in errors)


def test_pack_references_unknown_page(base_manifest):
    mpath = base_manifest(
        {"packs": {"x": {"version": "1.0.0", "pages": ["Template:Missing"]}}, "pages": {}}
    )
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")

    assert rc != 0
    assert any("references unknown page" in e for e in errors)


def test_pack_version_must_be_semver(base_manifest):
    mpath = base_manifest({"packs": {"p": {"version": "v1", "pages": []}}})
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")

    assert rc != 0
    assert any("semantic version" in e for e in errors)


def test_depends_on_unknown_pack_id(base_manifest):
    mpath = base_manifest({"packs": {"p": {"version": "1.0.0", "pages": [], "depends_on": ["q"]}}})
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")

    assert rc != 0
    assert any("depends_on unknown pack id" in e for e in errors)


def test_pack_pages_must_be_array(base_manifest, tmp_page):
    p = tmp_page(name="T")
    mpath = base_manifest(
        {"pages": {"Template:T": p}, "packs": {"p": {"version": "1.0.0", "pages": "Template:T"}}}
    )
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")

    assert rc != 0
    assert any("pages must be an array" in e for e in errors)


def test_duplicate_page_across_packs(base_manifest, tmp_page):
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
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")

    assert rc != 0
    assert any("included in multiple packs" in e for e in errors)
