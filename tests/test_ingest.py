from datetime import UTC, datetime

import pytest

from labki_packs_tools.ingest import update_manifest
from labki_packs_tools.manifest import Manifest


@pytest.mark.parametrize("export", ("latest.xml", "revisions.xml"))
def test_export_update(base_manifest, export_data, export):
    """
    Manifests can import pages from a mediawiki export

    - Add any new pages
    - Update any pages with older timestamps than in the export
    - Write new pages with a safe name
    - Touch updated at timestamps
    - Ignore non-updated pages
    """
    old_date = datetime(2020, 1, 1, tzinfo=UTC)
    future_date = datetime(2030, 1, 1, tzinfo=UTC)
    export_path = export_data / export

    # manifest with an old file to be updated,
    # a nonexistant file,
    # and a file more recent than the export
    manifest_path = base_manifest(
        {
            "last_updated": old_date,
            "pages": {
                # should not update
                "Category:Supply": {
                    "last_updated": future_date.isoformat(),
                    "file": "pages/category_supply.wiki",
                },
                # should update
                "Template:Supply": {"last_updated": old_date, "file": "pages/template_supply.wiki"},
            },
        }
    )

    updated = update_manifest(manifest_path, export_path)
    assert len(updated) == 3
    assert len(list((manifest_path.parent / "pages").glob("*.wiki"))) == 3
    manifest = Manifest.from_yaml(manifest_path)
    assert manifest.last_updated > old_date
    assert len(manifest.pages) == 4
    assert manifest.pages["Category:Supply"].last_updated == future_date


@pytest.mark.parametrize("export", ("latest.xml", "revisions.xml"))
def test_export_no_update(base_manifest, export_data, export):
    """
    For an export with pages that are older than all the pages in the manifest,
    we don't change anything
    """
    future_date = datetime(2030, 1, 1, tzinfo=UTC)
    export_path = export_data / export

    # all pages are in the future
    manifest_path = base_manifest(
        {
            "last_updated": future_date.isoformat(),
            "pages": {
                "Category:Supply": {
                    "last_updated": future_date.isoformat(),
                    "file": "pages/category_supply.wiki",
                },
                "Template:Supply": {
                    "last_updated": future_date.isoformat(),
                    "file": "pages/template_supply.wiki",
                },
                "Form:Supply": {
                    "last_updated": future_date.isoformat(),
                    "file": "pages/form_supply.wiki",
                },
                "Buffalo": {"last_updated": future_date.isoformat(), "file": "pages/buffalo.wiki"},
            },
        }
    )
    updated = update_manifest(manifest_path, export_path)
    assert len(updated) == 0
    assert len(list((manifest_path.parent / "pages").glob("*.wiki"))) == 0
    manifest = Manifest.from_yaml(manifest_path)
    assert manifest.last_updated == future_date
    assert len(manifest.pages) == 4
