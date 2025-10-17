from __future__ import annotations

from jsonschema import Draft202012Validator

from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.manifest_schema_validator import (
    ManifestSchemaValidator,
    _format_schema_error,
)


def test_format_schema_error_messages():
    """Ensure our schema error formatter produces human-friendly messages."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        },
        "required": ["name", "version"],
    }

    bad = {"name": "", "version": "v1"}
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(bad))

    formatted = "\n".join(m for e in errors for m in _format_schema_error(e))
    # We're not testing the exact text, just that it's meaningful
    assert "empty" in formatted or "version" in formatted


def test_manifest_schema_validator_collects_messages():
    """Ensure the ManifestSchemaValidator collects structured error messages."""
    schema = {
        "type": "object",
        "properties": {"foo": {"type": "string"}},
        "required": ["foo"],
    }

    validator = ManifestSchemaValidator()
    items = validator.validate(manifest={}, schema=schema)

    assert all(isinstance(i, ValidationItem) for i in items)
    assert any("foo" in i.message for i in items)
    assert any(i.level == "error" for i in items)


def test_format_schema_error_applies_custom_pack_message():
    """Ensure schema formatter returns our custom semantic-version error message."""
    schema = {
        "type": "object",
        "properties": {
            "packs": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "properties": {"version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"}},
                },
            }
        },
    }
    bad = {"packs": {"example": {"version": "v1"}}}
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(bad))

    messages = "\n".join(m for e in errors for m in _format_schema_error(e))
    assert "semantic version" in messages or "MAJOR.MINOR.PATCH" in messages
    