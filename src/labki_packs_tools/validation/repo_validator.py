from __future__ import annotations

from pathlib import Path

from labki_packs_tools.utils import load_json, load_yaml
from labki_packs_tools.validation.schema_resolver import resolve_schema
from labki_packs_tools.validation.result_types import ValidationItem, ValidationResults
from labki_packs_tools.validation.validators.base import Validator


def validate_repo(manifest_path: Path | str) -> tuple[int, ValidationResults]:
    """
    Validate a Labki content repository manifest.

    Orchestrates all validator subclasses:
      1. Loads manifest and schema.
      2. Applies all Validator subclasses for applicable schema_version.

    Returns:
        (exit_code, ValidationResults)
    """
    manifest_path = Path(manifest_path)
    results = ValidationResults()

    # ───────────────────────────────
    # Load manifest
    # ───────────────────────────────
    try:
        manifest = load_yaml(manifest_path)
    except Exception as e:
        results.add(ValidationItem(level="error", message=f"Failed to read manifest: {e}"))
        return results.rc, results

    # ───────────────────────────────
    # Resolve and load schema
    # ───────────────────────────────
    try:
        schema_path = resolve_schema(manifest)
        schema = load_json(schema_path)
    except Exception as e:
        results.add(ValidationItem(level="error", message=f"Failed to resolve schema: {e}"))
        return results.rc, results

    # ───────────────────────────────
    # Extract manifest fields
    # ───────────────────────────────
    pages = manifest.get("pages", {})
    packs = manifest.get("packs", {})
    schema_version = str(manifest.get("schema_version", "0.0.0"))

    # ───────────────────────────────
    # Apply all registered validators
    # ───────────────────────────────
    for validator_cls in Validator.registry:
        if validator_cls.applies_to_version(schema_version):
            validator = validator_cls()
            try:
                items = validator.validate(
                    manifest=manifest,
                    pages=pages,
                    packs=packs,
                    schema=schema,  # optional for schema-aware checks
                    manifest_path=manifest_path,  # optional for file-path-based checks
                )
                results.extend(items)
            except Exception as e:
                results.add(
                    ValidationItem(
                        level="error", message=f"Validator {validator_cls.__name__} failed: {e}"
                    )
                )

    return results.rc, results
