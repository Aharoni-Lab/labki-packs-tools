# Manifest specification (v2)

## Root manifest (manifest.yml)

Fields:

- `schema_version` (string): semantic version `MAJOR.MINOR.PATCH` used to select the schema
- `$schema` (string, optional): schema URL or path; if provided, it is used directly
- `last_updated` (string): ISO-like UTC timestamp `YYYY-MM-DDThh:mm:ssZ`
- `pages` (mapping): global flat registry of pages
  - key: canonical wiki title (e.g., `Template:Microscope`)
  - value: object with fields:
    - `file` (string): repository path to the file under `pages/`
    - `last_updated` (string): UTC timestamp `YYYY-MM-DDThh:mm:ssZ` when the page was last updated
Title keys and namespaces:
- Keys should follow [canonical page names](https://www.mediawiki.org/wiki/Manual:Page_naming#Canonical_form_of_page_names).
- Enforced by validator:
  - Use spaces, not underscores. Example: `"A Person"`, `"Template:A Person"` (underscores cause an error)
  - If no namespace is present (no `:`), a warning is emitted (still valid)
- Recommended (not strictly enforced):
  - Strip leading/trailing whitespace; normalize multiple spaces to one
  - Prefer unicode characters over percent-encoded sequences
  - Capitalize the first letter of a namespace (if present) and the first letter of the page
- The namespace is inferred from the key prefix before `:` (e.g., `Module:`, `Help:`, `MediaWiki:`).
  - `description` (string, optional)
- `packs` (mapping): flat registry of packs
  - Each key is a pack id; value has:
    - `description` (string, optional)
    - `version` (string, required): semantic version for the pack
    - `pages` (array of strings): page titles from the global `pages` registry
    - `depends_on` (array of strings, optional): pack ids this pack depends on. Each string must be a pack id, a key that exists under `packs`.
    - `tags` (array of strings, optional): free-form labels to aid discovery/filtering (e.g., `core`, `imaging`)

Example (aligned to validator and schema):

```yaml
schema_version: 1.0.0
last_updated: 2025-09-22T00:00:00Z

pages:
  Template:Publication:
    file: pages/Templates/Template_Publication.wiki
    last_updated: 2025-09-22T00:00:00Z
  Form:Publication:
    file: pages/Forms/Form_Publication.wiki
    last_updated: 2025-09-22T00:00:00Z

packs:
  publication:
    description: Templates and forms for managing publications
    version: 1.0.0
    pages: [Template:Publication, Form:Publication]
    depends_on: []
```

## Title resolution and filenames

- Canonical titles are the keys of the `pages` mapping; files are Windows-safe and live under `pages/`.
- Filenames must not include `:` (validator error). Use underscores around the namespace prefix in filenames, e.g., `Template_Microscope.wiki`.
- Importers do not guess titles from filenames in v2; they look up titles via the `pages` registry.

## Additional validation behavior (summary)

- Schema selection:
  - `schema_version` must be exact-matched in `schema/index.json` when using `auto` selection.
  - `$schema` may override schema selection via absolute or relative path.
- Pages:
  - Each page requires `file` and `last_updated` (UTC `YYYY-MM-DDThh:mm:ssZ`).
  - File must exist and must not contain `:`.
  - `Module:` pages: warnings suggest `.lua` extension and `pages/Modules/` location.
  - Orphan `.wiki`/`.md` files under `pages/` emit warnings.
- Packs:
  - `version` must be semantic `MAJOR.MINOR.PATCH`.
  - `pages` must be an array of known titles (unique within a pack by schema).
  - `depends_on` pack ids must exist; dependency cycles are rejected.
  - A page cannot be included by multiple packs (error).
  - `tags` must be lowercase slug strings (`^[a-z0-9-]+$`) and unique.

## Backward compatibility (v1)

In v1, the repository manifest referenced directory-level `pack.yml` files, which in turn referenced file paths and titles. v2 centralizes page metadata into a flat registry and references titles from packs. During migration, tooling can read v1 and emit v2 with the same titles and files.
