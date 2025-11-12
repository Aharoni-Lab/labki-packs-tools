# labki-packs-tools

CLI validator and JSON Schemas for Labki/MediaWiki content packs. Use this in CI or locally to validate a content repository like `labki-packs`.

## What it validates (v1)

- Manifest structure (`schema_version`, `name`, `pages`, `packs`) against the JSON Schema.
- Pages: required `file` and `last_updated` timestamp; Windows-safe filenames; file existence.
- Packs: required semantic version, page titles exist, dependency sanity and cycle detection.
- Additional conventions (warnings), e.g., `Module:` pages should be `.lua` under `pages/Modules/`.

## Quickstart (local)

Requires Python 3.10+.

```bash
pip install -e .

# Validate a manifest (auto-selects schema based on schema_version)
labki validate path/to/manifest.yml

# JSON output (suitable for CI ingestion)
labki validate path/to/manifest.yml --json

# Generate a graph of packs and pages
labki graph path/to/manifest.yml --format dot --output graph.dot

# Ingest pages from MediaWiki export
labki ingest path/to/export.xml

Exit code is non-zero on validation errors (suitable for CI). Warnings do not change the exit code.

### Example

This repo ships a small sample under `tests/fixtures/basic_repo/`:

```bash
labki validate tests/fixtures/basic_repo/manifest.yml
```

## Use in CI (content repo)

Add a job in the content repo (e.g., `labki-packs`) that installs Python deps and runs the validator.
Save the workflow as `.github/workflows/validate.yml` in your content repository.
The snippet below checks out this tools repo, installs it, and runs the validator:

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

      - name: Checkout validator tools
        uses: actions/checkout@v4
        with:
          repository: Aharoni-Lab/labki-packs-tools
          path: tools-cache

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Labki validator
        run: |
          pip install ./tools-cache
          # Copy schema files into installed package for runtime discovery
          site=$(python -c "import site; print(site.getsitepackages()[0])")
          mkdir -p "$site/labki_packs_tools/schema"
          cp -r tools-cache/schema/* "$site/labki_packs_tools/schema/"

      - name: Validate manifest
        id: validate
        run: |
          # schema_version field inside manifest.yml determines which schema is used
          export LABKI_SCHEMA_DIR=$GITHUB_WORKSPACE/tools-cache/schema
          set -o pipefail
          labki validate manifest.yml | tee validation.txt
        continue-on-error: true

      - name: Comment on PR with validation results
        if: ${{ github.event_name == 'pull_request' && steps.validate.outcome != 'success' }}
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('validation.txt', 'utf8');
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: [
                '### Labki validator output',
                '',
                '```',
                body.trim(),
                '```'
              ].join('\n')
            });

      - name: Fail if validation failed
        if: ${{ steps.validate.outcome != 'success' }}
        run: exit 1
```

### Repository Health Badge

You can add a badge to your content repository to show validation status:

```markdown
[![Validate content packs](https://github.com/your-org/your-content-repo/workflows/Validate%20content%20packs/badge.svg)](https://github.com/your-org/your-content-repo/actions/workflows/validate.yml)
```

**Important:** The badge URL uses the workflow **name** (not filename) with spaces encoded as `%20`. Replace `your-org/your-content-repo` with your actual repository details.

If your workflow name is different, update the badge URL accordingly. For example:
- Workflow name: `Content Validation` → URL: `.../workflows/Content%20Validation/badge.svg`
- Workflow name: `Validate` → URL: `.../workflows/Validate/badge.svg`
