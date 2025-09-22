# Development

## Adding pages and packs (v2)
1. Add or edit files under the top-level `pages/` directory (group by type if desired).
2. In `manifest.yml`, add entries under `pages:` with canonical titles, file paths, `type`, and `version`.
3. Under `packs:`, reference the titles you want included in each pack and arrange nested packs under `children`.
4. Commit and open a PR.

## Extension development quickstart
1. Scaffold `extensions/LabkiPackManager/` with `extension.json`, `includes/`, `i18n/`.
2. Register and verify on `Special:Version`.
3. Implement `Special:LabkiPackManager` page to render list and refresh.
4. Implement manifest fetch/caching (HTTP + YAML parse).
5. Implement import (v2): resolve pack titles via root `manifest.yml` `pages` registry; fetch `file` and save via `PageUpdater`.
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
