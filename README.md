# labki-packs-tools

CLI validator and JSON Schemas for Labki/MediaWiki content packs. Use this in CI or locally to validate a content repository like `labki-packs`.

## What it validates (v1)

- Manifest structure (`version`, `pages`, `packs`) against `schema/manifest.schema.json`.
- Page entries: required `file`, `type`, `version` (semantic version), Windows-safe filenames, file existence.
- Packs: required semantic version, page titles exist, dependency sanity and cycle detection.
- Additional conventions (warnings), e.g., `Module:` pages should be `.lua` under `pages/Modules/`.

## Quickstart (local)

Requires Python 3.10+.

```bash
pip install -e .

# Validate a manifest (auto-selects schema based on manifest.schema_version)
python -m labki_packs_tools.validate_repo validate path/to/manifest.yml

Exit code is non-zero on validation errors (suitable for CI). Warnings do not change the exit code.

### Example

This repo ships a small sample under `tests/fixtures/basic_repo/`:

```bash
python -m labki_packs_tools.validate_repo validate tests/fixtures/basic_repo/manifest.yml
```

## Use in CI (content repo)

Add a job in the content repo (e.g., `labki-packs`) that installs Python deps and runs the validator.
The snippet below checks out this tools repo, installs it, and runs the validator using `python -m` (as in our CI):

```yaml
name: Validate content packs
on:
  pull_request:
    branches: ['**']
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
        run: pip install ./tools-cache
      - name: Validate manifest (auto schema)
        run: |
          # Auto schema selection based on manifest.schema_version
          export LABKI_SCHEMA_DIR=$GITHUB_WORKSPACE/tools-cache/schema
          python -m labki_packs_tools.validate_repo validate manifest.yml
      # Optional: validate with an explicit schema path (pin to a version)
      - name: Validate manifest (explicit schema path)
        run: |
          python -m labki_packs_tools.validate_repo validate manifest.yml tools-cache/schema/v1_0_0/manifest.schema.json
```