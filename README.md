# labki-packs

Hierarchical, version-controlled content packs for Labki/MediaWiki. Packs contain reusable wiki pages (templates, forms, categories, properties, layouts) stored as plain `.wiki` or `.md` files and indexed by YAML manifests for import via the LabkiPackManager extension.

- Root manifest: `manifest.yml` (hierarchical registry referencing each pack's `pack.yml`)
- Packs live under `packs/` and may be nested; every directory is a pack with its own `pack.yml`
- Pages live in a `pages/` folder under any pack directory

Upstream repository: `Aharoni-Lab/labki-packs` on GitHub.

## Repository structure

```
labki-packs/
├─ manifest.yml          # Root registry with tree of packs (refs to pack.yml)
├─ README.md
├─ schema/               # (optional) JSON/YAML schemas for validation
└─ packs/
   ├─ lab-operations/
   │  ├─ pack.yml
   │  ├─ pages/
   │  │  └─ safety_overview.wiki
   │  ├─ equipment/
   │  │  ├─ calibration/
   │  │  │  ├─ microscope_pack/
   │  │  │  │  ├─ pack.yml
   │  │  │  │  └─ pages/
   │  │  │  │     ├─ intro.wiki
   │  │  │  │     └─ procedure.wiki
   │  │  │  └─ scale_pack/
   │  │  │     ├─ pack.yml
   │  │  │     └─ pages/...
   │  │  └─ maintenance_pack/
   │  │     ├─ pack.yml
   │  │     └─ pages/...
   │  └─ training_pack/
   │     ├─ pack.yml
   │     └─ pages/...
   └─ tool-development/
      ├─ imaging/
      │  └─ miniscope_pack/
      │     ├─ pack.yml
      │     └─ pages/...
      └─ acquisition_pack/
         ├─ pack.yml
         └─ pages/...
```

## Root manifest (manifest.yml)

Tracks the hierarchy and points to each pack's `pack.yml` via `ref`. Parent nodes can include nested `children`.

```yaml
version: 1.0.0
last_updated: 2025-09-22

packs:
  lab-operations:
    ref: packs/lab-operations/pack.yml
    children:
      equipment:
        ref: packs/lab-operations/equipment/pack.yml
        children:
          calibration:
            ref: packs/lab-operations/equipment/calibration/pack.yml
            children:
              microscope_pack:
                ref: packs/lab-operations/equipment/calibration/microscope_pack/pack.yml
              scale_pack:
                ref: packs/lab-operations/equipment/calibration/scale_pack/pack.yml
          maintenance_pack:
            ref: packs/lab-operations/equipment/maintenance_pack/pack.yml
      training_pack:
        ref: packs/lab-operations/training_pack/pack.yml

  tool-development:
    ref: packs/tool-development/pack.yml
    children:
      imaging:
        ref: packs/tool-development/imaging/pack.yml
        children:
          miniscope_pack:
            ref: packs/tool-development/imaging/miniscope_pack/pack.yml
      acquisition_pack:
        ref: packs/tool-development/acquisition_pack/pack.yml
```

## Pack metadata (pack.yml)

Every directory under `packs/` is a pack and includes a `pack.yml` describing its contents and dependencies.

Example (parent pack):

```yaml
name: lab-operations
version: 2.1.0
description: "Guides and procedures for day-to-day lab operations."
pages:
  - pages/safety_overview.wiki
  - pages/general_policies.wiki
dependencies: []
```

Example (intermediate/leaf pack):

```yaml
name: imaging
version: 2.0.0
description: "Imaging-related tools and methods."
pages: []
dependencies: []
```

### Mapping Windows-safe filenames to namespaced titles

Filenames on Windows cannot include `:`. Use Windows-safe filenames and map them to canonical wiki titles in `pack.yml`.

`pages` supports either simple strings or objects:

- String: the importer derives the title from the filename using heuristics.
- Object: explicitly specify the canonical title. This is recommended for namespaced pages like `Template:...`, `Form:...`, `Category:...`, `Property:...`.

Examples:

```yaml
pages:
  # Explicit title mapping (recommended)
  - file: pages/Template_Onboarding.wiki
    title: "Template:Onboarding"
  - file: pages/Form_Onboarding.wiki
    title: "Form:Onboarding"
  - file: pages/Category_Onboarding.wiki
    title: "Category:Onboarding"
  - file: pages/Property_Has author.wiki
    title: "Property:Has author"

  # Alternative explicit form using namespace + name
  - file: pages/Template_Publication.wiki
    namespace: Template
    name: Publication

  # Simple string (heuristic fallback)
  - pages/meeting_layout.md
```

Resolver order used by importers:

1. If a page entry is an object with `title`, use it.
2. Else if it has `namespace` and `name`, construct `"<namespace>:<name>"`.
3. Else if the file contains a leading comment like `<!-- Title: Namespace:Name -->`, use it.
4. Else derive from filename (e.g., convert leading `Template_` to `Template:` and underscores to spaces after the colon).

## Using with LabkiPackManager

LabkiPackManager integrates this repository with MediaWiki 1.44.

- Fetches `manifest.yml` from the default content URL
- Displays the pack tree on `Special:LabkiPackManager`
- On import, fetches `pack.yml` for selected packs and pulls each file listed in `pages:`
- Directly saves content to wiki pages (no XML imports)

Configuration keys (in `LocalSettings.php` via the extension):

- `$wgLabkiContentManifestURL`: raw URL to root `manifest.yml`
- `$wgLabkiContentBaseURL`: base URL for raw file access
- Right: `labkipackmanager-manage` (granted to `sysop` by default)

See `docs/usage.md` and `docs/overview.md`.

## Conventions

- `.wiki` and `.md` are supported page formats
- Store pack pages under `pages/` within the pack directory
- For Windows compatibility, avoid `:` in filenames; if needed, mirror the intended wiki title inside the page content
- Use semantic versioning in `pack.yml` and reflect changes in the root manifest

## Development & CI

Development plan, testing, permissions, and Docker integration are documented in `docs/overview.md` and `docs/development.md`.

## License

TBD
