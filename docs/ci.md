# CI integration

Validate a content repo (e.g., `labki-packs`) on every PR/push using this package.

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
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install labki-packs-tools
        run: pip install git+https://github.com/Aharoni-Lab/labki-packs-tools.git
      - name: Validate manifest (auto schema)
        run: |
          labki-validate validate manifest.yml
```

Notes:

- Fail the build on non-zero exit code.
- Consider caching the tools checkout with a pinned ref.
- To avoid PATH issues with console scripts, you can also run via modules: `python -m tools.validate_repo validate manifest.yml` (requires the package to be installed in the environment).

Optional: generate a graph artifact (DOT/SVG) and/or Mermaid/JSON from the same manifest.

```yaml
jobs:
  graph:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install git+https://github.com/Aharoni-Lab/labki-packs-tools.git
      - name: Generate DOT
        run: labki-graph manifest.yml --format dot --output graph.dot
      - name: Render SVG
        run: |
          sudo apt-get update && sudo apt-get install -y graphviz
          dot -Tsvg graph.dot -o graph.svg
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: pack-graph
          path: |
            graph.dot
            graph.svg

  graph-json-mermaid:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install git+https://github.com/Aharoni-Lab/labki-packs-tools.git
      - name: Generate Mermaid
        run: labki-graph manifest.yml --format mermaid --output graph.md
      - name: Generate JSON
        run: labki-graph manifest.yml --format json --output graph.json
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: pack-graph-text
          path: |
            graph.md
            graph.json
```
