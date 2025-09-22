# labki-packs

Hierarchical, version-controlled content packs for Labki/MediaWiki. Pages are stored flat in this repository and referenced by a manifest that defines packs and nested packs. Each page has a canonical wiki title and its own version.

- Flat pages registry: `manifest.yml` maps canonical titles (e.g., `Template:Microscope`) to files in `pages/` with per-page version metadata
- Packs live only in `manifest.yml` as a tree referencing titles from the pages registry
- Page files are stored under `pages/` (optionally grouped by type subfolders like `Templates/`, `Forms/`, `Categories/`, `Properties/`, `Layouts/`)

Upstream repository: `Aharoni-Lab/labki-packs` on GitHub.

## Repository structure

```text
labki-packs/
├─ manifest.yml          # Root registry: pages (flat) + packs (hierarchy of includes)
├─ README.md
├─ schema/               # JSON/YAML schemas for validation
├─ tools/                # Validation and utilities
└─ pages/
   ├─ Templates/
   │  ├─ Template_Microscope.wiki      # -> title: Template:Microscope
   │  └─ Template_Scale.wiki           # -> title: Template:Scale
   ├─ Forms/
   │  ├─ Form_Microscope.wiki          # -> title: Form:Microscope
   │  └─ Form_Scale.wiki               # -> title: Form:Scale
   ├─ Categories/
   │  └─ Category_Equipment.wiki       # -> title: Category:Equipment
   ├─ Properties/
   │  └─ Property_Has component.wiki   # -> title: Property:Has component
   └─ Layouts/
      └─ MeetingNotes.md               # -> title: Meeting Notes
```

## Root manifest (v2) – flat pages + hierarchical packs

Tracks a flat pages registry and a packs tree that includes titles from that registry.

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
  Category:Equipment:
    file: pages/Categories/Category_Equipment.wiki
    type: category
    version: 1.0.0
  Property:Has component:
    file: pages/Properties/Property_Has component.wiki
    type: property
    version: 1.0.0

packs:
  lab-operations:
    description: Lab operations content
    pages:
      - Template:Microscope
      - Form:Microscope
    children:
      equipment:
        description: Equipment-related packs
        pages:
          - Category:Equipment
```

### Page file naming and Windows compatibility

Filenames on Windows cannot include `:`. Use Windows-safe filenames (e.g., `Template_Microscope.wiki`) and map them to canonical titles in the `pages` registry of `manifest.yml`. The canonical page title is the key (e.g., `Template:Microscope`).

## Using with LabkiPackManager

LabkiPackManager integrates this repository with MediaWiki 1.44.

- Fetches `manifest.yml` from the default content URL
- Displays the pack tree on `Special:LabkiPackManager`
- On import, resolves `packs.*.pages[]` titles to files via `pages` registry and saves content as the canonical title
- Directly saves content to wiki pages (no XML imports)

Configuration keys (in `LocalSettings.php` via the extension):

- `$wgLabkiContentManifestURL`: raw URL to root `manifest.yml`
- `$wgLabkiContentBaseURL`: base URL for raw file access
- Right: `labkipackmanager-manage` (granted to `sysop` by default)

See `docs/usage.md` and `docs/overview.md`.

## Conventions

- `.wiki` and `.md` are supported page formats
- Store all page files under `pages/` (optionally grouped by type subfolders)
- Titles are defined in the manifest `pages` registry (keys)
- Track per-page `version` in the registry; use semantic versioning

## Development & CI

- Schemas for `manifest.yml` live under `schema/`
- CI validates YAML, Markdown, schema conformance, and repo rules via `tools/validate_repo.py`

## Legacy (v1) model

Older manifests referenced per-directory `pack.yml` files via `packs.*.ref` and stored pages beside each pack. The v2 model supersedes this with a flat pages registry and per-page versioning. The validator can detect and warn on v1 content during migration.

## License

TBD
