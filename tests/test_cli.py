from __future__ import annotations

import contextlib
import io
import json
from subprocess import run

import yaml


def test_formatter_prints_human():
    """
    Ensure human-readable output includes both error and warning sections.
    """
    from labki_packs_tools.validation.result_formatter import print_results
    from labki_packs_tools.validation.result_types import ValidationItem, ValidationResults

    # Create a fake result set
    results = ValidationResults()
    results.add(ValidationItem(message="err1", level="error"))
    results.add(ValidationItem(message="warn1", level="warning"))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_results(results, title="Test Section")

    out = buf.getvalue()
    assert "Errors" in out
    assert "Warnings" in out
    assert "Validation completed" in out


def test_formatter_prints_json():
    """
    Ensure JSON output mode produces valid JSON and correct counts.
    """
    from labki_packs_tools.validation.result_formatter import print_results_json
    from labki_packs_tools.validation.result_types import ValidationItem, ValidationResults

    results = ValidationResults()
    results.add(ValidationItem(message="e1", level="error"))
    results.add(ValidationItem(message="w1", level="warning"))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_results_json(results)

    parsed = json.loads(buf.getvalue())
    assert parsed["summary"]["errors"] == 1
    assert parsed["summary"]["warnings"] == 1
    assert "e1" in json.dumps(parsed)
    assert "w1" in json.dumps(parsed)


def test_cli_json_output(tmp_path):
    """
    Verify end-to-end CLI output in JSON mode runs and returns proper structure.
    """
    m = {
        "name": "cli-json",
        "schema_version": "1.0.0",
        "pages": {},
        "packs": {},
    }
    mpath = tmp_path / "manifest.yml"
    mpath.write_text(yaml.safe_dump(m))

    proc = run(
        ["labki-validate", "validate", str(mpath), "--json"],
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0, f"CLI failed: {proc.stderr}"
    data = json.loads(proc.stdout)

    assert "summary" in data
    assert "items" in data
    assert all(k in data["summary"] for k in ["errors", "warnings", "exit_code"])

