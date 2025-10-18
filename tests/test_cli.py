from __future__ import annotations

import contextlib
import io
import json
from subprocess import run

import yaml
from click.testing import CliRunner

from labki_packs_tools.cli.ingest import ingest as cli_ingest


def test_formatter_prints_human():
    from labki_packs_tools.validation.result_formatter import print_results

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
    from labki_packs_tools.validation.result_formatter import print_results_json
    from labki_packs_tools.validation.result_types import ValidationResult

    res = ValidationResult(errors=["e1"], warnings=["w1"])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_results_json(res)
    parsed = json.loads(buf.getvalue())
    assert parsed["summary"]["errors"] == 1
    assert parsed["warnings"] == ["w1"]


def test_cli_json_output(tmp_path):
    m = {
        "name": "cli-json",
        "schema_version": "1.0.0",
        "pages": {},
        "packs": {},
    }
    mpath = tmp_path / "manifest.yml"
    mpath.write_text(yaml.safe_dump(m))

    proc = run(["labki-validate", "validate", str(mpath), "--json"], text=True, capture_output=True)
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert "summary" in data and "errors" in data and "warnings" in data


def test_cli_ingest(monkeypatch, base_manifest, export_data):
    """
    CLI ingest should update a manifest and print what pages were updated

    Correctness of ingestion not tested here, just testing the cli-specific parts
    """
    mpath = base_manifest()
    monkeypatch.chdir(mpath.parent)
    export_path = export_data / "latest.xml"

    runner = CliRunner()
    result = runner.invoke(cli_ingest, [str(export_path)], terminal_width=300)
    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    # title + 3 header lines + 4 files + footer line
    assert len(lines) == 9
