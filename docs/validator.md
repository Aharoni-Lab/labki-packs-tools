# Validator CLI

## Commands

- `validate <manifest> [schema]`: Validate a manifest and its referenced files. Schema defaults to auto.

## Exit codes

- 0: Success (may include warnings)
- non-zero: Validation errors

## Examples

```bash
python tools/validate_repo.py validate tests/fixtures/basic_repo/manifest.yml

# Pin a specific schema if needed
python tools/validate_repo.py validate tests/fixtures/basic_repo/manifest.yml schema/v1/manifest.schema.json
```

## Common messages

- ERROR: Schema validation: ...
- ERROR: Page file not found: pages/... (for Title)
- ERROR: Page 'Title' must have semantic version (MAJOR.MINOR.PATCH)
- ERROR: Pack 'X' depends_on unknown pack id: Y
- ERROR: Dependency cycle detected among packs
- WARNING: Orphan page file not referenced in manifest: pages/...
- WARNING: Module files should use .lua extension: pages/...
