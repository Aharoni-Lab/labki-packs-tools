# Development (validator)

## Setup

1. Python 3.10+
2. Install deps: `pip install -r requirements-dev.txt` (or `pip install pyyaml jsonschema pytest`)

## Run tests

```bash
pytest -q
```

## Making schema changes

1. Edit `schema/root-manifest.schema.json`.
2. Update `docs/manifest.md` if you add/remove fields.
3. Add tests in `tests/` to cover new rules (errors vs. warnings).

## CLI changes

- The CLI lives at `tools/validate_repo.py`. Keep commands stable: `validate-root`.
- Ensure non-zero exit codes for errors; warnings should not fail CI.
- Keep output messages actionable and grep-friendly.

## Releasing (future)

- Package a CLI `labki-validate` that bundles schemas.
- Tag a release and publish to PyPI and/or attach schema artifacts.
