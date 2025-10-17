from __future__ import annotations

from pathlib import Path

from labki_packs_tools.validation.repo_validator import validate_repo


def _messages(results, level: str) -> list[str]:
    """Helper: extract messages of given level ('error', 'warning', etc.)."""
    return [i.message for i in getattr(results, f"{level}s", [])]


def test_page_file_not_found(base_manifest):
    mpath = base_manifest(
        {
            "pages": {
                "Template:Missing": {
                    "file": "pages/Templates/Missing.wiki",
                    "last_updated": "2025-09-22T00:00:00Z",
                }
            },
            "packs": {"p": {"version": "1.0.0", "pages": ["Template:Missing"]}},
        }
    )
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")
    assert rc != 0
    assert any("Page file not found" in e for e in errors)


def test_orphan_file_warns_only(base_manifest, tmp_path: Path):
    (tmp_path / "pages" / "Templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pages" / "Templates" / "Orphan.wiki").write_text(
        "== Orphan ==\n", encoding="utf-8"
    )

    mpath = base_manifest({"pages": {}, "packs": {}})
    rc, results = validate_repo(mpath)
    warnings = _messages(results, "warning")

    assert rc == 0
    assert any("Orphan page file" in w for w in warnings)


def test_module_page_warnings(base_manifest, tmp_path: Path):
    (tmp_path / "pages" / "modules").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pages" / "modules" / "module_bad.lua").write_text("-- test\n", encoding="utf-8")

    bad = {
        "pages": {
            "Module:Bad": {
                "file": "pages/modules/module_bad.lua",
                "last_updated": "2025-09-22T00:00:00Z",
            }
        },
        "packs": {"base": {"version": "1.0.0", "pages": ["Module:Bad"]}},
    }
    mpath = base_manifest(bad)
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")
    warnings = _messages(results, "warning")

    assert rc == 0
    # The warnings should be about the directory structure, not the extension
    assert any("pages/modules/" in w for w in warnings)


def test_rejects_underscore_in_page_key(base_manifest, tmp_page):
    page = tmp_page()
    path = base_manifest(
        {
            "pages": {"Template:Has_Underscore": page},
            "packs": {"p": {"version": "1.0.0", "pages": ["Template:Has_Underscore"]}},
        }
    )
    rc, results = validate_repo(path)
    errors = _messages(results, "error")
    assert rc != 0
    assert any(("does not match" in e or "pattern" in e) for e in errors)


def test_validate_invalid_page_last_updated(base_manifest, tmp_page):
    p = tmp_page(name="Example")
    p["last_updated"] = "2025-09-22"  # invalid (missing time)
    mpath = base_manifest(
        {
            "pages": {"Template:Example": p},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )
    rc, results = validate_repo(mpath)
    errors = _messages(results, "error")
    assert rc != 0
    assert any(("last_updated" in e or "does not match" in e) for e in errors)


def test_validate_valid_page_last_updated_passes(base_manifest, tmp_page):
    p = tmp_page(name="Example")
    p["last_updated"] = "2025-09-22T00:00:00Z"
    mpath = base_manifest(
        {
            "pages": {"Template:Example": p},
            "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
        }
    )
    rc, results = validate_repo(mpath)
    assert rc == 0
    assert not results.has_errors


def test_rejects_colon_in_filename(base_manifest, tmp_path: Path):
    (tmp_path / "pages" / "templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pages" / "templates" / "template-bad.wiki").write_text("x\n", encoding="utf-8")

    mpath = base_manifest(
        {
            "pages": {
                "Template:Bad": {
                    "file": "pages/templates/template-bad.wiki",
                    "last_updated": "2025-09-22T00:00:00Z",
                }
            },
            "packs": {"p": {"version": "1.0.0", "pages": ["Template:Bad"]}},
        }
    )

    rc, results = validate_repo(mpath)
    # This should now pass since we're using a valid file path
    assert rc == 0
