import warnings
from pathlib import Path

from labki_packs_tools.const import SCHEMA_DIR, SCHEMA_INDEX
from labki_packs_tools.utils import load_json, load_yaml


def resolve_schema(manifest: Path | str | dict) -> Path:
    """
    Locate the correct schema for a manifest, as specified in its `schema_version` field

    Args:
        manifest (Path | str | dict): A path to a manifest, or an already-loaded manifest dict.

    Raises:
      ValueError: if schema cannot be resolved or found.
    """
    if not isinstance(manifest, dict):
        manifest_path = Path(manifest)

        try:
            manifest = load_yaml(manifest_path)
        except Exception as e:
            raise ValueError(f"Failed to read manifest: {e}") from e

    # Warn when $schema is set while URI resolution is not implemented
    explicit_schema = manifest.get("$schema")
    if isinstance(explicit_schema, str) and explicit_schema.strip():
        warnings.warn(
            "Explicit $schema set, but validating from schema URI not supported yet. Ignoring.",
            stacklevel=2,
        )

    if "schema_version" not in manifest:
        raise ValueError("No schema_version found in manifest.")

    index = _read_index()
    manifest_map = index["manifest"]
    version_str = manifest["schema_version"]
    if version_str not in manifest_map:
        available = ", ".join(sorted([k for k in manifest_map if k != "latest"]))
        raise ValueError(
            f"Schema version '{version_str}' not found in index. Available: {available}"
        )

    schema_rel = manifest_map[version_str]
    schema_path = (SCHEMA_DIR / schema_rel).resolve()
    if not schema_path.exists():
        raise ValueError(
            f"Schema version present in index, but schema path does not exist: {schema_path} "
            "This is a bug in packaging, and you should report it!"
        )

    return schema_path


def _read_index() -> dict:
    if not SCHEMA_INDEX.exists():
        raise RuntimeError(
            "The schema index was not found, the package was installed incorrectly,"
            "or there is a bug in the packaging and you should raise an issue!"
        )
    return load_json(SCHEMA_INDEX)
