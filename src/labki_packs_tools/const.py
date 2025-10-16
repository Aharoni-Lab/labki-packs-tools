"""
const.py — Runtime constants for locating schemas and other package data.
This version safely handles both editable installs and direct source runs.
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------
# Schema directory resolution
# ---------------------------------------------------------------------


def _get_schema_dir() -> Path:
    """
    Resolve the location of the `schema` directory.

    Handles three cases:
    1. Installed package (schema inside site-packages)
    2. Editable install (`pip install -e .`)
    3. Running directly from source tree
    """
    here = Path(__file__).resolve()
    pkg_root = here.parent
    site_root = pkg_root.parent

    # Case 1: Installed package (look for schema as sibling to labki_packs_tools)
    installed_schema = site_root / "schema"
    if installed_schema.exists():
        return installed_schema

    # Case 2: Editable install with direct_url metadata
    for dist_info in site_root.glob("*.dist-info"):
        direct_url = dist_info / "direct_url.json"
        if direct_url.exists():
            try:
                data = json.loads(direct_url.read_text(encoding="utf-8"))
                if data.get("dir_info", {}).get("editable", False):
                    editable_schema = site_root / "schema"
                    if editable_schema.exists():
                        return editable_schema
            except Exception:
                pass

    # Case 3: Running directly from source (src/labki_packs_tools/const.py → ../../..)
    dev_schema = here.parent.parent.parent / "schema"
    if dev_schema.exists():
        return dev_schema

    raise RuntimeError(
        f"Could not resolve schema directory from {here}. "
        "Ensure schema files exist or install the package with `pip install -e .`."
    )


# ---------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------

SCHEMA_DIR = _get_schema_dir()
SCHEMA_INDEX = SCHEMA_DIR / "index.json"

__all__ = ["SCHEMA_DIR", "SCHEMA_INDEX"]
