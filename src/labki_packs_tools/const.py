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
    1. Installed package with direct_url.json metadata
    2. Editable install (`pip install -e .`)
    3. Running directly from source tree
    """
    here = Path(__file__).resolve()
    root = here.parent
    dist_info_dirs = list(root.glob("*.dist-info"))

    # Case 1: Installed package with metadata
    if dist_info_dirs:
        dist_info = dist_info_dirs[0]
        direct_url_path = dist_info / "direct_url.json"

        if direct_url_path.exists():
            try:
                direct_url_text = direct_url_path.read_text(encoding="utf-8")
                if direct_url_text:
                    direct_url = json.loads(direct_url_text)
                    is_editable = direct_url.get("dir_info", {}).get("editable", False)
                    if is_editable:
                        editable_schema = root / "schema"
                        if editable_schema.exists():
                            return editable_schema
            except Exception:
                # fall through to fallback below
                pass

        # Try packaged schema directory (inside site-packages)
        installed_schema = root / "schema"
        if installed_schema.exists():
            return installed_schema

    # Case 2: Running directly from repo (not installed)
    # Go three levels up: src/labki_packs_tools/ → src/ → project root → schema/
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
