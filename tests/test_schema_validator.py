from __future__ import annotations
from jsonschema import Draft202012Validator

from labki_packs_tools.validation.schema_validator import _format_schema_error, validate_schema
from labki_packs_tools.validation.result_types import ValidationResult


def test_format_schema_error_messages():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        },
        "required": ["name", "version"],
    }
    bad = {"name": "", "version": "v1"}
    v = Draft202012Validator(schema)
    errors = list(v.iter_errors(bad))
    flat = "\n".join(m for e in errors for m in _format_schema_error(e))
    assert ("minLength" in flat) or ("must not be empty" in flat)


def test_validate_schema_collects_messages():
    schema = {
        "type": "object",
        "properties": {"foo": {"type": "string"}},
        "required": ["foo"],
    }
    result = validate_schema({}, schema)
    assert isinstance(result, ValidationResult)
    assert result.errors and any("foo" in e for e in result.errors)
