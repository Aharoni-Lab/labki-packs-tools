# LabkiPackManager Development Plan

## Overview and Goals

LabkiPackManager integrates the `labki-packs` repository with MediaWiki 1.44 to import predefined wiki content (layouts, templates, forms) stored as `.wiki`/`.md` files. The upstream packs repo is `Aharoni-Lab/labki-packs` on GitHub.

### Key objectives

- Minimal MediaWiki extension structure visible on `Special:Version`. [Implemented]
- Special page `Special:LabkiPackManager` for admins. [Implemented]
- Fetch and parse root YAML manifest and display packs. [Implemented]
- Import `.wiki`/`.md` files directly as page text.
- Define `labkipackmanager-manage` right for access control.
- Plan for exporting changes back to the repo via PRs.

## Current Status

- Root manifest fetching via HTTP and YAML parsing implemented.
- Cached storage and refresh flow implemented.
- `Special:LabkiPackManager` lists available packs.
- Basic unit tests for manifest parsing, fetching, store, and i18n.

## Content Pack Repository Structure (labki-packs)

`labki-packs/` (GitHub: `Aharoni-Lab/labki-packs`)

- `manifest.yml` – v2 flat pages registry + hierarchical packs
- `README.md` – overview of how to use/update packs
- `schema/` – JSON/YAML schemas for validation
- `pages/` – flat directory of page files (optionally grouped by type)

### Pages and packs layout (v2)

- All page files live under the top-level `pages/` directory (flat). You may group by type for convenience.
- Packs are logical groups defined in the root `manifest.yml` under `packs`, referencing page titles from the global `pages` registry.

### Example

```text
packs/

├─ lab-operations/
│   ├─ manifest.yml             # optional local manifest (tracks sub-packs, version)
│   ├─ pages/
│   │   └─ safety_overview.wiki
│   ├─ equipment/
│   │   ├─ calibration/
│   │   │   ├─ microscope_pack/
│   │   │   │   ├─ pack.yml     # pack definition (name, version, dependencies)
│   │   │   │   └─ pages/
│   │   │   │       ├─ intro.wiki
│   │   │   │       └─ procedure.wiki
│   │   │   └─ scale_pack/
│   │   │       ├─ pack.yml
│   │   │       └─ pages/...
│   │   └─ maintenance_pack/
│   │       ├─ pack.yml
│   │       └─ pages/...
│   └─ training_pack/
│       ├─ pack.yml
│       └─ pages/...
│
└─ tool-development/
    ├─ imaging/
    │   └─ miniscope_pack/
    │       ├─ pack.yml
    │       └─ pages/...
    └─ acquisition_pack/
        ├─ pack.yml
        └─ pages/...
```

### Root-level manifest example (manifest.yml, v2)

```yaml
version: 2.0.0
last_updated: 2025-09-22

pages:
  Template:Microscope:
    file: pages/Templates/Template_Microscope.wiki
    type: template
    version: 1.0.0
  Form:Microscope:
    file: pages/Forms/Form_Microscope.wiki
    type: form
    version: 1.0.0

packs:
  lab-operations:
    description: Lab operations content
    pages:
      - Template:Microscope
    children:
      equipment:
        description: Equipment-related packs
        pages: []
```

### v1 vs v2

- v1: per-directory `pack.yml` files and nested `packs/` structure.
- v2: flat global `pages` registry in root manifest; packs reference titles and define hierarchy in the manifest.

### Notes

- Every directory under `packs/` is a pack with its own `pack.yml`.
- Leaf packs typically only have pages. Parent packs may have both pages and children.
- The root `manifest.yml` encodes hierarchy via `ref` pointers to each directory's `pack.yml` and optional nested `children`.
- `pages/` may contain `.wiki` or `.md` content files at any level.

## Steps

### Step 1: Bare-Bones Extension

- Directory: `extensions/LabkiPackManager/`
- Files: `extension.json`, `includes/`, `i18n/`, `README.md`
- Registration: `wfLoadExtension( 'LabkiPackManager' );`
- Verify on `Special:Version`.

### Step 2: Special Page (LabkiPackManager)

- Class: `LabkiPackManager\\Special\\SpecialLabkiPackManager` extending `SpecialPage`.
- Register via `extension.json` `SpecialPages`.
- Placeholder output confirming page loads.

### Step 3: Fetch Manifest (Implemented)

- Config: `LabkiContentManifestURL` (exposed as `$wgLabkiContentManifestURL`).
- Use MediaWiki HTTP facilities; parse YAML; handle errors.
- Future: recursively fetch folder-level manifests.

### Step 4: List Packs (UI) (Implemented)

- Render a form listing packs with checkboxes and CSRF token.
- Refresh control for re-fetch and cache.
- On POST, capture selected pack IDs for import.

### Step 5: Import `.wiki` Packs

- Config: `LabkiContentBaseURL` to construct raw file URLs.
- For each selected pack, fetch `pack.yml`, then fetch each file under `<pack>/pages/`.
- Save text via `WikiPageFactory` / `PageUpdater`.
- Provide success/error feedback per pack.

### Step 6: Permissions & Security

- Define `labkipackmanager-manage` right; grant to `sysop` by default.
- Restrict `Special:LabkiPackManager` accordingly.
- Validate POST token and selected IDs against the manifest.

### Step 7: Future Export & PRs

- Export selected pages’ wikitext.
- Commit to a new branch using GitHub REST API with `$wgLabkiGitHubToken`.
- Open a pull request and link back.

### Step 8: Testing & Docs

- PHPUnit tests for manifest parsing and import routines.
- GitHub Actions CI for PHPCS and PHPUnit.
- Expand README with Docker clone instructions and configuration.

## Docker Integration

- Clone this repository in your MediaWiki image build or bind mount under `extensions/LabkiPackManager`.
- Add `wfLoadExtension( 'LabkiPackManager' );` to `LocalSettings.php`.
