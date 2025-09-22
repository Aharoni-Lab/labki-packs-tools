# Development

## Adding a new pack to this repository
1. Create a new directory under `packs/your-pack/` (nested packs are allowed).
2. Add `pack.yml` with `name`, `version`, `description`, `pages`, `dependencies`.
3. Add pages under `packs/your-pack/pages/` as `.wiki` or `.md`.
4. Update the root `manifest.yml` to include a `ref` to the new `pack.yml` and nest it appropriately in `children`.
5. Commit and open a PR.

## Extension development quickstart
1. Scaffold `extensions/LabkiPackManager/` with `extension.json`, `includes/`, `i18n/`.
2. Register and verify on `Special:Version`.
3. Implement `Special:LabkiPackManager` page to render list and refresh.
4. Implement manifest fetch/caching (HTTP + YAML parse).
5. Implement import: resolve `pack.yml` and fetch `pages/` files; save via `PageUpdater`.
6. Add `labkipackmanager-manage` right and restrict access.
7. Add PHPUnit tests and GitHub Actions CI.
8. Document configuration and Docker integration.

## Testing
- Unit tests for YAML parsing, manifest traversal, and import logic.
- Integration tests against a local MediaWiki instance when feasible.

### Test title mapping
- Include cases where `pages:` entries specify `title`.
- Include cases with `namespace`+`name`.
- Include files with a leading `<!-- Title: Namespace:Name -->` comment.
- Include heuristic-only cases derived from filenames.

## CI
- Run PHPCS and PHPUnit on PRs.
- Optional: validate manifests with `schema/`.

## Docker integration
- Clone or mount the extension under `extensions/LabkiPackManager`.
- Add `wfLoadExtension( 'LabkiPackManager' );` to `LocalSettings.php`.
