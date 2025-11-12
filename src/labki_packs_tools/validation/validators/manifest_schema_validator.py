from __future__ import annotations

from fnmatch import fnmatch
from typing import Any, List, Tuple

from jsonschema import Draft202012Validator, ValidationError

from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.base import Validator

# ────────────────────────────────────────────────
# Declarative message map
# ────────────────────────────────────────────────

# Each key is (validator, path_pattern)
# - path_pattern supports fnmatch-style wildcards: "packs/*/version", "pages/*/file", etc.
# - The value is a message template, where {1}, {2} ... refer to path elements.
MESSAGES: dict[Tuple[str, str], str] = {
    # Pattern validator messages
    ("pattern", "packs/*/version"): "Pack '{1}' must have semantic version (MAJOR.MINOR.PATCH)",
    ("pattern", "packs/*/tags/*"): (
        "Pack '{1}' has tag '{3}' that must be slugified " "(lowercase letters, digits, hyphens)"
    ),
    ("pattern", "pages/*/last_updated"): (
        "Page '{1}' last_updated must match YYYY-MM-DDThh:mm:ssZ"
    ),
    ("pattern", "last_updated"): "'last_updated' must match YYYY-MM-DDThh:mm:ssZ",
    (
        "pattern",
        "pages/*/file",
    ): (
        "Page '{1}' file path must stay under 'pages/' and use only lowercase letters, digits, "
        "hyphens, underscores, and '/' before ending with .wiki, .lua, .js, or .css"
    ),
    ("pattern", "name"): "'name' may include letters, digits, spaces, hyphens, colons, underscores",
    # UniqueItems validator
    ("uniqueItems", "packs/*/tags"): "Pack '{1}' has duplicate tags",
    ("uniqueItems", "packs/*/pages"): "Pack '{1}' has duplicate page titles in 'pages'",
    # Additional properties
    ("additionalProperties", "pages/*"): "Page '{1}' contains unknown field(s)",
    ("additionalProperties", "packs/*"): "Pack '{1}' contains unknown field(s)",
    # Required fields
    ("required", "pages/*"): "Page '{1}' is missing required field(s)",
    ("required", "packs/*"): "Pack '{1}' is missing required field(s)",
    # Type mismatch
    ("type", "packs/*/pages"): "Pack '{1}' pages must be an array",
    # Min length
    ("minLength", "name"): "'name' must not be empty",
}


# ────────────────────────────────────────────────
# Formatter helpers
# ────────────────────────────────────────────────


def _match_path(pattern: str, path: List[str]) -> bool:
    """Return True if the path matches the fnmatch-style pattern."""
    joined = "/".join(path)
    return fnmatch(joined, pattern)


def _format_schema_error(e: ValidationError) -> list[str]:
    """Return user-friendly messages for known schema validation errors."""
    try:
        path_list = list(e.path)
    except Exception:
        path_list = []

    msgs: list[str] = []

    # Try to match in the declarative map
    for (validator, pattern), msg in MESSAGES.items():
        if e.validator == validator and _match_path(pattern, path_list):
            try:
                msgs.append(msg.format(*path_list))
            except Exception:
                msgs.append(msg)
            break  # Only return the first matching message

    # Fallback if nothing matched
    if not msgs:
        msgs.append(f"{e.message} at path {list(e.path)}")

    return msgs


def _format_anyof_error(e: ValidationError) -> list[str]:
    """Handle special anyOf validation cases."""
    path_list = list(e.path)
    msgs: list[str] = []
    if e.validator == "anyOf" and len(path_list) >= 2 and path_list[0] == "packs":
        pack_id = path_list[1]
        msgs.append(
            f"Pack '{pack_id}' must include at least one page or depend on at least two packs"
        )
    return msgs


# ────────────────────────────────────────────────
# Main validator class
# ────────────────────────────────────────────────


class ManifestSchemaValidator(Validator):
    code = "schema-validation"
    message = "Manifest must satisfy the declared schema"
    level = "error"
    min_version = None
    max_version = None

    def validate(self, *, manifest: dict, schema: dict, **kwargs: Any) -> list[ValidationItem]:
        results: list[ValidationItem] = []
        validator = Draft202012Validator(schema)
        errors: List[ValidationError] = sorted(
            validator.iter_errors(manifest), key=lambda e: e.path
        )

        for e in errors:
            # Format known schema and anyOf errors
            for msg in _format_anyof_error(e) + _format_schema_error(e):
                results.append(
                    ValidationItem(
                        level=self.level,
                        message=f"Schema validation: {msg}",
                        code=self.code,
                    )
                )

        return results
