# Conventions

## Layout (v2)

- All page files live under the top-level `pages/` directory.
- Optional type subfolders: `Templates/`, `Forms/`, `Categories/`, `Properties/`, `Layouts/`.
- Packs are defined only in the root `manifest.yml` under `packs` and reference titles from the global `pages` registry.
- Use `.wiki` for wikitext content and `.md` for Markdown content.

## Filenames and titles

- Avoid `:` in filenames (Windows-safe); use prefixes like `Template_`, `Form_`, etc.
- Canonical titles are defined in `manifest.yml` under `pages` keys; importers use this as the source of truth.
- One page per file.

## Templates, forms, properties, categories

- Templates (`Template:Name`) and forms (`Form:Name`) should be paired where applicable.
- Semantic properties should declare types (e.g., `[[Has type::Text]]`).
- Categories should include a concise description of scope and usage.

## Versioning

- Track per-page version in `manifest.yml` under `pages.*.version`.
- Use semantic versioning (MAJOR.MINOR.PATCH).
- Update `last_updated` when significant changes are merged.

## Style

- Keep wikitext minimal and portable.
- Avoid environment-specific hardcoding or external dependencies.
