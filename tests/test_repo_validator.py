from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from labki_packs_tools.validation.repo_validator import validate_repo
from labki_packs_tools.validation.result_formatter import print_results, print_results_json
from labki_packs_tools.validation.result_types import ValidationResult


def test_valid_fixture_repo_passes(fixtures_repo: Path, schema_v1: Path):
    manifest = fixtures_repo / "manifest.yml"
    rc, result = validate_repo(manifest, schema_v1)
    assert rc == 0
    assert not result.errors


def test_cli_parity_like_flow(base_manifest, schema_v1: Path, tmp_page):
    page = tmp_page(name="T")
    mpath = base_manifest(
        {
            "pages": {"Template:T": page},
            "packs": {"p": {"version": "1.0.0", "pages": ["Template:T"]}},
        }
    )
    rc, result = validate_repo(mpath, schema_v1)
    assert rc == 0, f"expected success, got rc={rc}, errors={result.errors}"


def test_formatter_prints_human():
    result = type(
        "Dummy",
        (),
        {
            "errors": ["err1"],
            "warnings": ["warn1"],
            "has_errors": True,
            "has_warnings": True,
            "summary": lambda self: "1 error(s), 1 warning(s)",
        },
    )()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_results(result, title="Test Section")
    out = buf.getvalue()
    assert "Errors" in out and "Warnings" in out


def test_formatter_prints_json():
    res = ValidationResult(errors=["e1"], warnings=["w1"])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_results_json(res)
    parsed = json.loads(buf.getvalue())
    assert parsed["summary"]["errors"] == 1
    assert parsed["warnings"] == ["w1"]
