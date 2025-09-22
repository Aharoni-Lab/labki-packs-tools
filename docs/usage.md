# Usage with LabkiPackManager

## Configure

- Set `$wgLabkiContentManifestURL` to the raw URL for this repository's `manifest.yml`.
- Set `$wgLabkiContentBaseURL` to the base raw URL for repository files.
- Ensure your admin account has `labkipackmanager-manage` rights (granted to `sysop` by default).

## Import packs

1. Visit `Special:LabkiPackManager`.
2. Click Refresh to fetch the latest manifest and cache it.
3. Browse the tree and select packs to import.
4. Submit to start the import.
5. Review success and error messages for each pack.

## How import works (v2)

- The extension fetches `manifest.yml` and reads the global `pages` registry and `packs` tree.
- When you select a pack, the importer resolves each title in `packs.*.pages[]` to its file via the `pages` registry.
- Content is fetched from `pages.*.file` and saved directly to the canonical title (no XML).

## Updating and removal

- To update, bump `pages.*.version` as appropriate and re-import the pack.
- Removal may require manual cleanup unless the extension provides uninstall flows.

## Troubleshooting

- Ensure YAML is valid; validate with `schema/` if provided.
- Verify the base URLs and network access.
- Check permissions and CSRF token validity.
