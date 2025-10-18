from pathlib import Path

import yaml

from labki_packs_tools.manifest import Manifest


def test_manifest_roundtrip_yaml(fixtures_repo: Path):
    """
    Test that the Manifest roundtrips a manifest correctly
    """
    manifest_path = fixtures_repo / "manifest.yml"
    with open(manifest_path) as f:
        data = yaml.safe_load(f)

    model = Manifest.from_yaml(manifest_path)
    dumped = model.model_dump(exclude_unset=True)
    assert dumped == data
