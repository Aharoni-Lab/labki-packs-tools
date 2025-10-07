from __future__ import annotations

from typing import List

from jsonschema import Draft202012Validator, ValidationError

from .result_types import ValidationResult


def _format_schema_error(e: ValidationError) -> list[str]:
    """
    Return friendly, contextualized messages for common schema errors.

    This adds human-readable hints while preserving the raw jsonschema message elsewhere.
    """
    try:
        path_list = list(e.path)
    except Exception:
        path_list = []

    msgs: list[str] = []

    # ───────────────────────────────
    # Pattern-specific hints
    # ───────────────────────────────
    if e.validator == "pattern":
        # Packs.tags pattern
        if len(path_list) >= 4 and path_list[0] == "packs" and path_list[2] == "tags":
            pack_id = path_list[1]
            tag_value = getattr(e, "instance", None)
            msgs.append(
                f"Schema validation: Pack '{pack_id}' has tag '{tag_value}' "
                "that must be slugified (lowercase letters, digits, hyphens)"
            )
        # Pack version pattern
        if len(path_list) >= 3 and path_list[0] == "packs" and path_list[2] == "version":
            pack_id = path_list[1]
            msgs.append(
                f"Schema validation: Pack '{pack_id}' must have semantic version "
                "(MAJOR.MINOR.PATCH)"
            )
        # Page last_updated pattern
        if len(path_list) >= 3 and path_list[0] == "pages" and path_list[2] == "last_updated":
            page_title = path_list[1]
            msgs.append(
                f"Schema validation: Page '{page_title}' last_updated must match "
                "YYYY-MM-DDThh:mm:ssZ"
            )
        # Root last_updated
        if path_list == ["last_updated"]:
            msgs.append("Schema validation: 'last_updated' must match YYYY-MM-DDThh:mm:ssZ")
        # File path no colon
        if len(path_list) >= 3 and path_list[0] == "pages" and path_list[2] == "file":
            page_title = path_list[1]
            msgs.append(f"Schema validation: Page '{page_title}' file path must not contain ':'")

    # ───────────────────────────────
    # Unique items (duplicate pages/tags)
    # ───────────────────────────────
    if e.validator == "uniqueItems" and len(path_list) >= 3 and path_list[0] == "packs":
        pack_id = path_list[1]
        field = path_list[2]
        if field == "tags":
            msgs.append(f"Schema validation: Pack '{pack_id}' has duplicate tags")
        if field == "pages":
            msgs.append(f"Schema validation: Pack '{pack_id}' has duplicate page titles in 'pages'")

    # ───────────────────────────────
    # Additional properties (unknown fields)
    # ───────────────────────────────
    if e.validator == "additionalProperties":
        if len(path_list) >= 2 and path_list[0] == "pages":
            page_title = path_list[1]
            msgs.append(f"Schema validation: Page '{page_title}' contains unknown field(s)")
        if len(path_list) >= 2 and path_list[0] == "packs":
            pack_id = path_list[1]
            msgs.append(f"Schema validation: Pack '{pack_id}' contains unknown field(s)")

    # ───────────────────────────────
    # Name field errors
    # ───────────────────────────────
    if e.validator == "minLength" and path_list == ["name"]:
        msgs.append("Schema validation: 'name' must not be empty")
    if e.validator == "pattern" and path_list == ["name"]:
        msgs.append(
            "Schema validation: 'name' may include letters, digits, spaces, "
            "hyphens, colons, underscores"
        )

    # ───────────────────────────────
    # Type errors
    # ───────────────────────────────
    if (
        e.validator == "type"
        and len(path_list) >= 3
        and path_list[0] == "packs"
        and path_list[2] == "pages"
    ):
        pack_id = path_list[1]
        msgs.append(f"Schema validation: Pack '{pack_id}' pages must be an array")

    # ───────────────────────────────
    # Missing required fields
    # ───────────────────────────────
    if e.validator == "required":
        if len(path_list) >= 2 and path_list[0] == "pages":
            page_title = path_list[1]
            msgs.append(f"Schema validation: Page '{page_title}' is missing required field(s)")
        if len(path_list) >= 2 and path_list[0] == "packs":
            pack_id = path_list[1]
            msgs.append(f"Schema validation: Pack '{pack_id}' is missing required field(s)")

    return msgs


def _format_anyof_error(e: ValidationError) -> list[str]:
    """
    Special handling for the packs 'anyOf' rule:
    A pack must have at least one page or depend on at least two packs.
    """
    msgs: list[str] = []
    path_list = list(e.path)
    if e.validator == "anyOf" and len(path_list) >= 2 and path_list[0] == "packs":
        pack_id = path_list[1]
        msgs.append(
            f"Schema validation: Pack '{pack_id}' must include at least one page "
            f"or depend on at least two packs"
        )
    return msgs


def validate_schema(manifest: dict, schema: dict) -> ValidationResult:
    """
    Run JSON Schema validation and return a structured ValidationResult.

    This wraps jsonschema.Draft202012Validator and adds friendly contextual messages.
    """
    result = ValidationResult()
    validator = Draft202012Validator(schema)
    errors: List[ValidationError] = sorted(validator.iter_errors(manifest), key=lambda e: e.path)

    for e in errors:
        # Friendly hints for special cases
        for msg in _format_anyof_error(e):
            result.add_error(msg)
        for msg in _format_schema_error(e):
            result.add_error(msg)

        # Always include the raw jsonschema message for context
        result.add_error(f"Schema validation: {e.message} at path {list(e.path)}")

    return result
