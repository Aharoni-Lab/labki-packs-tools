from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from labki_packs_tools.validation.repo_validator import validate_repo
from labki_packs_tools.validation.result_formatter import print_results, print_results_json
from labki_packs_tools.validation.result_types import ValidationItem, ValidationResults


def test_valid_fixture_repo_passes(fixtures_repo: Path):
    manifest = fixtures_repo / "manifest.yml"
    rc, results = validate_repo(manifest)
    assert rc == 0
    assert not results.has_errors
    assert not results.errors


def test_validate_repo_end_to_end_success(base_manifest, tmp_page):
    page = tmp_page(name="T")
    mpath = base_manifest(
        {
            "pages": {"Template:T": page},
            "packs": {"p": {"version": "1.0.0", "pages": ["Template:T"]}},
        }
    )
    rc, results = validate_repo(mpath)
    assert rc == 0, f"expected success, got rc={rc}, errors={[i.message for i in results.errors]}"


def test_formatter_prints_human():
    # Build a dummy ValidationResults with fake items
    dummy = ValidationResults()
    dummy.add(ValidationItem(level="error", message="err1"))
    dummy.add(ValidationItem(level="warning", message="warn1"))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_results(dummy, title="Test Section")

    out = buf.getvalue()
    assert "Errors" in out and "Warnings" in out
    assert "err1" in out and "warn1" in out


def test_formatter_prints_json():
    results = ValidationResults()
    results.add(ValidationItem(level="error", message="e1"))
    results.add(ValidationItem(level="warning", message="w1"))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_results_json(results)

    parsed = json.loads(buf.getvalue())
    summary = parsed["summary"]
    assert summary["errors"] == 1
    assert summary["warnings"] == 1
    assert any(i["message"] == "e1" for i in parsed["items"])
