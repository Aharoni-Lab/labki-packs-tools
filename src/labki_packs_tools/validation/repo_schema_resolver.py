import os
import re
from pathlib import Path
from labki_packs_tools.utils import load_yaml, load_json

def auto_resolve_schema(manifest_path: Path | str, schema_arg: Path | str = "auto") -> Path:
    """
    Determine which JSON Schema file to validate a manifest against.

    Resolution order:
      1. If user passed a non-'auto' schema_arg, return it directly.
      2. If manifest contains a `$schema` key, resolve that (absolute or relative).
      3. Otherwise, look up the manifest's 'schema_version' in index.json under LABKI_SCHEMA_DIR
         (or default to '<repo>/schema' if env var not set).

    Raises:
      ValueError: if schema cannot be resolved or found.
    """
    manifest_path = Path(manifest_path)
    if schema_arg != "auto":
        schema_path = Path(schema_arg)
        if not schema_path.exists():
            raise ValueError(f"Schema path not found: {schema_path}")
        return schema_path

    # 1️⃣ Load manifest so we can inspect $schema and schema_version
    try:
        manifest_data = load_yaml(manifest_path)
    except Exception as e:
        raise ValueError(f"Failed to read manifest: {e}")

    # 2️⃣ Case: manifest explicitly declares a $schema
    explicit_schema = manifest_data.get("$schema")
    if isinstance(explicit_schema, str) and explicit_schema.strip():
        schema_path = Path(explicit_schema)
        if not schema_path.is_absolute():
            schema_path = (manifest_path.parent / schema_path).resolve()
        if not schema_path.exists():
            raise ValueError(f"Explicit $schema file not found: {schema_path}")
        return schema_path

    # 3️⃣ Case: manifest specifies schema_version (e.g. 1.0.0)
    version_str = str(manifest_data.get("schema_version") or "").strip()
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str)
    if not m:
        raise ValueError("Manifest 'schema_version' must be semantic (MAJOR.MINOR.PATCH)")

    # 4️⃣ Find schema directory
    schema_dir_env = os.environ.get("LABKI_SCHEMA_DIR")
    # Default to repository layout when running from sources. This module lives under
    # src/labki_packs_tools/validation/, so repo root is parents[3].
    schema_dir = (
        Path(schema_dir_env)
        if schema_dir_env
        else Path(__file__).resolve().parents[3] / "schema"
    )

    index_path = schema_dir / "index.json"
    if not index_path.exists():
        raise ValueError(f"Schema index not found: {index_path}")

    try:
        index = load_json(index_path)
    except Exception as e:
        raise ValueError(f"Failed to load schema index: {e}")

    manifest_map = index.get("manifest") or {}
    if version_str not in manifest_map:
        available = ", ".join(sorted([k for k in manifest_map if k != "latest"]))
        raise ValueError(f"Schema version '{version_str}' not found in index. Available: {available}")

    schema_rel = manifest_map[version_str]
    schema_path = (schema_dir / schema_rel).resolve()
    if not schema_path.exists():
        raise ValueError(f"Resolved schema file does not exist: {schema_path}")

    return schema_path
