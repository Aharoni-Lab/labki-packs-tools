from __future__ import annotations

from typing import Any, List

from jsonschema import Draft202012Validator, ValidationError

from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.base import Validator


def _format_schema_error(e: ValidationError) -> list[str]:
    try:
        path_list = list(e.path)
    except Exception:
        path_list = []

    msgs: list[str] = []

    if e.validator == "pattern":
        if len(path_list) >= 4 and path_list[0] == "packs" and path_list[2] == "tags":
            pack_id = path_list[1]
            tag_value = getattr(e, "instance", None)
            msgs.append(
                f"Pack '{pack_id}' has tag '{tag_value}' that must be slugified "
                "(lowercase letters, digits, hyphens)"
            )
        if len(path_list) >= 3 and path_list[0] == "packs" and path_list[2] == "version":
            pack_id = path_list[1]
            msgs.append(f"Pack '{pack_id}' must have semantic version (MAJOR.MINOR.PATCH)")
        if len(path_list) >= 3 and path_list[0] == "pages" and path_list[2] == "last_updated":
            page_title = path_list[1]
            msgs.append(f"Page '{page_title}' last_updated must match YYYY-MM-DDThh:mm:ssZ")
        if path_list == ["last_updated"]:
            msgs.append("'last_updated' must match YYYY-MM-DDThh:mm:ssZ")
        if len(path_list) >= 3 and path_list[0] == "pages" and path_list[2] == "file":
            page_title = path_list[1]
            msgs.append(f"Page '{page_title}' file path must not contain ':'")

    if e.validator == "uniqueItems" and len(path_list) >= 3 and path_list[0] == "packs":
        pack_id = path_list[1]
        field = path_list[2]
        if field == "tags":
            msgs.append(f"Pack '{pack_id}' has duplicate tags")
        if field == "pages":
            msgs.append(f"Pack '{pack_id}' has duplicate page titles in 'pages'")

    if e.validator == "additionalProperties":
        if len(path_list) >= 2 and path_list[0] == "pages":
            page_title = path_list[1]
            msgs.append(f"Page '{page_title}' contains unknown field(s)")
        if len(path_list) >= 2 and path_list[0] == "packs":
            pack_id = path_list[1]
            msgs.append(f"Pack '{pack_id}' contains unknown field(s)")

    if e.validator == "minLength" and path_list == ["name"]:
        msgs.append("'name' must not be empty")
    if e.validator == "pattern" and path_list == ["name"]:
        msgs.append("'name' may include letters, digits, spaces, hyphens, colons, underscores")

    if (
        e.validator == "type"
        and len(path_list) >= 3
        and path_list[0] == "packs"
        and path_list[2] == "pages"
    ):
        pack_id = path_list[1]
        msgs.append(f"Pack '{pack_id}' pages must be an array")

    if e.validator == "required":
        if len(path_list) >= 2 and path_list[0] == "pages":
            page_title = path_list[1]
            msgs.append(f"Page '{page_title}' is missing required field(s)")
        if len(path_list) >= 2 and path_list[0] == "packs":
            pack_id = path_list[1]
            msgs.append(f"Pack '{pack_id}' is missing required field(s)")

    return msgs


def _format_anyof_error(e: ValidationError) -> list[str]:
    msgs: list[str] = []
    path_list = list(e.path)
    if e.validator == "anyOf" and len(path_list) >= 2 and path_list[0] == "packs":
        pack_id = path_list[1]
        msgs.append(
            f"Pack '{pack_id}' must include at least one page or depend on at least two packs"
        )
    return msgs


class ManifestSchemaValidator(Validator):
    code = "schema-validation"
    message = "Manifest must satisfy the declared schema"
    level = "error"
    min_version = None
    max_version = None

    def validate(self, *, manifest: dict, schema: dict, **kwargs: Any) -> list[ValidationItem]:
        results = []
        validator = Draft202012Validator(schema)
        errors: List[ValidationError] = sorted(
            validator.iter_errors(manifest), key=lambda e: e.path
        )

        for e in errors:
            for msg in _format_anyof_error(e) + _format_schema_error(e):
                results.append(
                    ValidationItem(
                        level=self.level, message=f"Schema validation: {msg}", code=self.code
                    )
                )

            # Always include raw fallback
            results.append(
                ValidationItem(
                    level=self.level,
                    message=f"Schema validation: {e.message} at path {list(e.path)}",
                    code=self.code,
                )
            )

        return results
