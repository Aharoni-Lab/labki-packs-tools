# Conventions

## Layout
- Every directory under `packs/` is a pack and includes a `pack.yml`.
- Packs may contain a `pages/` folder with one file per page.
- Use `.wiki` for wikitext content and `.md` for Markdown content.

## Filenames and titles
- Avoid `:` in filenames for cross-platform compatibility (Windows).
- Prefer explicit mapping in `pack.yml` using `pages:` entries with `title` or `namespace`+`name`.
- Optionally include a first-line comment `<!-- Title: Namespace:Name -->` inside the file as a secondary hint.
- One page per file.

## Templates, forms, properties, categories
- Templates (`Template:Name`) and forms (`Form:Name`) should be paired where applicable.
- Semantic properties should declare types (e.g., `[[Has type::Text]]`).
- Categories should include a concise description of scope and usage.

## Versioning
- Use semantic versioning (MAJOR.MINOR.PATCH) in each `pack.yml`.
- Keep the root `manifest.yml` up-to-date and maintain `last_updated`.

## Style
- Keep wikitext minimal and portable.
- Avoid environment-specific hardcoding or external dependencies.
