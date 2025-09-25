# Validator CLI

## Commands

- `validate-root <manifest> <schema>`: Validate a v2 root manifest and its referenced files.

## Exit codes

- 0: Success (may include warnings)
- non-zero: Validation errors

## Examples

```bash
python tools/validate_repo.py validate-root tests/fixtures/basic_repo/manifest.yml schema/manifest.schema.json
```

## Common messages

- ERROR: Schema validation: ...
- ERROR: Page file not found: pages/... (for Title)
- ERROR: Page 'Title' must have semantic version (MAJOR.MINOR.PATCH)
- ERROR: Pack 'X' depends_on unknown pack id: Y
- ERROR: Dependency cycle detected among packs
- WARNING: Orphan page file not referenced in manifest: pages/...
- WARNING: Module files should use .lua extension: pages/...
