from __future__ import annotations
from pathlib import Path
from typing import Callable

import pytest
import yaml


# ────────────────────────────────────────────────────────────────
# Paths
# ────────────────────────────────────────────────────────────────


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def schema_v1(repo_root: Path) -> Path:
    return repo_root / "schema" / "v1_0_0" / "manifest.schema.json"


@pytest.fixture
def fixtures_repo(repo_root: Path) -> Path:
    return repo_root / "tests" / "fixtures" / "basic_repo"


# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────


def _deep_merge(base: dict, override: dict | None) -> dict:
    result = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


@pytest.fixture
def base_manifest(tmp_path: Path) -> Callable[[dict | None], Path]:
    """Create a valid minimal manifest for mutation and return its path."""

    def _make(overrides: dict | None = None) -> Path:
        base = {
            "schema_version": "1.0.0",
            "name": "labki-demo",
            "last_updated": "2025-09-22T00:00:00Z",
            "pages": {},
            "packs": {},
        }
        data = _deep_merge(base, overrides or {})
        mpath = tmp_path / "manifest.yml"
        mpath.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return mpath

    return _make


@pytest.fixture
def tmp_page(tmp_path: Path) -> Callable[..., dict]:
    """Create a valid dummy page and return its manifest entry."""

    def _create(
        namespace: str = "Template", name: str = "Example", content: str = "== Example =="
    ) -> dict:
        rel_dir = "pages/Templates" if namespace == "Template" else "pages"
        rel_path = f"{rel_dir}/{namespace}_{name}.wiki"
        out = tmp_path / rel_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        return {"file": rel_path, "last_updated": "2025-09-22T00:00:00Z"}

    return _create
