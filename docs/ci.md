# CI integration

Validate a content repo (e.g., `labki-packs`) on every PR/push.

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
      - name: Validate manifest (auto schema)
        run: |
          python tools-cache/tools/validate_repo.py validate manifest.yml
```

Notes:

- Fail the build on non-zero exit code.
- Consider caching the tools checkout with a pinned ref.
- A reusable GitHub Action is planned; update this doc when available.
