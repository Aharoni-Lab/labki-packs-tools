# Manifest specification (v2)

## Root manifest (manifest.yml)

Fields:

- `version` (string): semantic version `MAJOR.MINOR.PATCH`
- `last_updated` (string): ISO-like timestamp `YYYY-MM-DDThh:mm:ssZ`
- `pages` (mapping): global flat registry of pages
  - key: canonical wiki title (e.g., `Template:Microscope`)
  - value: object with fields:
    - `file` (string): repository path to the file under `pages/`
    - `type` (string): one of `template|form|category|property|layout|module|help|mediawiki|other`
    - `version` (string): semantic version for this page
    - `description` (string, optional)
- `packs` (mapping): flat registry of packs
  - Each key is a pack id; value has:
    - `description` (string, optional)
    - `version` (string, required): semantic version for the pack
    - `pages` (array of strings): page titles from the global `pages` registry
    - `depends_on` (array of strings, optional): pack ids this pack depends on. Each string must be a key that exists under `packs`.
    - `tags` (array of strings, optional): free-form labels to aid discovery/filtering (e.g., `core`, `imaging`)
 

Example (aligned to repository samples; using `tests/fixtures/basic_repo/manifest.yml`):

```yaml
version: 2.0.0
last_updated: 2025-09-22T00:00:00Z

pages:
  Template:Publication:
    file: pages/Templates/Template_Publication.wiki
    type: template
    version: 1.0.0
  Form:Publication:
    file: pages/Forms/Form_Publication.wiki
    type: form
    version: 1.0.0

packs:
  publication:
    description: Templates and forms for managing publications
    version: 1.0.0
    pages: [Template:Publication, Form:Publication]
    depends_on: []

 
```

## Title resolution and filenames

- Canonical titles are the keys of the `pages` mapping; files are Windows-safe and live under `pages/`.
- Filenames must not include `:`. Use underscores around the namespace prefix in filenames, e.g., `Template_Microscope.wiki`.
- Importers do not guess titles from filenames in v2; they look up titles via the `pages` registry.

## Backward compatibility (v1)

In v1, the repository manifest referenced directory-level `pack.yml` files, which in turn referenced file paths and titles. v2 centralizes page metadata into a flat registry and references titles from packs. During migration, tooling can read v1 and emit v2 with the same titles and files.
