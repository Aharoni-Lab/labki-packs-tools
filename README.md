# labki-packs

Version-controlled content packs for Labki/MediaWiki. Pages are stored flat in the repository and referenced by a manifest that defines a flat packs registry with explicit dependencies. Each page has a canonical wiki title and its own version.

- Flat pages registry: `manifest.yml` maps canonical titles (e.g., `Template:Microscope`) to files in `pages/` with per-page version metadata
- Flat packs registry: `manifest.yml` lists packs with `version`, `pages` (titles), and `depends_on` (other packs)
- Optional groups tree: `manifest.yml` may define `groups` for navigation that reference pack ids
- Page files are stored under `pages/` (optionally grouped by type subfolders like `Templates/`, `Forms/`, `Categories/`, `Properties/`, `Layouts/`)

Upstream repository: `Aharoni-Lab/labki-packs` on GitHub.

## Repository structure

```text
labki-packs/
├─ manifest.yml          # Root registry (real content; minimal by default)
├─ README.md
├─ schema/               # JSON/YAML schemas for validation
├─ tools/                # Validation and utilities
├─ examples/
│  ├─ manifest.yml       # Example registry used for demos and tests
│  └─ pages/
│     ├─ Templates/
│     │  ├─ Template_Publication.wiki
│     │  └─ Template_MeetingNotes.wiki
│     ├─ Forms/
│     │  ├─ Form_Publication.wiki
│     │  └─ Form_MeetingNotes.wiki
│     ├─ Categories/
│     │  ├─ Category_Publication.wiki
│     │  └─ Category_Meeting.wiki
│     ├─ Properties/
│     │  └─ Property_Has author.wiki
│     └─ Layouts/
│        └─ Onboarding.md
└─ pages/                 # Real content lives here
```

## Root manifest (v2) – flat pages + flat packs (dependencies) + optional groups

Tracks a flat pages registry, a flat packs registry with explicit `depends_on`, and an optional `groups` tree for UI navigation.

```yaml
version: 2.0.0
last_updated: 2025-09-22

pages:
  Template:Publication:
    file: pages/Templates/Template_Publication.wiki
    type: template
    version: 1.0.0
  Form:Publication:
    file: pages/Forms/Form_Publication.wiki
    type: form
    version: 1.0.0
  Category:Publication:
    file: pages/Categories/Category_Publication.wiki
    type: category
    version: 1.0.0
  Property:Has author:
    file: pages/Properties/Property_Has author.wiki
    type: property
    version: 1.0.0
  Template:MeetingNotes:
    file: pages/Templates/Template_MeetingNotes.wiki
    type: template
    version: 1.0.0
  Form:MeetingNotes:
    file: pages/Forms/Form_MeetingNotes.wiki
    type: form
    version: 1.0.0
  Category:Meeting:
    file: pages/Categories/Category_Meeting.wiki
    type: category
    version: 1.0.0
  Onboarding:
    file: pages/Layouts/Onboarding.md
    type: layout
    version: 1.0.0

packs:
  publication:
    description: Templates and forms for managing publications
    version: 1.0.0
    pages:
      - Template:Publication
      - Form:Publication
      - Category:Publication
      - Property:Has author
    depends_on: []
  meeting_notes:
    description: Templates and forms for meeting notes
    version: 1.0.0
    pages:
      - Template:MeetingNotes
      - Form:MeetingNotes
      - Category:Meeting
    depends_on: []
  onboarding:
    description: Onboarding layout and example
    version: 1.0.0
    pages:
      - Onboarding
    depends_on: [publication]

groups:
  operations:
    description: Operational packs
    packs: [onboarding, meeting_notes]
    children:
      content:
        description: Content creation
        packs: [publication]
```

### Page file naming and Windows compatibility

Filenames on Windows cannot include `:`. Use Windows-safe filenames (e.g., `Template_Microscope.wiki`) and map them to canonical titles in the `pages` registry of `manifest.yml`. The canonical page title is the key (e.g., `Template:Microscope`).

## Using with LabkiPackManager

LabkiPackManager integrates this repository with MediaWiki 1.44.

- Fetches `manifest.yml` from the default content URL
- Displays groups (if present) and the packs registry on `Special:LabkiPackManager`
- On import, computes dependencies via `depends_on`, resolves pack `pages[]` titles to files via `pages` registry, and saves content to canonical titles
- Directly saves content to wiki pages (no XML imports)

Configuration keys (in `LocalSettings.php` via the extension):

- `$wgLabkiContentManifestURL`: raw URL to the target `manifest.yml` (use `examples/manifest.yml` for demo/testing)
- `$wgLabkiContentBaseURL`: base URL for raw file access (point to repo root; example files live under `examples/`)
- Right: `labkipackmanager-manage` (granted to `sysop` by default)

See `docs/usage.md` and `docs/overview.md`.

## How to add a new pack

1. Add page files under `pages/` (use type subfolders like `Templates/`, `Forms/`, etc.). Use Windows-safe filenames (no `:`), e.g., `Template_MyPage.wiki`.
2. In `manifest.yml` under `pages:`, add entries for each new page with canonical titles, `file`, `type`, and `version`.
3. Under `packs:`, create a new pack id with `version`, list its page titles in `pages:`, and add `depends_on` if it reuses other packs.
4. Optionally add the pack id to a `groups:` node to appear under a category in the UI.
5. Run validation:
   - `python tools/validate_repo.py validate-root manifest.yml schema/root-manifest.schema.json`
6. Commit and open a PR.

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
