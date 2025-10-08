import json

import pytest

pytestmark = pytest.mark.packaging


def test_schema_dir():
    """
    Schema dir is within the site-packages directory rather than the repo root,
    and it contains the schema
    """
    from labki_packs_tools.const import SCHEMA_DIR, SCHEMA_INDEX

    assert "site-packages" in str(SCHEMA_DIR)
    assert SCHEMA_DIR.exists()
    assert SCHEMA_INDEX.exists()
    with open(SCHEMA_INDEX) as jfile:
        index = json.load(jfile)
    with open(SCHEMA_DIR / index["latest"]) as jfile:
        latest = json.load(jfile)

    # boolean assert is enough here, we just want to confirm it contains something
    assert latest
