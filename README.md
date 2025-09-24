# labki-packs-tools

CLI validator and JSON Schemas for Labki/MediaWiki content packs. Use this in CI or locally to validate a content repository like `labki-packs`.

## What it validates (v2)

- Root manifest structure (`version`, `pages`, `packs`, optional `groups`) against `schema/root-manifest.schema.json`.
- Page entries: required `file`, `type`, `version` (semantic version), Windows-safe filenames, file existence.
- Packs: required semantic version, page titles exist, dependency sanity and cycle detection.
- Groups: pack references are valid; warns when a pack appears in multiple groups.
- Additional conventions (warnings), e.g., `Module:` pages should be `.lua` under `pages/Modules/`.

## Quickstart (local)

Requires Python 3.10+.

```bash
pip install pyyaml jsonschema

# Validate a repo's root manifest against the schema
python tools/validate_repo.py validate-root path/to/manifest.yml schema/root-manifest.schema.json

# Validate legacy per-pack structures (if migrating v1 → v2)
python tools/validate_repo.py validate-packs path/to/repo schema/pack.schema.json
```

Exit code is non-zero on validation errors (suitable for CI). Warnings do not change the exit code.

### Example

This repo ships a small sample under `tests/fixtures/basic_repo/`:

```bash
python tools/validate_repo.py validate-root tests/fixtures/basic_repo/manifest.yml schema/root-manifest.schema.json
```

## Use in CI (content repo)

Add a job in the content repo (e.g., `labki-packs`) that installs Python deps and runs the validator:

```yaml
name: Validate content packs
on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with:
          repository: Aharoni-Lab/labki-packs-tools
          path: tools-cache
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install pyyaml jsonschema
      - name: Validate manifest
        run: |
          python tools-cache/tools/validate_repo.py validate-root manifest.yml tools-cache/schema/root-manifest.schema.json
```

Alternatively, vendor or pin a release artifact of this repo. A reusable GitHub Action is on the roadmap.

## Repository layout

```text
labki-packs-tools/
├─ schema/                     # JSON Schemas used by the validator
├─ tools/
│  └─ validate_repo.py         # CLI validator
├─ tests/
│  ├─ fixtures/basic_repo/     # Sample manifest + pages for tests/examples
│  └─ test_validate_repo.py
└─ docs/                       # Validator spec and usage docs
```

## Docs

- Validator CLI: `docs/validator.md`
- CI integration: `docs/ci.md`
- Manifest spec (v2): `docs/manifest.md`
- Content conventions (warnings): `docs/content-conventions.md`

## Roadmap

- Packaged CLI `labki-validate` (bundled schemas)
- Reusable GitHub Action
- Optional Docker wrapper for hermetic CI

## License

TBD
