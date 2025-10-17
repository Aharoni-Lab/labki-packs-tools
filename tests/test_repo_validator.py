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
