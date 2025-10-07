#!/usr/bin/env python3
import argparse
import os
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

from labki_packs_tools.utils import is_semver, load_json, load_yaml


def validate_with_schema(data: dict, schema: dict) -> list[ValidationError]:
    """Validate manifest data against JSON Schema and return sorted errors.

    Sorting by error.path makes outputs deterministic for testing and easier to scan.
    """
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return errors


def error(msg: str) -> None:
    print(f"ERROR: {msg}")


def warn(msg: str) -> None:
    print(f"WARNING: {msg}")


def _format_schema_error(e: ValidationError) -> list[str]:
    """Return friendly, contextualized messages for common schema errors.

    Always preserve the raw jsonschema message elsewhere so tests and users
    can see the exact validator detail. This function only adds extra hints.
    """
    try:
        path_list = list(e.path)
    except Exception:
        path_list = []

    msgs: list[str] = []
    # Packs content rule handled elsewhere (anyOf)
    if e.validator == "pattern":
        # Packs tags slug pattern
        if len(path_list) >= 4 and path_list[0] == "packs" and path_list[2] == "tags":
            pack_id = path_list[1]
            tag_value = getattr(e, "instance", None)
            msgs.append(
                f"Schema validation: Pack '{pack_id}' has tag '{tag_value}' that must be slugified "
                "(lowercase letters, digits, hyphens)"
            )
        # Pack version pattern
        if len(path_list) >= 3 and path_list[0] == "packs" and path_list[2] == "version":
            pack_id = path_list[1]
            msgs.append(
                f"Schema validation: Pack '{pack_id}' must have semantic version "
                f"(MAJOR.MINOR.PATCH)"
            )
        # Page last_updated pattern
        if len(path_list) >= 3 and path_list[0] == "pages" and path_list[2] == "last_updated":
            page_title = path_list[1]
            msgs.append(
                f"Schema validation: Page '{page_title}' last_updated must match "
                "YYYY-MM-DDThh:mm:ssZ"
            )
        # last_updated timestamp pattern
        if path_list == ["last_updated"]:
            msgs.append("Schema validation: 'last_updated' must match YYYY-MM-DDThh:mm:ssZ")
        # file path (no colon) — only if schema adds this pattern in future
        if len(path_list) >= 3 and path_list[0] == "pages" and path_list[2] == "file":
            page_title = path_list[1]
            msgs.append(f"Schema validation: Page '{page_title}' file path must not contain ':'")

    if e.validator == "uniqueItems" and len(path_list) >= 3 and path_list[0] == "packs":
        pack_id = path_list[1]
        field = path_list[2]
        if field == "tags":
            msgs.append(f"Schema validation: Pack '{pack_id}' has duplicate tags")
        if field == "pages":
            msgs.append(f"Schema validation: Pack '{pack_id}' has duplicate page titles in 'pages'")

    if e.validator == "additionalProperties":
        if len(path_list) >= 2 and path_list[0] == "pages":
            page_title = path_list[1]
            msgs.append(f"Schema validation: Page '{page_title}' contains unknown field(s)")
        if len(path_list) >= 2 and path_list[0] == "packs":
            pack_id = path_list[1]
            msgs.append(f"Schema validation: Pack '{pack_id}' contains unknown field(s)")

    # Friendly messages for manifest-level fields
    if e.validator == "minLength" and path_list == ["name"]:
        msgs.append("Schema validation: 'name' must not be empty")
    if e.validator == "pattern" and path_list == ["name"]:
        msgs.append(
            "Schema validation: 'name' may include letters, digits, spaces, "
            "hyphens, colons, underscores"
        )

    if (
        e.validator == "type"
        and len(path_list) >= 3
        and path_list[0] == "packs"
        and path_list[2] == "pages"
    ):
        pack_id = path_list[1]
        msgs.append(f"Schema validation: Pack '{pack_id}' pages must be an array")

    if e.validator == "required":
        if len(path_list) >= 2 and path_list[0] == "pages":
            page_title = path_list[1]
            msgs.append(f"Schema validation: Page '{page_title}' is missing required field(s)")
        if len(path_list) >= 2 and path_list[0] == "packs":
            pack_id = path_list[1]
            msgs.append(f"Schema validation: Pack '{pack_id}' is missing required field(s)")

    return msgs


def validate_pages(manifest_path: Path, pages: dict) -> tuple[list[str], list[str], set[Path]]:
    """Validate pages mapping; return (errors, warnings, referenced_abs_paths)."""
    errors = []
    warnings = []
    referenced_abs_paths = set()
    for title, meta in pages.items():
        # Title underscore validation handled by JSON Schema (propertyNames).
        # Keep hints only hereafter.
        if ":" not in title:
            warnings.append(f"Title missing namespace: {title}")
        file_rel = meta.get("file")
        if not file_rel:
            errors.append(f"Page '{title}' missing file path")
            # Skip further file-based checks for this page
            continue
        # Colon check is handled by JSON Schema on 'file' pattern.
        abs_path = (manifest_path.parent / file_rel).resolve()
        referenced_abs_paths.add(abs_path)
        if not abs_path.exists():
            errors.append(f"Page file not found: {file_rel} (for {title})")
        # Per-page last_updated format is enforced by the JSON Schema; no extra check here.
        # Additional type-specific checks
        inferred_ns = None
        if ":" in title:
            inferred_ns = title.split(":", 1)[0]
        if inferred_ns == "Module":
            if abs_path.suffix != ".lua":
                warnings.append(f"Module files should use .lua extension: {file_rel}")
            if "Modules" not in file_rel.replace("\\", "/"):
                warnings.append(f"Module files should be stored under pages/Modules/: {file_rel}")
    return errors, warnings, referenced_abs_paths


def detect_orphan_pages(manifest_path: Path, referenced_abs_paths: set[Path]) -> list[str]:
    """Return warnings for .wiki/.md files under pages/ not referenced."""
    warnings = []
    pages_dir = (manifest_path.parent / "pages").resolve()
    if not pages_dir.exists():
        return warnings
    for root, _dirs, files in os.walk(pages_dir):
        for fname in files:
            if not (fname.endswith(".wiki") or fname.endswith(".md")):
                continue
            f_abs = Path(root) / fname
            if f_abs not in referenced_abs_paths:
                rel = os.path.relpath(f_abs, manifest_path.parent)
                warnings.append(f"Orphan page file not referenced in manifest: {rel}")
    return warnings


def validate_packs(pages: dict, packs: dict) -> tuple[list[str], list[tuple[str, str]]]:
    """Validate packs mapping; return (errors, dependency_edges)."""
    errors = []
    edges = []  # (dep, pack_id)
    seen_page_to_pack = {}
    for pack_id, meta in packs.items():
        version = meta.get("version")
        if not is_semver(version):
            errors.append(f"Pack '{pack_id}' must have semantic version (MAJOR.MINOR.PATCH)")
        pages_list = meta.get("pages", [])
        if pages_list and not isinstance(pages_list, list):
            errors.append(f"Pack '{pack_id}' pages must be an array")
        for title in pages_list or []:
            if title not in pages:
                errors.append(f"Pack '{pack_id}' references unknown page title: {title}")
            if title in seen_page_to_pack and seen_page_to_pack[title] != pack_id:
                other = seen_page_to_pack[title]
                errors.append(
                    f"Page title '{title}' included in multiple packs ('{other}' and '{pack_id}'). "
                    "Move to a shared dependency pack."
                )
            else:
                seen_page_to_pack[title] = pack_id
        for dep in meta.get("depends_on", []) or []:
            if dep not in packs:
                errors.append(f"Pack '{pack_id}' depends_on unknown pack id: {dep}")
            else:
                edges.append((dep, pack_id))
    return errors, edges


def detect_cycles(packs: dict, edges: list[tuple[str, str]]) -> list[str]:
    """Detect cycles among packs using Kahn's algorithm; return errors."""
    if not packs:
        return []
    from collections import defaultdict, deque

    indeg = defaultdict(int)
    graph = defaultdict(list)
    for pid in packs:
        indeg[pid] = 0
    for a, b in edges:
        graph[a].append(b)
        indeg[b] += 1
    q = deque([n for n in packs if indeg[n] == 0])
    visited = 0
    while q:
        n = q.popleft()
        visited += 1
        for m in graph[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    if visited != len(packs):
        return ["Dependency cycle detected among packs"]
    return []


def check_manifest(manifest_path: Path, schema_path: Path) -> int:
    """Validate a manifest file against the schema and repository rules (v1).

    Steps:
    1. Load YAML (reject duplicate keys) and load JSON Schema.
    2. Run JSON Schema validation and print friendly messages in addition to raw errors.
    3. Run repository-level checks:
       - Page rules: title format hints, file path checks, version format, file existence
       - Orphan detection: warn on unreferenced `.wiki`/`.md` files under `pages/`
       - Pack rules: version format, references to existing pages, dependency existence,
         cycle detection, cross-pack duplicate pages

    Note: Warnings do not affect the exit code; any ERROR makes the return code non-zero.
    """
    rc = 0
    try:
        manifest = load_yaml(manifest_path)
    except Exception as e:
        error(f"Failed to read manifest {manifest_path}: {e}")
        return 1

    try:
        schema = load_json(schema_path)
    except Exception as e:
        error(f"Failed to read schema {schema_path}: {e}")
        return 1

    schema_errors = validate_with_schema(manifest, schema)
    schema_msgs: list[tuple[str, str]] = []
    if schema_errors:
        for e in schema_errors:
            # Provide clearer message for anyOf failures on packs content rule
            if e.validator == "anyOf":
                path_list = list(e.path)
                if len(path_list) >= 2 and path_list[0] == "packs":
                    pack_id = path_list[1]
                    schema_msgs.append(
                        (
                            "error",
                            f"Schema validation: Pack '{pack_id}' must include "
                            f"at least one page or depend on at least two packs",
                        )
                    )
            # Extra friendly hints
            for msg in _format_schema_error(e):
                schema_msgs.append(("error", msg))
            # Always include the raw jsonschema message
            schema_msgs.append(("error", f"Schema validation: {e.message} at path {list(e.path)}"))
        rc = 1

    # v1: validate flat pages registry
    pages = manifest.get("pages", {})
    misc_errors: list[str] = []
    page_errors: list[str] = []
    page_warnings: list[str] = []
    page_warns_all: list[str] = []
    if not isinstance(pages, dict):
        misc_errors.append("'pages' must be a mapping of titles to objects")
        rc = 1
        referenced_abs_paths = set()
    else:
        page_errors, page_warnings, referenced_abs_paths = validate_pages(manifest_path, pages)
        orphan_warnings = detect_orphan_pages(manifest_path, referenced_abs_paths)
        page_warns_all = page_warnings + orphan_warnings
        if page_errors:
            rc = 1

    # v1 packs: flat registry with depends_on
    packs = manifest.get("packs", {})
    pack_errors: list[str] = []
    cycle_errors: list[str] = []
    if not isinstance(packs, dict):
        misc_errors.append("'packs' must be a mapping of pack_id to metadata")
        rc = 1
    else:
        pack_errors, edges = validate_packs(pages if isinstance(pages, dict) else {}, packs)
        cycle_errors = detect_cycles(packs, edges)
        if pack_errors or cycle_errors:
            rc = 1

    # Grouped output for readability
    total_errors = 0
    total_warnings = 0
    if schema_msgs:
        print("Schema validation errors:")
        for level, msg in schema_msgs:
            if level == "error":
                error(msg)
                total_errors += 1
            else:
                warn(msg)
                total_warnings += 1
    if misc_errors:
        print("Structural issues:")
        for msg in misc_errors:
            error(msg)
            total_errors += 1
    if isinstance(pages, dict):
        if page_errors:
            print("Page errors:")
            for msg in page_errors:
                error(msg)
                total_errors += 1
        if page_warns_all:
            print("Page warnings:")
            for msg in page_warns_all:
                warn(msg)
                total_warnings += 1
    if isinstance(packs, dict):
        if pack_errors:
            print("Pack errors:")
            for msg in pack_errors:
                error(msg)
                total_errors += 1
        if cycle_errors:
            print("Dependency graph errors:")
            for msg in cycle_errors:
                error(msg)
                total_errors += 1

    print(f"Validation completed: {total_errors} error(s), {total_warnings} warning(s)")
    return rc


def validate(manifest: Path | str, schema_arg: Path | str = "auto") -> int:
    manifest_path = Path(manifest)
    if schema_arg == "auto":
        try:
            manifest_data = load_yaml(manifest_path)
        except Exception as e:
            error(f"Failed to read manifest for auto schema selection: {e}")
            return 1
        # Allow explicit schema override via $schema in the manifest
        explicit_schema = manifest_data.get("$schema")
        if isinstance(explicit_schema, str) and explicit_schema.strip():
            schema_path = Path(explicit_schema)
            if not schema_path.is_absolute():
                schema_path = (manifest_path.parent / schema_path).resolve()
            return check_manifest(manifest_path, schema_path)

        version_str = str(manifest_data.get("schema_version") or "").strip()
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str or "")
        schema_dir = Path(__file__).resolve().parents[2] / "schema"
        if not m:
            error("Manifest 'schema_version' must be a semantic version (MAJOR.MINOR.PATCH)")
            return 1
        index_path = schema_dir / "index.json"
        schema_path = None
        # Require exact mapping in index
        try:
            index = load_json(index_path)
            manifest_map = index.get("manifest") or {}
            if version_str not in manifest_map:
                error(
                    f"Schema version '{version_str}' not found in index. Available: "
                    f"{', '.join(sorted([k for k in manifest_map if k != 'latest']))}"
                )
                return 1
            rel = manifest_map[version_str]
            schema_path = schema_dir / rel
        except Exception as e:
            error(f"Failed to read schema index: {e}")
            return 1
        if not schema_path.exists():
            error(f"Resolved schema path does not exist: {schema_path}")
            return 1
        return check_manifest(manifest_path, schema_path)
    else:
        schema_path = Path(schema_arg)
        return check_manifest(manifest_path, schema_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate labki-packs repository")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_root = sub.add_parser("validate", help="Validate manifest")
    p_root.add_argument("manifest", type=str)
    p_root.add_argument(
        "schema", type=str, nargs="?", default="auto", help="Path to schema or 'auto' (default)"
    )

    args = parser.parse_args()

    if args.cmd == "validate":
        rc = validate(args.manifest, args.schema)
        sys.exit(rc)


if __name__ == "__main__":
    main()
