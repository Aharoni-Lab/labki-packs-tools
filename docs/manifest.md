# Manifest specification (v2)

## Root manifest (manifest.yml)

Fields:

- `version` (string): manifest schema/version of the registry (v2 and up)
- `last_updated` (date/string): informational timestamp
- `pages` (mapping): global flat registry of pages
  - key: canonical wiki title (e.g., `Template:Microscope`)
  - value: object with fields:
    - `file` (string): repository path to the file under `pages/`
    - `type` (string): one of `template|form|category|property|layout|other`
    - `version` (string): semantic version for this page
    - `description` (string, optional)
- `packs` (mapping): hierarchical tree of packs
  - Each key is a node id; value has:
    - `description` (string, optional)
    - `pages` (array of strings): list of page titles from the global `pages` registry
    - `children` (mapping, optional): nested packs with same structure

Example:

```yaml
version: 2.0.0
last_updated: 2025-09-22

pages:
  Template:Microscope:
    file: pages/Templates/Template_Microscope.wiki
    type: template
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

## Title resolution and filenames

- Canonical titles are the keys of the `pages` mapping; files are Windows-safe and live under `pages/`.
- Filenames must not include `:`. Use underscores around the namespace prefix in filenames, e.g., `Template_Microscope.wiki`.
- Importers do not guess titles from filenames in v2; they look up titles via the `pages` registry.

## Backward compatibility (v1)

In v1, the root manifest referenced directory-level `pack.yml` files, which in turn referenced file paths and titles. v2 centralizes page metadata into a flat registry and references titles from packs. During migration, tooling can read v1 and emit v2 with the same titles and files.
