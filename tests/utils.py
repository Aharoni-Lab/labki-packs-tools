from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# ────────────────────────────────────────────────────────────────
# General-purpose utilities
# ────────────────────────────────────────────────────────────────


def deep_merge(base: dict[str, Any], override: dict[str, Any] | None = None) -> dict[str, Any]:
    """Recursively merge dictionaries, giving precedence to override values."""
    result = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# ────────────────────────────────────────────────────────────────
# Manifest helpers
# ────────────────────────────────────────────────────────────────


def make_manifest(path: Path, overrides: dict[str, Any] | None = None) -> Path:
    """
    Create a valid minimal manifest YAML file at the given path.

    Example:
        >>> make_manifest(tmp_path, {"packs": {"p": {"version": "1.0.0", "pages": []}}})
    """
    base = {
        "schema_version": "1.0.0",
        "name": "labki-demo",
        "last_updated": "2025-09-22T00:00:00Z",
        "pages": {},
        "packs": {},
    }
    data = deep_merge(base, overrides or {})
    out_path = path / "manifest.yml"
    out_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return out_path


# ────────────────────────────────────────────────────────────────
# Page helpers
# ────────────────────────────────────────────────────────────────


def make_page_file(
    path: Path,
    *,
    namespace: str = "Template",
    name: str = "Example",
    content: str = "== Example ==",
) -> dict[str, Any]:
    """
    Create a valid dummy page file and return its manifest entry.

    Example:
        >>> make_page_file(tmp_path, namespace="Module", name="Foo")
    """
    rel_dir = "pages/Templates" if namespace == "Template" else "pages"
    rel_path = f"{rel_dir}/{namespace}_{name}.wiki"

    out = path / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")

    return {"file": rel_path, "last_updated": "2025-09-22T00:00:00Z"}
