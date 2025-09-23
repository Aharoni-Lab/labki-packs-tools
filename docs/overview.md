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

- `manifest.yml` – v2 flat pages registry + flat packs (with depends_on) + optional groups
- `README.md` – overview of how to use/update packs
- `schema/` – JSON/YAML schemas for validation
- `pages/` – flat directory of page files (optionally grouped by type)

### Pages, packs, and groups (v2)

- All page files live under the top-level `pages/` directory (flat). You may group by type for convenience.
- Packs are defined in the root `manifest.yml` under `packs` as a flat registry with `version`, `pages` (titles), and `depends_on` (other packs).
- Optional `groups` provide hierarchical navigation, each node listing `packs` by id and nested `children`.

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
  imaging:
    description: Imaging templates and forms
    version: 1.0.0
    pages:
      - Template:Microscope
      - Form:Microscope
    depends_on: []
  equipment:
    description: Equipment taxonomy and properties
    version: 1.0.0
    pages:
      - Category:Equipment
      - Property:Has component
    depends_on: []
  lab-operations:
    description: Operational content combining imaging and equipment
    version: 1.0.0
    pages: []
    depends_on: [imaging, equipment]

groups:
  operations:
    description: Operational packs
    packs: [lab-operations]
```

### v1 vs v2

- v1: per-directory `pack.yml` files and nested `packs/` structure.
- v2: flat global `pages` registry; flat `packs` with explicit `depends_on`; optional `groups` for navigation.

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
- For each selected pack, resolve dependencies via `depends_on`, then fetch each referenced file from the `pages` registry.
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
