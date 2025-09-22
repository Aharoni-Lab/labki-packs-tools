# Manifest specification

## Root manifest (manifest.yml)

Fields:
- `version` (string): manifest schema/version of the registry
- `last_updated` (date/string): informational timestamp
- `packs` (mapping): hierarchical tree of packs
  - Each key is a node id; value has:
    - `ref` (string): relative path to the node's `pack.yml`
    - `children` (mapping, optional): nested packs with same structure

Example:

```yaml
version: 1.0.0
last_updated: 2025-09-22
packs:
  lab-operations:
    ref: packs/lab-operations/pack.yml
    children:
      equipment:
        ref: packs/lab-operations/equipment/pack.yml
```

## Pack manifest (pack.yml)

Fields:
- `name` (string): human-friendly name (typically equals directory name)
- `version` (string): semantic version (MAJOR.MINOR.PATCH)
- `description` (string): brief description
- `pages` (array): list of page entries. Each entry can be either:
  - string: path to `.wiki`/`.md` file (e.g., `pages/foo.wiki`)
  - object: `{ file, title? , namespace?, name? }` to explicitly set the wiki page title
- `dependencies` (array of strings): extension requirements or other packs (informational)

Example parent pack:

```yaml
name: lab-operations
version: 2.1.0
description: "Guides and procedures for day-to-day lab operations."
pages:
  - pages/safety_overview.wiki
  - pages/general_policies.wiki
dependencies: []
```

Example intermediate/leaf pack:

```yaml
name: imaging
version: 2.0.0
description: "Imaging-related tools and methods."
pages: []
dependencies: []
```

### Page entries and title resolution

Because filenames may be Windows-safe (no `:`), use explicit mapping where necessary.

Allowed page entry formats:

```yaml
pages:
  # Explicit title mapping (preferred for namespaced pages)
  - file: pages/Template_Onboarding.wiki
    title: "Template:Onboarding"

  # Alternative explicit mapping via namespace + name
  - file: pages/Form_Onboarding.wiki
    namespace: Form
    name: Onboarding

  # Simple string file path (heuristic fallback)
  - pages/meeting_layout.md
```

Resolver order:
1. Use `title` if present.
2. Else combine `namespace` + `name`.
3. Else read leading comment `<!-- Title: Namespace:Name -->` in file.
4. Else derive from filename using project heuristics.

## Resolution rules
- The root `manifest.yml` is the source of truth for traversal; importers should follow `ref` to load `pack.yml`.
- `pages` entries are relative to the directory containing `pack.yml`.
- Importers may optionally validate structure using schemas under `schema/`.
