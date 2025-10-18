from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from labki_packs_tools.const import SCHEMA_DIR, SCHEMA_INDEX
from labki_packs_tools.utils import load_json, load_yaml


def resolve_schema(manifest: Path | str | dict[str, Any]) -> Path:
    """
    Resolve and return the correct JSON Schema path for a given manifest.

    This function determines which schema file to use based on the `schema_version`
    field in the manifest. It supports both path and dict inputs.

    Args:
        manifest: Either a path to a manifest YAML file or a pre-loaded manifest dict.

    Returns:
        The resolved Path to the JSON schema file.

    Raises:
        ValueError: If the manifest cannot be read, the schema version is missing or unknown,
                    or the corresponding schema file does not exist.
        RuntimeError: If the schema index file itself is missing or corrupt.
    """
    # ───────────────────────────────
    # Load manifest if path provided
    # ───────────────────────────────
    if not isinstance(manifest, dict):
        manifest_path = Path(manifest)
        try:
            manifest = load_yaml(manifest_path)
        except Exception as e:
            raise ValueError(f"Failed to read manifest '{manifest_path}': {e}") from e

    # ───────────────────────────────
    # Handle explicit $schema (not yet supported)
    # ───────────────────────────────
    explicit_schema = manifest.get("$schema")
    if isinstance(explicit_schema, str) and explicit_schema.strip():
        warnings.warn(
            "Explicit $schema URIs are not yet supported. Ignoring explicit $schema field.",
            stacklevel=2,
        )

    # ───────────────────────────────
    # Resolve by schema_version
    # ───────────────────────────────
    version_str = manifest.get("schema_version")
    if not version_str:
        raise ValueError("No 'schema_version' field found in manifest.")

    index = _read_index()
    manifest_map: dict[str, str] = index.get("manifest", {})

    if version_str not in manifest_map:
        available = ", ".join(sorted(k for k in manifest_map if k != "latest"))
        raise ValueError(
            f"Schema version '{version_str}' not found in schema index. "
            f"Available versions: {available or 'none found'}"
        )

    schema_rel = manifest_map[version_str]
    schema_path = (SCHEMA_DIR / schema_rel).resolve()

    if not schema_path.exists():
        raise ValueError(
            f"Schema version '{version_str}' listed in index, but schema file not found: "
            f"{schema_path}. This indicates a packaging or installation error."
        )

    return schema_path


def _read_index() -> dict[str, Any]:
    """
    Load and return the schema index JSON file that maps schema versions to file paths.

    Raises:
        RuntimeError: If the schema index file does not exist or cannot be loaded.
    """
    if not SCHEMA_INDEX.exists():
        raise RuntimeError(
            "Schema index file not found. The package may be installed incorrectly "
            "or the schema index is missing. Please reinstall or report a packaging issue."
        )

    try:
        return load_json(SCHEMA_INDEX)
    except Exception as e:
        raise RuntimeError(f"Failed to load schema index from '{SCHEMA_INDEX}': {e}") from e
