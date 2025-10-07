from __future__ import annotations
from pathlib import Path

from labki_packs_tools.validation.repo_validator import validate_repo


def test_page_file_not_found(base_manifest, schema_v1: Path):
    mpath = base_manifest({
        "pages": {
            "Template:Missing": {"file": "pages/Templates/Missing.wiki", "last_updated": "2025-09-22T00:00:00Z"}
        },
        "packs": {"p": {"version": "1.0.0", "pages": ["Template:Missing"]}},
    })
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any("Page file not found" in e for e in result.errors)


def test_orphan_file_warns_only(base_manifest, schema_v1: Path, tmp_path: Path):
    (tmp_path / "pages" / "Templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pages" / "Templates" / "Orphan.wiki").write_text("== Orphan ==\n", encoding="utf-8")
    mpath = base_manifest({"pages": {}, "packs": {}})
    rc, result = validate_repo(mpath, schema_v1)
    assert rc == 0
    assert any("Orphan page file" in w for w in result.warnings)


def test_module_page_warnings(base_manifest, schema_v1: Path, tmp_path: Path):
    (tmp_path / "pages" / "Templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pages" / "Templates" / "Module_Bad.txt").write_text("x\n", encoding="utf-8")
    bad = {
        "pages": {"Module:Bad": {"file": "pages/Templates/Module_Bad.txt", "last_updated": "2025-09-22T00:00:00Z"}},
        "packs": {"base": {"version": "1.0.0", "pages": ["Module:Bad"]}},
    }
    mpath = base_manifest(bad)
    rc, result = validate_repo(mpath, schema_v1)
    assert rc == 0
    assert any(".lua extension" in w for w in result.warnings)
    assert any("pages/Modules/" in w for w in result.warnings)


def test_rejects_underscore_in_page_key(base_manifest, schema_v1: Path, tmp_page):
    page = tmp_page()
    path = base_manifest({
        "pages": {"Template:Has_Underscore": page},
        "packs": {"p": {"version": "1.0.0", "pages": ["Template:Has_Underscore"]}},
    })
    rc, result = validate_repo(path, schema_v1)
    assert rc != 0
    assert any(("does not match" in e or "pattern" in e) for e in result.errors)


def test_allows_main_namespace_title_without_colon_and_warns(base_manifest, schema_v1: Path, tmp_page):
    page = tmp_page(namespace="", name="Person")
    path = base_manifest({
        "pages": {"Person": page},
        "packs": {"p": {"version": "1.0.0", "pages": ["Person"]}},
    })
    rc, result = validate_repo(path, schema_v1)
    assert rc == 0
    assert any("Title missing namespace" in w for w in result.warnings)


def test_validate_invalid_page_last_updated(base_manifest, schema_v1: Path, tmp_page):
    p = tmp_page(name="Example")
    p["last_updated"] = "2025-09-22"  # invalid (missing time)
    mpath = base_manifest({
        "pages": {"Template:Example": p},
        "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
    })
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any(("last_updated" in e or "does not match" in e) for e in result.errors)


def test_validate_valid_page_last_updated_passes(base_manifest, schema_v1: Path, tmp_page):
    p = tmp_page(name="Example")
    p["last_updated"] = "2025-09-22T00:00:00Z"
    mpath = base_manifest({
        "pages": {"Template:Example": p},
        "packs": {"example": {"version": "1.0.0", "pages": ["Template:Example"]}},
    })
    rc, result = validate_repo(mpath, schema_v1)
    assert rc == 0


def test_rejects_colon_in_filename(base_manifest, schema_v1: Path, tmp_path: Path):
    (tmp_path / "pages" / "Templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pages" / "Templates" / "Template:Bad.wiki").write_text("x\n", encoding="utf-8")
    mpath = base_manifest({
        "pages": {"Template:Bad": {"file": "pages/Templates/Template:Bad.wiki", "last_updated": "2025-09-22T00:00:00Z"}},
        "packs": {"p": {"version": "1.0.0", "pages": ["Template:Bad"]}},
    })
    rc, result = validate_repo(mpath, schema_v1)
    assert rc != 0
    assert any(("file path must not contain ':'" in e or "does not match" in e) for e in result.errors)


