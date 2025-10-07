from __future__ import annotations
from pathlib import Path

from labki_packs_tools.utils import load_yaml, load_json
from .result_types import ValidationResult
from .schema_validator import validate_schema
from .page_validator import validate_pages, detect_orphans
from .pack_validator import validate_packs, detect_cycles
from .repo_schema_resolver import auto_resolve_schema


def validate_repo(
    manifest_path: Path | str, schema_arg: Path | str = "auto"
) -> tuple[int, ValidationResult]:
    """
    Validate a Labki content repository manifest.

    Orchestrates all validation stages:
      1. Resolve and load the correct JSON Schema.
      2. Run JSON Schema validation.
      3. Run page-level checks (file existence, namespaces, orphans).
      4. Run pack-level checks (semver, dependencies, cycles).

    Returns:
        (exit_code, ValidationResult)
    """
    manifest_path = Path(manifest_path)
    result = ValidationResult()

    # ───────────────────────────────
    # Resolve and load schema
    # ───────────────────────────────
    try:
        schema_path = auto_resolve_schema(manifest_path, schema_arg)
    except ValueError as e:
        result.add_error(str(e))
        return result.rc, result

    # ───────────────────────────────
    # Load manifest and schema files
    # ───────────────────────────────
    try:
        manifest = load_yaml(manifest_path)
    except Exception as e:
        result.add_error(f"Failed to read manifest {manifest_path}: {e}")
        return result.rc, result

    try:
        schema = load_json(schema_path)
    except Exception as e:
        result.add_error(f"Failed to read schema {schema_path}: {e}")
        return result.rc, result

    # ───────────────────────────────
    # 1. JSON Schema validation
    # ───────────────────────────────
    schema_result = validate_schema(manifest, schema)
    result.merge(schema_result)

    # ───────────────────────────────
    # 2. Page validation
    # ───────────────────────────────
    pages = manifest.get("pages")
    if not isinstance(pages, dict):
        result.add_error("'pages' must be a mapping of titles to objects")
        return result.rc, result

    page_result, referenced_paths = validate_pages(manifest_path, pages)
    result.merge(page_result)

    orphan_result = detect_orphans(manifest_path, referenced_paths)
    result.merge(orphan_result)

    # ───────────────────────────────
    # 3. Pack validation
    # ───────────────────────────────
    packs = manifest.get("packs")
    if not isinstance(packs, dict):
        result.add_error("'packs' must be a mapping of pack_id to metadata")
        return result.rc, result

    pack_result, dep_edges = validate_packs(pages, packs)
    result.merge(pack_result)

    cycle_result = detect_cycles(packs, dep_edges)
    result.merge(cycle_result)

    # ───────────────────────────────
    # Final result and exit code
    # ───────────────────────────────
    return result.rc, result
