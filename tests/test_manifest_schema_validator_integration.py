from __future__ import annotations

import pytest
from jsonschema import Draft202012Validator, ValidationError

from labki_packs_tools.validation.result_types import ValidationItem
from labki_packs_tools.validation.validators.manifest_schema_validator import (
    ManifestSchemaValidator,
    _format_schema_error,
)


# ────────────────────────────────────────────────
# Generic integration behavior
# ────────────────────────────────────────────────


def test_format_schema_error_with_real_validator():
    """End-to-end check that _format_schema_error handles real ValidationError objects."""
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
    assert "version" in formatted or "empty" in formatted


def test_manifest_schema_validator_collects_structured_messages():
    """Validate ManifestSchemaValidator collects structured messages via real jsonschema."""
    schema = {
        "type": "object",
        "properties": {"foo": {"type": "string"}},
        "required": ["foo"],
    }
    validator = ManifestSchemaValidator()
    results = validator.validate(manifest={}, schema=schema)

    assert all(isinstance(i, ValidationItem) for i in results)
    assert any("foo" in i.message for i in results)
    assert any(i.level == "error" for i in results)


def test_semantic_version_error_message_end_to_end():
    """Ensure semantic-version pattern violations trigger friendly messages."""
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


# ────────────────────────────────────────────────
# Manifest schema behavior tests
# ────────────────────────────────────────────────


@pytest.fixture(scope="module")
def manifest_schema():
    """Load the official manifest schema."""
    from labki_packs_tools.utils import load_json
    from labki_packs_tools.validation.schema_resolver import resolve_schema
    
    # Create a minimal manifest with schema_version to resolve the schema
    manifest = {"schema_version": "1.0.0"}
    schema_path = resolve_schema(manifest)
    return load_json(schema_path)


def _validate(schema, data):
    """Helper returning a list of validation errors."""
    validator = Draft202012Validator(schema)
    return list(validator.iter_errors(data))


def test_required_top_level_fields(manifest_schema):
    """schema_version, name, pages, and packs must all be present."""
    bad = {"name": "demo"}
    errors = _validate(manifest_schema, bad)
    fields = " ".join(e.message for e in errors)
    assert "schema_version" in fields and "pages" in fields and "packs" in fields


def test_schema_version_pattern_validation(manifest_schema):
    bad = {
        "schema_version": "abc",
        "name": "demo",
        "pages": {},
        "packs": {},
    }
    errors = _validate(manifest_schema, bad)
    assert any("does not match" in e.message and "schema_version" in str(e.path) for e in errors)


def test_valid_minimal_manifest_passes(manifest_schema):
    """Minimal valid manifest should validate cleanly."""
    good = {
        "schema_version": "1.0.0",
        "name": "demo",
        "pages": {
            "Template:Example": {
                "file": "pages/template-example.wiki",
                "last_updated": "2025-09-22T00:00:00Z",
            }
        },
        "packs": {
            "core": {
                "version": "1.0.0",
                "pages": ["Template:Example"],
            }
        },
    }
    validator = Draft202012Validator(manifest_schema)
    validator.validate(good)  # should not raise


def test_rejects_underscore_in_page_key(manifest_schema):
    bad = {
        "schema_version": "1.0.0",
        "name": "demo",
        "pages": {
            "Template:Bad_Key": {
                "file": "pages/template-bad.wiki",
                "last_updated": "2025-09-22T00:00:00Z",
            }
        },
        "packs": {"p": {"version": "1.0.0", "pages": ["Template:Bad_Key"]}},
    }
    errors = _validate(manifest_schema, bad)
    assert any("property name" in e.message or "does not match" in e.message for e in errors)


@pytest.mark.parametrize(
    "bad_path,reason",
    [
        # 1. uppercase letters not allowed
        ("pages/Template-Bad.Wiki", "uppercase letters"),
        # 2. contains colon (invalid in filenames, discouraged in schema)
        ("pages/template:bad.wiki", "colon in filename"),
        # 3. contains space
        ("pages/template bad.wiki", "space in filename"),
        # 4. missing file extension
        ("pages/template-bad", "missing extension"),
        # 5. wrong extension
        ("pages/template-bad.txt", "wrong extension"),
        # 6. backslashes instead of forward slashes
        ("pages\\template-bad.wiki", "backslashes"),
        # 7. not under pages/ directory (missing prefix)
        ("template-bad.wiki", "missing pages/ prefix"),
    ],
)
def test_invalid_file_path_variations(manifest_schema, bad_path, reason):
    """Cover common invalid path formats that violate file path pattern."""
    bad = {
        "schema_version": "1.0.0",
        "name": "demo",
        "pages": {
            "Template:Example": {
                "file": bad_path,
                "last_updated": "2025-09-22T00:00:00Z",
            }
        },
        "packs": {
            "core": {"version": "1.0.0", "pages": ["Template:Example"]}
        },
    }
    errors = _validate(manifest_schema, bad)
    assert any("does not match" in e.message and "file" in str(e.path) for e in errors), (
        f"Expected file path pattern violation for case: {reason}"
    )


def test_valid_file_path_edge_cases(manifest_schema):
    """Ensure plausible but valid lowercase, underscored, or dashed paths pass."""
    good_paths = [
        "pages/template.wiki",
        "pages/subdir/template-test.wiki",
        "pages/sub_dir/template_test.lua",
        "pages/a/b/c/template.js",
    ]
    for path in good_paths:
        good = {
            "schema_version": "1.0.0",
            "name": "demo",
            "pages": {
                "Template:Example": {
                    "file": path,
                    "last_updated": "2025-09-22T00:00:00Z",
                }
            },
            "packs": {
                "core": {"version": "1.0.0", "pages": ["Template:Example"]}
            },
        }
        Draft202012Validator(manifest_schema).validate(good)  # should not raise



def test_invalid_last_updated_pattern(manifest_schema):
    bad = {
        "schema_version": "1.0.0",
        "name": "demo",
        "pages": {
            "Template:Example": {
                "file": "pages/template-example.wiki",
                "last_updated": "2025-09-22",  # missing time component
            }
        },
        "packs": {"core": {"version": "1.0.0", "pages": ["Template:Example"]}},
    }
    errors = _validate(manifest_schema, bad)
    assert any("does not match" in e.message and "last_updated" in str(e.path) for e in errors)


def test_pack_requires_version_field(manifest_schema):
    bad = {
        "schema_version": "1.0.0",
        "name": "demo",
        "pages": {},
        "packs": {"p": {}},
    }
    errors = _validate(manifest_schema, bad)
    assert any("version" in e.message for e in errors)


def test_tags_pattern_and_uniqueness(manifest_schema):
    """Tag values must be slugified and unique."""
    bad = {
        "schema_version": "1.0.0",
        "name": "demo",
        "pages": {},
        "packs": {"p": {"version": "1.0.0", "tags": ["Bad_Tag", "Bad_Tag"]}},
    }
    errors = _validate(manifest_schema, bad)
    msgs = " ".join(e.message for e in errors)
    assert "pattern" in msgs or "unique" in msgs


def test_pack_must_have_pages_or_depends_on(manifest_schema):
    """Covers anyOf rule inside packRegistry."""
    bad = {
        "schema_version": "1.0.0",
        "name": "demo",
        "pages": {},
        "packs": {"p": {"version": "1.0.0"}},
    }
    errors = _validate(manifest_schema, bad)
    assert len(errors) > 0, "Expected validation errors for pack without pages or dependencies"
    assert any("anyOf" in str(e.validator) or "pages" in e.message or "depends_on" in e.message for e in errors)

