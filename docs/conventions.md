# Conventions

## Layout (v2)

- All page files live under the top-level `pages/` directory.
- Optional type subfolders: `Templates/`, `Forms/`, `Categories/`, `Properties/`, `Layouts/`, `Modules/`.
- Packs are defined in the root `manifest.yml` under a flat `packs` registry with `version`, `pages` (titles), and `depends_on` (other packs).
- Optional `groups` provide hierarchical navigation for the UI and reference pack ids.
- Use `.wiki` for wikitext content and `.md` for Markdown content.
- Lua modules use `.lua` files under `pages/Modules/` and titles in the `Module:` namespace.

## Filenames and titles

- Avoid `:` in filenames (Windows-safe); use prefixes like `Template_`, `Form_`, etc.
- Canonical titles are defined in `manifest.yml` under `pages` keys; importers use this as the source of truth.
- One page per file.

## Templates, forms, properties, categories

- Templates (`Template:Name`) and forms (`Form:Name`) should be paired where applicable.
- Semantic properties should declare types (e.g., `[[Has type::Text]]`).
- Categories should include a concise description of scope and usage.

## Modules, Help, MediaWiki

- `module`: Use `Module:` namespace titles and store files under `pages/Modules/` with `.lua` extension.
- `help`: Use `Help:` namespace titles for user-facing documentation.
- `mediawiki`: Use `MediaWiki:` namespace titles for system messages; handle carefully due to site-wide impact.

## Versioning

- Track per-page version in `manifest.yml` under `pages.*.version`.
- Use semantic versioning (MAJOR.MINOR.PATCH).
- Update `last_updated` when significant changes are merged.

## Packs and shared pages

- Do not duplicate the same page title in multiple packs. If two packs need the same page, move it into a common pack and reference it via `depends_on`.
- Each pack's `pages` list must not contain duplicates (enforced by schema) and duplicates across packs are flagged by the validator.

## Style

- Keep wikitext minimal and portable.
- Avoid environment-specific hardcoding or external dependencies.
