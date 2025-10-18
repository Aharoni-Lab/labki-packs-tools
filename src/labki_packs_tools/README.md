# Labki Packs Tools

This package provides CLI tools for validating a Labki content pack manifest and generating a graph of packs/pages.

Tools:
- labki validate: Validate a manifest against the JSON Schema and repository rules (supports --json)
- labki graph: Emit a Graphviz DOT / Mermaid / JSON graph of packs and pages
- labki ingest: Ingest pages from a MediaWiki XML export to a manifest

Quick start (Windows PowerShell):

1. Create and activate a virtualenv

    ```powershell
    python -m venv .venv
    . .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    ```

2. Install the project in editable mode

    ```powershell
    python -m pip install -e .
    ```

3. Run the tools

    ```powershell
    # Validate a manifest (auto-selects schema based on schema_version)
    labki validate tests/fixtures/basic_repo/manifest.yml

    # JSON output (useful in CI)
    labki validate tests/fixtures/basic_repo/manifest.yml --json

    # Generate DOT graph from a manifest
    labki graph tests/fixtures/basic_repo/manifest.yml --format dot --output graph.dot
    ```

Other formats:

- Mermaid (for docs/readmes/GitHub rendering):

```powershell
labki graph tests/fixtures/basic_repo/manifest.yml --format mermaid --output graph.md
```

In Markdown, wrap the output with a mermaid code fence for preview:

```mermaid
graph LR
...
```

- JSON (for MediaWiki extension or other tooling):

```powershell
labki graph tests/fixtures/basic_repo/manifest.yml --format json --output graph.json
```

If the commands are not found, either re-activate the venv or use one of these options:
- Full path to console scripts:

```powershell
 .\.venv\Scripts\labki.exe validate tests/fixtures/basic_repo/manifest.yml --json
 .\.venv\Scripts\labki.exe graph tests/fixtures/basic_repo/manifest.yml --format dot --output graph.dot
```

- Module form (no console scripts needed):

```powershell
python -m labki_packs_tools.cli.main validate tests/fixtures/basic_repo/manifest.yml --json
python -m labki_packs_tools.cli.main graph tests/fixtures/basic_repo/manifest.yml --format dot --output graph.dot
```

Auto schema selection (from another repo using this tool):

```powershell
labki validate path\to\manifest.yml --json
```

Graph rendering (optional):
- Install Graphviz locally to render DOT → SVG/PNG

```powershell
winget install Graphviz.Graphviz
# or
choco install graphviz -y

dot -Tsvg graph.dot -o graph.svg
```

Notes:
- Shared YAML/JSON helpers live in `labki_packs_tools/utils/common.py`.
- For CI examples and additional outputs, see the repository root `README.md`.
