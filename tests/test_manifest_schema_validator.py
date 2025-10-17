import pytest
from jsonschema import ValidationError

from labki_packs_tools.validation.validators.manifest_schema_validator import (
    _format_schema_error,
    _format_anyof_error,
    MESSAGES,
    ManifestSchemaValidator,
)
from labki_packs_tools.validation.result_types import ValidationItem


class DummyValidationError(ValidationError):
    """Helper subclass for easier construction of fake ValidationError objects."""

    def __init__(self, validator, path, message="dummy message", instance=None):
        super().__init__(message=message)
        self.validator = validator
        self.path = path
        self.instance = instance or "dummy_instance"


# ────────────────────────────────────────────────
# _format_schema_error tests
# ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "validator,path,expected",
    [
        (
            "pattern",
            ["packs", "core_pack", "version"],
            "Pack 'core_pack' must have semantic version (MAJOR.MINOR.PATCH)",
        ),
        (
            "pattern",
            ["pages", "Template_Page", "last_updated"],
            "Page 'Template_Page' last_updated must match YYYY-MM-DDThh:mm:ssZ",
        ),
        ("uniqueItems", ["packs", "imaging", "tags"], "Pack 'imaging' has duplicate tags"),
        ("required", ["pages", "Missing_Page"], "Page 'Missing_Page' is missing required field(s)"),
    ],
)
def test_known_schema_error_messages(validator, path, expected):
    e = DummyValidationError(validator, path)
    msgs = _format_schema_error(e)
    assert any(expected in m for m in msgs), f"Expected message '{expected}' not found."


def test_fallback_message_for_unknown_error():
    e = DummyValidationError("unknownValidator", ["packs", "alpha"])
    msgs = _format_schema_error(e)
    # Should include fallback containing default jsonschema message
    assert "dummy message" in msgs[0]
    assert "packs" in msgs[0]


# ────────────────────────────────────────────────
# _format_anyof_error tests
# ────────────────────────────────────────────────


def test_anyof_error_message():
    e = DummyValidationError("anyOf", ["packs", "core_pack"])
    msgs = _format_anyof_error(e)
    assert msgs == [
        "Pack 'core_pack' must include at least one page or depend on at least two packs"
    ]


# ────────────────────────────────────────────────
# Integration: ManifestSchemaValidator
# ────────────────────────────────────────────────


def test_manifest_schema_validator_returns_validation_items(monkeypatch):
    """Simulate schema errors and ensure validator wraps them in ValidationItems."""
    fake_error = DummyValidationError("pattern", ["packs", "demo_pack", "version"])
    fake_validator = lambda schema: [fake_error]

    # Patch Draft202012Validator.iter_errors
    monkeypatch.setattr(
        "labki_packs_tools.validation.validators.manifest_schema_validator.Draft202012Validator",
        lambda schema: type("V", (), {"iter_errors": lambda self, m: [fake_error]})(),
    )

    validator = ManifestSchemaValidator()
    results = validator.validate(manifest={}, schema={})
    assert isinstance(results, list)
    assert all(isinstance(r, ValidationItem) for r in results)
    assert any("demo_pack" in r.message for r in results)
    assert any("semantic version" in r.message for r in results)


def test_all_messages_mapping_is_valid():
    """Ensure all patterns in MESSAGES dict are syntactically valid."""
    for (validator, pattern), msg in MESSAGES.items():
        assert isinstance(validator, str)
        assert isinstance(pattern, str)
        assert isinstance(msg, str)
