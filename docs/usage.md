# Usage with LabkiPackManager

## Configure
- Set `$wgLabkiContentManifestURL` to the raw URL for this repository's `manifest.yml`.
- Set `$wgLabkiContentBaseURL` to the base raw URL for pack files.
- Ensure your admin account has `labkipackmanager-manage` rights (granted to `sysop` by default).

## Import packs
1. Visit `Special:LabkiPackManager`.
2. Click Refresh to fetch the latest manifest and cache it.
3. Browse the tree and select packs to import.
4. Submit to start the import.
5. Review success and error messages for each pack.

## How import works
- The extension fetches `pack.yml` for each selected node and traverses `pages:` entries.
- For each page entry:
  - If `title` is present, that becomes the wiki page title.
  - Else if `namespace` and `name` are present, the title is `Namespace:Name`.
  - Else if the file starts with `<!-- Title: Namespace:Name -->`, that title is used.
  - Else a heuristic derives a title from the filename (e.g., `Template_` -> `Template:`).
- The content is saved directly to the wiki (no XML). Existing pages are updated.

## Updating and removal
- To update, pull the latest manifest and re-import the same pack.
- Removal may require manual cleanup unless the extension provides uninstall flows.

## Troubleshooting
- Ensure YAML is valid; validate with `schema/` if provided.
- Verify the base URLs and network access.
- Check permissions and CSRF token validity.
