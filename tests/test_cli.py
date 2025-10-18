from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from labki_packs_tools.cli.graph import graph_command
from labki_packs_tools.cli.ingest import ingest as cli_ingest
from labki_packs_tools.cli.main import main as cli_main
from labki_packs_tools.cli.validate import validate as cli_validate


def test_formatter_prints_human(capsys):
    """
    Ensure human-readable output includes both error and warning sections.
    """
    from labki_packs_tools.validation.result_formatter import print_results
    from labki_packs_tools.validation.result_types import ValidationItem, ValidationResults

    results = ValidationResults()
    results.add(ValidationItem(message="err1", level="error"))
    results.add(ValidationItem(message="warn1", level="warning"))

    print_results(results, title="Test Section")

    out = capsys.readouterr().out
    assert "Errors" in out
    assert "Warnings" in out
    assert "Validation completed" in out


def test_formatter_prints_json(capsys):
    """
    Ensure JSON output mode produces valid JSON and correct counts.
    """
    from labki_packs_tools.validation.result_formatter import print_results_json
    from labki_packs_tools.validation.result_types import ValidationItem, ValidationResults

    results = ValidationResults()
    results.add(ValidationItem(message="e1", level="error"))
    results.add(ValidationItem(message="w1", level="warning"))

    print_results_json(results)
    out = capsys.readouterr().out

    parsed = json.loads(out)
    assert parsed["summary"]["errors"] == 1
    assert parsed["summary"]["warnings"] == 1
    assert "e1" in json.dumps(parsed)
    assert "w1" in json.dumps(parsed)


def test_cli_validate_json_output(tmp_path):
    """
    Verify end-to-end CLI validate command in JSON mode runs and returns proper structure.
    """
    m = {
        "name": "cli-json",
        "schema_version": "1.0.0",
        "pages": {},
        "packs": {},
    }
    mpath = tmp_path / "manifest.yml"
    mpath.write_text(yaml.safe_dump(m))

    runner = CliRunner()
    result = runner.invoke(cli_validate, [str(mpath), "--json"])
    
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    data = json.loads(result.output)
    assert "summary" in data and "items" in data
    assert "errors" in data["summary"] and "warnings" in data["summary"]


def test_cli_validate_human_output(tmp_path):
    """
    Verify CLI validate command produces human-readable output.
    """
    m = {
        "name": "cli-human",
        "schema_version": "1.0.0",
        "pages": {},
        "packs": {},
    }
    mpath = tmp_path / "manifest.yml"
    mpath.write_text(yaml.safe_dump(m))

    runner = CliRunner()
    result = runner.invoke(cli_validate, [str(mpath)])
    
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert "Validation results" in result.output


def test_cli_graph_dot_output(tmp_path):
    """
    Verify CLI graph command produces DOT output.
    """
    m = {
        "name": "cli-graph",
        "schema_version": "1.0.0",
        "pages": {},
        "packs": {},
    }
    mpath = tmp_path / "manifest.yml"
    mpath.write_text(yaml.safe_dump(m))

    runner = CliRunner()
    result = runner.invoke(graph_command, [str(mpath), "--format", "dot"])
    
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert "digraph Manifest" in result.output


def test_cli_graph_json_output(tmp_path):
    """
    Verify CLI graph command produces JSON output.
    """
    m = {
        "name": "cli-graph",
        "schema_version": "1.0.0",
        "pages": {},
        "packs": {},
    }
    mpath = tmp_path / "manifest.yml"
    mpath.write_text(yaml.safe_dump(m))

    runner = CliRunner()
    result = runner.invoke(graph_command, [str(mpath), "--format", "json"])
    
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    data = json.loads(result.output)
    assert "nodes" in data and "edges" in data and "meta" in data


def test_cli_main_help():
    """
    Verify main CLI shows help with all commands.
    """
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--help"])
    
    assert result.exit_code == 0
    assert "ingest" in result.output
    assert "validate" in result.output
    assert "graph" in result.output


def test_cli_main_validate_subcommand(tmp_path):
    """
    Verify main CLI validate subcommand works.
    """
    m = {
        "name": "cli-main",
        "schema_version": "1.0.0",
        "pages": {},
        "packs": {},
    }
    mpath = tmp_path / "manifest.yml"
    mpath.write_text(yaml.safe_dump(m))

    runner = CliRunner()
    result = runner.invoke(cli_main, ["validate", str(mpath), "--json"])
    
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    data = json.loads(result.output)
    assert "summary" in data


def test_cli_main_graph_subcommand(tmp_path):
    """
    Verify main CLI graph subcommand works.
    """
    m = {
        "name": "cli-main",
        "schema_version": "1.0.0",
        "pages": {},
        "packs": {},
    }
    mpath = tmp_path / "manifest.yml"
    mpath.write_text(yaml.safe_dump(m))

    runner = CliRunner()
    result = runner.invoke(cli_main, ["graph", str(mpath), "--format", "dot"])
    
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert "digraph Manifest" in result.output


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
